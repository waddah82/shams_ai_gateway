"""Generate and maintain Markdown files for SAG Skill records."""

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional

import frappe
from frappe import _
from frappe.utils import get_files_path

SKILL_FILES_FOLDER = "Home/SAG Skills"


def build_skill_markdown(skill_doc) -> str:
    """Return canonical installable SKILL.md content for an SAG Skill."""
    content = (skill_doc.content or "").strip()
    if content.startswith("---"):
        closing = content.find("\n---", 3)
        if closing != -1:
            content = content[closing + 4 :].lstrip("\r\n")

    description = " ".join((skill_doc.description or "").split())
    frontmatter = (
        "---\n"
        f"name: {skill_doc.skill_id}\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        "---\n"
    )
    return f"{frontmatter}\n{content.rstrip()}\n"


def _file_name(skill_id: str) -> str:
    return f"{skill_id}.md"


def _matches_generated_file(file_name: str, skill_id: str) -> bool:
    """Return whether file_name is the canonical or legacy suffixed Skill file."""
    pattern = re.compile(rf"^{re.escape(skill_id)}(?:[0-9a-f]{{6}})?\.md$")
    return bool(pattern.match(file_name or ""))


def _existing_generated_files(skill_doc) -> List[str]:
    folder_files = frappe.get_all(
        "File",
        filters={
            "folder": SKILL_FILES_FOLDER,
            "is_folder": 0,
        },
        fields=["name", "file_name"],
        ignore_permissions=True,
    )
    legacy_files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "SAG Skill",
            "attached_to_name": skill_doc.name,
        },
        fields=["name", "file_name"],
        ignore_permissions=True,
    )
    # Frappe may append a six-character hexadecimal suffix when a physical
    # filename already exists, e.g. delete-document-usage4ff906.md. Treat
    # both that form and the original deterministic name as generated files.
    matches = {
        row.name
        for row in [*folder_files, *legacy_files]
        if _matches_generated_file(row.file_name, skill_doc.skill_id)
    }
    return sorted(matches)


def delete_skill_files(skill_id: str, skill_name: Optional[str] = None) -> Dict[str, Any]:
    """Delete canonical and legacy Markdown files for one SAG Skill."""
    rows = frappe.get_all(
        "File",
        filters={"folder": SKILL_FILES_FOLDER, "is_folder": 0},
        fields=["name", "file_name"],
        ignore_permissions=True,
    )
    if skill_name:
        rows += frappe.get_all(
            "File",
            filters={"attached_to_doctype": "SAG Skill", "attached_to_name": skill_name},
            fields=["name", "file_name"],
            ignore_permissions=True,
        )

    matched = {
        row.name: row.file_name
        for row in rows
        if _matches_generated_file(row.file_name, skill_id)
    }
    removed_files = set()
    for file_doc_name, file_name in matched.items():
        physical_path = get_files_path(file_name, is_private=1)
        frappe.delete_doc("File", file_doc_name, ignore_permissions=True, force=True)
        if os.path.isfile(physical_path):
            os.remove(physical_path)
        removed_files.add(file_name)

    # Remove an orphan canonical file even if its File record was lost.
    canonical_name = _file_name(skill_id)
    canonical_path = get_files_path(canonical_name, is_private=1)
    if os.path.isfile(canonical_path):
        os.remove(canonical_path)
        removed_files.add(canonical_name)

    return {
        "success": True,
        "skill_id": skill_id,
        "status": "deleted" if removed_files else "missing",
        "removed_files": sorted(removed_files),
    }


def _delete_files_not_in_manifest(published_skill_ids: set[str]) -> List[str]:
    """Remove generated files not represented by the published Skill manifest."""
    rows = frappe.get_all(
        "File",
        filters={"folder": SKILL_FILES_FOLDER, "is_folder": 0},
        fields=["name", "file_name"],
        ignore_permissions=True,
    )
    removed = set()
    for row in rows:
        file_name = row.file_name or ""
        if not file_name.endswith(".md"):
            continue

        is_canonical = any(file_name == _file_name(skill_id) for skill_id in published_skill_ids)
        if is_canonical:
            continue

        physical_path = get_files_path(file_name, is_private=1)
        frappe.delete_doc("File", row.name, ignore_permissions=True, force=True)
        if os.path.isfile(physical_path):
            os.remove(physical_path)
        removed.add(file_name)

    # Clean orphan files for known unpublished SAG Skill records.
    inactive_ids = frappe.get_all(
        "SAG Skill",
        filters={"status": ["!=", "Published"]},
        pluck="skill_id",
        ignore_permissions=True,
    )
    for skill_id in inactive_ids:
        canonical_name = _file_name(skill_id)
        canonical_path = get_files_path(canonical_name, is_private=1)
        if os.path.isfile(canonical_path):
            os.remove(canonical_path)
            removed.add(canonical_name)

    return sorted(removed)


def _ensure_skill_files_folder() -> None:
    """Create the generated-skills File Manager folder when missing."""
    if frappe.db.exists("File", {"is_folder": 1, "file_name": "SAG Skills", "folder": "Home"}):
        return

    folder = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": "SAG Skills",
            "is_folder": 1,
            "folder": "Home",
        }
    )
    folder.insert(ignore_permissions=True)


def sync_skill_file(skill_doc, *, require_published: bool = True) -> Dict[str, Any]:
    """Create or replace one generated Markdown file without duplicates."""
    if require_published and skill_doc.status != "Published":
        return delete_skill_files(skill_doc.skill_id, skill_doc.name)

    markdown = build_skill_markdown(skill_doc)
    content = markdown.encode("utf-8")
    checksum = hashlib.sha256(content).hexdigest()
    existing_names = _existing_generated_files(skill_doc)
    desired_name = _file_name(skill_doc.skill_id)
    desired_url = f"/private/files/{desired_name}"
    _ensure_skill_files_folder()

    if len(existing_names) == 1:
        existing = frappe.get_doc("File", existing_names[0])
        existing_content = existing.get_content()
        if isinstance(existing_content, str):
            existing_content = existing_content.encode("utf-8")
        if existing_content == content and existing.file_name == desired_name:
            return {
                "success": True,
                "skill_id": skill_doc.skill_id,
                "status": "unchanged",
                "file_name": existing.file_name,
                "file_url": existing.file_url,
                "folder": existing.folder,
                "checksum": checksum,
            }

    # Never overwrite an unrelated File record merely to claim its filename.
    exact_file = frappe.db.get_value(
        "File",
        {"file_url": desired_url},
        ["name", "folder", "attached_to_doctype", "attached_to_name"],
        as_dict=True,
    )
    if exact_file and not (
        exact_file.folder == SKILL_FILES_FOLDER
        or (
            exact_file.attached_to_doctype == "SAG Skill"
            and exact_file.attached_to_name == skill_doc.name
        )
    ):
        frappe.throw(
            _("Cannot generate '{0}' because that filename belongs to another File record").format(
                desired_name
            )
        )

    # Replace generated files so there is exactly one File record and its
    # filename always equals <skill_id>.md.
    for file_name in existing_names:
        frappe.delete_doc("File", file_name, ignore_permissions=True, force=True)

    # save_file() deliberately makes a filename unique and may append a
    # six-character hash. Generated Skill files need deterministic names, so
    # write the canonical private file atomically and register its exact URL.
    physical_path = get_files_path(desired_name, is_private=1)
    temporary_path = f"{physical_path}.{frappe.generate_hash(length=10)}.tmp"
    with open(temporary_path, "wb") as file_handle:
        file_handle.write(content)
    os.replace(temporary_path, physical_path)

    file_doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": desired_name,
            "file_url": desired_url,
            "is_private": 1,
            "folder": SKILL_FILES_FOLDER,
            "file_size": len(content),
            "content_hash": checksum,
        }
    )
    # The physical file was already written above. A normal File.insert()
    # runs File hooks that write it again and append a uniqueness suffix.
    # Register the exact URL directly so File Manager points to the canonical
    # file without creating a second physical copy.
    file_doc.db_insert()
    return {
        "success": True,
        "skill_id": skill_doc.skill_id,
        "status": "created" if not existing_names else "updated",
        "file_name": file_doc.file_name,
        "file_url": file_doc.file_url,
        "folder": file_doc.folder,
        "checksum": checksum,
    }


def sync_published_skill_files(skill_id: Optional[str] = None) -> Dict[str, Any]:
    """Synchronize one or every published SAG Skill Markdown file."""
    filters: Dict[str, Any] = {"status": "Published"}
    if skill_id:
        filters["skill_id"] = skill_id

    rows = frappe.get_all(
        "SAG Skill",
        filters=filters,
        fields=["name", "skill_id"],
        order_by="skill_id asc",
        ignore_permissions=True,
    )
    if skill_id and not rows:
        frappe.throw(_("Published SAG Skill '{0}' was not found").format(skill_id))

    results = [sync_skill_file(frappe.get_doc("SAG Skill", row.name)) for row in rows]
    manifest_ids = [row.skill_id for row in rows]
    removed_files = [] if skill_id else _delete_files_not_in_manifest(set(manifest_ids))
    return {
        "success": True,
        "count": len(results),
        "created": sum(row["status"] == "created" for row in results),
        "updated": sum(row["status"] == "updated" for row in results),
        "unchanged": sum(row["status"] == "unchanged" for row in results),
        "removed": len(removed_files),
        "removed_files": removed_files,
        "authoritative_manifest": not bool(skill_id),
        "skill_ids": manifest_ids,
        "client_sync_policy": {
            "install_missing": True,
            "update_matching": True,
            "remove_absent": not bool(skill_id),
            "content_tool": "get_sag_skill_file",
            "note": (
                "A client may mirror this manifest into its native Skills only when that "
                "client exposes Skill installation and removal capabilities."
            ),
        },
        "files": results,
    }


def get_skill_file(skill_id: str, include_content: bool = True) -> Dict[str, Any]:
    """Return the generated file metadata and optionally its Markdown content."""
    skill_name = frappe.db.get_value(
        "SAG Skill", {"skill_id": skill_id, "status": "Published"}, "name"
    )
    if not skill_name:
        frappe.throw(_("Published SAG Skill '{0}' was not found").format(skill_id))

    skill_doc = frappe.get_doc("SAG Skill", skill_name)
    if not skill_doc.has_permission("read"):
        frappe.throw(_("You do not have permission to read this SAG Skill"), frappe.PermissionError)

    desired_name = _file_name(skill_id)
    desired_url = f"/private/files/{desired_name}"
    desired_path = get_files_path(desired_name, is_private=1)

    # Always prefer the deterministic <skill_id>.md file. Older versions of
    # the exporter could leave a File record with a six-character suffix, and
    # sorting File document names does not reliably select the exact file.
    exact_file_name = frappe.db.get_value("File", {"file_url": desired_url}, "name")
    if exact_file_name:
        file_doc = frappe.get_doc("File", exact_file_name)
        content_source = file_doc.get_content
        file_name = file_doc.file_name
        file_url = file_doc.file_url
        folder = file_doc.folder
    elif os.path.isfile(desired_path):
        # The physical file can exist even when an earlier sync failed to
        # create or update its File record. It is still the canonical Skill
        # file and must take precedence over legacy suffixed records.
        file_doc = None
        content_source = lambda: _read_private_file(desired_path)
        file_name = desired_name
        file_url = desired_url
        folder = SKILL_FILES_FOLDER
    else:
        file_names = _existing_generated_files(skill_doc)
        file_doc = frappe.get_doc("File", file_names[0]) if file_names else None
        if file_doc:
            content_source = file_doc.get_content
            file_name = file_doc.file_name
            file_url = file_doc.file_url
            folder = file_doc.folder

    if not file_doc and not os.path.isfile(desired_path):
        return {
            "success": False,
            "skill_id": skill_id,
            "error": "Generated Markdown file is missing. Ask an Assistant Admin to synchronize it.",
        }

    result = {
        "success": True,
        "skill_id": skill_id,
        "title": skill_doc.title,
        "description": skill_doc.description,
        "file_name": file_name,
        "file_url": file_url,
        "folder": folder,
        "modified": skill_doc.modified,
    }
    if include_content:
        content = content_source()
        result["content"] = content.decode("utf-8") if isinstance(content, bytes) else content
    return result


def _read_private_file(path: str) -> bytes:
    """Read a canonical generated Skill file from the private files directory."""
    with open(path, "rb") as file_handle:
        return file_handle.read()

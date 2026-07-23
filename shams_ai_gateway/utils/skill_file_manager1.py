"""Generate and maintain Markdown files for SAG Skill records."""

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional

import frappe
from frappe import _
from frappe.utils import get_files_path
from frappe.utils.file_manager import save_file

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
    pattern = re.compile(rf"^{re.escape(skill_doc.skill_id)}(?:[0-9a-f]{{6}})?\.md$")
    matches = {
        row.name
        for row in [*folder_files, *legacy_files]
        if pattern.match(row.file_name or "")
    }
    return sorted(matches)


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
        return {
            "success": False,
            "skill_id": skill_doc.skill_id,
            "status": "skipped",
            "reason": "Skill is not Published",
        }

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

    # Replace generated files so there is exactly one File record and
    # its filename always equals <skill_id>.md. Frappe can leave an untracked
    # physical file after older attempts; remove it only when no File record
    # references the deterministic URL.
    for file_name in existing_names:
        frappe.delete_doc("File", file_name, ignore_permissions=True, force=True)

    if not frappe.db.exists("File", {"file_url": desired_url}):
        physical_path = get_files_path(desired_name, is_private=1)
        if os.path.isfile(physical_path):
            os.remove(physical_path)

    file_doc = save_file(
        desired_name,
        content,
        None,
        None,
        folder=SKILL_FILES_FOLDER,
        is_private=1,
    )
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
        fields=["name"],
        order_by="skill_id asc",
        ignore_permissions=True,
    )
    if skill_id and not rows:
        frappe.throw(_("Published SAG Skill '{0}' was not found").format(skill_id))

    results = [sync_skill_file(frappe.get_doc("SAG Skill", row.name)) for row in rows]
    return {
        "success": True,
        "count": len(results),
        "created": sum(row["status"] == "created" for row in results),
        "updated": sum(row["status"] == "updated" for row in results),
        "unchanged": sum(row["status"] == "unchanged" for row in results),
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

    file_names = _existing_generated_files(skill_doc)
    if not file_names:
        return {
            "success": False,
            "skill_id": skill_id,
            "error": "Generated Markdown file is missing. Ask an Assistant Admin to synchronize it.",
        }

    file_doc = frappe.get_doc("File", file_names[0])
    result = {
        "success": True,
        "skill_id": skill_id,
        "title": skill_doc.title,
        "description": skill_doc.description,
        "file_name": file_doc.file_name,
        "file_url": file_doc.file_url,
        "folder": file_doc.folder,
        "modified": skill_doc.modified,
    }
    if include_content:
        content = file_doc.get_content()
        result["content"] = content.decode("utf-8") if isinstance(content, bytes) else content
    return result
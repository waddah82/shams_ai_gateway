"""MCP tool for synchronizing SAG Skill Markdown files."""

from typing import Any, Dict

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool
from shams_ai_gateway.utils.skill_file_manager import sync_published_skill_files


class SyncSAGSkillFiles(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "sync_sag_skill_files"
        self.description = (
            "Mirror published SAG Skills into private Markdown files in the "
            "ERPNext File Manager folder Home/SAG Skills. "
            "A full synchronization creates or updates published Skills and deletes Markdown "
            "files for Skills that are unpublished or absent. The response is an authoritative "
            "manifest: AI clients with native Skill-management capabilities should install "
            "missing Skills, update matching Skills via get_sag_skill_file, and remove installed "
            "Skills absent from skill_ids. Clients without native Skill-management APIs must "
            "report that limitation instead of claiming installation or removal."
        )
        self.requires_permission = "SAG Skill"
        self.inputSchema = {
            "type": "object",
            "properties": {
                "skill_id": {
                    "type": "string",
                    "description": "Optional SAG Skill ID. Omit to synchronize every published skill.",
                }
            },
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # This tool operates on local files and cannot run on a remote site.
        target_url = getattr(frappe.local, "target_site_url", None)
        if target_url:
            return {
                "success": False,
                "error": "The sync_sag_skill_files tool is not available for remote sites. It operates on the central gateway's file system only.",
            }

        if not frappe.has_permission("SAG Skill", "write"):
            frappe.throw(_("Write permission on SAG Skill is required"), frappe.PermissionError)
        return sync_published_skill_files((arguments.get("skill_id") or "").strip() or None)


sync_sag_skill_files = SyncSAGSkillFiles
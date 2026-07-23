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
            "Generate or update private Markdown files for published SAG Skills in ERPNext. "
            "Use when an administrator asks to update, rebuild, or synchronize Skill files. "
            "Repeated runs update changed files without accumulating duplicates."
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
        if not frappe.has_permission("SAG Skill", "write"):
            frappe.throw(_("Write permission on SAG Skill is required"), frappe.PermissionError)
        return sync_published_skill_files((arguments.get("skill_id") or "").strip() or None)


sync_sag_skill_files = SyncSAGSkillFiles

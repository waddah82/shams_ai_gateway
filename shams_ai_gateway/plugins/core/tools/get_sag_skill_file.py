"""MCP tool for retrieving generated SAG Skill Markdown files."""

from typing import Any, Dict

from shams_ai_gateway.core.base_tool import BaseTool
from shams_ai_gateway.utils.skill_file_manager import get_skill_file


class GetSAGSkillFile(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "get_sag_skill_file"
        self.description = (
            "Retrieve the generated Markdown file for a published SAG Skill from ERPNext. "
            "Use when users ask to load, read, or download a Skill by skill_id. Returns its "
            "private file URL and, by default, the complete Markdown content."
        )
        self.requires_permission = "SAG Skill"
        self.inputSchema = {
            "type": "object",
            "properties": {
                "skill_id": {
                    "type": "string",
                    "description": "Published SAG Skill ID, for example delete-document-usage.",
                },
                "include_content": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include the complete Markdown content in the response.",
                },
            },
            "required": ["skill_id"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        target_url = getattr(frappe.local, "target_site_url", None)
        if target_url:
            return {
                "success": False,
                "error": "The get_sag_skill_file tool is not available for remote sites. It reads local files only.",
            }
        return get_skill_file(
            arguments["skill_id"].strip(),
            include_content=arguments.get("include_content", True),
        )


get_sag_skill_file = GetSAGSkillFile
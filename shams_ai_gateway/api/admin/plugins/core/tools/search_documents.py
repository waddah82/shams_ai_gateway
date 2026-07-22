# (license header unchanged)
"""
Search Documents Tool for Core Plugin.
Global search across all accessible documents.
"""

from typing import Any, Dict

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool


class SearchDocuments(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "search_documents"
        self.description = "Global search across all accessible documents"
        self.requires_permission = None

        self.inputSchema = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "default": 20, "description": "Maximum results"},
            },
            "required": ["query"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from .search_tools import SearchTools
            target_url = getattr(frappe.local, "target_site_url", None)
            return SearchTools.global_search(
                query=arguments.get("query"),
                limit=arguments.get("limit", 20),
                site_url=target_url,
            )
        except Exception as e:
            frappe.log_error(title=_("Search Documents Error"), message=f"Error searching documents: {str(e)}")
            return {"success": False, "error": str(e)}


search_documents = SearchDocuments
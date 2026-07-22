# (license header unchanged)
"""
Search DocType Tool for Core Plugin.
Search within a specific DocType with permission-aware results.
"""

from typing import Any, Dict

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool


class SearchDoctype(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "search_doctype"
        self.description = "Search within a specific DocType"
        self.requires_permission = None

        self.inputSchema = {
            "type": "object",
            "properties": {
                "doctype": {"type": "string", "description": "DocType to search in"},
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "default": 20, "description": "Maximum results"},
            },
            "required": ["doctype", "query"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from .search_tools import SearchTools
            target_url = getattr(frappe.local, "target_site_url", None)
            return SearchTools.search_doctype(
                doctype=arguments.get("doctype"),
                query=arguments.get("query"),
                limit=arguments.get("limit", 20),
                site_url=target_url,
            )
        except Exception as e:
            frappe.log_error(title=_("Search DocType Error"), message=f"Error searching DocType: {str(e)}")
            return {"success": False, "error": str(e)}


search_doctype = SearchDoctype
# (license header unchanged)
"""
Search Link Tool for Core Plugin.
Search for link field options with filtering.
"""

from typing import Any, Dict

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool


class SearchLink(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "search_link"
        self.description = "Search for link field options"
        self.requires_permission = None

        self.inputSchema = {
            "type": "object",
            "properties": {
                "doctype": {"type": "string", "description": "Target DocType for link"},
                "query": {"type": "string", "description": "Search query"},
                "filters": {"type": "object", "default": {}, "description": "Additional filters"},
            },
            "required": ["doctype", "query"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from .search_tools import SearchTools
            target_url = getattr(frappe.local, "target_site_url", None)
            return SearchTools.search_link(
                doctype=arguments.get("doctype"),
                query=arguments.get("query"),
                filters=arguments.get("filters", {}),
                site_url=target_url,
            )
        except Exception as e:
            frappe.log_error(title=_("Search Link Error"), message=f"Error searching link options: {str(e)}")
            return {"success": False, "error": str(e)}


search_link = SearchLink
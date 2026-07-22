# (license header unchanged)
"""
Get DocType Info Tool for Core Plugin.
Get DocType metadata and field information.
"""

from typing import Any, Dict

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool


class GetDoctypeInfo(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "get_doctype_info"
        self.description = "Get DocType metadata and field information"
        self.requires_permission = None

        self.inputSchema = {
            "type": "object",
            "properties": {"doctype": {"type": "string", "description": "DocType name"}},
            "required": ["doctype"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from .metadata_tools import MetadataTools
            target_url = getattr(frappe.local, "target_site_url", None)
            return MetadataTools.get_doctype_metadata(doctype=arguments.get("doctype"), site_url=target_url)
        except Exception as e:
            frappe.log_error(title=_("Get DocType Info Error"), message=f"Error getting DocType info: {str(e)}")
            return {"success": False, "error": str(e)}


get_doctype_info = GetDoctypeInfo
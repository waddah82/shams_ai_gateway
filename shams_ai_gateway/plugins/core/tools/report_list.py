# (license header unchanged)
"""
Report List Tool for Core Plugin.
Discover available Frappe reports for business intelligence.
"""

from typing import Any, Dict

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool


class ReportList(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "report_list"
        self.description = "Discover and search available Frappe business reports across all modules..."
        self.requires_permission = None

        self.inputSchema = {
            "type": "object",
            "properties": {
                "module": {
                    "type": "string",
                    "description": "Filter by Frappe module (e.g., 'Accounts', 'Selling', 'Stock', 'HR', 'CRM'). Leave empty to see all modules.",
                },
                "report_type": {
                    "type": "string",
                    "enum": ["Report Builder", "Query Report", "Script Report"],
                    "description": "Filter by report type...",
                },
            },
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from .report_tools import ReportTools
            target_url = getattr(frappe.local, "target_site_url", None)
            return ReportTools.list_reports(
                module=arguments.get("module"),
                report_type=arguments.get("report_type"),
                site_url=target_url,
            )
        except Exception as e:
            frappe.log_error(title=_("Report List Error"), message=f"Error listing reports: {str(e)}")
            return {"success": False, "error": str(e)}


report_list = ReportList
# (license header unchanged)
"""
Generate Report Tool for Core Plugin.
Execute Frappe reports for business data and analytics.
"""

from typing import Any, Dict

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool


class GenerateReport(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "generate_report"
        self.description = "Execute a Frappe report..."
        self.requires_permission = None

        self.inputSchema = {
            "type": "object",
            "properties": {
                "report_name": {
                    "type": "string",
                    "description": "Exact name of the Frappe report to execute...",
                },
                "filters": {
                    "type": "object",
                    "default": {},
                    "description": "Filter key-value pairs...",
                },
                "format": {
                    "type": "string",
                    "enum": ["json", "csv", "excel"],
                    "default": "json",
                    "description": "Output format...",
                },
            },
            "required": ["report_name"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from .report_tools import ReportTools
            target_url = getattr(frappe.local, "target_site_url", None)
            return ReportTools.execute_report(
                report_name=arguments.get("report_name"),
                filters=arguments.get("filters", {}),
                format=arguments.get("format", "json"),
                site_url=target_url,
            )
        except Exception as e:
            frappe.log_error(title=_("Generate Report Error"), message=f"Error generating report: {str(e)}")
            return {"success": False, "error": str(e)}


generate_report = GenerateReport
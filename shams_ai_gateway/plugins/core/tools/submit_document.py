# Shams AI Gateway - AI Assistant integration for Frappe Framework
# Copyright (C) 2025 Paul Clinton
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Document Submit Tool for Core Plugin.
Submits draft documents after validation.
"""

from typing import Any, Dict

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool
from shams_ai_gateway.core.utils import remote_frappe_call


class DocumentSubmit(BaseTool):
    """
    Tool for submitting draft documents.

    Provides capabilities for:
    - Submitting draft documents
    - Validating submission permissions
    - Providing workflow guidance
    """

    def __init__(self):
        super().__init__()
        self.name = "submit_document"
        self.description = "Submit a draft document after validation. Only works with documents in draft state (docstatus=0). Use when users want to finalize a document."
        self.requires_permission = None  # Permission checked dynamically per DocType

        self.inputSchema = {
            "type": "object",
            "properties": {
                "doctype": {
                    "type": "string",
                    "description": "The Frappe DocType name (e.g., 'Customer', 'Sales Invoice', 'Item')",
                },
                "name": {
                    "type": "string",
                    "description": "The document name/ID to submit (e.g., 'CUST-00001', 'SINV-00001')",
                },
            },
            "required": ["doctype", "name"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a draft document, optionally on a remote site."""
        target_url = getattr(frappe.local, "target_site_url", None)

        doctype = arguments.get("doctype")
        name = arguments.get("name")

        if target_url:
            # Remote submission via frappe.client.submit API
            res = remote_frappe_call(
                target_url,
                "frappe.client.submit",
                params={"doc": {"doctype": doctype, "name": name}},
                http_method="POST"
            )
            if isinstance(res, dict) and "message" in res:
                return {"success": True, "message": res["message"], "doctype": doctype, "name": name}
            return {"success": False, "error": res.get("error") or res.get("message", "Remote submission failed")}

        # Local execution (original code unchanged)
        from shams_ai_gateway.core.security_config import validate_document_access

        validation_result = validate_document_access(
            user=frappe.session.user, doctype=doctype, name=name, perm_type="submit"
        )

        if not validation_result["success"]:
            return validation_result

        user_role = validation_result["role"]

        try:
            if not frappe.db.exists(doctype, name):
                return {"success": False, "error": f"{doctype} '{name}' not found"}

            doc = frappe.get_doc(doctype, name)
            current_docstatus = getattr(doc, "docstatus", 0)
            current_workflow_state = getattr(doc, "workflow_state", None)

            if current_docstatus != 0:
                state_description = {1: "submitted", 2: "cancelled"}.get(current_docstatus, "unknown")
                return {
                    "success": False,
                    "error": f"Cannot submit {state_description} document {doctype} '{name}'. Only draft documents can be submitted.",
                    "docstatus": current_docstatus,
                    "workflow_state": current_workflow_state,
                    "suggestion": f"Document is already {state_description}. Use document_get to view its current state.",
                }

            meta = frappe.get_meta(doctype)
            if not getattr(meta, "is_submittable", False):
                return {
                    "success": False,
                    "error": f"{doctype} is not a submittable DocType",
                    "suggestion": f"Only submittable DocTypes can be submitted. {doctype} doesn't support submission.",
                }

            doc.submit()
            doc.reload()
            updated_docstatus = getattr(doc, "docstatus", 0)
            updated_workflow_state = getattr(doc, "workflow_state", None)

            result = {
                "success": True,
                "name": doc.name,
                "doctype": doctype,
                "docstatus": updated_docstatus,
                "state_description": "Submitted" if updated_docstatus == 1 else "Unknown",
                "workflow_state": updated_workflow_state,
                "owner": doc.owner,
                "modified": str(doc.modified),
                "modified_by": doc.modified_by,
                "message": f"{doctype} '{doc.name}' submitted successfully",
            }

            if updated_docstatus == 1:
                result["next_steps"] = [
                    "Document is now submitted and read-only",
                    "Use document_get to view the submitted document",
                    f"Submit permissions: {'Available' if frappe.has_permission(doctype, 'cancel') else 'Not available'} for cancellation",
                ]
                if updated_workflow_state:
                    result["next_steps"].append(f"Current workflow state: {updated_workflow_state}")
            else:
                result["next_steps"] = [
                    f"Submission may have failed - document status: {updated_docstatus}",
                    "Check document validation errors or permissions",
                ]

            return result

        except Exception as e:
            frappe.log_error(
                title=_("Document Submit Error"), message=f"Error submitting {doctype} '{name}': {str(e)}"
            )
            return {
                "success": False,
                "error": str(e),
                "doctype": doctype,
                "name": name,
                "suggestion": "Check if the document has all required fields filled and passes validation.",
            }


document_submit = DocumentSubmit
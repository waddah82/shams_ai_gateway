# (license header unchanged)
"""
Comprehensive workflow tool that properly uses Frappe's workflow system.
...
"""

from typing import Any, Dict

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool
from shams_ai_gateway.core.utils import remote_frappe_call


class RunWorkflow(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "run_workflow"
        self.description = "Execute workflow actions on documents (Submit, Approve, Reject, etc.)..."
        self.requires_permission = None

        self.inputSchema = {
            "type": "object",
            "properties": {
                "doctype": {
                    "type": "string",
                    "description": "Document type (e.g., 'Sales Order', 'Purchase Order')",
                },
                "name": {"type": "string", "description": "Document name/ID"},
                "action": {
                    "type": "string",
                    "description": "Exact workflow action name to execute...",
                },
                "workflow": {
                    "type": "string",
                    "description": "Workflow name (optional - will be auto-detected)",
                },
            },
            "required": ["doctype", "name", "action"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        target_url = getattr(frappe.local, "target_site_url", None)

        doctype = arguments.get("doctype")
        name = arguments.get("name")
        action = arguments.get("action")
        workflow_name = arguments.get("workflow")

        if target_url:
            # Remote workflow: call the apply_workflow method
            res = remote_frappe_call(
                target_url,
                "frappe.model.workflow.apply_workflow",
                params={
                    "doc": frappe.get_doc(doctype, name).as_dict(),
                    "action": action,
                },
                http_method="POST"
            )
            if isinstance(res, dict) and "message" in res:
                return {"success": True, "message": res["message"]}
            return {"success": False, "error": res.get("error") or res.get("message", "Remote workflow failed")}

        # Local execution (original code unchanged)
        try:
            if not frappe.db.exists(doctype, name):
                return {"success": False, "error": f"Document {doctype} '{name}' not found"}

            doc = frappe.get_doc(doctype, name)
            original_state = getattr(doc, "workflow_state", None)

            if not workflow_name:
                from frappe.model.workflow import get_workflow_name
                workflow_name = get_workflow_name(doctype)
                if not workflow_name:
                    return {
                        "success": False,
                        "error": f"No workflow configured for {doctype}",
                        "explanation": f"The {doctype} document type doesn't have any workflows set up...",
                        "suggestion": "Use the 'update_document' tool instead to modify document fields directly...",
                    }

            available_transitions = self._get_available_transitions(doc, workflow_name)
            available_actions = [t.get("action") for t in available_transitions]
            if action not in available_actions:
                return {
                    "success": False,
                    "error": f"Action '{action}' is not available for document in state '{original_state}'",
                    "explanation": ...,
                    "current_state": original_state,
                    "available_actions": available_actions,
                    "transitions_details": available_transitions,
                    "suggestion": f"Try one of these available actions: {', '.join(available_actions) if available_actions else 'None available'}",
                }

            from frappe.model.workflow import apply_workflow
            before_docstatus = doc.docstatus
            updated_doc = apply_workflow(doc, action)
            new_state = getattr(updated_doc, "workflow_state", None)
            new_docstatus = updated_doc.docstatus

            changes = []
            if original_state != new_state:
                changes.append(f"State: {original_state} ? {new_state}")
            if before_docstatus != new_docstatus:
                status_names = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
                changes.append(f"Status: {status_names[before_docstatus]} ? {status_names[new_docstatus]}")

            return {
                "success": True,
                "message": f"Workflow action '{action}' executed successfully",
                "changes": changes,
                "document": {
                    "doctype": doctype,
                    "name": name,
                    "previous_state": original_state,
                    "current_state": new_state,
                    "docstatus": new_docstatus,
                },
                "workflow": workflow_name,
                "next_available_actions": [
                    t.get("action") for t in self._get_available_transitions(updated_doc, workflow_name)
                ],
            }

        except frappe.exceptions.WorkflowTransitionError as e:
            try:
                doc = frappe.get_doc(doctype, name)
                available_transitions = self._get_available_transitions(doc, workflow_name)
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": "WorkflowTransitionError",
                    "current_state": getattr(doc, "workflow_state", None),
                    "available_actions": [t.get("action") for t in available_transitions],
                    "help": "Check available actions and try again with a valid action",
                }
            except Exception:
                return {"success": False, "error": str(e), "error_type": "WorkflowTransitionError"}

        except frappe.exceptions.WorkflowPermissionError as e:
            return {"success": False, "error": str(e), "error_type": "WorkflowPermissionError", "help": "You don't have permission to execute this workflow action"}

        except Exception as e:
            frappe.log_error(title=_("Workflow Execution Error"), message=f"Error executing workflow action: {str(e)}")
            return {"success": False, "error": f"Workflow execution failed: {str(e)}", "error_type": "ExecutionError"}

    def _get_available_transitions(self, doc, workflow_name):
        # unchanged
        try:
            from frappe.model.workflow import get_transitions
            transitions = get_transitions(doc)
            enhanced_transitions = []
            for t in transitions:
                enhanced_transitions.append({
                    "action": t.get("action"),
                    "next_state": t.get("next_state"),
                    "allowed_roles": t.get("allowed", "").split(",") if t.get("allowed") else [],
                    "condition": t.get("condition"),
                    "allow_self_approval": t.get("allow_self_approval", 0),
                })
            return enhanced_transitions
        except Exception as e:
            frappe.log_error(f"Error getting workflow transitions: {e}")
            return []

    def _get_workflow_info(self, doc, workflow_name):
        # unchanged
        try:
            workflow_doc = frappe.get_doc("Workflow", workflow_name)
            current_state = getattr(doc, workflow_doc.workflow_state_field, None)
            state_info = {}
            for state in workflow_doc.states:
                if state.state == current_state:
                    state_info = {
                        "state": state.state,
                        "doc_status": state.doc_status,
                        "allow_edit": state.allow_edit,
                        "is_optional_state": getattr(state, "is_optional_state", 0),
                    }
                    break
            return {
                "workflow_name": workflow_name,
                "current_state": current_state,
                "state_info": state_info,
                "workflow_field": workflow_doc.workflow_state_field,
            }
        except Exception as e:
            frappe.log_error(f"Error getting workflow info: {e}")
            return {"workflow_name": workflow_name}


run_workflow = RunWorkflow
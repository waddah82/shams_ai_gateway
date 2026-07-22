# (license header unchanged)
"""
Pending Approvals Discovery Tool for Core Plugin.
Queries Workflow Actions to find documents awaiting the current user's approval.
"""

from typing import Any, Dict

import frappe
from frappe import _
from frappe.query_builder import DocType

from shams_ai_gateway.core.base_tool import BaseTool

MAX_TRANSITION_DOCS = 20


class GetPendingApprovals(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "get_pending_approvals"
        self.description = (
            "Get documents pending the current user's approval..."
        )
        self.requires_permission = None

        self.inputSchema = {
            "type": "object",
            "properties": {
                "doctype": {
                    "type": "string",
                    "description": "Optional: filter to a specific doctype...",
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "maximum": 200,
                    "description": "Maximum number of pending actions to return. Default 50.",
                },
                "include_actions": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include available workflow actions...",
                },
            },
            "required": [],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        target_url = getattr(frappe.local, "target_site_url", None)
        if target_url:
            return {"success": False, "error": "The get_pending_approvals tool is not available for remote sites."}

        # Local execution (original code unchanged)
        doctype_filter = arguments.get("doctype")
        limit = min(arguments.get("limit", 50), 200)
        include_actions = arguments.get("include_actions", True)

        user = frappe.session.user
        roles = frappe.get_roles(user)

        WA = DocType("Workflow Action")
        WAPR = DocType("Workflow Action Permitted Role")

        role_subquery = (
            frappe.qb.from_(WA)
            .join(WAPR)
            .on(WA.name == WAPR.parent)
            .select(WA.name)
            .where(WAPR.role.isin(roles))
        )

        query = (
            frappe.qb.from_(WA)
            .select(
                WA.name,
                WA.reference_doctype,
                WA.reference_name,
                WA.workflow_state,
                WA.user,
                WA.creation,
            )
            .where(WA.status == "Open")
            .orderby(WA.creation, order=frappe.qb.desc)
            .limit(limit)
        )

        if user != "Administrator":
            query = query.where(WA.name.isin(role_subquery) | (WA.user == user))

        if doctype_filter:
            query = query.where(WA.reference_doctype == doctype_filter)

        try:
            pending_actions = query.run(as_dict=True)
        except Exception as e:
            frappe.log_error(title=_("Pending Approvals Query Error"), message=str(e))
            return {"success": False, "error": str(e)}

        if not pending_actions:
            return {
                "success": True,
                "total_pending": 0,
                "doctypes_with_pending": [],
                "pending_approvals": {},
                "message": "No documents pending your approval",
            }

        action_names = [a.name for a in pending_actions]
        all_roles = frappe.get_all(
            "Workflow Action Permitted Role",
            filters={"parent": ["in", action_names]},
            fields=["parent", "role"],
        )
        roles_map: Dict[str, list] = {}
        for r in all_roles:
            roles_map.setdefault(r.parent, []).append(r.role)

        transitions_map: Dict[tuple, list] = {}
        if include_actions:
            seen = set()
            for action in pending_actions:
                key = (action.reference_doctype, action.reference_name)
                if key in seen:
                    continue
                seen.add(key)
                if len(seen) > MAX_TRANSITION_DOCS:
                    break
                try:
                    from frappe.model.workflow import get_transitions
                    doc = frappe.get_doc(action.reference_doctype, action.reference_name)
                    transitions = get_transitions(doc)
                    transitions_map[key] = [
                        {"action": t.get("action"), "next_state": t.get("next_state")} for t in transitions
                    ]
                except Exception:
                    transitions_map[key] = []

        grouped: Dict[str, list] = {}
        for action in pending_actions:
            dt = action.reference_doctype
            key = (dt, action.reference_name)
            entry = {
                "document_name": action.reference_name,
                "workflow_state": action.workflow_state,
                "permitted_roles": roles_map.get(action.name, []),
                "creation": str(action.creation),
            }
            if include_actions and key in transitions_map:
                entry["available_actions"] = transitions_map[key]
            grouped.setdefault(dt, []).append(entry)

        actions_truncated = (
            include_actions
            and len({(a.reference_doctype, a.reference_name) for a in pending_actions}) > MAX_TRANSITION_DOCS
        )

        result = {
            "success": True,
            "total_pending": len(pending_actions),
            "doctypes_with_pending": list(grouped.keys()),
            "pending_approvals": grouped,
            "message": f"Found {len(pending_actions)} document(s) pending your approval across {len(grouped)} document type(s)",
        }

        if actions_truncated:
            result["actions_truncated"] = True
            result["actions_truncated_note"] = (
                f"Available actions shown for first {MAX_TRANSITION_DOCS} documents only. "
                "Use include_actions=false or filter by doctype for full lists."
            )

        return result


get_pending_approvals = GetPendingApprovals
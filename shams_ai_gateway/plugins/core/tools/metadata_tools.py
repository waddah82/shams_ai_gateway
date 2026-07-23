# (license header unchanged)
from typing import Any, Dict, List

import frappe
from frappe import _
from shams_ai_gateway.core.utils import remote_frappe_call


class MetadataTools:
    """assistant tools for Frappe metadata operations"""

    @staticmethod
    def get_tools() -> List[Dict]:
        """Return list of metadata-related assistant tools"""
        return [
            {
                "name": "get_doctype_info",
                "description": "Get DocType metadata and field information",
                "inputSchema": {
                    "type": "object",
                    "properties": {"doctype": {"type": "string", "description": "DocType name"}},
                    "required": ["doctype"],
                },
            },
            {
                "name": "metadata_list_doctypes",
                "description": "List all available DocTypes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "module": {"type": "string", "description": "Filter by module"},
                        "custom_only": {
                            "type": "boolean",
                            "default": False,
                            "description": "Show only custom DocTypes",
                        },
                    },
                },
            },
            {
                "name": "metadata_permissions",
                "description": "Get permission information for a DocType",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "doctype": {"type": "string", "description": "DocType name"},
                        "user": {"type": "string", "description": "User to check permissions for (optional)"},
                    },
                    "required": ["doctype"],
                },
            },
            {
                "name": "metadata_workflow",
                "description": "Get workflow information for a DocType",
                "inputSchema": {
                    "type": "object",
                    "properties": {"doctype": {"type": "string", "description": "DocType name"}},
                    "required": ["doctype"],
                },
            },
        ]

    @staticmethod
    def execute_tool(tool_name: str, arguments: Dict[str, Any], site_url: str = None) -> Dict[str, Any]:
        """Execute a metadata tool with given arguments, optionally on a remote site."""
        if tool_name == "get_doctype_info":
            return MetadataTools.get_doctype_metadata(site_url=site_url, **arguments)
        elif tool_name == "metadata_list_doctypes":
            return MetadataTools.list_doctypes(site_url=site_url, **arguments)
        elif tool_name == "metadata_permissions":
            return MetadataTools.get_permissions(site_url=site_url, **arguments)
        elif tool_name == "metadata_workflow":
            return MetadataTools.get_workflow(site_url=site_url, **arguments)
        else:
            raise Exception(f"Unknown metadata tool: {tool_name}")

    @staticmethod
    def _serialize_field(field) -> Dict[str, Any]:
        """Serialize a DocField row into the shape returned by get_doctype_metadata."""
        return {
            "fieldname": field.fieldname,
            "label": field.label,
            "fieldtype": field.fieldtype,
            "options": field.options,
            "reqd": field.reqd,
            "read_only": field.read_only,
            "hidden": field.hidden,
            "default": field.default,
            "description": field.description,
        }

    @staticmethod
    def get_doctype_metadata(doctype: str, site_url: str = None) -> Dict[str, Any]:
        """Get DocType metadata and field information, optionally remote."""
        if site_url:
            # Remote: fetch DocType document via REST and parse fields
            res = remote_frappe_call(site_url, f"DocType/{doctype}", http_method="GET")
            if not isinstance(res, dict) or "data" not in res:
                return {"success": False, "error": f"DocType '{doctype}' not found on remote site"}
            dt = res["data"]
            fields = dt.get("fields", [])
            # Build a simplified structure similar to local metadata
            result = {
                "success": True,
                "doctype": doctype,
                "module": dt.get("module"),
                "is_submittable": dt.get("is_submittable", 0),
                "is_tree": dt.get("is_tree", 0),
                "is_single": dt.get("issingle", 0),
                "is_child_table": dt.get("istable", 0),
                "naming_rule": dt.get("naming_rule"),
                "title_field": dt.get("title_field"),
                "fields": [
                    {
                        "fieldname": f.get("fieldname"),
                        "label": f.get("label"),
                        "fieldtype": f.get("fieldtype"),
                        "options": f.get("options"),
                        "reqd": f.get("reqd"),
                        "read_only": f.get("read_only"),
                        "hidden": f.get("hidden"),
                        "default": f.get("default"),
                        "description": f.get("description"),
                    }
                    for f in fields
                ],
                "link_fields": [
                    {"fieldname": f.get("fieldname"), "label": f.get("label"), "options": f.get("options")}
                    for f in fields if f.get("fieldtype") == "Link"
                ],
                "child_tables": [],
                "permissions": [],
            }
            return result

        # Local execution (original code)
        try:
            if not frappe.db.exists("DocType", doctype):
                return {"success": False, "error": f"DocType '{doctype}' not found"}
            if not frappe.has_permission(doctype, "read"):
                return {"success": False, "error": f"No permission to access DocType '{doctype}'"}

            meta = frappe.get_meta(doctype)
            fields = [MetadataTools._serialize_field(field) for field in meta.fields]
            link_fields = [
                {"fieldname": field.fieldname, "label": field.label, "options": field.options}
                for field in meta.get_link_fields()
            ]
            child_tables = []
            for table_field in meta.get_table_fields():
                child_doctype = table_field.options
                child_entry = {
                    "fieldname": table_field.fieldname,
                    "label": table_field.label,
                    "fieldtype": table_field.fieldtype,
                    "options": child_doctype,
                    "reqd": table_field.reqd,
                    "fields": [],
                }
                if child_doctype and frappe.db.exists("DocType", child_doctype):
                    child_meta = frappe.get_meta(child_doctype)
                    child_entry["fields"] = [MetadataTools._serialize_field(f) for f in child_meta.fields]
                child_tables.append(child_entry)

            return {
                "success": True,
                "doctype": doctype,
                "module": meta.module,
                "is_submittable": bool(meta.is_submittable),
                "is_tree": bool(meta.is_tree),
                "is_single": bool(meta.issingle),
                "is_child_table": bool(meta.istable),
                "naming_rule": meta.naming_rule,
                "title_field": meta.title_field,
                "fields": fields,
                "link_fields": link_fields,
                "child_tables": child_tables,
                "permissions": [p.as_dict() for p in meta.permissions],
            }
        except Exception as e:
            frappe.log_error(f"assistant Get DocType Metadata Error: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_doctypes(module: str = None, custom_only: bool = False, site_url: str = None) -> Dict[str, Any]:
        """List all available DocTypes, optionally remote."""
        if site_url:
            filters = {}
            if module:
                filters["module"] = module
            if custom_only:
                filters["custom"] = 1
            res = remote_frappe_call(
                site_url,
                "frappe.client.get_list",
                params={
                    "doctype": "DocType",
                    "filters": filters,
                    "fields": ["name", "module", "is_submittable", "is_tree", "istable", "custom", "description"],
                    "limit_page_length": 500,
                },
                http_method="GET",
            )
            if isinstance(res, dict) and "message" in res:
                return {
                    "success": True,
                    "doctypes": res["message"],
                    "count": len(res["message"]),
                    "filters_applied": {"module": module, "custom_only": custom_only},
                }
            return {"success": False, "error": res.get("error", "Remote list failed")}

        try:
            filters = {}
            if module:
                filters["module"] = module
            if custom_only:
                filters["custom"] = 1

            doctypes = frappe.get_all(
                "DocType",
                filters=filters,
                fields=["name", "module", "is_submittable", "is_tree", "istable", "custom", "description"],
                order_by="name",
            )
            accessible_doctypes = [dt for dt in doctypes if frappe.has_permission(dt.name, "read")]
            return {
                "success": True,
                "doctypes": accessible_doctypes,
                "count": len(accessible_doctypes),
                "filters_applied": {"module": module, "custom_only": custom_only},
            }
        except Exception as e:
            frappe.log_error(f"assistant List DocTypes Error: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_permissions(doctype: str, user: str = None, site_url: str = None) -> Dict[str, Any]:
        """Get permission information for a DocType, optionally remote."""
        if site_url:
            # Remote: we can't easily check permissions for a user on remote; return limited info.
            return {"success": False, "error": "Permission check not supported on remote sites."}

        try:
            if not frappe.db.exists("DocType", doctype):
                return {"success": False, "error": f"DocType '{doctype}' not found"}

            check_user = user or frappe.session.user
            permissions = {
                "read": frappe.has_permission(doctype, "read", user=check_user, throw=False),
                "write": frappe.has_permission(doctype, "write", user=check_user, throw=False),
                "create": frappe.has_permission(doctype, "create", user=check_user, throw=False),
                "delete": frappe.has_permission(doctype, "delete", user=check_user, throw=False),
                "submit": frappe.has_permission(doctype, "submit", user=check_user, throw=False),
                "cancel": frappe.has_permission(doctype, "cancel", user=check_user, throw=False),
                "amend": frappe.has_permission(doctype, "amend", user=check_user, throw=False),
            }
            user_roles = frappe.get_roles(check_user)
            meta = frappe.get_meta(doctype)
            permission_rules = [p.as_dict() for p in meta.permissions]

            return {
                "success": True,
                "doctype": doctype,
                "user": check_user,
                "permissions": permissions,
                "user_roles": user_roles,
                "permission_rules": permission_rules,
            }
        except Exception as e:
            frappe.log_error(f"assistant Get Permissions Error: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_workflow(doctype: str, site_url: str = None) -> Dict[str, Any]:
        """Get workflow information for a DocType, optionally remote."""
        if site_url:
            # Remote: fetch Workflow via REST
            res = remote_frappe_call(
                site_url,
                "frappe.client.get_list",
                params={
                    "doctype": "Workflow",
                    "filters": {"document_type": doctype},
                    "fields": ["name"],
                },
                http_method="GET",
            )
            if isinstance(res, dict) and "message" in res:
                wf_list = res["message"]
                if not wf_list:
                    return {"success": True, "doctype": doctype, "has_workflow": False, "message": f"No workflow defined for DocType '{doctype}'"}
                wf_name = wf_list[0]["name"]
                # Fetch full workflow doc
                wf_res = remote_frappe_call(site_url, f"Workflow/{wf_name}", http_method="GET")
                if isinstance(wf_res, dict) and "data" in wf_res:
                    wf = wf_res["data"]
                    return {
                        "success": True,
                        "doctype": doctype,
                        "has_workflow": True,
                        "workflow_name": wf.get("name"),
                        "workflow_state_field": wf.get("workflow_state_field"),
                        "states": wf.get("states", []),
                        "transitions": wf.get("transitions", []),
                    }
            return {"success": False, "error": "Remote workflow fetch failed"}

        try:
            if not frappe.db.exists("DocType", doctype):
                return {"success": False, "error": f"DocType '{doctype}' not found"}

            workflow = frappe.db.get_value("Workflow", {"document_type": doctype}, "name")
            if not workflow:
                return {"success": True, "doctype": doctype, "has_workflow": False, "message": f"No workflow defined for DocType '{doctype}'"}

            workflow_doc = frappe.get_doc("Workflow", workflow)
            states = [{"state": s.state, "doc_status": s.doc_status, "allow_edit": s.allow_edit, "message": s.message} for s in workflow_doc.states]
            transitions = [
                {"state": t.state, "action": t.action, "next_state": t.next_state, "allowed": t.allowed, "allow_self_approval": t.allow_self_approval}
                for t in workflow_doc.transitions
            ]
            return {
                "success": True,
                "doctype": doctype,
                "has_workflow": True,
                "workflow_name": workflow_doc.name,
                "workflow_state_field": workflow_doc.workflow_state_field,
                "states": states,
                "transitions": transitions,
            }
        except Exception as e:
            frappe.log_error(f"assistant Get Workflow Error: {str(e)}")
            return {"success": False, "error": str(e)}
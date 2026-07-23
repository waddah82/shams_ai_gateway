# (license header unchanged)
"""
Document Update Tool for Core Plugin.
Updates existing Frappe documents.
"""

from typing import Any, Dict, List, Optional, Set

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool
from shams_ai_gateway.core.utils import remote_frappe_call


def _restricted_fields_for_doctype(doctype: str, user_role: str) -> Set[str]:
    """Resolve the union of SENSITIVE_FIELDS + (role-conditional) ADMIN_ONLY_FIELDS for a doctype."""
    from shams_ai_gateway.core.security_config import ADMIN_ONLY_FIELDS, SENSITIVE_FIELDS

    restricted: Set[str] = set()
    restricted.update(SENSITIVE_FIELDS.get("all_doctypes", []))
    restricted.update(SENSITIVE_FIELDS.get(doctype, []))

    if user_role == "Assistant User":
        restricted.update(ADMIN_ONLY_FIELDS.get("all_doctypes", []))
        doctype_admin_fields = ADMIN_ONLY_FIELDS.get(doctype, [])
        if doctype_admin_fields != "*":
            restricted.update(doctype_admin_fields)

    return restricted


def _apply_child_table_update(
    doc: Any,
    field: str,
    child_doctype: str,
    rows: Any,
    restricted_child_fields: Set[str],
) -> Optional[Dict[str, Any]]:
    """Apply patch- or replace-mode updates to a child table on `doc`."""
    if not isinstance(rows, list):
        return {
            "success": False,
            "error": f"Child table '{field}' requires a list of dictionaries, got: {type(rows).__name__}",
            "error_type": "child_table_handling_error",
            "field": field,
        }

    for row in rows:
        if not isinstance(row, dict):
            return {
                "success": False,
                "error": f"Child table '{field}' rows must be dictionaries, got: {type(row).__name__}",
                "error_type": "child_table_handling_error",
                "field": field,
            }

    has_named_row = any("name" in row and row["name"] for row in rows)

    for row in rows:
        violating = [k for k in row.keys() if k in restricted_child_fields]
        if violating:
            row_id = row.get("name", "<new row>")
            return {
                "success": False,
                "error": (
                    f"Cannot update restricted child-table fields: "
                    f"{', '.join(violating)} in {child_doctype} (row {row_id}). "
                    f"These fields require higher privileges."
                ),
            }

    if not has_named_row:
        if any("_delete" in row for row in rows):
            return {
                "success": False,
                "error": (
                    f"'_delete' marker on child table '{field}' requires a 'name' to identify "
                    f"the row to remove."
                ),
                "error_type": "child_row_not_found",
                "field": field,
            }
        doc.set(field, [])
        for row in rows:
            doc.append(field, row)
        return None

    existing_rows = doc.get(field) or []
    existing_by_name = {r.name: r for r in existing_rows if getattr(r, "name", None)}

    for row in rows:
        row_name = row.get("name")
        delete_marker = bool(row.get("_delete"))

        if not row_name:
            if delete_marker:
                return {
                    "success": False,
                    "error": (
                        f"'_delete' marker on child table '{field}' requires a 'name' to identify "
                        f"the row to remove."
                    ),
                    "error_type": "child_row_not_found",
                    "field": field,
                }
            from frappe.utils import getdate
            meta = frappe.get_meta(child_doctype)
            coerced_row = {}
            for k, v in row.items():
                field_meta = meta.get_field(k)
                if field_meta and field_meta.fieldtype == "Date" and isinstance(v, str) and v:
                    coerced_row[k] = getdate(v)
                else:
                    coerced_row[k] = v
            doc.append(field, coerced_row)
            continue

        target = existing_by_name.get(row_name)
        if target is None:
            return {
                "success": False,
                "error": f"Row '{row_name}' not found in {child_doctype} table '{field}'.",
                "error_type": "child_row_not_found",
                "field": field,
            }

        if delete_marker:
            doc.remove(target)
            continue

        for k, v in row.items():
            if k in ("name", "_delete"):
                continue
            target.set(k, v)

    return None


class DocumentUpdate(BaseTool):
    """Tool for updating existing Frappe documents."""

    def __init__(self):
        super().__init__()
        self.name = "update_document"
        self.description = (
            "Update/modify an existing Frappe document. Use when users want to change field values "
            "in an existing record. Always fetch the document first to understand current values. "
            "Supports child tables: send a list of row dicts under the table fieldname. If any row "
            "has a 'name' key, patch mode is used (rows matched by 'name' are updated, rows without "
            "'name' are appended, rows with '_delete': true are removed). If no row has a 'name', "
            "the entire child table is replaced. "
            "IMPORTANT: do NOT call this tool with a child-table doctype directly..."
        )
        self.requires_permission = None

        self.inputSchema = {
            "type": "object",
            "properties": {
                "doctype": {
                    "type": "string",
                    "description": "The Frappe DocType name (e.g., 'Customer', 'Sales Invoice', 'Item')",
                },
                "name": {
                    "type": "string",
                    "description": "The document name/ID to update (e.g., 'CUST-00001', 'SINV-00001')",
                },
                "data": {
                    "type": "object",
                    "description": (
                        "Field updates as key-value pairs. Only include fields that need to be changed. "
                        "For top-level scalar fields: {'customer_name': 'Updated Corp Name'}. "
                        "For child tables, pass a list of row dicts under the table fieldname. "
                        "Patch mode (any row has 'name'): matched rows are updated, unmatched rows are "
                        "appended, rows with '_delete': true are removed; existing rows not mentioned "
                        "are left untouched. Replace mode (no row has 'name'): the table is cleared and "
                        "refilled. Example patch: {'items': [{'name': 'abc-123', 'qty': 5}, "
                        "{'item_code': 'NEW', 'qty': 1}, {'name': 'old-1', '_delete': true}]}."
                    ),
                },
            },
            "required": ["doctype", "name", "data"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing document, optionally on a remote site."""
        target_url = getattr(frappe.local, "target_site_url", None)

        doctype = arguments.get("doctype")
        name = arguments.get("name")
        data = arguments.get("data", {})

        # Reject direct updates to child-table doctypes (also applies locally)
        try:
            child_meta = frappe.get_meta(doctype)
        except Exception:
            child_meta = None
        if child_meta is not None and getattr(child_meta, "istable", 0):
            parent_info: Dict[str, Any] = {
                "success": False,
                "error": (
                    f"'{doctype}' is a child-table doctype and cannot be updated directly. "
                    f"Updating a child row in isolation skips the parent doc's validate() "
                    f"pipeline, leaving derived fields (row totals, parent grand_total, "
                    f"total_qty, etc.) stale. Update the parent document instead and pass "
                    f"the child rows under the table fieldname in `data`."
                ),
                "error_type": "child_doctype_direct_update",
                "child_doctype": doctype,
            }
            if name:
                try:
                    parent_name = frappe.db.get_value(doctype, name, "parent")
                    parent_type = frappe.db.get_value(doctype, name, "parenttype")
                    parent_field = frappe.db.get_value(doctype, name, "parentfield")
                    if parent_name and parent_type and parent_field:
                        parent_info["parent_doctype"] = parent_type
                        parent_info["parent_name"] = parent_name
                        parent_info["parent_table_fieldname"] = parent_field
                        parent_info["suggestion"] = (
                            f"Call update_document with doctype='{parent_type}', "
                            f"name='{parent_name}', and data={{'{parent_field}': "
                            f"[{{'name': '{name}', ...fields to change...}}]}}. "
                            f"Patch mode will update only the named row; other rows are untouched."
                        )
                except Exception:
                    pass
            return parent_info

        if target_url:
            # Remote update via PUT request
            res = remote_frappe_call(
                target_url,
                f"{doctype}/{name}",
                params={"data": data},
                http_method="PUT"
            )
            if isinstance(res, dict) and "data" in res:
                return {
                    "success": True,
                    "name": name,
                    "doctype": doctype,
                    "data": res["data"],
                    "message": f"{doctype} '{name}' updated successfully",
                }
            return {"success": False, "error": res.get("error") or res.get("message", "Remote update failed")}

        # Local execution (original code)
        from shams_ai_gateway.core.security_config import validate_document_access

        validation_result = validate_document_access(
            user=frappe.session.user, doctype=doctype, name=name, perm_type="write", data=data
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

            if current_docstatus == 2:
                return {
                    "success": False,
                    "error": f"Cannot modify cancelled document {doctype} '{name}'. Cancelled documents are read-only.",
                    "docstatus": current_docstatus,
                    "workflow_state": current_workflow_state,
                    "suggestion": "Use document_get to view the cancelled document, or create a new document if needed.",
                }

            parent_restricted = _restricted_fields_for_doctype(doctype, user_role)
            meta = frappe.get_meta(doctype)
            table_fields = {f.fieldname: f.options for f in meta.fields if f.fieldtype == "Table"}

            restricted_top_level = [
                field for field in data.keys() if field in parent_restricted and field not in table_fields
            ]
            if restricted_top_level:
                return {
                    "success": False,
                    "error": (
                        f"Cannot update restricted fields: {', '.join(restricted_top_level)}. "
                        f"These fields require higher privileges."
                    ),
                }

            for field, value in data.items():
                if field in table_fields:
                    child_doctype = table_fields[field]
                    child_restricted = _restricted_fields_for_doctype(child_doctype, user_role)
                    err = _apply_child_table_update(doc, field, child_doctype, value, child_restricted)
                    if err is not None:
                        return err
                else:
                    setattr(doc, field, value)

            doc.save()
            doc.reload()
            updated_docstatus = getattr(doc, "docstatus", 0)
            updated_workflow_state = getattr(doc, "workflow_state", None)

            result = {
                "success": True,
                "name": doc.name,
                "doctype": doctype,
                "updated_fields": list(data.keys()),
                "docstatus": updated_docstatus,
                "state_description": "Draft" if updated_docstatus == 0 else "Unknown",
                "workflow_state": updated_workflow_state,
                "owner": doc.owner,
                "modified": str(doc.modified),
                "modified_by": doc.modified_by,
                "message": f"{doctype} '{doc.name}' updated successfully",
            }

            if updated_docstatus == 0:
                try:
                    result["can_submit"] = frappe.has_permission(doctype, "submit", doc=doc.name)
                except Exception:
                    result["can_submit"] = False
            else:
                result["can_submit"] = False

            if updated_docstatus == 0:
                result["next_steps"] = [
                    "Document remains in draft state",
                    "You can continue updating this document",
                    f"Submit permission: {'Available' if result['can_submit'] else 'Not available'}",
                ]
                if updated_workflow_state:
                    result["next_steps"].append(f"Current workflow state: {updated_workflow_state}")
            else:
                result["next_steps"] = [
                    f"Document state: {result['state_description']}",
                    "Further modifications may be restricted",
                ]

            return result

        except Exception as e:
            frappe.log_error(
                title=_("Document Update Error"), message=f"Error updating {doctype} '{name}': {str(e)}"
            )
            return {"success": False, "error": str(e), "doctype": doctype, "name": name}


document_update = DocumentUpdate
# (license header unchanged)
"""
ChatGPT-Compatible Fetch Tool
...
"""

import json
from typing import Any, Dict

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool
from shams_ai_gateway.core.utils import remote_frappe_call
from shams_ai_gateway.core.security_config import (
    filter_sensitive_fields,
    validate_document_access,
)


class ChatGPTFetch(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "fetch"
        self.description = "Retrieve complete document content by ID for detailed analysis and citation..."
        self.inputSchema = {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Document ID from search results (format: 'doctype/name', e.g., 'Customer/CUST-00001')",
                }
            },
            "required": ["id"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        target_url = getattr(frappe.local, "target_site_url", None)
        doc_id = arguments.get("id", "").strip()

        if not doc_id:
            raise ValueError("Document ID is required")
        if "/" not in doc_id:
            raise ValueError(f"Invalid document ID format. Expected 'doctype/name', got: {doc_id}")

        doctype, name = doc_id.split("/", 1)

        if target_url:
            # Remote fetch
            res = remote_frappe_call(target_url, f"{doctype}/{name}", http_method="GET")
            if not isinstance(res, dict) or "data" not in res:
                raise ValueError(f"Document not found: {doc_id}")
            doc_dict = res["data"]
            title = doc_dict.get("title") or doc_dict.get("name") or name
            text_content = self._format_document_as_text(doc_dict, doctype, name)
            site_url = target_url  # Use remote URL for citation
            url = f"{site_url}/app/{frappe.scrub(doctype)}/{name}"
            metadata = {
                "doctype": doctype,
                "modified": str(doc_dict.get("modified", "")),
                "owner": doc_dict.get("owner", ""),
                "docstatus": doc_dict.get("docstatus", 0),
            }
            return {"id": doc_id, "title": title, "text": text_content, "url": url, "metadata": metadata}

        # Local execution
        try:
            validation_result = validate_document_access(
                user=frappe.session.user, doctype=doctype, name=name, perm_type="read"
            )
            if not validation_result["success"]:
                raise frappe.PermissionError(validation_result.get("error", f"Access denied for {doctype} {name}"))

            user_role = validation_result["role"]
            doc = frappe.get_doc(doctype, name)
            doc_dict = filter_sensitive_fields(doc.as_dict(), doctype, user_role)

            title = doc_dict.get("title") or doc_dict.get("name") or name
            text_content = self._format_document_as_text(doc_dict, doctype, name)
            site_url = frappe.utils.get_url()
            url = f"{site_url}/app/{frappe.scrub(doctype)}/{name}"
            metadata = {
                "doctype": doctype,
                "modified": str(doc_dict.get("modified", "")),
                "owner": doc_dict.get("owner", ""),
                "docstatus": doc_dict.get("docstatus", 0),
            }
            return {"id": doc_id, "title": title, "text": text_content, "url": url, "metadata": metadata}

        except frappe.DoesNotExistError:
            raise ValueError(f"Document not found: {doc_id}") from None
        except frappe.PermissionError as e:
            raise ValueError(f"Permission denied: {str(e)}") from e
        except ValueError:
            raise

    def _format_document_as_text(self, doc_dict: Dict, doctype: str, name: str) -> str:
        lines = [f"# {doctype}: {name}", ""]
        priority_fields = ["title", "subject", "description", "customer_name", "item_name"]
        for field in priority_fields:
            if field in doc_dict and doc_dict[field]:
                label = field.replace("_", " ").title()
                lines.append(f"**{label}**: {doc_dict[field]}")
        lines.append("")
        lines.append("## All Fields")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(doc_dict, indent=2, default=str))
        lines.append("```")
        return "\n".join(lines)


chatgpt_fetch = ChatGPTFetch
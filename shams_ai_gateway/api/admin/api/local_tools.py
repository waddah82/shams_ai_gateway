# Local All Tools API for Shams AI Gateway
# Add/replace this file at:
# apps/shams_ai_gateway/shams_ai_gateway/api/local_tools.py

import json
import time
from typing import Any, Dict, List

import frappe
from frappe import _


CORE_TOOLS = {
    "get_document",
    "list_documents",
    "create_document",
    "update_document",
    "delete_document",
    "submit_document",
    "get_doctype_info",
    "report_list",
    "report_requirements",
    "generate_report",
    "get_pending_approvals",
    "run_workflow",
    "search",
    "search_documents",
    "search_doctype",
    "search_link",
    "fetch",
}

WRITE_TOOLS = {
    "create_document",
    "update_document",
    "submit_document",
    "run_workflow",
    "create_dashboard",
    "create_dashboard_chart",
}

DANGEROUS_TOOLS = {
    "delete_document",
}

CODE_ANALYSIS_TOOLS = {
    "run_python_code",
    "run_database_query",
    "analyze_business_data",
}

FILE_OCR_TOOLS = {
    "extract_file_content",
}

VISUALIZATION_TOOLS = {
    "create_dashboard",
    "create_dashboard_chart",
    "list_user_dashboards",
}

HEAVY_TOOLS = CODE_ANALYSIS_TOOLS | FILE_OCR_TOOLS

# Examples are intentionally small and safe. Edit before running.
TOOL_EXAMPLES = {
    # Core / documents
    "list_documents": {
        "doctype": "Customer",
        "filters": {},
        "fields": ["name", "customer_name", "creation"],
        "limit": 5,
        "order_by": "creation desc",
    },
    "get_document": {"doctype": "Customer", "name": "CUSTOMER-NAME-HERE"},
    "create_document": {"doctype": "ToDo", "data": {"description": "Created from SAG Local Tools"}},
    "update_document": {"doctype": "ToDo", "name": "DOCUMENT-NAME-HERE", "data": {"description": "Updated from SAG Local Tools"}},
    "delete_document": {"doctype": "ToDo", "name": "DOCUMENT-NAME-HERE"},
    "submit_document": {"doctype": "Sales Invoice", "name": "DOCUMENT-NAME-HERE"},
    "get_doctype_info": {"doctype": "Sales Invoice"},
    "search_documents": {"doctype": "Customer", "query": "test", "limit": 10},
    "search_doctype": {"query": "Customer", "limit": 10},
    "search_link": {"doctype": "Customer", "txt": "", "limit": 10},
    "search": {"query": "customer", "limit": 10},
    "fetch": {"id": "DOCUMENT-OR-RESOURCE-ID-HERE"},
    # Reports / workflow
    "report_list": {},
    "report_requirements": {"report_name": "Accounts Receivable"},
    "generate_report": {"report_name": "Accounts Receivable", "filters": {}},
    "get_pending_approvals": {"doctype": "Leave Application", "limit": 10},
    "run_workflow": {"doctype": "Leave Application", "docname": "DOCUMENT-NAME-HERE", "action": "Approve"},
    # Data Science
    "run_python_code": {
        "code": "docs = tools.get_documents('Customer', fields=['name', 'customer_name'], limit=5)\nprint(docs)",
        "timeout": 30,
        "capture_output": True,
    },
    "run_database_query": {
        "query": "SELECT name, creation FROM `tabCustomer` ORDER BY creation DESC LIMIT 5",
        "analysis_type": "basic",
        "validate_query": True,
        "limit": 5,
    },
    "analyze_business_data": {
        "data_source": "doctype",
        "doctype": "Sales Invoice",
        "fields": ["name", "customer", "grand_total", "posting_date"],
        "filters": {"docstatus": 1},
        "analysis_type": "summary",
        "limit": 100,
    },
    "extract_file_content": {
        "file_url": "/private/files/YOUR-FILE.pdf",
        "operation": "extract",
        "language": "en",
        "output_format": "text",
        "max_pages": 5,
    },
    # Visualization
    "list_user_dashboards": {},
    "create_dashboard": {
        "dashboard_name": "AI Local Dashboard Test",
        "description": "Created from SAG Local Tools",
    },
    "create_dashboard_chart": {
        "dashboard_name": "AI Local Dashboard Test",
        "chart_title": "Sample Chart",
        "chart_type": "Bar",
        "doctype": "Sales Invoice",
        "x_field": "posting_date",
        "y_field": "grand_total",
        "aggregation": "sum",
    },
}


def _json_loads(value: Any) -> Dict[str, Any]:
    if value is None or value == "":
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value or "{}")
        except Exception as exc:
            frappe.throw(_("Invalid JSON arguments: {0}").format(str(exc)))
        if not isinstance(parsed, dict):
            frappe.throw(_("Arguments must be a JSON object."))
        return parsed
    frappe.throw(_("Arguments must be a JSON object."))


def _user_has_local_tools_access() -> bool:
    if frappe.session.user == "Guest":
        return False
    if frappe.session.user == "Administrator":
        return True
    roles = set(frappe.get_roles(frappe.session.user))
    return bool(roles.intersection({"System Manager", "Assistant Admin", "Assistant User"}))


def _assert_access():
    if not _user_has_local_tools_access():
        frappe.throw(
            _("Not permitted. User must have System Manager, Assistant Admin, or Assistant User role."),
            frappe.PermissionError,
        )


def _get_plugin_names_by_tool() -> Dict[str, str]:
    """Return tool_name -> plugin_name for enabled plugin tools and external custom tools."""
    from shams_ai_gateway.core.tool_registry import get_tool_registry
    from shams_ai_gateway.utils.plugin_manager import get_plugin_manager

    registry = get_tool_registry()
    plugin_manager = get_plugin_manager()

    mapping: Dict[str, str] = {}
    try:
        all_tools = plugin_manager.get_all_tools()
        for name, info in all_tools.items():
            mapping[name] = getattr(info, "plugin_name", None) or "unknown"
    except Exception:
        pass

    try:
        external_tools = registry._get_external_tools()  # noqa: SLF001 - local admin UI helper
        for name, info in external_tools.items():
            mapping[name] = getattr(info, "plugin_name", None) or "custom_tools"
    except Exception:
        pass

    return mapping


def _get_tool_category(tool_name: str, plugin_name: str = "") -> str:
    if tool_name in DANGEROUS_TOOLS:
        return "dangerous"
    if tool_name in FILE_OCR_TOOLS:
        return "file_ocr"
    if tool_name in CODE_ANALYSIS_TOOLS:
        return "code_analysis"
    if tool_name in VISUALIZATION_TOOLS or plugin_name == "visualization":
        return "visualization"
    if plugin_name == "custom_tools":
        return "custom"
    if tool_name in WRITE_TOOLS:
        return "write"
    return "read_only"


def _requires_confirmation(category: str, tool_name: str) -> bool:
    return category in {"write", "dangerous", "code_analysis", "file_ocr", "visualization", "custom"} or tool_name in WRITE_TOOLS


def _normalize_limits(arguments: Any) -> Any:
    """Resource guard for local UI calls. Final limits still belong to the tool itself."""
    if isinstance(arguments, dict):
        for key in list(arguments.keys()):
            lower = key.lower()
            if lower in {"limit", "limit_page_length", "page_length", "limit_start"}:
                try:
                    if lower == "limit_start":
                        arguments[key] = max(int(arguments.get(key) or 0), 0)
                    else:
                        arguments[key] = min(max(int(arguments.get(key) or 20), 1), 500)
                except Exception:
                    arguments[key] = 20
            elif lower in {"max_pages"}:
                try:
                    arguments[key] = min(max(int(arguments.get(key) or 5), 1), 20)
                except Exception:
                    arguments[key] = 5
            elif isinstance(arguments[key], (dict, list)):
                arguments[key] = _normalize_limits(arguments[key])
    elif isinstance(arguments, list):
        return [_normalize_limits(item) for item in arguments]
    return arguments


@frappe.whitelist()
def ping() -> Dict[str, Any]:
    _assert_access()
    return {
        "success": True,
        "user": frappe.session.user,
        "roles": frappe.get_roles(frappe.session.user),
        "all_tools_mode": True,
    }


@frappe.whitelist()
def list_all_tools() -> Dict[str, Any]:
    """Return every enabled SAG tool available to the current user, including OCR/Data Science/Visualization/Custom."""
    _assert_access()

    from shams_ai_gateway.core.tool_registry import get_tool_registry
    from shams_ai_gateway.utils.plugin_manager import get_plugin_manager

    registry = get_tool_registry()
    plugin_manager = get_plugin_manager()
    enabled_plugins = list(plugin_manager.get_enabled_plugins())
    plugin_names = _get_plugin_names_by_tool()

    available = registry.get_available_tools(user=frappe.session.user)
    tools: List[Dict[str, Any]] = []

    for tool in available:
        tool_name = tool.get("name")
        if not tool_name:
            continue
        plugin_name = plugin_names.get(tool_name, "unknown")
        category = _get_tool_category(tool_name, plugin_name)
        tools.append(
            {
                "name": tool_name,
                "display_name": tool_name.replace("_", " ").title(),
                "description": tool.get("description", ""),
                "inputSchema": tool.get("inputSchema", {}),
                "category": category,
                "plugin": plugin_name,
                "example": TOOL_EXAMPLES.get(tool_name, {}),
                "requires_confirmation": _requires_confirmation(category, tool_name),
            }
        )

    order = {
        "read_only": 0,
        "write": 1,
        "file_ocr": 2,
        "code_analysis": 3,
        "visualization": 4,
        "custom": 5,
        "dangerous": 6,
    }
    tools.sort(key=lambda x: (order.get(x["category"], 9), x.get("plugin") or "", x["name"]))

    categories = {}
    for tool in tools:
        categories[tool["category"]] = categories.get(tool["category"], 0) + 1

    return {
        "success": True,
        "user": frappe.session.user,
        "enabled_plugins": enabled_plugins,
        "total": len(tools),
        "categories": categories,
        "tools": tools,
        "policy": {
            "all_enabled_tools": True,
            "requires_confirmation_categories": ["write", "dangerous", "code_analysis", "file_ocr", "visualization", "custom"],
            "local_ui_limit_guard": {"max_limit": 500, "max_pages": 20},
            "note": "This page exposes all SAG tools that are enabled for the current user. Disable unwanted tools from SAG Admin > Tools.",
        },
    }


@frappe.whitelist()
def list_core_tools() -> Dict[str, Any]:
    """Backward compatible alias. The page now returns all tools."""
    return list_all_tools()


@frappe.whitelist(methods=["POST"])
def run_tool(tool_name: str, arguments: Any = None, confirm_action: int = 0) -> Dict[str, Any]:
    """Run any enabled SAG tool locally from Desk page.

    Security rules:
    - Logged-in user only.
    - User must have System Manager, Assistant Admin, or Assistant User role.
    - Tool must be available to the user via SAG Tool Configuration and role access.
    - Write/delete/code/OCR/visualization/custom tools require confirm_action=1.
    - Final permissions still happen inside SAG and Frappe.
    """
    _assert_access()

    tool_name = (tool_name or "").strip()
    if not tool_name:
        frappe.throw(_("Tool name is required."))

    from shams_ai_gateway.core.tool_registry import get_tool_registry

    registry = get_tool_registry()
    available_names = {tool.get("name") for tool in registry.get_available_tools(user=frappe.session.user)}
    if tool_name not in available_names:
        frappe.throw(_("Tool is not enabled or not permitted for this user: {0}").format(tool_name), frappe.PermissionError)

    plugin_name = _get_plugin_names_by_tool().get(tool_name, "unknown")
    category = _get_tool_category(tool_name, plugin_name)

    if _requires_confirmation(category, tool_name) and not frappe.utils.cint(confirm_action):
        frappe.throw(_("This tool may read sensitive files, run analysis, or change data. Enable confirmation before running it."), frappe.PermissionError)

    parsed_args = _json_loads(arguments)
    parsed_args = _normalize_limits(parsed_args)

    started = time.time()

    try:
        result = registry.execute_tool(tool_name, parsed_args)
        elapsed_ms = int((time.time() - started) * 1000)
        return {
            "success": True,
            "tool_name": tool_name,
            "plugin": plugin_name,
            "category": category,
            "execution_ms": elapsed_ms,
            "arguments": parsed_args,
            "result": result,
        }
    except Exception as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        frappe.log_error(
            title="SAG Local Tool Execution Failed",
            message=frappe.get_traceback(),
        )
        return {
            "success": False,
            "tool_name": tool_name,
            "plugin": plugin_name,
            "category": category,
            "execution_ms": elapsed_ms,
            "arguments": parsed_args,
            "error": str(exc),
            "error_type": type(exc).__name__,
        }


@frappe.whitelist(methods=["POST"])
def run_core_tool(tool_name: str, arguments: Any = None, confirm_write: int = 0) -> Dict[str, Any]:
    """Backward compatible alias for old page JS."""
    return run_tool(tool_name=tool_name, arguments=arguments, confirm_action=confirm_write)


@frappe.whitelist()
def list_recent_files(search: str = "", limit: int = 20) -> Dict[str, Any]:
    """List recent File records visible to current user for extract_file_content."""
    _assert_access()
    limit = min(max(frappe.utils.cint(limit) or 20, 1), 50)
    filters = {}
    if search:
        filters = [["file_name", "like", f"%{search}%"]]

    files = frappe.get_list(
        "File",
        filters=filters,
        fields=["name", "file_name", "file_url", "is_private", "attached_to_doctype", "attached_to_name", "creation"],
        order_by="creation desc",
        limit_page_length=limit,
    )

    return {"success": True, "files": files, "count": len(files)}

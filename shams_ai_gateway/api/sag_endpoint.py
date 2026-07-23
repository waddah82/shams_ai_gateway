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
MCP StreamableHTTP Endpoint

Custom MCP implementation that properly handles JSON serialization
and integrates seamlessly with Frappe's existing tool infrastructure.
"""

import frappe
from frappe import _
from shams_ai_gateway.mcp.server import MCPServer


def _get_mcp_server_name():
    try:
        settings = frappe.get_single("SAG Settings")
        return settings.mcp_server_name or "shams-ai-gateway"
    except Exception:
        return "shams-ai-gateway"


mcp = MCPServer(_get_mcp_server_name())


def _check_assistant_enabled(user: str) -> bool:
    try:
        assistant_enabled = frappe.db.get_value("User", user, "assistant_enabled")
        if assistant_enabled is None:
            return False
        return bool(int(assistant_enabled)) if assistant_enabled else False
    except Exception:
        return False


def _build_tool_registry():
    from collections import OrderedDict
    registry_dict = OrderedDict()
    try:
        from shams_ai_gateway.core.tool_registry import get_tool_registry
        from shams_ai_gateway.mcp.tool_adapter import build_tool_dict
        from shams_ai_gateway.utils.tool_category_detector import category_to_annotations

        registry = get_tool_registry()
        available_tools = registry.get_available_tools(user=frappe.session.user)
        categories = _resolve_tool_categories(
            [t.get("name") for t in available_tools if t.get("name")], registry
        )
        for tool_metadata in available_tools:
            tool_name = tool_metadata.get("name")
            if tool_name:
                tool_instance = registry.get_tool(tool_name)
                if tool_instance:
                    tool_dict = build_tool_dict(tool_instance)
                    configured_description = (tool_metadata.get("description") or "").strip()
                    if configured_description:
                        tool_dict["description"] = configured_description
                    annotations = category_to_annotations(categories.get(tool_name, "read_write"))
                    if annotations:
                        tool_dict["annotations"] = {**(tool_dict.get("annotations") or {}), **annotations}
                    registry_dict[tool_name] = tool_dict
        frappe.logger().info(f"Built {len(registry_dict)} enabled tools for user {frappe.session.user}")
    except Exception as e:
        frappe.log_error(title="Tool Import Error", message=f"Error importing tools: {str(e)}")
    return registry_dict


def _resolve_tool_categories(tool_names: list, registry) -> dict:
    from shams_ai_gateway.utils.tool_category_detector import detect_tool_category
    categories = {}
    try:
        rows = frappe.get_all(
            "SAG Tool Configuration",
            filters={"tool_name": ["in", tool_names]} if tool_names else {},
            fields=["tool_name", "tool_category"],
            ignore_permissions=True,
        )
        for row in rows:
            if row.get("tool_category"):
                categories[row["tool_name"]] = row["tool_category"]
    except Exception as e:
        frappe.logger().warning(f"Could not batch-fetch tool categories: {e}")
    for tool_name in tool_names:
        if tool_name in categories:
            continue
        try:
            tool_instance = registry.get_tool(tool_name)
            categories[tool_name] = detect_tool_category(tool_instance) if tool_instance else "read_write"
        except Exception:
            categories[tool_name] = "read_write"
    return categories


def _unauthorized_response(error="unauthorized", message="Authentication required"):
    """Return the OAuth challenge expected by Claude and other MCP clients."""
    from werkzeug.wrappers import Response
    from shams_ai_gateway.api.oauth_discovery import get_public_base_url

    metadata_url = f"{get_public_base_url()}/.well-known/oauth-protected-resource"
    response = Response()
    response.status_code = 401
    response.headers["WWW-Authenticate"] = (
        f'Bearer realm="Shams AI Gateway", '
        f'error="{error}", '
        f'resource_metadata="{metadata_url}"'
    )
    response.headers["Content-Type"] = "application/json"
    response.data = frappe.as_json({"error": error, "message": message})
    return response


def _authenticate_mcp_request():
    """Authenticate Claude with OAuth Bearer or a gateway User API token."""
    from werkzeug.wrappers import Response

    # Frappe validates OAuth Bearer tokens before invoking a whitelisted
    # method and sets frappe.session.user to the token owner.  Some proxy/
    # authentication paths do not leave the raw Authorization header
    # available to the method afterwards, so trust Frappe's authenticated
    # request context first.  Guest requests still continue through the
    # explicit header validation below.
    session_user = str(getattr(frappe.session, "user", "") or "")
    if session_user and session_user != "Guest":
        return session_user

    auth_header = frappe.request.headers.get("Authorization", "").strip()

    if auth_header.startswith("Bearer "):
        access_token = auth_header[7:].strip()
        if not access_token:
            return _unauthorized_response("invalid_token", "Bearer token is missing")

        try:
            token_doc = frappe.get_doc("OAuth Bearer Token", {"access_token": access_token})
            if token_doc.status != "Active":
                return _unauthorized_response("invalid_token", "OAuth token is not active")

            from frappe.utils import now_datetime

            if token_doc.expiration_time and token_doc.expiration_time < now_datetime():
                return _unauthorized_response("invalid_token", "OAuth token has expired")

            user = str(token_doc.user)
            if not frappe.db.get_value("User", user, "enabled"):
                return _unauthorized_response("invalid_token", "OAuth user is disabled")

            frappe.set_user(user)
            return user
        except frappe.DoesNotExistError:
            return _unauthorized_response("invalid_token", "OAuth token was not found")
        except Exception as exc:
            frappe.log_error(
                title="SAG OAuth Token Validation Error",
                message=f"{type(exc).__name__}: {exc}",
            )
            return _unauthorized_response("invalid_token", "OAuth token validation failed")

    if auth_header.startswith("token "):
        token_value = auth_header[6:].strip()
        if ":" not in token_value:
            return _unauthorized_response("invalid_credentials", "Invalid API token format")

        api_key, api_secret = token_value.split(":", 1)
        user = frappe.db.get_value(
            "User", {"api_key": api_key, "enabled": 1}, "name"
        )
        if not user:
            return _unauthorized_response("invalid_credentials", "Invalid API credentials")

        try:
            from frappe.utils.password import get_decrypted_password

            saved_secret = get_decrypted_password("User", user, "api_secret")
        except Exception:
            saved_secret = None

        if not saved_secret or api_secret != saved_secret:
            return _unauthorized_response("invalid_credentials", "Invalid API credentials")

        frappe.set_user(str(user))
        return str(user)

    # Keep the return type explicit for callers and static analysis.
    response: Response = _unauthorized_response()
    return response


def _set_target_site_for_user(user: str):
    """Bind this request to the remote ERPNext site assigned to the OAuth user."""
    if not frappe.db.table_exists("SAG Client Site"):
        return None

    site = frappe.db.get_value(
        "SAG Client Site",
        {"gateway_user": user, "is_active": 1},
        ["name", "site_url", "use_http"],
        as_dict=True,
    )
    if not site:
        return None

    domain = (site.site_url or "").strip().rstrip("/")
    if domain.startswith("http://") or domain.startswith("https://"):
        domain = domain.split("://", 1)[1]

    protocol = "http" if site.use_http else "https"
    frappe.local.target_site_name = site.name
    frappe.local.target_site_url = f"{protocol}://{domain}"
    return site.name


@mcp.register(allow_guest=True, xss_safe=True, methods=["GET", "POST", "HEAD", "OPTIONS"])
def handle_mcp():
    from werkzeug.wrappers import Response


    if frappe.request.method == "OPTIONS":
        resp = Response()
        resp.status_code = 200
        resp.headers["Content-Type"] = "application/json"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, GET, HEAD, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, token, X-SAG-Auth"
        resp.data = '{"status":"ok"}'
        return resp


    if frappe.request.method == "HEAD":
        resp = Response()
        challenge = _unauthorized_response()
        resp.status_code = challenge.status_code
        resp.headers.update(challenge.headers)
        return resp

    auth_result = _authenticate_mcp_request()

    if isinstance(auth_result, Response):
        return auth_result

    authenticated_user = auth_result

    if not _check_assistant_enabled(authenticated_user):
        frappe.throw(
            _("Assistant access is disabled for user {0}").format(authenticated_user),
            frappe.PermissionError,
        )

    # A mapped user operates on its assigned remote site. An unmapped user
    # keeps the original local-site behavior for backwards compatibility.
    _set_target_site_for_user(authenticated_user)

    return _build_tool_registry()

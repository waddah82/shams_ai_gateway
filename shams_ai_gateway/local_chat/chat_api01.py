# Copyright (c) 2026, Shams Solutions
# Local chat API for Shams AI Gateway.
# Uses Chat Module + SAG Local Chat Settings and executes SAG tools locally.

import json
import time
from typing import Any, Dict, List, Optional, Tuple

import frappe
import requests
from frappe import _


WRITE_TOOL_HINTS = {"create", "update", "delete", "submit", "workflow", "run_workflow"}


def _assert_access():
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required"), frappe.PermissionError)
    if frappe.session.user == "Administrator":
        return
    roles = set(frappe.get_roles(frappe.session.user))
    if not roles.intersection({"System Manager", "Assistant Admin", "Assistant User"}):
        frappe.throw(
            _("Not permitted. User must have System Manager, Assistant Admin, or Assistant User role."),
            frappe.PermissionError,
        )


def _safe_json_loads(value: Any, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if default is None:
        default = {}
    if not value:
        return default
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else default
    except Exception:
        return default


def _get_settings_and_module():
    if not frappe.db.exists("DocType", "SAG Local Chat Settings"):
        frappe.throw(_("SAG Local Chat Settings DocType is not installed. Install the chat settings patch first."))

    settings = frappe.get_single("SAG Local Chat Settings")
    if not settings.enable_local_chat:
        frappe.throw(_("SAG Local Chat is disabled in SAG Local Chat Settings."))

    if not settings.chat_module:
        frappe.throw(_("Please select Chat Module in SAG Local Chat Settings."))

    module_doc = frappe.get_doc("Chat Module", settings.chat_module)
    if not module_doc.enabled:
        frappe.throw(_("Selected Chat Module is disabled."))

    api_key = module_doc.get_password("api_key") if hasattr(module_doc, "get_password") else module_doc.get("api_key")
    provider = (module_doc.provider or "OpenAI Compatible").strip()
    if provider not in {"Ollama"} and not api_key:
        frappe.throw(_("API Key is missing in selected Chat Module."))

    model = settings.selected_model or module_doc.default_chat_model
    if not model:
        frappe.throw(_("Selected Model is missing in SAG Local Chat Settings or Chat Module."))

    return settings, module_doc, api_key, model


def _get_registry():
    from shams_ai_gateway.core.tool_registry import get_tool_registry

    return get_tool_registry()


def _available_tools() -> List[Dict[str, Any]]:
    registry = _get_registry()
    tools = registry.get_available_tools(user=frappe.session.user)
    safe_tools = []
    for tool in tools:
        name = tool.get("name")
        if not name:
            continue
        schema = tool.get("inputSchema") or tool.get("input_schema") or {"type": "object", "properties": {}}
        if not isinstance(schema, dict):
            schema = {"type": "object", "properties": {}}
        if not schema.get("type"):
            schema["type"] = "object"
        safe_tools.append({
            "name": name,
            "description": tool.get("description") or name,
            "inputSchema": schema,
        })
    return safe_tools


def _tool_is_write_like(tool_name: str) -> bool:
    lower = (tool_name or "").lower()
    return any(hint in lower for hint in WRITE_TOOL_HINTS)


def _normalize_limits(arguments: Any) -> Any:
    if isinstance(arguments, dict):
        for key in list(arguments.keys()):
            lower = key.lower()
            if lower in {"limit", "limit_page_length", "page_length"}:
                try:
                    arguments[key] = min(max(int(arguments.get(key) or 20), 1), 200)
                except Exception:
                    arguments[key] = 20
            elif lower == "limit_start":
                try:
                    arguments[key] = max(int(arguments.get(key) or 0), 0)
                except Exception:
                    arguments[key] = 0
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


def _execute_tool(tool_name: str, arguments: Dict[str, Any], user_message: str = "") -> Dict[str, Any]:
    registry = _get_registry()
    available_names = {tool.get("name") for tool in registry.get_available_tools(user=frappe.session.user)}
    if tool_name not in available_names:
        raise frappe.PermissionError(f"Tool is not enabled or not permitted: {tool_name}")

    # No duplicate enable/disable settings here. SAG Admin controls availability.
    # This guard only prevents accidental writes when the user did not explicitly ask for them.
    if _tool_is_write_like(tool_name):
        lower_request = (user_message or "").lower()
        explicit_words = [
            "create", "update", "delete", "submit", "approve", "cancel",
            "أنشئ", "انشئ", "حدث", "عدل", "احذف", "اعتمد", "ارسل", "قدّم", "قدم", "وافق",
        ]
        if not any(word in lower_request for word in explicit_words):
            raise frappe.PermissionError(f"Write-like tool '{tool_name}' requires an explicit user request.")

    normalized = _normalize_limits(arguments or {})
    started = time.time()
    result = registry.execute_tool(tool_name, normalized)
    return {
        "success": True,
        "tool_name": tool_name,
        "arguments": normalized,
        "execution_ms": int((time.time() - started) * 1000),
        "result": result,
    }


def _truncate_text(text: str, max_chars: int) -> str:
    if text is None:
        return ""
    text = str(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[TRUNCATED: original length {len(text)} characters]"


def _json_dumps_safe(obj: Any, max_chars: int = 60000) -> str:
    try:
        text = json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        text = str(obj)
    return _truncate_text(text, max_chars)


def _build_system_prompt(settings, tools: List[Dict[str, Any]]) -> str:
    language = settings.default_language or "Arabic"
    base = settings.system_instruction or "You are a helpful ERPNext assistant."
    tool_names = ", ".join([t["name"] for t in tools[:80]])
    return f"""{base}

Local execution rules:
- You are running inside ERPNext/Frappe for the logged-in user: {frappe.session.user}.
- Use available Shams AI Gateway tools only when needed.
- SAG Admin controls which tools are enabled; do not claim a disabled tool is available.
- Respect Frappe permissions and do not try to bypass roles or permissions.
- For write/delete/submit/workflow operations, proceed only when the user explicitly asks for that action.
- Keep answers concise, structured, and useful.
- Default response language: {language}.
- Available tool names: {tool_names}
""".strip()


def _prepare_history(history: Any, max_messages: int = 20) -> List[Dict[str, str]]:
    if isinstance(history, str):
        try:
            history = json.loads(history or "[]")
        except Exception:
            history = []
    if not isinstance(history, list):
        history = []

    cleaned = []
    for row in history[-max_messages:]:
        if not isinstance(row, dict):
            continue
        role = row.get("role")
        content = row.get("content")
        if role not in {"user", "assistant"}:
            continue
        if not content:
            continue
        cleaned.append({"role": role, "content": str(content)[:8000]})
    return cleaned


def _headers(module_doc, api_key: str, provider: str) -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    extra = _safe_json_loads(module_doc.extra_headers_json)
    headers.update(extra)

    if provider == "Anthropic":
        headers["x-api-key"] = api_key
        headers.setdefault("anthropic-version", "2023-06-01")
    elif provider == "Gemini":
        # Gemini uses key query parameter by default.
        pass
    elif provider != "Ollama":
        headers["Authorization"] = f"Bearer {api_key}"
        if provider == "OpenAI":
            if module_doc.organization_id:
                headers["OpenAI-Organization"] = module_doc.organization_id
            if module_doc.project_id:
                headers["OpenAI-Project"] = module_doc.project_id
    return headers


def _openai_tool_specs(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description") or tool["name"],
                "parameters": tool.get("inputSchema") or {"type": "object", "properties": {}},
            },
        }
        for tool in tools
    ]


def _post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code >= 400:
        raise Exception(f"LLM API error {resp.status_code}: {resp.text[:2000]}")
    try:
        return resp.json()
    except Exception as exc:
        raise Exception(f"Invalid JSON response from LLM API: {exc}. Body: {resp.text[:1000]}")


def _chat_openai_compatible(settings, module_doc, api_key: str, model: str, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], user_message: str) -> Dict[str, Any]:
    provider = module_doc.provider or "OpenAI Compatible"
    base_url = (module_doc.api_base_url or "").rstrip("/")
    if not base_url:
        base_url = "https://api.openai.com/v1"
    url = f"{base_url}/chat/completions"
    timeout = int(module_doc.request_timeout or 120)
    max_tool_calls = int(settings.max_tool_calls or 6)
    max_result_chars = int(settings.max_tool_result_chars or 60000)

    headers = _headers(module_doc, api_key, provider)
    extra_payload = _safe_json_loads(module_doc.extra_payload_json)
    tool_specs = _openai_tool_specs(tools) if module_doc.supports_tools else []

    tool_trace = []
    working_messages = list(messages)

    for _ in range(max_tool_calls + 1):
        payload = {
            "model": model,
            "messages": working_messages,
            "temperature": float(settings.temperature if settings.temperature is not None else module_doc.temperature or 0.1),
            "max_tokens": int(settings.max_tokens or module_doc.max_tokens or 4000),
        }
        if tool_specs:
            payload["tools"] = tool_specs
            payload["tool_choice"] = "auto"
        payload.update(extra_payload)

        data = _post_json(url, headers, payload, timeout)
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            return {"answer": content, "tool_trace": tool_trace, "raw_finish_reason": choice.get("finish_reason")}

        working_messages.append(message)

        for call in tool_calls:
            function = call.get("function") or {}
            tool_name = function.get("name")
            raw_args = function.get("arguments") or "{}"
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
            except Exception:
                args = {}

            try:
                tool_result = _execute_tool(tool_name, args, user_message=user_message)
            except Exception as exc:
                tool_result = {"success": False, "tool_name": tool_name, "error": str(exc), "error_type": type(exc).__name__}
                frappe.log_error(title="SAG Local Chat Tool Failed", message=frappe.get_traceback())

            tool_trace.append(tool_result)
            working_messages.append({
                "role": "tool",
                "tool_call_id": call.get("id"),
                "name": tool_name,
                "content": _json_dumps_safe(tool_result, max_result_chars),
            })

    return {
        "answer": "تم الوصول إلى الحد الأقصى لعدد استدعاءات الأدوات لهذه الرسالة. يرجى تضييق الطلب أو زيادة Max Tool Calls.",
        "tool_trace": tool_trace,
        "raw_finish_reason": "max_tool_calls_reached",
    }


def _gemini_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Best-effort JSON schema cleanup for Gemini function declarations."""
    if not isinstance(schema, dict):
        return {"type": "object", "properties": {}}
    allowed = {"type", "properties", "required", "description", "items", "enum"}
    cleaned = {k: v for k, v in schema.items() if k in allowed}
    if "properties" in cleaned and isinstance(cleaned["properties"], dict):
        cleaned["properties"] = {k: _gemini_schema(v) for k, v in cleaned["properties"].items() if isinstance(v, dict)}
    if "items" in cleaned and isinstance(cleaned["items"], dict):
        cleaned["items"] = _gemini_schema(cleaned["items"])
    cleaned.setdefault("type", "object")
    return cleaned


def _chat_gemini(settings, module_doc, api_key: str, model: str, history: List[Dict[str, str]], user_message: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    base_url = (module_doc.api_base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    url = f"{base_url}/models/{model}:generateContent?key={api_key}"
    timeout = int(module_doc.request_timeout or 120)
    max_tool_calls = int(settings.max_tool_calls or 6)
    max_result_chars = int(settings.max_tool_result_chars or 60000)
    headers = _headers(module_doc, api_key, "Gemini")

    contents = []
    for row in history:
        role = "model" if row["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": row["content"]}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    declarations = [
        {"name": t["name"], "description": t.get("description") or t["name"], "parameters": _gemini_schema(t.get("inputSchema") or {})}
        for t in tools
    ] if module_doc.supports_tools else []

    tool_trace = []
    system_instruction = _build_system_prompt(settings, tools)

    for _ in range(max_tool_calls + 1):
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {
                "temperature": float(settings.temperature if settings.temperature is not None else module_doc.temperature or 0.1),
                "maxOutputTokens": int(settings.max_tokens or module_doc.max_tokens or 4000),
            },
        }
        if declarations:
            payload["tools"] = [{"function_declarations": declarations}]
        payload.update(_safe_json_loads(module_doc.extra_payload_json))

        data = _post_json(url, headers, payload, timeout)
        candidate = (data.get("candidates") or [{}])[0]
        parts = (((candidate.get("content") or {}).get("parts")) or [])

        function_calls = [p.get("functionCall") for p in parts if p.get("functionCall")]
        text_parts = [p.get("text") for p in parts if p.get("text")]

        if not function_calls:
            return {"answer": "\n".join(text_parts), "tool_trace": tool_trace, "raw_finish_reason": candidate.get("finishReason")}

        contents.append({"role": "model", "parts": parts})
        response_parts = []
        for fc in function_calls:
            tool_name = fc.get("name")
            args = fc.get("args") or {}
            try:
                tool_result = _execute_tool(tool_name, args, user_message=user_message)
            except Exception as exc:
                tool_result = {"success": False, "tool_name": tool_name, "error": str(exc), "error_type": type(exc).__name__}
                frappe.log_error(title="SAG Local Chat Gemini Tool Failed", message=frappe.get_traceback())
            tool_trace.append(tool_result)
            response_parts.append({"functionResponse": {"name": tool_name, "response": {"content": _json_dumps_safe(tool_result, max_result_chars)}}})
        contents.append({"role": "user", "parts": response_parts})

    return {"answer": "تم الوصول إلى الحد الأقصى لعدد استدعاءات الأدوات.", "tool_trace": tool_trace, "raw_finish_reason": "max_tool_calls_reached"}


@frappe.whitelist()
def get_boot() -> Dict[str, Any]:
    _assert_access()
    settings, module_doc, _api_key, model = _get_settings_and_module()
    tools = _available_tools()
    return {
        "success": True,
        "user": frappe.session.user,
        "settings": {
            "chat_title": settings.chat_title or "SAG Local Chat",
            "chat_module": settings.chat_module,
            "provider": module_doc.provider,
            "model": model,
            "default_language": settings.default_language,
            "max_tool_calls": settings.max_tool_calls,
            "max_tool_result_chars": settings.max_tool_result_chars,
            "keep_chat_history": settings.keep_chat_history,
            "max_history_messages": settings.max_history_messages,
        },
        "tools": [{"name": t["name"], "description": t["description"]} for t in tools],
        "tool_count": len(tools),
    }


@frappe.whitelist(methods=["POST"])
def send_message(message: str, history: Any = None) -> Dict[str, Any]:
    _assert_access()
    message = (message or "").strip()
    if not message:
        frappe.throw(_("Message is required."))

    settings, module_doc, api_key, model = _get_settings_and_module()
    tools = _available_tools()
    max_history = int(settings.max_history_messages or 20)
    clean_history = _prepare_history(history, max_history)

    system_prompt = _build_system_prompt(settings, tools)
    provider = module_doc.provider or "OpenAI Compatible"

    started = time.time()
    try:
        if provider == "Gemini":
            result = _chat_gemini(settings, module_doc, api_key, model, clean_history, message, tools)
        elif provider in {"OpenAI", "Mistral", "OpenRouter", "Groq", "Ollama", "OpenAI Compatible", "Custom", "Anthropic"}:
            if provider == "Anthropic":
                # Use Anthropic through an OpenAI-compatible proxy only in this first local chat patch.
                # Set provider to OpenAI Compatible if your gateway exposes /chat/completions.
                frappe.throw(_("Anthropic native messages API is not enabled in this patch. Use OpenAI Compatible endpoint or another provider."))
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(clean_history)
            messages.append({"role": "user", "content": message})
            result = _chat_openai_compatible(settings, module_doc, api_key, model, messages, tools, message)
        else:
            frappe.throw(_("Unsupported provider: {0}").format(provider))

        answer = result.get("answer") or ""
        if not answer:
            answer = "تم تنفيذ الطلب، لكن النموذج لم يرجع نصًا واضحًا."
        elapsed_ms = int((time.time() - started) * 1000)
        return {
            "success": True,
            "answer": answer,
            "tool_trace": result.get("tool_trace") or [],
            "tool_calls_count": len(result.get("tool_trace") or []),
            "provider": provider,
            "model": model,
            "execution_ms": elapsed_ms,
            "finish_reason": result.get("raw_finish_reason"),
        }
    except Exception as exc:
        frappe.log_error(title="SAG Local Chat Failed", message=frappe.get_traceback())
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@frappe.whitelist()
def clear_browser_history_notice() -> Dict[str, Any]:
    _assert_access()
    return {"success": True, "message": "History is stored in browser localStorage. Use the page Clear button."}

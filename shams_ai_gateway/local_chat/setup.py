# Utility functions for SAG Local Chat setup.
# Run manually after migrate:
# bench --site <site> execute shams_ai_gateway.local_chat.setup.install_default_chat_modules

import frappe


DEFAULT_CHAT_MODULES = [
    {
        "module_code": "openai",
        "module_name": "OpenAI",
        "provider": "OpenAI",
        "api_base_url": "https://api.openai.com/v1",
        "default_chat_model": "gpt-4.1-mini",
        "default_ocr_model": "gpt-4.1-mini",
        "supports_tools": 1,
        "supports_vision": 1,
        "supports_ocr": 1,
        "supports_streaming": 1,
    },
    {
        "module_code": "mistral",
        "module_name": "Mistral",
        "provider": "Mistral",
        "api_base_url": "https://api.mistral.ai/v1",
        "default_chat_model": "mistral-medium-latest",
        "default_ocr_model": "mistral-ocr-latest",
        "supports_tools": 1,
        "supports_vision": 1,
        "supports_ocr": 1,
        "supports_streaming": 1,
    },
    {
        "module_code": "gemini",
        "module_name": "Gemini",
        "provider": "Gemini",
        "api_base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_chat_model": "gemini-1.5-pro",
        "default_ocr_model": "gemini-1.5-pro",
        "supports_tools": 1,
        "supports_vision": 1,
        "supports_ocr": 1,
        "supports_streaming": 1,
    },
    {
        "module_code": "openrouter",
        "module_name": "OpenRouter",
        "provider": "OpenRouter",
        "api_base_url": "https://openrouter.ai/api/v1",
        "default_chat_model": "openai/gpt-4o-mini",
        "supports_tools": 1,
        "supports_vision": 1,
        "supports_ocr": 0,
        "supports_streaming": 1,
    },
    {
        "module_code": "ollama",
        "module_name": "Ollama Local",
        "provider": "Ollama",
        "api_base_url": "http://127.0.0.1:11434/v1",
        "default_chat_model": "llama3.1",
        "supports_tools": 0,
        "supports_vision": 0,
        "supports_ocr": 0,
        "supports_streaming": 1,
    },
    {
        "module_code": "openai-compatible",
        "module_name": "OpenAI Compatible",
        "provider": "OpenAI Compatible",
        "api_base_url": "",
        "default_chat_model": "",
        "supports_tools": 1,
        "supports_vision": 0,
        "supports_ocr": 0,
        "supports_streaming": 1,
    },
]


@frappe.whitelist()
def install_default_chat_modules():
    created = []
    updated = []

    for row in DEFAULT_CHAT_MODULES:
        name = row["module_code"]
        if frappe.db.exists("Chat Module", name):
            doc = frappe.get_doc("Chat Module", name)
            changed = False
            for key, value in row.items():
                if key == "module_code":
                    continue
                if doc.get(key) in (None, "") and value not in (None, ""):
                    doc.set(key, value)
                    changed = True
            if changed:
                doc.save(ignore_permissions=True)
                updated.append(name)
        else:
            doc = frappe.get_doc({"doctype": "Chat Module", "enabled": 1, **row})
            doc.insert(ignore_permissions=True)
            created.append(name)

    # Set SAG Local Chat Settings default to OpenAI if empty.
    settings = frappe.get_single("SAG Local Chat Settings")
    if not settings.chat_module and frappe.db.exists("Chat Module", "openai"):
        settings.chat_module = "openai"
        settings.save(ignore_permissions=True)

    frappe.db.commit()
    return {"created": created, "updated": updated}

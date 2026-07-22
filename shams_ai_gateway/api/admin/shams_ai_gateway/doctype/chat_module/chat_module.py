# Copyright (c) 2026, Shams Solutions
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document


DEFAULT_BASE_URLS = {
    "OpenAI": "https://api.openai.com/v1",
    "Mistral": "https://api.mistral.ai/v1",
    "Gemini": "https://generativelanguage.googleapis.com/v1beta",
    "Anthropic": "https://api.anthropic.com/v1",
    "OpenRouter": "https://openrouter.ai/api/v1",
    "Groq": "https://api.groq.com/openai/v1",
    "Ollama": "http://127.0.0.1:11434/v1",
}


class ChatModule(Document):
    def validate(self):
        self.module_code = (self.module_code or "").strip().lower().replace(" ", "-").replace("_", "-")
        self.module_name = (self.module_name or "").strip()

        if not self.module_code:
            frappe.throw("Module Code is required")

        if self.provider in DEFAULT_BASE_URLS and not self.api_base_url:
            self.api_base_url = DEFAULT_BASE_URLS[self.provider]

        self._validate_json_field("extra_headers_json")
        self._validate_json_field("extra_payload_json")

    def _validate_json_field(self, fieldname):
        value = self.get(fieldname)
        if not value:
            return
        try:
            parsed = json.loads(value)
        except Exception as exc:
            frappe.throw(f"{fieldname} must be valid JSON: {exc}")
        if not isinstance(parsed, dict):
            frappe.throw(f"{fieldname} must be a JSON object")

    def get_api_key_value(self):
        return self.get_password("api_key")

# Copyright (c) 2026, Shams Solutions
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FACLocalChatSettings(Document):
    def validate(self):
        if self.chat_module:
            if not frappe.db.exists("Chat Module", self.chat_module):
                frappe.throw("Selected Chat Module does not exist")
            enabled = frappe.db.get_value("Chat Module", self.chat_module, "enabled")
            if not enabled:
                frappe.throw("Selected Chat Module is disabled")

        if not self.max_tool_calls or int(self.max_tool_calls) < 1:
            self.max_tool_calls = 6

        if not self.max_tool_result_chars or int(self.max_tool_result_chars) < 1000:
            self.max_tool_result_chars = 60000

    def get_effective_chat_module(self):
        if not self.chat_module:
            frappe.throw("Please select a Chat Module in SAG Local Chat Settings")

        module_doc = frappe.get_doc("Chat Module", self.chat_module)
        if not module_doc.enabled:
            frappe.throw("Selected Chat Module is disabled")

        return module_doc

    def get_effective_model(self):
        module_doc = self.get_effective_chat_module()
        return self.selected_model or module_doc.default_chat_model

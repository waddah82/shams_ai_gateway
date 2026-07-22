# Shams AI Gateway - AI Assistant integration for Frappe Framework
# Copyright (C) 2025 Paul Clinton
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Migration patch to install system skills for existing sites.
"""

import frappe


def execute():
    """Install system skills and set skill_mode default for existing sites."""
    frappe.reload_doc("shams_ai_gateway", "doctype", "shams_ai_gateway_settings")
    frappe.reload_doc("shams_ai_gateway", "doctype", "sag_skill")

    # Set default for new skill_mode field
    frappe.db.set_single_value("Shams AI Gateway Settings", "skill_mode", "supplementary")

    from shams_ai_gateway.utils.migration_hooks import _install_system_skills

    _install_system_skills()

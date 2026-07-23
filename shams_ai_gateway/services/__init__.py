# Shams AI Gateway - Services Module
# Copyright (C) 2025 Paul Clinton

"""
Services module for Shams AI Gateway

SSE Bridge has been deprecated and removed.
Use StreamableHTTP (OAuth-based) transport instead.
"""

# Import version from parent module
try:
    from shams_ai_gateway import __version__
except ImportError:
    __version__ = "unknown"

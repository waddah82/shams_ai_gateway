# (license header unchanged)
"""
ChatGPT-Compatible Search Tool
...
"""

from typing import Any, Dict

import frappe
from frappe import _

from shams_ai_gateway.core.base_tool import BaseTool


class ChatGPTSearch(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "search"
        self.description = "Search for documents using OpenAI Vector Store search. Returns a list of search results with basic information. Use the fetch tool to get complete document content."

        self.inputSchema = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string. Natural language queries work best for semantic search.",
                }
            },
            "required": ["query"],
        }

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = arguments.get("query", "").strip()
            if not query:
                return {"results": []}

            from .search_tools import SearchTools

            target_url = getattr(frappe.local, "target_site_url", None)
            search_result = SearchTools.global_search(query=query, limit=20, site_url=target_url)

            results = []
            if search_result.get("success") and search_result.get("results"):
                for item in search_result.get("results", []):
                    doctype = item.get("doctype", "Document")
                    name = item.get("name", "")
                    title = item.get("title") or name or "Untitled"
                    result_id = f"{doctype}/{name}"
                    site_url = frappe.utils.get_url()
                    url = f"{site_url}/app/{frappe.scrub(doctype)}/{name}"
                    results.append({"id": result_id, "title": title, "url": url})

            return {"results": results}

        except Exception as e:
            frappe.log_error(title=_("ChatGPT Search Error"), message=f"Error in ChatGPT search: {str(e)}")
            return {"results": []}


chatgpt_search = ChatGPTSearch
import json

import requests
import frappe


def remote_frappe_call(site_name_or_url, method_path, params=None, http_method="GET"):
    """
    Execute a REST API call to a remote Frappe site.

    The first argument can be either:
      - A domain/URL (e.g., "customer1.example.com") that matches a record in
        "SAG Client Site".
      - The full URL (e.g., "https://customer1.example.com") that is stored in
        the remote site's `site_url` field (with or without protocol).

    The function looks up the matching enabled "SAG Client Site" record and
    uses its API credentials to perform the request.

    Args:
        site_name_or_url: Domain or full URL of the remote site.
        method_path: API endpoint path (e.g., "frappe.client.get_list" or
            "DocType/name").
        params: Query parameters (GET) or JSON body (POST/PUT/DELETE).
        http_method: HTTP method (GET, POST, PUT, DELETE).

    Returns:
        The JSON response from the remote site, or an error dict.
    """
    if not site_name_or_url:
        return {"error": "site_name_or_url is required"}

    # Normalize the input: remove any protocol and trailing slash to get the
    # pure domain part that is stored in site_url.
    clean_domain = site_name_or_url.strip().rstrip("/")
    if clean_domain.startswith("http://") or clean_domain.startswith("https://"):
        # Extract domain
        clean_domain = clean_domain.split("://", 1)[1].split("/", 1)[0]

    # Look up an active client site matching that domain
    site_name = frappe.db.get_value(
        "SAG Client Site",
        {"site_url": clean_domain, "is_active": 1},
        "name"
    )
    if not site_name:
        return {"error": f"No active client site found with domain: {clean_domain}"}

    site_doc = frappe.get_doc("SAG Client Site", site_name)

    # Build the full base URL using the protocol flag
    protocol = "http" if site_doc.use_http else "https"
    base_url = f"{protocol}://{site_doc.site_url}"

    # Construct the full endpoint URL
    if method_path.startswith("frappe."):
        url = f"{base_url}/api/method/{method_path}"
    else:
        url = f"{base_url}/api/resource/{method_path}"

    headers = {
        "Authorization": f"token {site_doc.api_key}:{site_doc.get_password('api_secret')}",
        "Content-Type": "application/json"
    }

    try:
        if http_method.upper() == "GET":
            # Frappe's HTTP API expects structured query values such as
            # fields and filters as one JSON-encoded parameter. Passing Python
            # lists directly to requests expands them into repeated keys
            # (fields=name&fields=posting_date), which frappe.client.get_list
            # rejects. Preserve scalar values and JSON-encode containers.
            query_params = {
                key: json.dumps(value, ensure_ascii=False)
                if isinstance(value, (dict, list, tuple))
                else value
                for key, value in (params or {}).items()
            }
            resp = requests.get(url, headers=headers, params=query_params, timeout=20)
        elif http_method.upper() == "DELETE":
            resp = requests.delete(url, headers=headers, params=params, timeout=20)
        else:  # POST, PUT, etc.
            resp = requests.request(http_method, url, headers=headers, json=params, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        frappe.log_error(title="Remote Frappe Call Failed", message=str(e))
        return {"error": str(e)}

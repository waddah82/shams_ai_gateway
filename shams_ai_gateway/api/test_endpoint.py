import frappe

@frappe.whitelist(allow_guest=True, methods=["POST"])
def test_auth():
    """Test endpoint that mimics the authentication logic."""
    from werkzeug.wrappers import Response

    auth_header = frappe.request.headers.get("Authorization", "")
    if not auth_header:
        response = Response()
        response.status_code = 401
        response.data = frappe.as_json({"error": "No Authorization header"})
        response.mimetype = "application/json"
        return response

    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if ":" in token:
            api_key, api_secret = token.split(":", 1)
            site_name = frappe.db.get_value(
                "SAG Client Site",
                {"api_key": api_key, "is_active": 1},
                "name"
            )
            if site_name:
                from frappe.utils.password import get_decrypted_password
                decrypted = get_decrypted_password("SAG Client Site", site_name, "api_secret")
                if api_secret == decrypted:
                    site_doc = frappe.get_doc("SAG Client Site", site_name)
                    protocol = "http" if site_doc.use_http else "https"
                    return {
                        "success": True,
                        "target_site_url": f"{protocol}://{site_doc.site_url}",
                    }

    response = Response()
    response.status_code = 401
    response.data = frappe.as_json({"error": "Invalid credentials"})
    response.mimetype = "application/json"
    return response
import frappe
import requests
from frappe import _

@frappe.whitelist()
def call_client_site_api(client_site_name, method, payload=None, http_method="POST"):
    """
    دالة وسيطة لتنفيذ أوامر وميثودز Frappe على سايت العميل عن بُعد.
    """
    if not frappe.db.exists("SAG Client Site", client_site_name):
        frappe.throw(_("سايت العميل {0} غير مسجل في النظام المركزي").format(client_site_name))
        
    client_site = frappe.get_doc("SAG Client Site", client_site_name)
    
    if not client_site.is_active:
        frappe.throw(_("سايت العميل {0} متوقف حالياً").format(client_site_name))
        
    protocol = "http" if client_site.use_http else "https"
    url = f"{protocol}://{client_site.site_url}/api/method/{method}"
    
    headers = {
        "Authorization": f"token {client_site.api_key}:{client_site.get_password('api_secret')}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        if http_method.upper() == "POST":
            response = requests.post(url, json=payload or {}, headers=headers, timeout=20)
        else:
            response = requests.get(url, params=payload or {}, headers=headers, timeout=20)
            
        if response.status_code == 200:
            return response.json().get("message")
        else:
            frappe.log_error(f"خطأ من سايت العميل {client_site_name}: {response.text}", "SAG Gateway Error")
            frappe.throw(_("فشل الاتصال بسايت العميل: {0}").format(response.json().get('exception', response.text)))
            
    except requests.exceptions.RequestException as e:
        frappe.log_error(f"فشل الاتصال بالخادم: {str(e)}", "SAG Gateway Connection Exception")
        frappe.throw(_("تعذر الوصول إلى خادم العميل، يرجى التحقق من الرابط أو الشبكة."))
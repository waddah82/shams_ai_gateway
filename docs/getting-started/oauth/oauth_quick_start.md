# OAuth Quick Start Guide

## 🚀 Get Started in 2 Minutes

### Step 1: Open Settings
1. Go to your Frappe site
2. Search for "Shams AI Gateway Settings"
3. Click the **OAuth** tab

### Step 2: Enable OAuth
Check the box: ✅ **Enable Dynamic Client Registration**

### Step 3: Configure Client Access

**For MCP Inspector (testing):**
In "Allowed Public Client Origins", add:
```
http://localhost:6274
```

**For Claude Desktop:**
Leave "Allowed Public Client Origins" blank (Claude Desktop doesn't need it)

**For your web app:**
Add your app's URL:
```
https://your-app.com
```

### Step 4: Save
Click **Save** button

---

## ✅ That's It!

Your OAuth is now configured. MCP clients can auto-register and connect.

---

## 🧪 Test with MCP Inspector

1. Open http://localhost:6274/
2. Select "Streamable HTTP"
3. Enter your MCP endpoint URL:
   ```
   https://your-frappe-site.com/api/method/shams_ai_gateway.api.sag_endpoint.handle_mcp
   ```
4. Click "Open Auth Settings"
5. Click "Quick OAuth Flow"
6. Authorize when prompted ✅

---

## 🎯 What You See

### Main Section (Always Visible)
```
┌─────────────────────────────────────────────┐
│ OAuth Configuration                         │
├─────────────────────────────────────────────┤
│ ☑ Enable Dynamic Client Registration        │
│                                             │
│ Allowed Public Client Origins:              │
│ ┌─────────────────────────────────────────┐ │
│ │ http://localhost:6274                   │ │
│ │ https://your-app.com                    │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Advanced Settings (Collapsed)
**Don't touch these unless you know what you're doing!**

Click to expand "Advanced OAuth Settings" only if needed.

### Resource Metadata (Collapsed)
**Optional branding info - skip for now**

Click to expand "Resource Metadata" only if you want to customize URLs.

---

## 🔒 Security Quick Tips

✅ **DO:**
- Use specific URLs in "Allowed Public Client Origins"
- Use HTTPS in production
- Keep "Skip Authorization Prompt" disabled

❌ **DON'T:**
- Use `*` in production (allows all origins)
- Enable "Skip Authorization Prompt" in production
- Share OAuth client secrets

---

## 🐛 Common Issues

### "Dynamic client registration is not enabled"
→ Check the box: ✅ Enable Dynamic Client Registration

### "CORS error"
→ Add your client's URL to "Allowed Public Client Origins"

### "redirect_uris must be https"
→ Use `https://` or `http://localhost:` only

---

## 📚 Need More Help?

Read the full guide: [OAuth Setup Guide](./oauth_setup_guide.md)

---

## 🎉 You're All Set!

Your Shams AI Gateway is now OAuth-enabled and ready for MCP clients.

Questions? Open an issue: https://github.com/buildswithpaul/Shams_AI_Gateway/issues

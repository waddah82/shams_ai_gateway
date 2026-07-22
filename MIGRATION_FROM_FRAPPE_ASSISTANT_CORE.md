# Migration from frappe_shams_ai_gateway

This release changes the Python package, Frappe app name, routes, and `FAC`-prefixed identifiers. It is a breaking change for an existing installation.

1. Take a full backup and test on a cloned site.
2. Do not overwrite the old app while the site still lists `frappe_shams_ai_gateway` as installed.
3. Fresh installations can install `shams_ai_gateway` normally.
4. Existing installations require database renaming/migration of installed-app and DocType/Page references before the old app is removed.

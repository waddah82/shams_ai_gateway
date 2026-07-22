# Inspection Report

## Scope

- Renamed Frappe app and Python package from `frappe_assistant_core` to `shams_ai_gateway`.
- Renamed the Frappe module from `Assistant Core` to `Shams AI Gateway`.
- Renamed `FAC` identifiers, routes, files, DocTypes, Pages, API modules, CSS selectors, and JavaScript identifiers to `SAG`.
- Renamed `Assistant Core Settings` to `Shams AI Gateway Settings`.

## Removed files

The following categories were removed because they are generated, vendored, cached, or confirmed unreferenced backups:

- `.git/`
- root `node_modules/`
- `shams_ai_gateway/public/node_modules/`
- `frappe_assistant_core.egg-info/`
- all `__pycache__/` directories and `.pyc` files
- empty root `__init__.py`
- duplicate backup files ending in `1`, `2`, or `01` that had an active canonical counterpart and no references

## Validation performed

- Parsed every JSON file successfully.
- Compiled every Python source file successfully with `compileall`.
- Verified every patch path in `patches.txt` resolves to an existing Python file.
- Verified DocType controller files and Page JavaScript files exist.
- Scanned the active source for remaining old app/module/FAC identifiers; only historical attribution and migration documentation intentionally retain the old name.

## Important migration warning

This package is internally renamed, not merely rebranded. Installing it over a site that currently has `frappe_assistant_core` installed requires a controlled database migration. Use a cloned site and full backup. A fresh installation is the safest deployment path.

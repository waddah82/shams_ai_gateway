---
name: document-doctype
description: Generate structured technical and business documentation for a Frappe or ERPNext DocType. Use when asked to explain or document a DocType, its fields, child tables, links, permissions, statuses, workflows, validations, API usage, or common record examples.
---

# Document a DocType

## Inspect before writing

1. Call `get_doctype_info` for authoritative metadata: fields, types, requirements, options, links, child tables, submission behavior, and permissions.
2. Use `list_documents` only when representative records are useful and permitted. Never expose sensitive values in examples.
3. Use `get_document` only for a specifically authorized example record.
4. If workflow details are not returned by metadata, query the relevant Workflow configuration with read-only tools and label any inferred transitions.

## Produce documentation

Include:

1. Purpose and business position.
2. Lifecycle, `docstatus`, statuses, and workflow actions.
3. Field reference grouped by sections, including required fields, defaults, options, links, read-only fields, and dependencies.
4. Child tables and their row structure.
5. Relationships, linked documents, and deletion/submission implications.
6. Permissions and role considerations without claiming permissions not verified.
7. Common use cases, validations, and pitfalls.
8. API examples when requested, using current Frappe patterns and exact fieldnames.

Separate metadata-confirmed facts from business interpretation. Do not invent validations, workflows, or field meanings.


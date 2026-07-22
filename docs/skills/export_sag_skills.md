---
name: export-sag-skills
description: Export one specific or all published ERPNext SAG Skill records into installable skill archives containing valid SKILL.md files. Use when asked to download, package, back up, migrate, or install SAG Skills from the SAG Skill DocType into Claude, ChatGPT, or Codex.
---

# Export SAG Skills

## Fetch

Use `list_documents` with DocType `SAG Skill`, status `Published`, and fields `name`, `skill_id`, `title`, `description`, `content`, and `skill_type`. Filter by `skill_id` for a specific export. Stop clearly if no matching published record exists.

## Normalize

For each non-empty skill:

1. Use `skill_id` as a lowercase hyphenated folder and skill name; reject unsafe paths.
2. If `content` already has YAML frontmatter, preserve the body but normalize frontmatter to exactly `name` and `description`.
3. Otherwise prepend:

```yaml
---
name: <skill-id>
description: <what the skill does and when it should trigger>
---
```

4. Keep instructions concise and preserve meaningful examples and safeguards.
5. Skip empty content and report it.

## Validate and package

Create `<skill-id>/SKILL.md`, validate its YAML and naming, then package that folder as `<skill-id>.skill`. For an all-skills request, create each individual archive and a combined ZIP containing them. Build files in the local execution environment, not in ERPNext's sandboxed Python tool.

Report the exported count, skill names, skipped records, and validation failures. Do not claim that packaging installs the skill; installation is a separate client-side action.




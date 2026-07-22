---
name: audit-data-quality
description: Perform a read-only data-quality audit on a Frappe or ERPNext DocType for completeness, consistency, duplicates, invalid links, anomalies, and business-rule violations. Use for data cleanup assessment, migration readiness, missing-field analysis, duplicate detection, integrity checks, or data-quality reports.
---

# Audit Data Quality

## Keep the audit read-only

Do not update, merge, or delete records during an audit. Recommend corrections separately and request explicit authorization before any mutation.

## Establish scope

Confirm DocType, company or organizational scope, time range, candidate duplicate keys, and relevant business rules. If these are unknown, inspect metadata and report which rules are structural versus business-specific.

## Inspect and extract

1. Use `get_doctype_info` to identify required fields, types, options, Link targets, unique fields, and child tables.
2. Use `run_database_query` for aggregate checks, null rates, duplicate candidates, invalid patterns, orphan links, and distributions.
3. Use `list_documents` for bounded samples of affected records.
4. Use `analyze_business_data` for profiling, statistics, anomalies, trends, and correlations. Use `run_python_code` only for additional safe calculations on retrieved data.

Respect permissions and avoid returning sensitive field values unnecessarily. Use stable record names for remediation lists.

## Audit dimensions

- Completeness: required and important optional field fill rates.
- Uniqueness: exact and normalized duplicate candidates; never auto-merge fuzzy matches.
- Validity: field types, options, ranges, formats, dates, and business rules.
- Consistency: conflicting statuses, units, currencies, naming, and cross-field rules.
- Integrity: missing Link targets and child-row anomalies.
- Timeliness: stale records and quality changes across the selected period.

## Report

Provide an executive scorecard, test definitions, counts and rates, severity, bounded record samples, limitations, remediation priority, and preventive controls. Distinguish confirmed defects from candidates requiring review.


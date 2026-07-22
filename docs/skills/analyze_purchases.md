---
name: analyze-purchases
description: Analyze ERPNext procurement performance, supplier reliability, purchase costs, lead times, pending orders, and inventory implications. Use for purchase analysis, spend analysis, supplier performance, price variance, procurement efficiency, cost reduction, reorder, overstock, or dead-stock requests.
---

# Analyze Purchases

## Establish scope

Confirm company, date range, currency, focus, and whether inventory analysis is required. Default to the last complete month with an equivalent prior-period comparison.

## Gather reliable data

1. Prefer `report_list` → `report_requirements` → `generate_report` for standard procurement and stock reports.
2. Inspect schemas with `get_doctype_info` before querying.
3. Use `run_database_query` for spend, supplier, item, and cycle-time aggregations; use `list_documents` for discovery.
4. Use `analyze_business_data` for trends and anomalies; reserve `run_python_code` for derived calculations.

Use submitted Purchase Invoices, Purchase Orders, and Purchase Receipts as appropriate to each metric. Separate taxes, returns, cancelled documents, and currencies. Do not treat PO value as realized spend. Reconcile totals before analysis.

## Analyze

- Procurement: invoice spend, ordered value, received value, trends, and budget variance when budgets exist.
- Suppliers: value, delivery timeliness, lead time, short receipt, rejection, concentration, and reliability.
- Costs: item price history, price variance, inflation signals, and savings opportunities.
- Process: Material Request to PO and PO to receipt cycle times, open orders, delays, and partial receipts.
- Inventory: reorder exposure, stockouts, excess stock, slow/dead stock, and working-capital impact when requested.

## Report

Provide an executive summary, definitions, reconciled KPIs, supplier and item findings, exceptions, risks, and prioritized cost/process recommendations. Label estimates and data limitations.


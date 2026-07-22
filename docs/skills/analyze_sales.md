---
name: analyze-sales
description: Analyze ERPNext sales performance using revenue, customers, products, pipeline, territories, and period comparisons. Use for requests to analyze sales, revenue trends, customer concentration, product performance, quotations, orders, invoices, sales teams, or territory results.
---

# Analyze Sales

## Establish scope

Confirm or infer the company, date range, currency, analysis focus, and whether to include territories. Default to the last complete month and compare it with the preceding equivalent period. State every assumption.

## Gather reliable data

1. Use `report_list`, `report_requirements`, then `generate_report` when a standard ERPNext sales report fits.
2. Use `get_doctype_info` before unfamiliar DocTypes or fields.
3. Use `run_database_query` for controlled aggregations and joins; use `list_documents` for record-level discovery.
4. Use `analyze_business_data` for profiles, trends, statistics, quality, and correlations. Use `run_python_code` only for additional calculations on already retrieved data.

Base booked revenue on submitted Sales Invoices. Separate returns, taxes, discounts, and cancelled or draft documents. Do not combine currencies without conversion rules. Reconcile headline totals to the source report before interpreting them.

## Analyze

- Revenue: totals, net sales, growth, seasonality, anomalies, and prior-period comparison.
- Customers: top customers, concentration, acquisition/retention signals, and segments.
- Products: best sellers, item groups, quantities, margins when cost data is available, and slow movers.
- Pipeline: Quotation to Sales Order conversion, open values, aging, and sales-cycle duration.
- Territories and teams: include only when requested and supported by populated fields.
- KPIs: average order value, growth rate, return rate, conversion rate, and concentration.

## Report

Present an executive summary, scope and assumptions, reconciled KPI table, trends, drivers, exceptions, and prioritized actions. Distinguish facts from inferences and disclose missing or weak data.


---
name: analyze-manufacturing
description: Analyze ERPNext manufacturing performance across Work Orders, BOMs, production quantities, material consumption, Job Cards, cycle time, bottlenecks, and quality. Use for production efficiency, work-order status, BOM cost, material variance, throughput, delays, defects, or overall manufacturing analysis.
---

# Analyze Manufacturing

## Establish scope

Confirm company, plants or warehouses, date range, analysis focus, and whether quality inspection is included. State assumptions and compare with an equivalent prior period when useful.

## Gather reliable data

1. Discover standard manufacturing reports with `report_list`, inspect requirements, and run them with `generate_report` when suitable.
2. Use `get_doctype_info` for Work Order, BOM, Stock Entry, Job Card, and Quality Inspection structures.
3. Use `run_database_query` for controlled production, time, cost, and material aggregations.
4. Use `analyze_business_data` for trends and anomalies; use `run_python_code` only for additional derived metrics.

Separate planned, in-process, completed, stopped, and cancelled work. Distinguish planned quantities from completed quantities and planned consumption from actual manufacture Stock Entries. Reconcile totals before interpretation.

## Analyze

- Production: planned versus completed quantity, completion rate, backlog, delays, and bottlenecks.
- BOM: required versus consumed material, cost drivers, substitutions, and variance.
- Efficiency: cycle time, throughput, Job Card time, idle signals, and capacity constraints where data permits.
- Quality: inspection outcomes, rejection and defect patterns when requested.
- Improvement: quantify the effect and feasibility of each recommendation.

## Report

Present an executive summary, scope, KPI table, bottlenecks, material and quality exceptions, root-cause hypotheses, and prioritized actions. Clearly identify unavailable capacity or costing data.


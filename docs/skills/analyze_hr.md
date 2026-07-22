---
name: analyze-hr
description: Analyze authorized ERPNext HR data covering workforce, departments, attendance, lateness, absence, leave, tenure, hiring, separation, payroll, overtime, and allowances. Use for HR dashboards, workforce analysis, attendance patterns, leave utilization, retention, or payroll cost analysis.
---

# Analyze HR

## Protect people data

Use only data the current user is authorized to access. Default to aggregate results. Do not expose individual salary, attendance, health, or leave details unless explicitly requested and permitted. Suppress or generalize very small groups when disclosure could identify a person.

## Establish scope

Confirm company, employee population, departments, date range, focus, and whether payroll is included. Default to the last complete month and state assumptions.

## Gather reliable data

1. Use `report_list`, `report_requirements`, and `generate_report` for standard HR and payroll reports.
2. Inspect fields with `get_doctype_info` before querying Employee, Attendance, Leave Application, Salary Slip, Department, or Designation.
3. Use `run_database_query` for authorized aggregations and `list_documents` for discovery.
4. Use `analyze_business_data` for trends and statistics; use `run_python_code` only for derived calculations.

Use submitted records where the DocType is submittable. Apply employee status and effective dates correctly. Do not infer absence solely from missing Attendance without considering shifts, holidays, leave, joining, relieving, and attendance requests.

## Analyze

- Workforce: active headcount, department, designation, employment type, tenure, hires, and separations.
- Attendance: present/absent rates, lateness, early departure, shifts, and department patterns.
- Leave: applications, utilization, types, balances, seasonality, and pending items.
- Payroll when authorized: submitted salary costs, overtime, allowances, deductions, and department trends.
- Retention: turnover and tenure patterns without making unsupported causal claims.

## Report

Provide aggregated KPIs, trends, exceptions, policy/process observations, limitations, and prioritized recommendations. Separate measured results from hypotheses.


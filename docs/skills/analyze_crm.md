---
name: analyze-crm
description: Analyze ERPNext CRM data across Leads, Opportunities, Customers, Communications, Campaigns, Contacts, and sales owners. Use for lead pipeline, conversion, opportunity stages, aging, win/loss, engagement, campaign effectiveness, follow-up, or CRM team-performance analysis.
---

# Analyze CRM

## Establish scope

Confirm company, date range, focus, owners or teams, and whether campaigns are included. Define conversion, win, loss, open pipeline, and aging before calculating them.

## Gather reliable data

1. Use `report_list`, `report_requirements`, and `generate_report` when standard CRM reports fit.
2. Inspect Lead, Opportunity, Customer, Communication, Campaign, and Contact with `get_doctype_info`.
3. Use `run_database_query` for funnel, aging, owner, and campaign aggregations; use `list_documents` for discovery.
4. Use `analyze_business_data` for distributions and trends; use `run_python_code` only for derived calculations.

Verify that status, stage, source, owner, and campaign fields are consistently populated. Do not claim satisfaction or campaign ROI unless outcome and cost data actually support it.

## Analyze

- Leads: volume, sources, conversion, aging, follow-up, and stale records.
- Opportunities: pipeline value, stage distribution, probability-weighted value when valid, win/loss, and cycle time.
- Engagement: communication frequency, channel, response or follow-up indicators.
- Campaigns: generated leads, conversions, value, and ROI only when costs are available.
- Teams: workload, activity, conversion, and outcomes; avoid ranking without accounting for assignment mix.

## Report

Present a funnel, KPIs, aging and leakage, source/campaign findings, team observations, data-quality caveats, and prioritized actions.


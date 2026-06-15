---
schema: agentcompanies/v1
kind: task
slug: kpi-setup-gate
name: KPI Setup Gate
assignee: analytics
project: askuno-runtime-proof
lifecycleStage: kpi-setup
priority: medium
dependsOn: deployment-readiness-gate
recurring: true
evidenceRequired: kpi-or-omission-record
---

# KPI Setup Gate

Define the KPI sources, telemetry shape, reporting cadence, and omission record
after deployment readiness is explicit and before Askuno Runtime Proof enters
marketing.

Acceptance:

- KPI source is named
- metrics to be captured are named
- deployment surface or deployment deferral is linked
- missing analytics are recorded as an omission
- reporting surface is named before any campaign or distribution work starts
- public metrics are separated from private operational metrics

---
schema: agentcompanies/v1
kind: task
slug: deployment-readiness-gate
name: Deployment Readiness Gate
assignee: engineering
project: askuno-runtime-proof
lifecycleStage: deployment-readiness
priority: high
dependsOn: qa-runtime-readiness
recurring: false
evidenceRequired: deployment-readiness-evidence
---

# Deployment Readiness Gate

Prepare the deployment surface for Askuno Runtime Proof without performing a
production deploy. This task records the package shape, target environment,
provider/DNS capability boundary, post-deploy QA requirement, and rollback note.

Acceptance:

- deployment target or explicit deployment deferral is named
- package shape is described
- provider credentials and DNS authority remain owner-gated
- post-deploy QA or staging validation is required before KPI/marketing claims
- rollback or recovery path is recorded
- no production deploy, DNS mutation, or public launch is performed

---
schema: agentcompanies/v1
kind: task
slug: qa-runtime-readiness
name: QA Runtime Readiness
assignee: qa
project: live-visual-studio
lifecycleStage: qa-readiness
priority: high
dependsOn: engineering-first-primitive
recurring: false
evidenceRequired: qa-evidence
---

# QA Runtime Readiness

Verify that the local runtime is usable, stable, and honest about its limits.

Acceptance:

- functional check passes
- visual evidence exists when UI changed
- unavailable live-pipeline stages are emitted as unavailable
- no Livepeer runtime proof is claimed without real output evidence

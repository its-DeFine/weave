# WEAVE Month 1 Overview

Month 1 is the lifecycle-first version of WEAVE. The goal is to get to a real working application path quickly, using an execution runtime to do the work and WEAVE to guide the lifecycle, evidence, gates, approvals, KPIs, and iteration history.

This is the low-hanging-fruit path. It keeps operating costs low, lets the application be offered cheaply, and aligns the runtime with orchestrator benefit.

As of **Saturday 2026-05-09**, the Month 1 work is in evidence packaging and
review mode after the Friday 2026-05-08 delivery window.

## Runtime authority

The active Month 1 runtime operator is Hermes. The operator-facing lifecycle
surface should make Hermes' app selection, lifecycle stage state, agent
activity, evidence paths, approval gates, and Gestalt Runtime Pack outputs
visible.

## What Month 1 delivers

Live KPI dashboard: <https://atumera.com/kpis>.

### M1-D1. The WEAVE tool and method

The WEAVE tool is the lifecycle wrapper for agent-run product work. It should be able to support the full application lifecycle end to end while keeping stage state, evidence, review gates, owner approvals, KPI signals, and iteration history visible.

That means it should be able to:
- study existing Livepeer pipelines and understand what they can do
- synthesize those pipelines into reusable primitives
- identify viable applications from those primitives
- engineer applications on top of existing Livepeer workloads
- QA those applications
- set KPI capture before marketing starts
- generate marketing workflows
- collect KPI and feedback data
- support iteration from the resulting evidence

In practical terms, Month 1 should leave behind a clear lifecycle contract, stage model, gate model, evidence model, owner approval model, and Askuno worked example.

### M1-D2. Runtime proof

The execution runtime performs the work. WEAVE wraps that runtime with a state machine, evidence ledger, review gates, and public KPI reporting.

Month 1 should deliver:
- a website or hosted runtime surface
- Hermes as the execution runtime
- an operator lifecycle surface backed by runtime evidence
- at least one real application
- engineering and QA evidence attached to lifecycle stages
- KPI setup and marketing evidence tracked honestly
- review gates marked as passed, blocked, deferred, or owner-required

Current Askuno URL state: the app is live at <https://askuno.app>.

### M1-D3. Public KPI reporting

Month 1 should also produce public reporting on what the runtime is actually doing.

That reporting should cover:
- what applications were researched and selected
- what was built
- what passed QA
- what marketing or distribution work happened
- what real usage or payment evidence exists
- what changed based on the resulting evidence

## Why this version of Month 1 is better

This version is better because it concentrates effort into a real runtime instead of splitting attention across a heavier structure.

It gives WEAVE:
- a faster path to a working application
- a lower operating cost because the agent can act as a lean operating team
- a direct path from application usage to orchestrator benefit
- a public story that is easier to understand and easier to verify

For the economics model behind that claim, see [Orchestrator Economics](orchestrator-economics.md).
For the public accountability boundary, see [Program Transparency](program-transparency.md).
For the lifecycle contract, see [WEAVE Lifecycle Contract v0](weave-lifecycle-contract-v0.md).
For the agent runtime contract, see [WEAVE Agent Operating Contract v0](weave-agent-operating-contract-v0.md).

## Governance and timing

WEAVE is maintained by Atumera LLC. Atumera does not extract profit from operating the runtime. The goal is to route value into the runtime and toward orchestrator benefit, not to create an Atumera profit-taking layer on top.

Month 2 is intentionally not fixed yet. Month 1 will be reviewed first, and Month 2 deliverables will be set after that review.

## Related document

- [Application Lifecycle Summary](app-lifecycle.md)
- [WEAVE Lifecycle Contract v0](weave-lifecycle-contract-v0.md)
- [WEAVE Agent Operating Contract v0](weave-agent-operating-contract-v0.md)
- [Orchestrator Economics](orchestrator-economics.md)
- [Program Transparency](program-transparency.md)

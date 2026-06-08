# WEAVE Lifecycle Contract v0

WEAVE is a lifecycle wrapper for agent-run product work.

It helps a human and their execution runtime move from intent to shipped
application with stage state, evidence, review gates, owner approvals, KPI
signals, and iteration history tracked as first-class objects.

## Layer Model

WEAVE separates three layers:

1. Execution runtime
   - Hermes and approved execution tools.
   - This layer reads repositories, writes code, runs tests, opens pull
     requests, queues commands, and performs approved work.

2. WEAVE wrapper and tooling
   - The lifecycle state machine, evidence ledger, review interface, gate
     model, KPI publishing contract, and owner approval process.
   - This layer guides and records the work. It is not the execution runtime
     itself.
   - Agent behavior follows the separate WEAVE Agent Operating Contract v0.

3. Application output
   - Askuno in Month 1.
   - Future WEAVE applications such as compute warrants or other Livepeer
     applications.

## Lifecycle Stages

1. Intent
2. Research
3. Selection
4. Plan
5. Engineering
6. QA
7. KPI Setup
8. Marketing
9. Iteration
10. Analysis

Each stage records a target, current state, evidence, gates, and the next review
action.

Stage changes should be append-only in evidence. Returning to an earlier stage
requires an overwrite record that names the reason and affected downstream
stages.

Stage outputs:

- Intent records the target user, application idea, constraints, authority
  boundary, and owner goal.
- Research records demand, infrastructure, pricing, competitors, technical
  risks, and unanswered questions.
- Selection records why this application is the chosen wedge and what is being
  deferred.
- Plan records tasks, done criteria, gates, and approval boundaries.
- Engineering records implementation work and the runtime lane that performed
  it.
- QA records tests, live checks, failures, fixes, and claim limits.
- KPI Setup records aggregate usage, credit, public reporting, payment, or
  monetization-path metrics before marketing starts.
- Marketing records docs, ads, onboarding, publication, or approved
  distribution actions.
- Iteration records what changed because of feedback, QA, usage, payment, or
  marketing evidence.
- Analysis records the analytics and feedback interpretation that recommends
  the next iteration.

## Review Gates

Review gates are stage-exit controls. They explain why something can or cannot
be claimed as complete.

Common gates:

- `owner_approval_required`
- `qa_pass_required`
- `public_publish_required`
- `payment_mainnet_required`
- `legal_terms_required`
- `runtime_supervisor_required`
- `kpi_publication_required`

Gate states:

- `passed`
- `blocked`
- `deferred`
- `owner_required`

The implemented local runtime treats stage approval and stage movement as two
separate deterministic controls:

- `/approve_stage [app_id] [stage]` records owner approval only after foundation
  context, prior-stage approvals, current-stage proof, blockers, and credential
  capability gates pass.
- `/advance [app_id]` moves the app to the next lifecycle stage only after the
  current stage is approved.
- `/lifecycle [app_id]` shows the current stage gate, missing proof, and
  lifecycle row state without model-generated text.

KPI Setup, Marketing, and Analysis can require credential capability. If the
owner explicitly chooses to proceed without that capability, the runtime records
a credential deferral instead of silently ignoring the missing dependency.

## Month 1 Mapping

For Month 1:

- WEAVE is the lifecycle wrapper, evidence model, gate model, and review
  surface.
- Hermes is the execution runtime.
- Askuno is the proof application.
- Atumera KPIs is the public reporting surface.
- Review gates are the lifecycle controls.

This delivers:

- M1-D1 as the WEAVE method and lifecycle contract.
- M1-D2 as the Askuno replay through that lifecycle using Hermes as the
  execution runtime.
- M1-D3 as public KPI reporting through Atumera.

## Interaction Shape

```text
human sets target
  -> WEAVE creates lifecycle record
  -> execution runtime performs approved work
  -> WEAVE records stage, evidence, gates, and KPIs
  -> human reviews gates
  -> execution runtime continues
  -> public KPI dashboard reports aggregate outcomes
```

Example command language:

```text
/create_app askuno
/status askuno
/lifecycle askuno
/requirements askuno
/approve_stage askuno intent
/advance askuno
/blockers
/next
```

Month 1 does not require the perfect terminal product. It requires a clear
contract and a convincing replay.

The historical Askuno proof ledger used eight implementation-oriented local
check categories. For reporting and future work those categories map into the
main lifecycle plus the parallel growth loop above; new WEAVE work should use
that contract directly.

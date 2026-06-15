# WEAVE V1 Backend Architecture Spec

Status: review draft before implementation.
Date: 2026-06-15
Scope: backend architecture required for the approved Textual TUI direction.

This document is the implementation bridge between the WEAVE v1 product
contract, the Textual TUI mockups, and the code that must eventually make the
product real.

It does not claim the backend is implemented. It defines what must exist before
WEAVE v1 can be honestly called functional.

## 1. Simple Model

The Textual TUI is the cockpit. The backend is the machinery behind the
cockpit.

The backend must answer these questions for the TUI:

- What app is active?
- What lifecycle stage is active?
- What is the current question for the owner?
- What choices can the owner take now?
- What artifacts, files, evidence, and blockers exist?
- What agent or QA job is running?
- What can advance safely?
- What must stop for owner approval?
- What is only planned, not executed?

The backend is not a separate web product in v1. It is a local Python service
layer used by `bin/weave tui`. A REST API can be added later, but v1 should work
as an in-process local backend for the Textual app.

## 2. Source Contracts Read

This spec consolidates these existing contracts and code surfaces:

- `docs/WEAVE_V1_PRODUCT_CONTRACT.md`
- `docs/WEAVE_V1_AGENT_ORCHESTRATION_SPEC.md`
- `docs/weave-tui-full-product-contract-v0.1.md`
- `docs/lifecycle-artifact-contracts-v0.1.md`
- `docs/weave-runtime-architecture-contract-v0.1.md`
- `docs/runtime-agent-qa-contract.md`
- `docs/capability-broker-contract-v0.1.md`
- `docs/scheduler-heartbeat-contract-v0.1.md`
- `bin/weave`
- `scripts/weave_cli.py`
- `scripts/weave_tui.py`

## 3. Backend Done State

The backend is done when the Textual TUI can drive a real local lifecycle run
from first run through QA without hidden scripts or fake state.

Minimum done state:

1. `bin/weave tui` opens the Textual cockpit.
2. The cockpit reads all visible state from backend services, not ad hoc
   terminal strings.
3. The owner can create/select an app.
4. The owner can fill owner profile and intent.
5. The backend validates intent sufficiency and blocks research until the gate
   passes.
6. The backend creates research, selection, and plan artifacts.
7. The owner can approve or revise artifacts through the TUI.
8. The backend launches a Codex executor job for engineering.
9. Executor output, status, changed files, and manifest are visible in the TUI.
10. The backend runs surface-aware QA.
11. QA artifacts and failure routes are visible in the TUI.
12. Deployment, KPI, marketing, iteration, and analysis are represented as
    gated plans and jobs without unauthorized live effects.
13. Closing and reopening the TUI resumes the same app, stage, review queue,
    and artifact context.
14. Tests and dogfood prove the flow through QA with real executor work.

## 4. Non-Goals For V1 Backend

The v1 backend must not require:

- a hosted web backend;
- user login;
- multi-user cloud sync;
- production deployment execution;
- real public posting;
- paid ad spend;
- raw credential collection;
- remote Hermes or Telegram control;
- arbitrary background daemons.

It may model those later capabilities as gated plans, capability requirements,
and owner review items.

## 5. Core Backend Components

### 5.1 Textual Controller

Responsible for translating backend state into Textual screens.

It owns:

- widget state;
- focus and keybindings;
- command palette actions;
- selected file/artifact;
- visual transitions between lifecycle stages;
- non-blocking rendering of executor and QA progress.

It must not:

- write arbitrary lifecycle files directly;
- bypass gates;
- inspect secrets;
- decide lifecycle progression by itself.

All mutations go through backend commands.

### 5.2 Backend Facade

The TUI talks to one facade, conceptually:

```text
WeaveBackend
  load_workspace()
  get_dashboard()
  get_app(app_id)
  dispatch(command)
  subscribe_events(app_id)
```

The facade routes commands to the correct service and returns a fresh
owner-visible projection after each mutation.

### 5.3 Workspace Store

Responsible for local workspace paths, app registry, app manifests, and safe
file IO.

It owns:

- workspace root detection;
- app registry;
- app creation;
- app import;
- active app selection;
- public-safe path normalization;
- JSON/Markdown read/write helpers;
- atomic writes for state files.

### 5.4 Lifecycle Engine

Responsible for the lifecycle state machine and stage gates.

It owns:

- current stage;
- stage status;
- stage inputs;
- stage outputs;
- required artifact refs;
- approval requirements;
- transition rules;
- hard-stop boundaries;
- failure routing.

The Textual app renders lifecycle state. It does not invent it.

### 5.5 Event Ledger

Append-only record of what happened.

It owns:

- owner actions;
- agent actions;
- artifact creation events;
- state transition events;
- approval events;
- blocked-action events;
- executor job events;
- QA run events;
- capability grant/audit events;
- scheduler job/run events.

No event may contain raw secrets or private payloads.

### 5.6 Artifact Store

Responsible for stage artifacts and proof files.

It owns:

- artifact manifests;
- artifact refs;
- stage artifact directories;
- validation metadata;
- claims and non-claims;
- owner-readable summaries;
- source refs for derived artifacts.

The TUI uses this store for the right-side evidence/files panes and file
inspection views.

### 5.7 World Model Service

Responsible for the current owner-reviewable understanding of the app.

It owns:

- current app intent;
- selected direction;
- business/engineering/QA/deployment/KPI/marketing assumptions;
- important changes after engineering or QA;
- known gaps and contradictions;
- source artifact refs for each claim.

Every lifecycle stage that changes the app's actual state must update the world
model or explicitly say no world-model change was needed.

### 5.8 Review Queue

Responsible for owner attention.

It owns:

- pending approvals;
- missing information;
- failed checks;
- blocked actions;
- credential/capability gaps;
- file-specific feedback;
- stage revision requests.

The review queue is the owner-facing inbox inside the TUI.

### 5.9 Executor Service

Responsible for launching and supervising agent work.

V1 executor:

- Codex.

Future executors:

- Hermes;
- remote agents;
- workflow runners.

The executor service owns:

- prompt packet creation;
- allowed working directory;
- process start;
- stdout/stderr/event streaming;
- changed file detection;
- timeout handling;
- abort handling;
- executor manifest writing;
- public-safe output summaries;
- failure classification.

The executor must not receive raw secrets.

### 5.10 Agent Orchestration Service

Responsible for turning stage definitions, prompt templates, owner input,
prior artifacts, stop boundaries, and required output contracts into concrete
prompt packets.

It owns:

- prompt library lookup;
- stage/substage trigger selection;
- context selection;
- prompt packet creation;
- user feedback attachment;
- handoff packet inclusion;
- prompt/output traceability;
- required output validation handoff.

The detailed methodology lives in
`docs/WEAVE_V1_AGENT_ORCHESTRATION_SPEC.md`. A WEAVE v1 implementation must not
hardcode stage behavior only in Textual widgets or executor scripts; the TUI
must ask this orchestration layer what prompt/action is appropriate for the
current stage.

### 5.11 QA Service

Responsible for surface-aware QA.

It owns:

- QA plan creation;
- QA authorization;
- surface detection;
- test command execution;
- browser proof when needed;
- CLI/TUI proof when needed;
- backend/API proof when needed;
- mixed-surface orchestration;
- QA result artifacts;
- failure route selection.

Browser QA alone is not sufficient for non-browser apps.

### 5.12 Capability Broker

Responsible for capabilities, secret references, grants, and audits.

It owns:

- capability inventory;
- connection status;
- capability requirements;
- owner approval requests;
- scoped grants;
- grant expiration;
- external effect classification;
- audit events.

The model and TUI may see capability names and statuses. They must not see raw
tokens, passwords, private keys, provider refresh payloads, or account-specific
secret material.

### 5.13 Scheduler Service

Responsible for planned recurring jobs and visible heartbeat state.

It owns:

- marketing engagement jobs;
- feedback intake jobs;
- competitor/sentiment scans;
- staged implementation jobs;
- analytics review jobs;
- owner follow-up jobs;
- job state;
- run events;
- pause/resume;
- kill switches.

V1 may store and display jobs without running a daemon. Running jobs live in a
later capability-gated implementation.

### 5.14 Notification Service

Responsible for turning gates, failures, and job outputs into owner-visible
attention items.

In v1 this is local TUI review queue state. Telegram, email, and external
notifications are future gated capabilities.

## 6. Command Model

The TUI sends commands to the backend. Commands are the only mutation path.

Example command families:

```text
workspace.create_app
workspace.select_app
owner_profile.save
stage.answer
stage.approve
stage.revise
stage.inspect_artifact
stage.attach_feedback
research.approve_plan
research.run
selection.choose_option
plan.approve
executor.start
executor.abort
executor.retry
qa.authorize
qa.run
qa.accept
qa.route_feedback
capability.request
capability.record_unavailable
scheduler.create_job
scheduler.pause_job
scheduler.kill_switch
```

Every command returns:

```json
{
  "ok": true,
  "message": "owner-readable summary",
  "events_written": ["event-ref"],
  "artifacts_written": ["artifact-ref"],
  "next_projection": "dashboard projection"
}
```

Failed commands return:

```json
{
  "ok": false,
  "failure_class": "gate_blocked | validation_error | executor_failed | qa_failed | capability_missing | internal_error",
  "message": "owner-readable explanation",
  "blocked_by": ["gate or missing input"],
  "safe_next_actions": ["owner-visible choices"]
}
```

## 7. Projection Model

The TUI should not assemble state by reading many files directly. The backend
returns projections optimized for screens.

Required projections:

### 7.1 Dashboard Projection

For the home screen:

- active app;
- app list;
- lifecycle rail;
- review queue count;
- running jobs;
- latest proof;
- next safe action;
- global blockers.

### 7.2 App Projection

For an app:

- app manifest;
- current stage;
- stage status;
- stage prompt;
- available actions;
- artifact refs;
- file refs;
- QA/executor status;
- review queue;
- world model summary.

### 7.3 Stage Projection

For one lifecycle stage:

- user-visible stage script;
- current question;
- expected owner input;
- choices;
- generated artifacts;
- gate status;
- failure lane;
- next stage if accepted.

### 7.4 Artifact/File Projection

For inspection panes:

- display name;
- type;
- path/ref;
- stage;
- summary;
- claims;
- non-claims;
- validation status;
- preview text;
- feedback target id.

### 7.5 Executor Projection

For engineering:

- executor available/running/failed/complete;
- job id;
- current task summary;
- prompt packet ref;
- output summary;
- changed files;
- manifest ref;
- stop boundary.

### 7.6 QA Projection

For QA:

- QA plan;
- surface type;
- authorization state;
- run status;
- checks;
- artifacts;
- screenshots/video refs when relevant;
- route: owner review, engineering, or QA-plan revision.

## 8. State Machine

The lifecycle state machine is strict. The TUI may let the owner inspect any
stage, but it may only advance through valid transitions.

### 8.1 Stages

```text
first_run
owner_profile
app
intent
research
selection
plan
engineering
qa
deployment
kpi
marketing
iteration
analysis
completion
```

The existing product vocabulary may display shorter labels:

```text
First, Owner, App, Intent, Research, Select, Plan, Engineer, QA, Deploy, KPI,
Market, Iterate, Analyze.
```

### 8.2 Stage Statuses

```text
not_started
active
needs_owner_input
running
blocked
ready_for_review
approved
failed
deferred
gated
```

### 8.3 Transition Rules

| From | To | Required gate |
| --- | --- | --- |
| first_run | owner_profile | environment route selected |
| owner_profile | app | owner profile saved or explicitly skipped |
| app | intent | app workspace exists |
| intent | research | intent sufficiency passes or owner approves assumptions |
| research | selection | research artifacts reviewed as sufficient |
| selection | plan | selected option approved |
| plan | engineering | business, engineering, QA, SEO, deployment/KPI/marketing plans reviewed |
| engineering | qa | executor manifest and source manifest exist; owner or handoff policy allows QA |
| qa | deployment | QA accepted by owner |
| deployment | kpi | deployment plan recorded; live deployment may remain deferred |
| kpi | marketing | KPI plan accepted or deferred |
| marketing | iteration | marketing plan/jobs accepted or deferred |
| iteration | analysis | iteration plan accepted or deferred |
| analysis | completion | analysis cadence accepted or deferred |

### 8.4 Revision Loops

Any reviewable stage can loop back to itself:

```text
stage -> owner feedback -> agent/backend revision -> artifact update -> review
```

Engineering and QA can route to each other:

```text
engineering -> qa -> engineering
qa -> qa_plan_revision -> qa
iteration -> engineering -> qa -> iteration
```

### 8.5 Hard Gates

These actions always require explicit owner approval and capability grants:

- raw credential handling;
- production deployment;
- DNS mutation;
- public send;
- paid spend;
- destructive change;
- credential scope change;
- contacting real users;
- changing provider billing or plans.

Hands-off or handoff mode does not bypass hard gates.

## 9. Persistence Layout

The backend should keep state durable and reviewable under the WEAVE root.

Recommended layout:

```text
apps/
  <app-id>/
    app.json
    worldmodel.md
    worldmodel.json
    ui/
      textual-session.json
      selected-view.json
    lifecycle/
      lifecycle-state.json
      event-ledger.jsonl
      review-queue.json
      first-run/
        artifacts/
      owner-profile/
        artifacts/
      app/
        artifacts/
      intent/
        artifacts/
      research/
        artifacts/
      selection/
        artifacts/
      plan/
        artifacts/
      engineering/
        artifacts/
        executor-jobs/
      qa/
        artifacts/
        qa-runs/
      deployment/
        artifacts/
      kpi/
        artifacts/
      marketing/
        artifacts/
        jobs/
      iteration/
        artifacts/
        issues/
      analysis/
        artifacts/
        jobs/
    repo/
      primary/
    capabilities/
      requirements.json
      grants.json
      audit-ledger.jsonl
    scheduler/
      jobs.json
      run-ledger.jsonl
      kill-switches.json
```

Notes:

- `repo/primary/` is the generated or imported app source tree.
- The event ledger is append-only JSONL.
- Artifacts are human-readable Markdown plus machine-readable JSON when useful.
- Session files store TUI resume state, not lifecycle truth.
- Lifecycle truth comes from lifecycle state and event ledger.

## 10. Artifact Contract

Every significant backend output must be an artifact with:

- stable id;
- schema/version when machine-readable;
- app id;
- lifecycle stage;
- created time;
- creator;
- source refs;
- claims;
- non-claims;
- public-safe flag;
- validation status;
- owner-readable summary.

Minimum artifact types:

```text
owner-profile
intent
intent-review
research-plan
research-report
selection-options
selection-decision
business-plan
engineering-plan
qa-plan
deployment-plan
kpi-plan
marketing-plan
iteration-plan
analysis-plan
executor-prompt-packet
executor-manifest
source-manifest
qa-result
seo-qa-result
capability-requirements
scheduler-job
completion-matrix
```

## 11. Event Ledger Contract

The event ledger records actual system history. It must never be overwritten to
make the story look cleaner.

Minimum event shape:

```json
{
  "schema": "weave/event/v1",
  "event_id": "evt_...",
  "created_at": "2026-06-15T12:00:00Z",
  "app_id": "launch-studio",
  "stage": "intent",
  "actor": "owner | backend | codex | qa | scheduler",
  "type": "stage.answer",
  "summary": "Owner added missing deployment region.",
  "artifact_refs": [],
  "evidence_refs": [],
  "claims": [],
  "non_claims": [],
  "requires_owner_review": false,
  "public_safe": true
}
```

## 12. Executor Backend

### 12.1 Codex Job Lifecycle

Codex executor jobs use this lifecycle:

```text
queued
preparing_prompt_packet
starting
running
waiting_for_process
collecting_outputs
verifying_outputs
complete
failed
aborted
timed_out
blocked
```

### 12.2 Prompt Packet

Before Codex starts, the backend writes a prompt packet containing:

- app id and app name;
- selected lifecycle stage;
- allowed task;
- intent artifact refs;
- research artifact refs;
- selection decision ref;
- business/engineering/QA plan refs;
- stop boundaries;
- expected output files;
- expected artifacts;
- forbidden actions;
- verification command;
- public-safe context only.

The prompt packet is an artifact. It must not contain raw secrets.

### 12.3 Process Execution

The first implementation can call Codex through a configured CLI command. The
adapter must be isolated behind `CodexExecutorAdapter` so later programmatic
Codex primitives can replace the CLI without changing the Textual UI.

The adapter records:

- command ref, not secret-bearing command text;
- working directory;
- started/finished timestamps;
- stdout/stderr summaries;
- exit code;
- changed files;
- created artifacts;
- timeout;
- failure class.

### 12.4 Pause And Abort Semantics

If the underlying Codex interface does not support true pause/resume, WEAVE
must be honest:

- pause means stop accepting advancement and show the current job as guarded;
- abort sends a termination signal if supported;
- resume starts a new job with prior artifacts and prior manifest refs;
- the UI must not imply a perfect process-level resume unless proven.

### 12.5 Executor Output Verification

Codex output is not accepted because the process exited successfully. The
backend verifies:

- required files exist;
- required artifacts exist;
- source manifest is complete;
- forbidden paths were not touched;
- public-safe scan passes;
- verification command passes or fails honestly.

## 13. QA Backend

QA adapts to the generated app surface.

### 13.1 Surface Types

```text
website
backend_api
cli
tui
mixed
library
data_pipeline
```

### 13.2 QA Plans

Before QA runs, the backend creates a QA plan and the TUI asks for approval
unless policy allows automatic local QA.

QA plan fields:

- surface type;
- target paths;
- commands to run;
- browser checks if website;
- API checks if backend;
- terminal interaction checks if CLI/TUI;
- security/public-safe checks;
- SEO checks when website exists;
- expected evidence artifacts;
- failure routes.

### 13.3 QA Run Results

QA result fields:

- run id;
- plan ref;
- surface type;
- commands executed;
- checks;
- passed/failed/skipped counts;
- screenshots/video refs when relevant;
- logs summary;
- failure classification;
- route: owner_review, engineering, or qa_plan_revision;
- claims;
- non-claims.

### 13.4 Failure Routing

QA failures route as follows:

- product/code failure -> engineering;
- test method failure -> QA plan revision;
- environment failure -> blocked with safe retry;
- owner expectation mismatch -> owner review and possible intent/plan revision.

## 14. Capability And Credential Backend

The backend represents credentials as capability requirements and secret refs.

The TUI may ask:

- which provider the owner wants;
- whether credentials exist;
- whether the owner wants to defer;
- whether the owner wants to create/connect a capability later.

The TUI must not ask the owner to paste raw secrets into a normal chat/composer.

Allowed stored values:

```text
capability:vercel-staging
capability:cloudflare-dns
secret_ref:deployment-provider-staging
secret_ref:analytics-readonly
```

Forbidden stored values:

- tokens;
- passwords;
- refresh payloads;
- private keys;
- 2FA codes;
- provider console cookies;
- private endpoints that reveal topology.

## 15. Scheduler And Heartbeat Backend

Marketing, iteration, and analysis continue after the initial build lifecycle,
but v1 can represent these as planned jobs.

Required job types:

- marketing engagement;
- feedback intake;
- competitor/sentiment scan;
- staged implementation;
- analytics review;
- owner follow-up.

V1 job behavior:

- create job artifact;
- show in TUI;
- require owner approval before activation;
- classify external effect;
- require capability grant for live effects;
- write run events if manually triggered;
- support pause and kill switch.

No hidden cron is allowed in v1.

## 16. Textual TUI Boundary

The Textual app should be built as a client of backend projections and
commands.

Recommended widget-to-backend mapping:

| Textual surface | Backend source |
| --- | --- |
| Header | dashboard/app projection |
| Lifecycle rail | lifecycle engine projection |
| Work/chat pane | stage projection and event stream |
| Action cards | available commands from stage projection |
| Composer | `stage.answer`, `stage.attach_feedback`, command palette |
| Evidence pane | artifact/file projection |
| Files pane | workspace/source manifest projection |
| Review queue | review queue projection |
| Executor status | executor projection/event stream |
| QA status | QA projection/event stream |
| Footer/keybindings | static Textual controls plus command availability |

The TUI should stay responsive while jobs run. Long tasks must stream events
into the backend, and the TUI should re-render from projections.

## 17. Security And Safety Invariants

The implementation must preserve these invariants:

1. Raw secrets are never printed, logged, committed, sent to Codex, or stored in
   artifacts.
2. External effects are classified before execution.
3. Production writes, public sends, paid spend, credential changes, and
   destructive actions require explicit owner approval and grants.
4. Event ledger entries are append-only.
5. Stage advancement requires gate evidence.
6. Fixture, deterministic, local, and live proof are labeled differently.
7. A passing unit test is not proof of full lifecycle completion.
8. A running executor is not proof of a successful build.
9. A successful build is not proof of QA acceptance.
10. Local QA is not deployment proof.
11. Hands-off/handoff mode still stops at hard gates.
12. The TUI never claims a capability exists because the owner discussed it.

## 18. Testing Strategy

### 18.1 Unit Tests

Required:

- lifecycle transition rules;
- command validation;
- event ledger append behavior;
- artifact validation;
- world model update rules;
- capability grant rules;
- scheduler job state rules;
- public-safe scanning helpers.

### 18.2 Integration Tests

Required:

- create app through backend command;
- save owner profile;
- validate intent;
- produce research/selection/plan artifacts;
- approve/revise loop;
- launch fixture executor;
- launch Codex executor when available;
- collect executor manifest;
- run QA;
- route QA failure honestly;
- resume app state.

### 18.3 Textual Tests

Required:

- app opens to home screen;
- keybindings navigate between stages;
- stage action buttons dispatch backend commands;
- review queue updates after command results;
- file/artifact selection is visible;
- executor stream updates UI without blocking;
- closing and reopening restores session.

### 18.4 Dogfood Test

Required final proof:

1. Start from a clean app id.
2. Enter a substantial app intent.
3. Advance through intent, research, selection, and plan.
4. Run Codex engineering from WEAVE context.
5. Verify generated app files and executor manifest.
6. Run surface-aware QA.
7. Review QA proof in the Textual TUI.
8. Record acceptance or route feedback.
9. Reopen the TUI and verify resume state.

## 19. Implementation Slices

### Slice 1: Backend Core

- workspace store;
- app registry;
- lifecycle state;
- event ledger;
- artifact store;
- projections;
- command dispatcher;
- unit tests.

### Slice 2: Textual Shell

- Textual app layout;
- lifecycle rail;
- work pane;
- evidence/files/review panes;
- composer;
- command palette;
- projections wired read-only first.

### Slice 3: Owner Loops

- first-run;
- owner profile;
- app creation;
- intent input;
- review/approve/revise loop;
- session resume.

### Slice 4: Planning Stages

- research plan artifact;
- research artifact review;
- selection options;
- plan tracks;
- world model updates.

### Slice 5: Executor

- Codex adapter;
- prompt packet;
- streaming/job status;
- changed file detection;
- executor manifest;
- failure handling.

### Slice 6: QA

- QA planner;
- website/CLI/TUI/backend/mixed adapters;
- QA result artifacts;
- screenshot/video refs where relevant;
- failure routing.

### Slice 7: Gated Ops

- deployment plan;
- KPI plan;
- marketing plan;
- iteration/analysis jobs;
- capability requirements;
- scheduler job fixtures;
- kill switches.

### Slice 8: Full Dogfood And CI

- substantial example app;
- end-to-end run through QA;
- Textual screenshot/capture proof;
- CI tests;
- final completion matrix.

## 20. Open Decisions For Owner Review

These should be reviewed before implementation:

1. Should v1 backend be strictly in-process only, or should it expose a local
   HTTP API from the start?
2. Should Codex executor use the CLI first, with adapter isolation, or should
   implementation wait for lower-level Codex primitives?
3. Should research use live web in v1, or start with owner-provided/context-only
   research artifacts until live browsing policy is designed?
4. Should Textual screenshots/captures be required in CI, or only in dogfood
   evidence?
5. Should deployment/KPI/marketing/iteration stages be fully navigable in v1
   but non-executing, or should manual local job runs be allowed for read-only
   analysis?

## 21. Acceptance Checklist For This Spec

This spec is acceptable if the owner can answer yes to all:

- I understand what the backend is responsible for.
- I understand what the Textual app does and does not own.
- I can see how lifecycle state advances.
- I can see where artifacts, event ledger, world model, and review queue live.
- I can see how Codex work becomes visible and auditable.
- I can see how QA adapts to different app surfaces.
- I can see how credentials and live effects are blocked.
- I can see how marketing, iteration, and analysis become visible jobs without
  hidden cron.
- I can see what tests must pass before WEAVE v1 can be called done.
- I can identify any part of the backend I disagree with before implementation.

## 22. Implementation Non-Claim

This document is not implementation proof.

It is the backend contract that a future WEAVE v1 build goal must satisfy.
Implementation is only complete when the code, tests, dogfood run, Textual
captures, executor evidence, QA artifacts, and owner review all agree with this
spec.

# WEAVE To Symphony Adapter Compound Engineering Plan

Status: implementation plan
Date: 2026-06-22

## Simple Model

WEAVE is the user-facing Chief of Staff agent. Symphony is the orchestra that
can run isolated Codex workers for WEAVE.

The adapter is the small, testable bridge between them:

```text
WEAVE intent -> WEAVE WorkItem -> Symphony-dispatchable item ->
isolated Codex worker -> ProofEnvelope -> WEAVE readback
```

The user should keep talking to one WEAVE Chief of Staff. The user should not
need to open Symphony, classify lifecycle stages, or understand worker routing.

## User Value

The adapter is valuable only if it gives the user:

- one stable chat surface for asking for work;
- clear lifecycle state before, during, and after worker execution;
- visible worker progress without losing the owner's intent;
- proof envelopes that distinguish done, blocked, unproven, and gated;
- repeatable execution without hand-crafted prompts every time;
- safe continuation after compaction, restart, or stale workers.

If the adapter only starts agents but does not improve visibility, proof, or
continuity, it is not good enough for WEAVE.

## Compound Engineering Objective

Build the adapter in slices that each prove a specific target surface:

```text
intent contract -> adapter schema -> queue fixture -> prompt renderer ->
worker closeout -> orchestrator state -> WEAVE readback -> gated live run
```

Each slice must include:

- exact input and output contract;
- local deterministic test;
- proof boundary;
- adversarial review question;
- non-claims.

## Architecture

### WEAVE-Owned Responsibilities

- Talk to the user.
- Infer lifecycle stage from ordinary language.
- Maintain owner/app/profile context.
- Write `WorkItem`, `LifecycleCard`, `WorkerPacket`, and `ProofEnvelope`
  records.
- Decide whether work is safe, gated, blocked, stale, done, or unproven.
- Summarize state back to the user.
- Enforce WEAVE evaluations, governance, and non-claim boundaries.

### Symphony-Owned Responsibilities

- Poll or receive dispatchable work.
- Create one isolated workspace per work item.
- Launch Codex app-server with a rendered workflow prompt.
- Track running, retrying, blocked, and terminal execution state.
- Stop or clean up workspaces when the dispatch item becomes terminal.
- Expose logs, JSON state, and optional Phoenix dashboard state.

### Adapter-Owned Responsibilities

- Convert WEAVE `WorkItem` into a Symphony-dispatchable item.
- Render a WEAVE-specific `WORKFLOW.md` prompt for Codex workers.
- Preserve WEAVE IDs through Symphony execution state.
- Map Symphony operational state back into WEAVE readback state.
- Refuse to convert incomplete or unsafe work items.
- Keep queue/tracker state separate from lifecycle truth.

## Minimal Data Contracts

### WorkItem

Required fields:

- `schema`: `weave-work-item/v0.1`
- `work_item_id`
- `app_id`
- `lifecycle_stage`
- `intent_truth`
- `owner_boundary`
- `worker_packet`
- `proof_required`
- `allowed_actions`
- `forbidden_actions`
- `public_gate`
- `non_claims`

### SymphonyDispatchItem

Required fields:

- `id`
- `identifier`
- `title`
- `description`
- `state`
- `labels`
- `branch_name`
- `url`
- `weave`: embedded WEAVE metadata containing `app_id`, `lifecycle_stage`,
  `work_item_id`, and `proof_required`

The adapter may use a local JSON queue first. Linear is a later adapter, not the
first proof surface.

### ProofEnvelope

Required fields:

- `schema`: `weave-proof-envelope/v0.1`
- `work_item_id`
- `app_id`
- `lifecycle_stage`
- `state`: `done`, `blocked`, `needs_owner_action`, `revise`, or
  `accepted_for_scope`
- `claim`
- `proof_surface`
- `commands`
- `artifacts`
- `non_claims`
- `reviewer`
- `next_action`

## Implementation Slices

### Slice 0: Contract And Fixtures

Goal: make the adapter contract unambiguous.

Build:

- JSON examples for `WorkItem`, `SymphonyDispatchItem`, and `ProofEnvelope`;
- validators for required fields and allowed state values;
- documentation examples that do not mention private local paths or secrets.

Tests:

- valid examples pass;
- missing `proof_required` fails;
- missing owner boundary fails;
- invalid lifecycle stage fails;
- private-path and credential-looking strings fail public-safe scan.

Non-claim:

- no Symphony process is started.

### Slice 1: Local Queue Adapter

Goal: prove WEAVE can create work that Symphony can read without Linear.

Build:

- append-only local queue writer;
- queue reader that returns normalized Symphony-like issue records;
- deterministic IDs and replay-safe state transitions.

Tests:

- ordinary user intent becomes a complete `WorkItem`;
- `WorkItem` becomes one dispatch item;
- unsafe/gated work is not dispatchable;
- terminal items are not dispatched;
- queue replay does not duplicate active work.

Non-claim:

- no Codex app-server worker is launched.

### Slice 2: WEAVE Workflow Prompt Renderer

Goal: prove dispatched workers receive WEAVE behavior, not generic Symphony
ticket behavior.

Build:

- renderer for a WEAVE-specific `WORKFLOW.md` body;
- prompt sections for lifecycle stage, intent truth, owner boundary, proof
  required, forbidden actions, and closeout format;
- fixture prompt for one calculator-style app work item.

Tests:

- prompt contains lifecycle procedure and proof envelope requirement;
- prompt refuses public sends, secrets, billing, deploys, and destructive work
  unless explicitly gated;
- prompt does not ask the user to classify the lifecycle stage;
- prompt includes exact closeout states.

Non-claim:

- prompt correctness does not prove worker execution.

### Slice 3: Fake Worker End-To-End

Goal: prove WEAVE can read a worker closeout without live Codex.

Build:

- fake Symphony runner that consumes one dispatch item;
- fake worker that writes a valid `ProofEnvelope`;
- WEAVE readback command that summarizes the result.

Tests:

- done envelope becomes `accepted_for_scope` readback;
- blocked envelope names exact owner action;
- incomplete envelope is rejected;
- overclaiming envelope is rejected;
- stale worker state becomes `resume`, `replace`, `supersede`, or `block`.

Non-claim:

- no real Codex app-server worker has run.

### Slice 4: Local Codex App-Server Smoke

Goal: prove Symphony can launch a real Codex worker with a WEAVE packet in an
isolated workspace.

Build:

- one local, non-secret work item;
- isolated workspace creation;
- Codex app-server invocation through Symphony or a minimal adapter runner;
- proof envelope closeout required by the worker.

Tests:

- worker starts in the isolated workspace;
- worker receives WEAVE prompt;
- worker writes required artifact;
- worker writes proof envelope;
- WEAVE readback reports exact scope and non-claims.

Stop boundary:

- do not use live Linear, production deploys, public sends, paid calls, or raw
  secrets.

### Slice 5: Observability And Dashboard Mapping

Goal: prove Symphony operational state can be shown as WEAVE state.

Build:

- state mapper from Symphony running/blocked/retrying/completed to WEAVE
  lifecycle readback;
- JSON status surface with app ID, stage, worker packet, proof path, blocker,
  and next action;
- optional Phoenix dashboard extension plan, if the UI is needed.

Tests:

- running maps to `agent_in_progress`;
- blocked maps to `needs_owner_action` or `blocked` with exact blocker;
- completed without proof maps to `revise`;
- completed with valid proof maps to `accepted_for_scope`;
- terminal tracker state does not automatically mean lifecycle done.

Non-claim:

- dashboard mapping does not prove the owner will use the dashboard.

### Slice 6: Gated Live Tracker Run

Goal: prove the real tracker path only after local proof is strong.

Requires explicit owner approval because it touches live tracker state.

Build:

- disposable Linear or selected tracker item;
- Symphony run using WEAVE workflow;
- attached proof envelope;
- WEAVE Chief of Staff readback.

Tests:

- one live work item is dispatched;
- live worker comments/status are correct;
- no duplicate workers are created;
- CI/local proof is linked;
- owner sees the result in WEAVE, not only in the tracker.

Non-claim:

- this does not prove production deploys, payments, or public sends.

## Adversarial Review Questions

After each slice, the reviewer must answer:

- Did this prove the target surface, or only a nearby artifact?
- Can a worker overclaim completion without a valid proof envelope?
- Can queue/tracker state hide a failed lifecycle step?
- Does the user get better visibility than plain Codex or plain Symphony?
- Is there a smaller adapter path that preserves the same user value?
- Did any test depend on private local state, secrets, live sessions, or manual
  owner memory?
- Should the slice be accepted, revised, blocked, or killed?

## Acceptance Criteria

The adapter is ready for first real use when:

- a normal user intent creates a complete `WorkItem` without manual stage
  classification;
- the adapter dispatches exactly one worker for the item;
- the worker receives a WEAVE workflow prompt;
- the worker cannot close without a valid `ProofEnvelope`;
- WEAVE reports state back to the Chief of Staff chat;
- local deterministic tests cover done, blocked, revise, stale, and gated paths;
- public-safe scans and package validation pass;
- live tracker use remains gated until explicitly approved.

## Continuous Use

When future work touches WEAVE orchestration, agent spawning, Symphony, Linear,
worker packets, proof envelopes, or lifecycle readback, agents should use the
`compound-engineering` skill and this plan as the standing adapter contract.


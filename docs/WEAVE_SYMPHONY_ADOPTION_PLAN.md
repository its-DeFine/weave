# WEAVE Symphony Adoption Plan

Status: adoption plan, no adaptation code yet
Date: 2026-06-22

## Simple Model

Symphony is the orchestration kernel. WEAVE is the app-company product layer.

The Symphony import gives WEAVE a reference implementation for:

- tracker polling;
- per-work-item workspace isolation;
- Codex app-server sessions;
- retry, stall, and reconciliation handling;
- operator-visible status;
- repository-owned workflow policy.

The WEAVE vNext contract remains the product source of truth. Symphony must be
adapted to serve WEAVE's identity-first app lifecycle, not the other way around.

## Source Snapshot

Imported source:

- Repository: `https://github.com/openai/symphony`
- Branch: `main`
- Commit: `4cbe3a9699a73b862466c0b157ceca0c1985d6d7`
- Local path: `vendor/symphony/`
- License: Apache-2.0, retained in `vendor/symphony/LICENSE`

`vendor/symphony/` is the upstream reference snapshot. Do not mix WEAVE
adaptation commits into that directory unless the change is deliberately
documented as a fork delta. Prefer new WEAVE code under a separate implementation
path after the plan is accepted.

Import hygiene deltas in this branch:

- trailing whitespace was removed from imported dashboard evidence fixtures so
  the repository-wide `git diff --check` gate can pass;
- WEAVE public-safety scanners skip only the vetted `vendor/symphony/` prefix so
  upstream public examples do not block WEAVE-specific scans;
- no Symphony behavior has been adapted to WEAVE yet.

## Authoritative WEAVE Inputs

Before adapting Symphony, agents must read:

- `docs/WEAVE_VNEXT_GROUND_ZERO_CONTRACT.md`
- `docs/WEAVE_HARNESS_ENGINEERING_ADOPTION.md`
- `docs/WEAVE_OBSERVABILITY_EVAL_GOVERNANCE.md`
- `docs/WEAVE_REVIEW_LOOP_PROCESS.md`
- `docs/WEAVE_INTENT_TRUTH_AND_COMPLETION_CONTRACT.md`

These documents define WEAVE's identity gate, lifecycle stages, proof envelopes,
owner-memory visibility, review loop, and public-safe boundaries.

## Adoption Decision

Use Symphony as a base for the WEAVE orchestrator, but do not rename Symphony as
WEAVE.

Reasons:

- Symphony already solves long-running Codex orchestration with isolated
  workspaces and tracker-driven dispatch.
- Symphony's own README and spec present it as an orchestration preview and
  language-agnostic specification, not as a complete product framework.
- WEAVE needs app lifecycle state, identity formation, monetization/GTM gates,
  proof envelopes, and app primitives that Symphony does not define.
- A contained import preserves the change map and lets future agents compare
  upstream Symphony to WEAVE adaptation work.

## Concept Map

| Symphony concept | WEAVE concept | Adaptation rule |
| --- | --- | --- |
| `SPEC.md` | Orchestrator kernel spec | Use as the base coordination model, then add WEAVE lifecycle/proof extensions. |
| `WORKFLOW.md` | `WEAVE_WORKFLOW.md` or lifecycle worker policy | Replace PR-centric ticket instructions with identity-first app lifecycle instructions. |
| Issue | Work item | Add `app_id`, lifecycle stage, intent truth, proof requirement, non-claims, and owner boundary. |
| Issue tracker state | Dispatch state | Keep for scheduling only; do not let it replace WEAVE lifecycle state. |
| Workspace | Isolated app/work item workspace | Keep per-work-item isolation; add app runtime/proof directories. |
| Agent runner | Codex worker runner | Keep Codex app-server pattern; packet must include WEAVE lifecycle procedure and proof path. |
| Workpad comment | Lifecycle card and proof envelope | Replace single ticket comment as source of truth with repo/home state plus optional tracker mirror. |
| PR handoff | Stage closeout | Completion means proof-reviewed lifecycle closeout, not necessarily PR merge. |
| Status dashboard/API | WEAVE status/proof surface | Extend with app, stage, proof, blockers, stale workers, non-claims, and next action. |
| Terminal issue cleanup | Stale worker cleanup | Map to `resume`, `replace`, `supersede`, or `block` decisions. |

## Required WEAVE Extensions

### 1. Workflow Contract

Create a WEAVE workflow contract that routes normal user or tracker intent to
WEAVE lifecycle stages:

- Start
- Identity
- App Intent
- Product Brief
- Research
- Selection
- Plan
- Engineering
- QA
- Deployment Gate
- Monetization Gate
- GTM Gate
- Launch Readback
- Iteration

The workflow must not ask users to name stages manually. It must infer the
stage, record intent truth, ask focused missing questions, and block overclaims.

### 2. Data Model

Add WEAVE-specific records:

- `App`
- `WorkItem`
- `LifecycleCard`
- `IntentTruth`
- `WorkerPacket`
- `ProofEnvelope`
- `OwnerDecision`
- `StaleWorkerCleanupDecision`

The minimal first slice can serialize these as JSON/Markdown before introducing
a database.

### 3. App Primitives

Add app-company primitives that a worker can call or execute through bounded
packets:

- create or resume app record;
- scaffold app source;
- run local app;
- inspect files;
- run checks;
- capture browser DOM or screenshot proof when applicable;
- write lifecycle artifact;
- write proof envelope;
- update monetization state;
- record non-claims.

### 4. Validation Surfaces

Symphony's local runner must become target-surface aware:

- local file checks prove files only;
- unit/smoke tests prove code behavior only inside their scope;
- browser/DOM/screenshot checks prove visible UX;
- local runtime proof does not prove public availability;
- public/live checks require exact owner approval;
- payment/revenue checks require exact owner approval and target readback.

### 5. Governance And Cleanup

Add mechanical checks for:

- public-safe repository output;
- proof envelope shape;
- lifecycle card shape;
- claim-without-proof;
- proof-without-claim;
- stale worker lanes;
- old Textual/TUI residue in vNext paths;
- doc index and source-of-truth drift.

## Implementation Phases

### Phase 0: Preserve Baseline

Done in this branch when:

- Symphony is imported under `vendor/symphony/`.
- This adoption plan records the upstream commit and concept map.
- No adaptation code is mixed into the import.

### Phase 1: WEAVE Orchestrator Spec

Create `docs/WEAVE_ORCHESTRATOR_SPEC.md` from the Symphony spec plus WEAVE
extensions:

- tracker/local queue abstraction;
- work item model;
- lifecycle stage model;
- proof envelope model;
- status payload model;
- safety and public-safe policy;
- owner approval gates.

### Phase 2: Minimal Runner Slice

Implement the smallest runner that can:

- load WEAVE workflow policy;
- create an isolated workspace;
- run one Codex app-server worker;
- pass a WEAVE worker packet;
- capture worker status;
- require proof envelope closeout.

The first slice may use a local file queue before Linear/Plane integration.

### Phase 3: Lifecycle Integration

Add lifecycle routing and artifacts:

- app record;
- intent truth;
- lifecycle cards;
- stage-specific packet procedures;
- closeout and non-claim enforcement;
- `bin/weave eval` integration.

### Phase 4: App Runtime Proof

Add agent-legible app surfaces:

- per-workspace app launch;
- browser navigation and screenshot/DOM proof;
- local logs and runtime status;
- before/after proof capture.

### Phase 5: Tracker And Review Automation

Add tracker adapters only after local lifecycle proof works:

- Linear adapter;
- Plane adapter if required;
- tracker mirror comments;
- PR/review handoff where relevant.

Tracker state must remain a mirror or dispatch surface unless the owner
explicitly selects it as source of truth.

## Stop Boundaries

Do not:

- push or publish without explicit owner approval;
- deploy Symphony or WEAVE services from this branch;
- move secrets, tokens, cookies, browser sessions, or private topology into
  public artifacts;
- claim WEAVE runtime implementation exists from this import alone;
- claim Symphony proves WEAVE lifecycle behavior before a WEAVE worker loop is
  implemented and tested.

## Acceptance Checks For The Adoption Plan

This plan is accepted when a controller can answer:

- which Symphony commit was imported;
- where the untouched upstream snapshot lives;
- which WEAVE documents remain authoritative;
- how each major Symphony concept maps to WEAVE;
- which phases produce the first useful proof;
- which claims are still non-claims.

## Current Non-Claims

- The imported Symphony code has not been adapted to WEAVE.
- The imported Symphony code has not been run in this branch.
- This plan does not prove Codex app-server behavior in WEAVE.
- This plan does not prove app creation, browser validation, payment, launch, or
  revenue behavior.
- This plan does not authorize deployment, public sends, destructive cleanup, or
  secret handling.

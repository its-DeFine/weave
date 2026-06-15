# WEAVE Lifecycle Artifact Contracts v0.1

Trace: ATM-241

This contract turns the lifecycle blueprint into public-safe artifacts that
later implementation PRs can validate. It is a specification layer only: it
does not claim live runtime execution, deployment, analytics, public sends, or
credential handling.

## Purpose

WEAVE needs durable state that both humans and agents can inspect without
collapsing product intent, local proof, runtime proof, and external effects into
one vague status line.

This contract defines four core artifacts:

1. **Lifecycle state**: where an app is in the product lifecycle and what is
   currently allowed.
2. **World model**: the current owner-reviewable understanding of the app.
3. **Event ledger entry**: an append-only record of actions, approvals,
   evidence, and stage transitions.
4. **Owner decision card**: the explicit unit of hands-on owner input when an
   agent reaches a consequential fork.

The corresponding schema files are:

- `schemas/lifecycle-state.schema.json`
- `schemas/world-model.schema.json`
- `schemas/event-ledger-entry.schema.json`
- `schemas/owner-decision-card.schema.json`

## Public-Safe Rules

These artifacts are safe for public repository use only when they follow these
rules:

- never contain raw tokens, credentials, private payloads, private addresses, or
  owner-specific operating procedures;
- use references such as `secret_ref`, `capability_ref`, `artifact_ref`, or
  `evidence_ref` instead of sensitive values;
- distinguish local deterministic proof from runtime/live proof;
- record non-claims whenever a user or agent might otherwise overread the
  evidence;
- record approval boundaries before external actions, paid spend, production
  deployment, public sends, or destructive changes.

Credential and capability mechanics are intentionally deferred to the
capability broker contract. This document only reserves reference fields so
later stages know where such references belong.

## Lifecycle Stages

The stage vocabulary is:

```text
first_run
owner_profile
create_app
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
```

`deployment` is included as a proposed first-class stage because production KPI
setup should usually be wired after a deployed surface exists. Existing runtime
code may still expose the prior stage set until implementation issues migrate
the product surface.

## Stage Statuses

Each stage instance uses one of these statuses:

```text
not_started
collecting
drafting
review
revision_requested
approved
running
owner_input_needed
blocked
ready_for_review
completed
deferred
```

Stage status is not a proof claim by itself. A stage can be `ready_for_review`
only when the relevant artifact references exist. A stage can be `approved`
only when the event ledger contains the approval event or the spec explicitly
allows deterministic auto-approval.

## Baseline Flow

The intended flow is:

```text
first_run
-> owner_profile
-> create_app
-> intent
-> research
-> selection
-> plan
-> engineering
-> qa
-> deployment
-> kpi
-> marketing
-> iteration
-> analysis
```

Marketing and iteration/analysis are ongoing loops. They do not close the app;
they create recurring jobs, feedback items, staged changes, and owner approval
requests.

## Lifecycle State Contract

`lifecycle-state` is the app-level state packet. It answers:

- what app is this;
- what stage is current;
- which stages exist and what their statuses are;
- what owner attention is needed;
- what proof and non-claims are attached;
- what hard boundaries are active.

Minimum shape:

```json
{
  "schema": "weave/lifecycle-state/v0.1",
  "app_id": "pocket-orchard",
  "updated_at": "2026-06-15T12:00:00Z",
  "current_stage": "research",
  "stage_source": "event-ledger",
  "stages": [
    {
      "stage": "intent",
      "status": "approved",
      "artifact_refs": ["apps/pocket-orchard/lifecycle/intent/artifacts/intent.json"],
      "proof_refs": ["apps/pocket-orchard/lifecycle/intent/artifacts/intent-review.json"],
      "non_claims": ["does not prove implementation exists"]
    }
  ],
  "attention": {
    "state": "owner_input_needed",
    "decision_refs": ["decision-card:architecture-fork-001"]
  },
  "approval_boundaries": [
    "public_send_requires_owner_approval",
    "paid_spend_requires_owner_approval",
    "production_deploy_requires_owner_approval"
  ]
}
```

Allowed `stage_source` values:

```text
derived
event-ledger
owner-approved
agent-proposed
system-imported
```

## World Model Contract

`world-model` is the durable owner-reviewable truth snapshot for an app. It is
not a transcript dump and not hidden reasoning. It is a compact state model that
later stages can consume.

It should include:

- current app state;
- selected approach;
- business plan snapshot;
- engineering plan snapshot;
- deployment state;
- KPI definitions;
- marketing state;
- active recurring jobs;
- known risks;
- owner preferences;
- approval boundaries;
- capability gaps;
- proof boundary and non-claims.

Minimum shape:

```json
{
  "schema": "weave/world-model/v0.1",
  "app_id": "pocket-orchard",
  "updated_at": "2026-06-15T12:00:00Z",
  "current_stage": "plan",
  "selected_approach": {
    "summary": "Build a local static proof before deployment work.",
    "source_artifact_refs": ["selection-matrix.json"]
  },
  "plans": {
    "business": "artifact:business-plan-v1",
    "engineering": "artifact:engineering-plan-v1",
    "qa": "artifact:qa-plan-v1"
  },
  "proof_boundary": {
    "highest_proven_surface": "local_deterministic",
    "non_claims": ["not deployed", "not live-market validated"]
  },
  "approval_boundaries": ["production deploy", "public send", "paid spend"],
  "capability_gaps": ["deployment provider not connected"]
}
```

The world model must be updated after:

- owner profile or preference changes;
- intent approval;
- research sufficiency approval;
- selection approval;
- plan approval;
- consequential engineering decision;
- QA result;
- deployment state change;
- KPI, marketing, or iteration plan change;
- recurring job creation or cancellation.

## Event Ledger Entry Contract

The event ledger is append-only. Each entry records one event and the evidence
that supports it.

Minimum shape:

```json
{
  "schema": "weave/event-ledger-entry/v0.1",
  "event_id": "evt_20260615_0001",
  "at": "2026-06-15T12:00:00Z",
  "app_id": "pocket-orchard",
  "stage": "selection",
  "actor": "owner",
  "event_type": "stage.approved",
  "summary": "Owner approved the selected wedge.",
  "evidence_refs": ["artifact:selection-matrix-v2"],
  "claims": ["selection stage owner-approved"],
  "non_claims": ["does not prove implementation exists"],
  "requires_owner_review": false,
  "public_safe": true
}
```

Required event families:

```text
stage.entered
stage.artifact_created
stage.review_requested
stage.revision_requested
stage.approved
stage.blocked
decision.created
decision.answered
decision.deferred
world_model.updated
proof.recorded
non_claim.recorded
capability.requested
capability.deferred
job.created
job.paused
job.cancelled
```

The event ledger must not store raw private payloads. If an event needs to cite
sensitive material, it must cite a public-safe reference plus the allowed claim
boundary.

## Owner Decision Card Contract

A decision card is created when a stage reaches a consequential fork that should
not be silently assumed.

Examples:

- architecture fork;
- library or framework choice;
- cost/spend fork;
- security posture change;
- deployment shape change;
- product scope change;
- credential/capability gap;
- public-send or external-action boundary.

Minimum shape:

```json
{
  "schema": "weave/owner-decision-card/v0.1",
  "decision_id": "architecture-fork-001",
  "app_id": "pocket-orchard",
  "stage": "engineering",
  "status": "open",
  "created_at": "2026-06-15T12:00:00Z",
  "decision_type": "architecture",
  "question": "Should the first proof stay static or add a backend now?",
  "why_it_matters": "Adding a backend changes deployment, QA, and data handling.",
  "options": [
    {
      "id": "static-first",
      "label": "Static first",
      "description": "Ship a local static proof and defer backend work.",
      "agent_recommendation": true
    },
    {
      "id": "backend-now",
      "label": "Backend now",
      "description": "Add backend, API, persistence, and backend QA now.",
      "agent_recommendation": false
    }
  ],
  "hard_boundary_flags": ["deployment_shape"],
  "evidence_refs": ["artifact:engineering-plan-v1"]
}
```

Allowed `status` values:

```text
open
answered
deferred
blocked
superseded
```

When a decision is answered:

1. write `decision.answered` to the event ledger;
2. update the world model;
3. update lifecycle state attention fields;
4. resume the blocked stage if no other blockers remain.

## Proof And Non-Claim Policy

Every artifact can name both `claims` and `non_claims`.

Use `claims` only for evidence-backed statements. Use `non_claims` for adjacent
truths that a reviewer might otherwise assume.

Examples:

```text
Claim: "Intent stage owner-approved."
Non-claim: "Does not prove implementation exists."

Claim: "Local deterministic QA passed."
Non-claim: "Does not prove deployed production behavior."

Claim: "Marketing plan approved."
Non-claim: "Does not prove public posts were sent."
```

## Implementation Implications

Later implementation PRs should:

- validate artifacts against the schema files in this spec;
- write event ledger entries for stage transitions and owner decisions;
- derive visible UI state from lifecycle state instead of raw filesystem guesses;
- keep world model updates owner-reviewable;
- block external effects until capability and approval contracts exist;
- add fixtures that demonstrate a full app lifecycle skeleton without live
  external effects.

## Acceptance For ATM-241

This spec PR is acceptable when:

- the lifecycle state, world model, event ledger entry, and owner decision card
  contracts are documented;
- schema files exist for those four artifact types;
- the stage vocabulary includes the full intended lifecycle including
  deployment;
- the proof/non-claim boundary is explicit;
- no implementation claims live runtime behavior from these spec artifacts.

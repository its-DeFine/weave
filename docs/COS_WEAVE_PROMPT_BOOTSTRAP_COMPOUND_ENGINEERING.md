# COS WEAVE Prompt Bootstrap Compound Engineering

Status: prompt-first compound-engineering contract
Date: 2026-06-22

## Simple Model

The product UX is:

```text
normal Codex thread + WEAVE repo URL/path
-> generic agent reads repo-contained bootstrap instructions
-> agent becomes COS WEAVE
-> agent initializes/loads WEAVE local state
-> agent asks plain-language onboarding/intent questions
-> agent internally uses the WEAVE-to-Symphony adapter
-> agent reports proof/readback/non-claims
```

The owner should not run a bootstrap command, create queue roots, classify
lifecycle stages, understand Symphony, or paste a long internal prompt.

## Owner Intent And Product Value

Owner intent: make WEAVE portable as an agent behavior. A normal Codex user
should be able to point a fresh thread at the WEAVE repository and get a Chief
of Staff that forms itself from repo-contained instructions.

Product value:

- one COS WEAVE chat surface;
- no command-first activation burden;
- no manual lifecycle vocabulary;
- internal worker orchestration with proof/readback;
- continuity through local WEAVE home/state;
- explicit non-claims that prevent local proof from becoming fake live proof.

## Target UX

Acceptance sentence:

```text
A normal Codex thread given only a WEAVE repo URL/path plus ordinary intent can
discover the repo bootstrap contract, become COS WEAVE, create/load local WEAVE
state, use the WEAVE-to-Symphony adapter internally, and report proof/readback
without asking the user to run commands, classify lifecycle stages, create queue
roots, or understand Symphony.
```

The expected user prompt is one line:

```text
Use this repo as COS WEAVE: <WEAVE repo URL or local path>. Help me move my app forward.
```

## Capability Question

What repo-contained instructions must exist so a generic Codex agent can
self-bootstrap?

Required capability surfaces:

- root `AGENTS.md` points prompt-first agents to bootstrap instructions;
- `README.md` and `docs/README.md` expose the prompt-first entrypoint;
- `docs/COS_WEAVE_BOOTSTRAP.md` gives the exact agent procedure;
- `packages/weave-tool/skills/cos-weave/SKILL.md` packages the reusable agent
  behavior;
- deterministic tests verify the instructions are discoverable and reject
  command-first relapse.

## Lifecycle Scope And Non-Claims

In scope:

- source discovery from repo URL/path;
- COS WEAVE state line;
- local WEAVE home creation/loading;
- first-run onboarding questions in plain language;
- intent truth and lifecycle inference;
- local WorkItem creation;
- internal WEAVE-to-Symphony adapter dispatch;
- local worker proof envelope;
- WEAVE readback state.

Non-claims:

- no live Symphony service execution;
- no live Codex app-server execution;
- no live tracker or Linear mutation;
- no production deploy;
- no public send;
- no billing, payment, or paid call;
- no credential access or secret handling.

## Architecture Boundary

COS WEAVE is user-facing. Symphony is behind the scenes.

| Layer | Owns |
| --- | --- |
| COS WEAVE | User chat, onboarding, intent truth, lifecycle stage inference, owner gates, proof review, non-claims, readback |
| Adapter | Conversion from WorkItem to dispatch item, prompt rendering, local queue/workspace/proof plumbing |
| Symphony | Future live workspace orchestration, retries, Codex app-server sessions, operational status |
| Worker | Bounded task execution and proof envelope closeout |

The owner talks to COS WEAVE, not Symphony.

## Implementation Slices

### Slice 0: Instruction Discovery

Goal: a generic Codex agent knows what to read after seeing the repo URL/path.

Build:

- root pointer in `AGENTS.md`;
- public pointer in `README.md`;
- bootstrap doc and skill;
- tests for prompt-first discovery.

Proof surface:

- deterministic text tests over repo docs and skill files.

Non-claim:

- docs do not prove actual worker execution.

### Slice 1: COS WEAVE Home

Goal: the agent creates or loads local WEAVE home/state automatically.

Build:

- public-safe local home selection rule;
- state line and home-state write path;
- onboarding question policy.

Proof surface:

- local state file and tests that do not require user command execution.

Non-claim:

- local home does not prove live runtime attachment.

### Slice 2: Normal Intent To WorkItem

Goal: ordinary user intent becomes a valid WorkItem without manual stage
classification.

Build:

- intent truth;
- lifecycle inference;
- owner boundary and proof requirements;
- non-claims.

Proof surface:

- WorkItem validator tests and fixture tests.

Non-claim:

- inferred local slice does not prove full lifecycle completion.

### Slice 3: Internal Adapter Proof

Goal: COS WEAVE uses the WEAVE-to-Symphony adapter internally.

Build:

- local queue/workspace creation;
- dispatch item;
- WEAVE workflow prompt;
- local worker process;
- proof envelope and readback.

Proof surface:

- local worker proof path and readback `ACCEPT_FOR_SCOPE`.

Non-claim:

- local worker process does not prove live Symphony or live Codex app-server.

### Slice 4: Prompt-First End-To-End Rehearsal

Goal: a generic-agent simulation from repo URL/path plus ordinary intent can
recover the instructions and know the correct internal path.

Build:

- deterministic tests over docs and skill;
- optional internal helper for agent/test use only;
- no product-facing command requirement.

Proof surface:

- tests prove the instructions contain enough steps and forbid manual user
  queue/lifecycle/Symphony work.

Non-claim:

- a deterministic text test does not prove a live generic Codex thread followed
  the instructions.

### Slice 5: Gated Live Symphony/Codex App-Server

Goal: prove a live Symphony/Codex app-server path only after local prompt-first
proof is strong.

Requires:

- explicit owner approval;
- disposable public-safe work item;
- no deploy, public send, billing, credentials, or live tracker mutation unless
  separately approved.

Proof surface:

- live target-surface readback from the approved service.

Non-claim:

- one live smoke does not prove production readiness.

## Adversarial Review Questions

- Did the product relapse into command-first UX?
- Did any instruction ask the user to run adapter, queue, dispatch, or Symphony
  commands?
- Did the agent ask the user to classify lifecycle stage manually?
- Did a fake proof replace actual local worker proof on the happy path?
- Did local proof overclaim live Symphony, live Codex app-server, tracker,
  deploy, public-send, billing, or credential success?
- Is there hidden setup burden that the user would discover only after pasting
  the repo path?
- Does readback preserve proof path and non-claims?
- Does a blocked source produce `BLOCKED` or `NEEDS_OWNER_ACTION`, not a
  traceback?

## Acceptance Checks

- `docs/COS_WEAVE_BOOTSTRAP.md` exists and names the one-line prompt-first UX.
- `packages/weave-tool/skills/cos-weave/SKILL.md` exists and says internal
  commands are not product UX.
- root `AGENTS.md` points generic agents to the bootstrap doc.
- README surfaces the prompt-first entrypoint.
- Tests verify the bootstrap contract contains enough information for a generic
  agent to self-bootstrap from repo URL/path plus ordinary intent.
- Tests verify the CE doc acceptance sentence rejects command-first UX.
- Local adapter tests still prove WorkItem, dispatch, prompt, local worker,
  proof envelope, and readback behavior.

## Stop Boundaries

Stop as `BLOCKED` or `NEEDS_OWNER_ACTION` when:

- the source repo cannot be opened safely;
- bootstrap instructions are missing or contradictory;
- local state cannot be created safely;
- proof envelope validation fails;
- the next step needs live Symphony, live Codex app-server, live tracker,
  deploy, public send, billing, credentials, destructive action, or paid calls
  without explicit approval.

## Future Live-Service Gate

Live Symphony/Codex app-server proof is a separate gated slice. The prompt-first
bootstrap contract must remain true when that slice is added: the owner still
starts from one normal Codex thread plus repo URL/path, while the agent handles
service setup, proof, readback, and non-claims internally.

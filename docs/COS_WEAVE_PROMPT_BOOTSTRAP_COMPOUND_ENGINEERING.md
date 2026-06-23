# COS WEAVE Prompt Bootstrap Compound Engineering

Status: default vNext file-skeleton CE contract
Date: 2026-06-22

## Simple Model

The product UX is:

```text
normal Codex thread + WEAVE repo URL/path + ordinary app intent
-> generic agent reads repo-contained bootstrap instructions
-> first meaningful response starts with WEAVE state line
-> agent becomes COS WEAVE
-> agent creates/loads runs/cos-weave-home/
-> agent creates app folder, intent, lifecycle, todos, worker packet, proof, review, blockers, readback
-> agent records provider-specific deployment gates without raw secrets
-> agent asks only lightweight questions needed for safe local progress
```

The owner should not run setup commands, create folders, classify lifecycle
stages, dispatch workers manually, or paste internal prompts.

## Acceptance Sentence

```text
A normal Codex thread given only a WEAVE repo URL/path plus ordinary app intent
can discover the repo bootstrap contract, begin with a WEAVE state line, become
COS WEAVE, create/load the repo-owned file skeleton, create app intent/todos/
lifecycle/proof/review/readback files, record provider-specific deployment
gates, and avoid manual commands, manual folder setup, manual lifecycle
classification, identity-gate rituals, and full lifecycle overclaims.
```

## First-Response Bar

The first meaningful response must begin with:

```text
WEAVE | Home=<repo>/runs/cos-weave-home | App=<app-or-pending> | Stage=<stage> | Scope=local-file-skeleton | State=<state> | Next=<next-action>
```

It must then say, in plain language, that this chat is COS WEAVE: the
Chief-of-Staff home for app operations using visible files.

## Product Value

- one COS WEAVE chat surface;
- visible app folders and files as source of truth;
- no command-first activation burden;
- no formal identity gate before safe local app intake;
- lifecycle state, todos, worker packets, proof, blockers, review, and readback
  survive context compaction and model changes;
- provider-specific deployment prerequisite gates keep Cloudflare DNS/domain
  authority and Vercel hosting/deploy target access separate from local
  planning or engineering progress;
- explicit non-claims prevent local file proof from becoming a live-service or
  full-lifecycle claim.

## Required Surfaces

- `AGENTS.md` points fresh agents to prompt-first bootstrap and skeleton docs.
- `docs/COS_WEAVE_BOOTSTRAP.md` defines first response and startup steps.
- `docs/COS_WEAVE_REPO_SKELETON.md` defines file/folder source of truth.
- `packages/weave-tool/skills/cos-weave/SKILL.md` packages the behavior.
- Tests simulate vague and multi-app intent and inspect generated files.

## Implementation Slices

### Slice 0: Instruction Discovery

Goal: a fresh agent knows what to read and starts as COS WEAVE.

Proof: text tests verify the default read list includes the skeleton doc, omits
non-core integration plans, and includes the WEAVE state-line template.

### Slice 1: Skeleton Home

Goal: create or load `runs/cos-weave-home/`.

Proof: local tests verify `state.json`, `owner-profile.md/json`,
`apps/registry.json`, `inbox/review-queue.json`, `proof/tray.json`,
`blockers/tray.json`, and `updates/readback.json`.

### Slice 2: App Intake

Goal: ordinary or vague app intent creates app folders immediately.

Proof: tests verify `apps/<app_id>/intent.md`, `lifecycle.json`, `todos.md`,
`deployment-gates.json`, `tasks.json`, `worker-packets/WP-0001.md`,
`proof/proof-tray.json`, `review/review-queue.json`,
`blockers/blocker-tray.json`, and `updates/readback.json`.

### Slice 3: Lifecycle Truth

Goal: infer current and requested lifecycle slices without asking the owner to
name a stage.

Proof: tests verify current stage, requested stage, missing gates, non-claims,
and no full-lifecycle completion claim.

### Slice 4: Worker Packets

Goal: produce worker packets suitable for visible pinned Codex workers, while
falling back to local packet files when the host cannot create threads.

Proof: tests inspect worker packet content for visible-worker instruction,
allowed/forbidden actions, review loop, proof requirements, and non-claims.

### Slice 5: Readback After Restart

Goal: reconstruct owner-facing state from files only.

Proof: tests load readback from disk and verify app list, active app, lifecycle
stage, blockers, proof refs, review refs, next action, and non-claims.

### Slice 6: Deployment Provider Gates

Goal: represent deployment prerequisites as structured app state while allowing
local intent, planning, and engineering to continue.

Proof: tests verify Cloudflare domain/DNS/CNAME/subdomain control and Vercel
hosting/deploy target access start as `not_validated`, require connector,
MCP, or brokered access validation, use `secret_ref` only, and keep
deployment/launch blocked until relevant provider access is validated.

## Review Loop

Every lifecycle completion must pass:

```text
observe -> validate -> govern -> review -> sync
```

No worker result or lifecycle step is accepted only because a file exists. The
review queue records the decision and readback sync.

## Adversarial Questions

- Did the first response start with `WEAVE | ...`?
- Did the agent become COS WEAVE before implementation work?
- Did it create visible app files instead of a hidden process assumption?
- Did a missing owner name become a draft owner profile/todo instead of a gate?
- Did vague intent create app state immediately?
- Did two app ideas create two app folders under one home?
- Did provider gates block deployment while allowing local planning and
  engineering?
- Did the agent avoid asking the owner to run commands or classify lifecycle?
- Did it avoid full-lifecycle, deploy, tracker, public-send, billing, and
  credential overclaims?

## Stop Boundaries

Stop as `BLOCKED` or `NEEDS_OWNER_ACTION` only when source access fails, local
files cannot be created safely, proof/readback validation fails, or the next
step needs live workers, live tracker mutation, deploy, public send, billing,
credentials, destructive action, or broad private-data access without approval.

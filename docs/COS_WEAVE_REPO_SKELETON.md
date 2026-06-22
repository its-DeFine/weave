# COS WEAVE Repo Skeleton

Status: default vNext source of truth
Date: 2026-06-22

COS WEAVE starts as a simple file/folder system. A normal Codex or Hermes agent
can read these files after context compaction, model changes, or handoff and
continue without hidden process memory.

## Default Home

Default ignored local home:

```text
runs/cos-weave-home/
```

The owner may choose another home, but the normal prompt-first flow should not
ask the owner to create folders or run setup commands manually.

## Required Layout

```text
runs/cos-weave-home/
  README.md
  state.json
  owner-profile.md
  owner-profile.json
  apps/
    registry.json
    <app-id>/
      app.json
      intent.md
      intent.json
      lifecycle.json
      todos.md
      tasks.json
      lifecycle/
        lifecycle-state.json
        01-intent/
          procedure.md
          state.json
        ...
      worker-packets/
        WP-0001.md
      tasks/
        tasks.json
        worker-packets/
          WP-0001.md
      proof/
        proof-tray.json
      blockers/
        blocker-tray.json
      review/
        review-queue.json
      updates/
        readback.json
  procedures/
    lifecycle/
      01-intent.md
      ...
  tasks/
    worker-packets.json
  proof/
    tray.json
  blockers/
    tray.json
  review/
    queue.json
  inbox/
    review-queue.json
  updates/
    readback.json
```

## First-Run Behavior

When the user says something ordinary such as:

```text
Use this repo as COS WEAVE: <repo URL/path>. I want to build a tiny local calculator app.
```

COS WEAVE should:

1. Emit the WEAVE state line before implementation work.
2. Create or load the WEAVE home.
3. Create or update `owner-profile.md/json` as `draft` /
   `assumed_for_local_scope` if no owner profile exists.
4. Create one app folder per inferred app.
5. Record the owner words in `intent.md/json`.
6. Infer lifecycle stage from ordinary language.
7. Create todos and worker-packet files for the next bounded step.
8. Record proof, blockers, review state, readback, and explicit non-claims.

Missing owner preferences are questions and todos, not a hard blocker for safe
local planning or engineering. Hard gates still apply to credentials, public
sends, billing, production deploys, tracker mutation, destructive actions, and
broad private-data access.

## Acceptance

The file skeleton is the product acceptance surface for the current vNext.
Optional orchestration backends may be added later, but they are not required
for default COS WEAVE startup, app intake, todo creation, lifecycle state,
proof, review, or readback.

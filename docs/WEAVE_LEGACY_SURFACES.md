# WEAVE Legacy Surface Inventory

WEAVE vNext default startup is COS-first and file-skeleton-first. The current
product source of truth is `runs/cos-weave-home/` with app registry, app
folders, lifecycle state, todos, worker packets, proof, blockers, review, and
readback.

This inventory explains why older public artifacts remain in the repository.
They are not part of first contact, onboarding, or product acceptance.

## Default Path

- Start from `COS_WEAVE_FIRST_CONTACT.md`, `COS_WEAVE_LAUNCHER.md`, and
  `docs/COS_WEAVE_BOOTSTRAP.md`.
- Create or load `runs/cos-weave-home/`.
- Record each app under `apps/<app-id>/` with `intent.md/json`,
  `lifecycle.json`, `todos.md`, `worker-packets/`, `proof/`, `blockers/`,
  `review/`, and `updates/readback.json`.
- Treat missing owner preferences as draft questions/todos, not as a hard
  identity gate for safe local planning.

## Retained Advanced References

- TUI/Textual files remain as historical cockpit proof and regression coverage.
  They are not the default user path.
- Hermes/runtime files remain as bounded integration references for older local
  runtime experiments. They are not required for COS WEAVE first run.
- Telegram/gateway/deployment files remain as proof-bound optional references.
  They do not prove live sends, deployment, production runtime, or public
  operation unless those exact surfaces are run under separate approval.
- Month 1 runtime QA and dogfood artifacts remain as historical evidence and
  local deterministic tests. They are not owner-facing launch instructions.

## Removed Or Archived By Current Direction

- The default product no longer requires an external orchestration adapter.
- No default startup doc should ask the owner to understand adapter internals,
  create queues, classify lifecycle stages, choose runtime modes, or run TUI
  commands before app intake.
- Optional future orchestration can be reintroduced only as a separate
  integration slice after the file skeleton path is working.

## Review Rule

If a fresh Codex agent is following default startup, it should not read this file
before it has emitted the WEAVE state line and created or loaded the local file
skeleton. This file is for cleanup, review, and later integration decisions.

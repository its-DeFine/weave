# Build-Ready Handoff Packet: WEAVE Runtime Slice 1

Date: 2026-05-30
Contract: `docs/weave-runtime-technical-gestalt-contract-v0.1.md`
Authority level: local artifact / modify provided project

## Target

Build the first local WEAVE runtime substrate:

- setup contract
- git-tracked root and app workspace model
- document templates
- app registry
- append-only event ledger
- REST API skeleton contract
- multi-app UI projection contract
- Hermes adapter contract
- foundation gate rules

## Whole-System Trace

Final vision supported: Hermes helps the owner create and manage multiple apps,
while WEAVE records, verifies, exposes, and visualizes the work.

Gestalt invariants protected:

1. Hermes is the agent.
2. WEAVE is the deterministic machine around Hermes.
3. The UI is not chat.
4. Foundation context is unskippable.
5. Every app is git tracked.
6. The owner can see what changed.

## Inputs

- `docs/weave-runtime-story-contract-v0.1.md`
- `docs/weave-runtime-technical-gestalt-contract-v0.1.md`
- `docs/weave-runtime-document-templates-v0.1.md`
- current WEAVE package and scripts

## Outputs

Expected future implementation outputs:

- setup command
- root folder creator/checker
- app registry reader/writer
- event schema validator
- document template installer
- REST API server
- UI projection updates
- test suite

## Non-Goals

Do not implement:

1. Telegram bot behavior.
2. Production deployment.
3. Remote API exposure.
4. Paid jobs or provider mutation.
5. Full autonomous executor.

## Tests

Functional:

Given a clean local directory, when `weave setup` runs, then required root,
template, registry, and runtime profile files exist.

Failure:

Given missing `soul.md`, when Hermes attempts app work, then the foundation gate
blocks and records missing context.

Gestalt:

Given multiple apps, when the UI opens, then the owner sees app stage, changes,
blockers, and contract status without using the UI as chat.

## Definition Of Complete

This slice is complete when:

1. Setup and doctor behavior are implemented.
2. Root/app workspace schemas are implemented.
3. Templates are installed.
4. Ledger validates and appends events.
5. API exposes health, app list, app state, and events.
6. UI projects multiple apps and changes per app.
7. Foundation gate is enforced in the Hermes adapter contract.
8. Public-safe checks and tests pass.

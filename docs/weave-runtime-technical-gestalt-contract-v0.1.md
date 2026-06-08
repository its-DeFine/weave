# WEAVE Runtime Technical Gestalt Contract v0.1

Date: 2026-05-30
Status: technical contract draft
Source: `docs/weave-runtime-story-contract-v0.1.md`

## 1. Contract Metadata

Project name: WEAVE Hermes operating environment
Version: 0.1
Owner: repository owner
Contract maturity level: Level 3 target for first slice
Current mode: Contract Mode

## 2. Raw Vision

The owner wants an agent to help create and manage multiple applications
properly. Hermes is the primary agent. WEAVE is the operating environment around
Hermes: setup, folders, git tracking, ledger, verifier, deterministic Telegram
commands, REST API, and document templates.

The interaction model is story-first:

- Hermes is the man in the box.
- Telegram is the cellphone.
- WEAVE root is the house.
- App workspaces are rooms.
- Lifecycle folders are shelves.
- Ledger is the recording machine.
- Telegram slash commands are the viewing window for this slice.
- REST API is the remote control.
- Verifier is the inspector.

## 3. Gestalt Kernel

Core outcome: a Hermes-led, WEAVE-supported environment where multiple apps can
be created, managed, validated, and iterated without losing owner intent,
project context, evidence, or lifecycle state.

Finished-state experience: the owner talks to Hermes through Telegram, while
deterministic slash commands show all apps, stage per app, changes per app,
current blockers, approvals, evidence, and contract diffs.

Non-negotiables:

1. Hermes owns semantic reasoning.
2. WEAVE owns deterministic substrate, verification, ledger, Telegram status
   commands, and runtime control.
3. Foundation context is unskippable.
4. Every app has its own git-tracked room.
5. Every app has app-specific context used throughout the lifecycle.
6. Every important artifact belongs to a lifecycle stage.
7. Reused artifacts are referenced, not copied.
8. Gestaltian Contracts are versioned, git tracked, and diff-visible.
9. Slash commands are not chat; normal Telegram messages remain Hermes
   conversation.

Definition of done for the first slice:

1. `weave setup` creates or verifies the WEAVE root, Telegram channel config,
   REST API auth, document templates, and app registry.
2. `weave start` launches or reconnects to the runtime API and Telegram gateway.
3. `/apps` shows multiple apps and stage per app.
4. Hermes foundation gate blocks work until `soul.md`, `owner-profile.md`, app
   context, contract, lifecycle state, and capabilities are sufficient.
5. Hermes can emit structured events.
6. WEAVE records events in an append-only ledger.
7. A sample app reaches Kernel and Contract stages.
8. Contract diff is visible through deterministic status or REST output.
9. REST API can report health, list apps, read app state, and stop runtime.

Definition of wrong:

1. Slash commands are answered by Hermes instead of deterministic runtime state.
2. WEAVE becomes a second planner.
3. Hermes starts work before foundation context exists.
4. App contexts are mixed or absent.
5. Contract changes disappear into chat.
6. Command output becomes noisy, stale, or misleading.
7. Remote API is exposed before auth and transport are clear.

## 4. System Boundary

Inside scope:

1. Local WEAVE root setup.
2. Telegram as first Hermes communication channel.
3. Local REST API.
4. Multi-app registry.
5. Git-tracked app workspaces.
6. Foundation gate.
7. Document templates.
8. Ledger and event schemas.
9. Telegram status information architecture.
10. Hermes adapter contract.
11. First Build-Ready Handoff Packet.

Outside scope for first slice:

1. Production deploys.
2. Paid jobs.
3. External sends.
4. Credential mutation.
5. Public remote API exposure.
6. Full autonomous implementation executor.
7. Multi-user collaboration.

## 5. Root File Structure

```text
<weave-root>/
  .git/
  artifacts/
    general/
      soul.md
      owner-profile.md
  apps/
    registry.json
    <app_id>/
      .git/ or git-reference.json
      app.weave.json
      context/
        app-context.md
        user-context-for-this-app.md
        domain-context.md
        reality-briefs/
        decisions.md
      inventory/
        app-inventory.md
      repos/
        primary/
        worktrees/
        prs/
      contract/
        gestaltian-contract.md
        versions/
        diffs/
      lifecycle/
        01-intent/
          artifacts/
          refs/
        02-kernel/
          artifacts/
          refs/
        03-contract/
          artifacts/
          refs/
        04-premortem/
          artifacts/
          refs/
        05-handoff/
          artifacts/
          refs/
        06-implementation/
          artifacts/
          refs/
        07-qa/
          artifacts/
          refs/
        08-kpi-setup/
          artifacts/
          refs/
        09-marketing/
          artifacts/
          refs/
        10-iteration/
          artifacts/
          refs/
        11-analysis/
          artifacts/
          refs/
      evidence/
      approvals/
      ledger/
        events.jsonl
        procedure-feedback/
      exports/
  runtime/
    profiles/
    logs/
    tokens/
```

## 6. File Schemas

### `app.weave.json`

```json
{
  "schema": "weave-app/v0.1",
  "app_id": "",
  "name": "",
  "status": "active | paused | archived",
  "created_at": "",
  "current_stage": "",
  "stage_source": "hermes | derived",
  "contract_version": "",
  "primary_repo": "",
  "context_paths": [],
  "ledger_path": "ledger/events.jsonl"
}
```

### `apps/registry.json`

```json
{
  "schema": "weave-app-registry/v0.1",
  "apps": [
    {
      "app_id": "",
      "name": "",
      "path": "",
      "stage": "",
      "stage_source": "hermes | derived",
      "last_changed_at": "",
      "contract_version": ""
    }
  ]
}
```

### Event schema

```json
{
  "schema": "weave-event/v0.1",
  "event_id": "",
  "type": "",
  "app_id": "",
  "created_at": "",
  "created_by": "hermes | weave-runtime | owner",
  "stage": "",
  "summary": "",
  "payload": {},
  "artifact_refs": [],
  "contract_version": "",
  "approval_ref": "",
  "git_commit": ""
}
```

Required event types:

- `app.created`
- `foundation.missing_context`
- `foundation.completed`
- `soul.updated`
- `owner_profile.updated`
- `app_context.updated`
- `lifecycle.stage_registered`
- `lifecycle.stage_derived`
- `artifact.created`
- `artifact.updated`
- `artifact.reference_recorded`
- `contract.updated`
- `contract.diff_recorded`
- `approval.requested`
- `approval.resolved`
- `procedure.violation`
- `procedure.feedback_sent`
- `validation.completed`
- `window.changed`

### Artifact reference schema

```json
{
  "schema": "weave-artifact-ref/v0.1",
  "artifact_id": "",
  "canonical_path": "",
  "source_stage": "",
  "used_by_stage": "",
  "reason": "",
  "checksum": "sha256:"
}
```

### Approval schema

```json
{
  "schema": "weave-approval/v0.1",
  "approval_id": "",
  "app_id": "",
  "requested_by": "hermes",
  "requested_at": "",
  "channel": "telegram",
  "action": "",
  "reason": "",
  "risk_level": "",
  "information_shown_to_owner": [],
  "decision": "approved | rejected | deferred",
  "decided_at": "",
  "conditions": [],
  "ledger_event_id": ""
}
```

## 7. Setup Commands

```bash
weave setup
weave doctor
weave start
weave stop
weave app list
weave app create <app_id>
weave open
weave export-handoff <app_id>
```

`weave setup` must:

1. Create or verify the WEAVE root repo.
2. Create required folders.
3. Create document templates if missing.
4. Configure Telegram channel metadata.
5. Generate local REST API token.
6. Create runtime profile.
7. Create app registry.
8. Run `weave doctor`.

## 8. REST API Contract

Default bind: loopback only.

Default auth: generated bearer token.

Endpoints:

```text
GET  /health
GET  /runtime/status
POST /runtime/stop
POST /runtime/restart-hermes
GET  /apps
POST /apps
GET  /apps/{app_id}/state
GET  /apps/{app_id}/events
POST /apps/{app_id}/events
GET  /apps/{app_id}/artifacts
GET  /apps/{app_id}/contract/diff
POST /apps/{app_id}/procedure-feedback
GET  /telegram/commands
```

Non-local access requires a separate approval packet.

## 9. Telegram Status Information Architecture

Default command set:

1. `/apps`: app list with stage per app.
2. `/app <app_id>`: selected app summary.
3. `/blockers`: foundation gate and blocker status.
4. `/changes [app_id]`: latest changes.
5. `/next`: next owner-visible action.
4. Current lifecycle shelf.
5. Current blocker or next action.
6. Changes in this app:
   - contract diff
   - app context diff
   - latest artifact change
   - latest lifecycle stage change
   - latest approval change
   - latest owner-visible status change
7. Evidence and approval status.
8. Secondary drawers:
   - raw ledger events
   - transcript summary
   - files
   - REST/API health

Slash commands must not include a Hermes message composer. They are status
requests, not conversation turns.

Command output changes require the same lifecycle flow: intent, packet,
worktree, validation, ledger, and contract update if the change affects the
product meaning.

## 10. Hermes Adapter Contract

The adapter translates between Hermes and WEAVE. It is not an agent.

Responsibilities:

1. Confirm Telegram or runtime reachability.
2. Load `soul.md`, `owner-profile.md`, app context, app inventory, contract,
   lifecycle artifacts, and allowed capabilities.
3. Enforce foundation gate checks before task execution.
4. Receive or poll Hermes outputs.
5. Normalize outputs into WEAVE events.
6. Post events to the REST API.
7. Provide procedure feedback when Hermes omits required fields.
8. Prevent approval-gated action translation unless approval exists.

Non-responsibilities:

1. Decide lifecycle meaning.
2. Route approvals.
3. Replace Hermes reasoning.
4. Hide uncertainty.
5. Mutate production systems.

## 11. Foundation Gate

Hermes must not begin serious app work until the foundation gate passes.

Gate inputs:

- `soul.md`
- `owner-profile.md`
- `context/app-context.md`
- `inventory/app-inventory.md`
- `contract/gestaltian-contract.md`
- lifecycle stage
- available capabilities
- blockers

Pass condition:

Hermes has high confidence that all required context exists, is current enough,
and is sufficient for the requested work.

Fail behavior:

Hermes asks the owner through Telegram, updates the missing document, and emits
`foundation.missing_context` followed by `foundation.completed` when resolved.

## 12. Build-Ready Handoff Packet: Slice 1

Target: create the local WEAVE operating substrate for setup, multi-app state,
event ledger, document templates, and Telegram slash-command status.

Authority level: local artifact / modify provided project.

Whole-system trace:

This slice supports the vision of Hermes as the agent and WEAVE as the machine
that records, verifies, exposes, and visualizes Hermes-led app work.

Included components:

1. Setup command contract.
2. WEAVE root folder schema.
3. Document template files.
4. App registry schema.
5. Event ledger schema.
6. REST API contract.
7. Telegram status information architecture.
8. Hermes adapter contract.
9. Foundation gate rules.

Non-goals:

1. Real production deployment.
2. Full Telegram bot daemon implementation.
3. Full web UI implementation.
4. External remote API exposure.
5. Paid or provider-mutating actions.

Acceptance criteria:

1. `weave setup` can create or validate the folder model.
2. Multiple apps can be listed with stage per app.
3. App context documents exist and are loaded by contract.
4. Foundation gate blocks missing `soul.md`, `owner-profile.md`, or app context.
5. Ledger can append valid events and reject malformed ones.
6. Slash commands can show app list, stage per app, changes per app, and
   current blocker.
7. REST API can return health, runtime status, app list, app state, and events.
8. Command output changes are treated as editable artifacts with ledger records.
9. Contract diffs are recorded and visible.
10. Telegram gateway setup is represented as a required setup gate that can be
    executed through the setup command with a redacted local configuration path
    and explicit live-run verification.

## 13. Validation Protocol

Functional:

- Given a WEAVE root, when `weave doctor` runs, then it reports missing setup
  pieces without requiring Hermes to be online.

Failure:

- Given missing `owner-profile.md`, when Hermes receives a task, then the
  foundation gate blocks task execution and asks the owner through Telegram.

Gestalt:

- Given multiple apps, when the owner sends `/apps`, `/blockers`, or `/next`,
  then they can understand which apps exist, what stage each is in, what
  changed, and what requires attention without reading raw logs.

## 14. Story-To-Technical Mapping

| Story object | Technical primitive |
|---|---|
| Owner | Human operator |
| Man in the box | Hermes agent |
| Cellphone | Telegram channel |
| House | WEAVE root git repo |
| App room | App workspace |
| Shelves | Lifecycle directories |
| Recording machine | Event ledger |
| Viewing window | WEAVE Telegram slash commands |
| Inspector | Deterministic verifier |
| Remote control | REST API |
| Character paper | `soul.md` |
| Owner paper | `owner-profile.md` |
| App context shelf | `context/` |
| App paper | Gestaltian Contract |
| Permission slip | Approval record |

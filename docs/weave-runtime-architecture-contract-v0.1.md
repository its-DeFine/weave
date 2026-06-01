# WEAVE Runtime Architecture Contract v0.1

Date: 2026-05-30
Status: architecture contract
Scope: CLI launch, Hermes lifecycle authority, local state, and Telegram status UX

## 1. Verdict

WEAVE should not become a second brain beside Hermes.

Hermes is the primary agent and lifecycle authority. If Hermes is equipped with
the WEAVE company package, the Gestalt Runtime Pack, the
`gestalt-to-artifact` method, the app workspace state, and the allowed
capability list, Hermes should decide and register the current lifecycle stage,
identify missing ingredients, compile the next packet, and follow the work from
intent to operational app.

The WEAVE CLI and local wrapper should do only the work that cannot reasonably
be delegated to Hermes:

- launch and supervise local processes
- configure or verify the user's Hermes communication channel
- expose deterministic Telegram slash-command status
- persist an append-only local ledger
- mirror Hermes' lifecycle state without reinterpreting it
- validate schemas and public-safe boundaries
- record approval requests and resolutions
- verify that Hermes followed required procedures before allowing gated actions
- provide diagnostics when Hermes, the command surface, or local state is unavailable
- expose a REST API for runtime control and remote inspection

This keeps the product simple: Hermes does the cognitive work; WEAVE makes the
cognitive work legible, durable, and locally operable.

## Term Definitions

Gestalt Kernel: the compact essence of a whole-system vision before it is
decomposed. It captures core outcome, finished-state experience,
non-negotiables, done, wrong, core entities, transformations, human role,
system role, and smallest living version.

Gestaltian Contract: the versioned contract derived from the kernel. It defines
system boundary, actors, workflows, decisions, information requirements,
rules, component contracts, failure modes, approval loops, tests, slices, open
questions, and traceability.

Build-Ready Handoff Packet: the bounded implementation packet that says exactly
what can be built, what authority it has, what inputs and outputs are required,
what tests protect it, and what not to implement.

Lifecycle stage: Hermes' current registered phase of work for an app or
artifact. WEAVE may also show a derived stage when artifact rules make that
stage mechanically provable.

Derived state: a WEAVE runtime projection computed from artifacts, schemas,
paths, and ledger events. Derived state is useful for command clarity, but it
is not Hermes' semantic judgment.

## 2. Finished-State UX

The user runs:

```bash
weave start
```

WEAVE starts or reconnects to the local runtime and gateway. The user
communicates with Hermes through Telegram. Telegram slash commands are the
deterministic operating surface that shows what Hermes currently understands,
what lifecycle stage is registered or deterministically inferred, what is
missing, what is blocked, and what action is next.

The desired feeling is not "dashboard management." It is "I am in a calm
operating room with the right agent, the right method, and the right state."

The user should be able to answer these questions in seconds:

- What app or artifact are we making?
- What apps do we have, and what stage is each app in?
- What stage are we in?
- Why are we in that stage?
- What does Hermes need next?
- What assumptions are active?
- What is blocked on me?
- What evidence exists?
- What will happen if I approve the next action?

## 3. Gestalt Kernel For This Architecture Contract

This kernel describes the architecture contract itself. It is not the Gestalt
Kernel for any particular app that Hermes will build later.

Project name: WEAVE Hermes operating environment

Core outcome: A local WEAVE tool connects the user to a Hermes agent and a
deterministic Telegram status surface that can carry an app idea through the
`gestalt-to-artifact` method into a validated operational app.

Finished-state experience: The user starts WEAVE from the CLI, talks to Hermes
through Telegram, and uses clear low-clutter slash commands to inspect Hermes'
stage, reasoning artifacts, evidence, blockers, and handoff readiness.

Non-negotiable qualities:

1. Hermes owns lifecycle semantics.
2. WEAVE does not duplicate Hermes' judgment.
3. The command surface reduces cognitive clutter.
4. State is durable enough to survive process restarts.
5. Every build action traces back to the Gestalt contract.
6. External effects remain approval-gated.
7. Runtime readiness is not overclaimed.

Definition of done:

1. `weave start` opens or reconnects to the runtime and Telegram gateway.
2. Hermes is initialized with WEAVE knowledge, prompts, skills, and current app
   state.
3. The user can communicate with Hermes through the configured channel.
4. Hermes registers lifecycle stage events.
5. Telegram slash commands mirror Hermes' registered state and packet progress.
6. The local ledger records stage, decision, evidence, assumption, blocker, and
   approval events.
7. The first app intent can reach at least Gestalt Kernel and Contract stages
   with visible missing ingredients and next action.

Definition of wrong:

1. WEAVE becomes a competing planner or project manager beside Hermes.
2. The CLI invents or mutates lifecycle stages independently from Hermes.
3. Slash commands show too much noise and make the user supervise
   implementation details.
4. Simulated proof is treated as proof of a real Hermes-backed runtime.
5. The ledger hides uncertainty or overwrites history.
6. Approval-gated work happens because status output made it feel routine.

Smallest living version:

```text
weave setup
  -> creates or verifies the git-tracked WEAVE root
  -> configures the Telegram Hermes communication channel
  -> configures local REST API authentication
  -> verifies WEAVE package and Hermes profile readiness

weave start
  -> starts or reconnects to the local WEAVE runtime API
  -> starts or reconnects to the Telegram gateway
  -> indexes all app workspaces under the WEAVE root
  -> resumes visible state for every app
  -> initializes or checks Hermes context
  -> user sends raw intent through Telegram
  -> Hermes emits lifecycle and artifact events
  -> local ledger persists them
  -> slash commands show app list, stage per app, Kernel, missing ingredients, blockers, and next action
```

`weave start` does not imply Hermes can only work on one app at a time. It
starts the local runtime and status layer, then loads the app index. The
command surface must support multiple apps from the first slice.

If Hermes is already active before `weave start`, Hermes can still work through
Telegram. WEAVE mirrors that work live only when the runtime API is active and
Hermes can write or post structured events. If Hermes worked while WEAVE was
offline, `weave start` should offer a sync/import path from the git-tracked app
folders and Hermes event artifacts.

## 4. Setup Model

Setup is a first-class workflow, separate from start.

```bash
weave setup
```

Setup responsibilities:

1. Create or verify a git-tracked WEAVE root repository.
2. Create the root folder structure.
3. Configure Telegram as the first Hermes communication channel.
4. Configure local REST API authentication.
5. Create or verify the Hermes runtime profile.
6. Install or verify the WEAVE company package, Gestalt Runtime Pack, and
   custom skills.
7. Create the app registry.
8. Create the unskippable foundation gate.
9. Run `weave doctor` checks.

The WEAVE root must always be git tracked. The user may choose not to publish
it to GitHub, but local git history, branches, worktrees, and pull-request-like
review records are still required.

Recommended first REST API security model:

1. Bind to loopback by default.
2. Require a local bearer token generated during setup.
3. Store the token outside public repo artifacts.
4. Allow remote access only through an explicit owner-approved transport.
5. Require a separate auth/transport packet before non-local exposure.

This is easy to use locally while still making accidental remote exposure hard.

## Foundation Gate

Before serious work begins, Hermes must confirm that it has enough context to
operate with high confidence. This is not a user-optional flow and should not
wait until the user asks for a task.

The foundation gate checks:

1. `soul.md`: how Hermes should think, behave, challenge, ask, and proceed.
2. `owner-profile.md`: who the owner is, how they work, and what help they need.
3. app context: the specific app's users, domain, constraints, reality sources,
   and known decisions.
4. current Gestaltian Contract.
5. lifecycle state.
6. available capabilities.
7. current blockers and approvals.

If required context is missing, stale, contradictory, or low-confidence, Hermes
must ask the owner through Telegram and update the relevant document before
continuing.

## 5. Authority Split

### 5.1 Hermes Owns

Hermes owns the cognitive and lifecycle layer:

- interpreting user intent
- preserving the whole before decomposition
- applying `gestalt-to-artifact`
- deciding current lifecycle stage
- registering stage transitions
- compiling the Gestalt Kernel
- compiling and updating the app's versioned Gestaltian Contract
- committing Gestaltian Contract updates to the app git repo or requesting the
  runtime to do so through a structured event
- maintaining and consulting `soul.md`, `owner-profile.md`, and app context
- stopping at the foundation gate when required context is missing or
  low-confidence
- running premortem reasoning
- compiling Build-Ready Handoff Packets
- identifying missing ingredients
- classifying assumptions and gaps
- deciding whether implementation is blocked
- requesting human approval where required
- routing approval requests to the user through the configured communication
  channel
- validating functional, failure, and Gestalt correctness
- producing Contract Update events after reality contact

Reason: these require context, judgment, and preservation of the user's whole
intent. They are exactly what Hermes should be equipped to do.

### 5.2 WEAVE CLI Owns

The CLI owns only local operating commands:

- `weave start`
- `weave stop`
- `weave status`
- `weave doctor`
- `weave setup`
- `weave app list`
- `weave app create`
- `weave resume <app>`
- `weave channel setup`
- `weave export-handoff`
- `weave open`

Reasons these stay outside Hermes:

1. Process control must work even when Hermes is down.
2. Diagnostics must be available before a model or agent is initialized.
3. Local ports, files, and process IDs are operating-system concerns.
4. The user needs a predictable entrypoint that does not depend on a chat
   session already working.
5. The CLI must support non-interactive checks for CI and local repair.

The CLI must not:

- decide lifecycle stage
- rewrite Hermes' contract
- silently advance the workflow
- perform approval-gated external work
- summarize away blockers as if they were resolved
- become the approval-routing agent

### 5.3 WEAVE Local Wrapper Owns

The local wrapper is the runtime shell launched by the CLI. It owns:

- local API process
- Hermes adapter process
- ledger writer
- deterministic stage projector
- app workspace path resolution
- git/worktree status checks
- schema validation
- local health checks
- REST API server
- process restart and shutdown

Reasons these stay outside Hermes:

1. They need deterministic behavior.
2. They must survive model restarts and communication-channel failures.
3. They are mechanical infrastructure, not product reasoning.
4. They provide a stable substrate for status and audit.

### 5.4 Telegram Slash Commands Own

Slash commands own projection, not interpretation.

They show:

- all known apps and current stage per app
- active app
- Hermes connection status
- current Hermes-registered stage
- stage rationale
- Gestalt Kernel
- contract readiness
- premortem blockers
- handoff readiness
- missing ingredients
- active assumptions
- evidence binder
- approval queue
- next action
- Gestaltian Contract version and diff
- latest changed artifact per app
- latest app context diff
- owner-visible status change history

Slash commands must not invent state. If state is missing, they show absence
clearly. They are not a model chat surface for Hermes communication.
Hermes may propose command-output changes only through the app's normal
contract, worktree, review, validation, and ledger flow.

## 6. Lifecycle Registration Model

Hermes registers lifecycle state by emitting structured events.

Example event:

```json
{
  "schema": "weave-event/v0.1",
  "type": "lifecycle.stage_registered",
  "app_id": "local-repair-tracker",
  "created_by": "hermes",
  "stage": "contract",
  "previous_stage": "kernel",
  "reason": "The Gestalt Kernel is complete and structural contract fields are being compiled.",
  "confidence": "high",
  "blocking_gaps": [],
  "non_blocking_gaps": [
    "Deployment target is not selected yet."
  ],
  "evidence_refs": [
    "contracts/local-repair-tracker/gestalt-kernel.md"
  ]
}
```

The wrapper validates the event shape and appends it to the ledger. It does not
reinterpret Hermes' semantic judgment. If the event is malformed, it records an
ingestion failure and gives Hermes structured feedback to repair the event.

The runtime may also project a lifecycle stage deterministically when artifact
criteria prove it. For example, if the required QA artifact exists at the
declared path, validates against schema, and has a matching `artifact.created`
event, the runtime may show the app as being in QA even before Hermes emits a
fresh summary. Deterministic projection must be labeled as derived state and
must name the artifact rules that caused it.

This preserves the authority split:

```text
Hermes decides, registers, and routes approvals.
WEAVE persists, verifies procedure, and mirrors or deterministically projects.
Telegram status commands explain and reduce clutter.
Human approves high-risk actions.
```

## 7. Hermes Environment Root

Hermes needs a disciplined folder organization in the environment where it is
hosted. The root path should be configured in the runtime profile and treated as
the top-level workspace for all Hermes-led WEAVE work.

Generic structure:

```text
<weave-root>/
  .git/
  artifacts/
    general/
  apps/
    <app_id>/
      app.weave.json
      .git/ or git-reference.json
      repos/
        primary/
        worktrees/
        prs/
      inventory/
      context/
        app-context.md
        user-context-for-this-app.md
        domain-context.md
        reality-briefs/
        decisions.md
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
      exports/
  runtime/
    profiles/
    logs/
    sockets/
```

Rules:

1. General artifacts go under `artifacts/general/`.
2. Each app gets exactly one app folder under `apps/<app_id>/`.
3. The WEAVE root must be git tracked.
4. Each app workspace must be git tracked, even if it is never published to a
   remote host.
5. App repos live under the app folder's `repos/` directory or are referenced in
   the app inventory when they must remain elsewhere.
6. App worktrees and pull-request-like review branches live under `repos/`.
7. App inventories record repositories, external systems, artifacts, state
   files, owner-approved capabilities, and known blockers.
8. App context records the app-specific world state that every lifecycle stage
   needs before reasoning.
9. Hermes should avoid writing outside `<weave-root>` unless the action is
   explicitly authorized and recorded.
10. Telegram commands and API read from this structure; they do not require the
   user to remember where artifacts live.
11. Lifecycle-stage artifacts live under the first lifecycle stage that owns
    the full artifact.
12. If a later lifecycle stage reuses the same artifact, that later stage stores
    a reference JSON in `refs/`, not a duplicate copy.

Reference JSON shape:

```json
{
  "schema": "weave-artifact-ref/v0.1",
  "artifact_id": "contract-v3",
  "canonical_path": "../../03-contract/artifacts/gestaltian-contract.md",
  "source_stage": "contract",
  "used_by_stage": "qa",
  "reason": "QA validates implementation against the current contract.",
  "checksum": "sha256:<digest>"
}
```

This folder model is a UX feature as much as an implementation detail. It
reduces search cost, prevents hidden state, and gives future agents a stable
map of the workspace.

## 8. State And Event Ledger

### 8.1 Ownership

Semantic owner: Hermes.

Technical owner: WEAVE local wrapper.

Storage owner: the local app workspace created by WEAVE.

This is not a contradiction. Hermes owns the meaning of lifecycle state. WEAVE
owns durable local storage because persistence, crash recovery, status
projection, and append-only audit cannot depend on a live agent process.

### 8.2 Location

Default local workspace:

```text
<weave-root>/apps/<app_id>/
  app.weave.json
  context/
    app-context.md
    user-context-for-this-app.md
    domain-context.md
    reality-briefs/
    decisions.md
  contract/
    gestaltian-contract.md
    versions/
    diffs/
  lifecycle/
    <stage>/
      artifacts/
      refs/
  evidence/
  approvals/
  ledger/
    events.jsonl
  exports/
```

For public repo use, generated runtime state remains ignored unless explicitly
exported as a public-safe artifact.

### 8.3 What The Ledger Does

The ledger is not a planner. It is the append-only record that lets Hermes,
WEAVE, and the user share a durable view of what happened.

It does five concrete jobs:

1. Recovery: rebuild current app state after a process or channel restart.
2. Projection: give slash commands a fast local source for current stage,
   blockers, assumptions, evidence, approvals, and next action.
3. Audit: preserve who or what registered an event, when it happened, what it
   referenced, and what changed.
4. Verification: let WEAVE check that Hermes followed required procedure before
   gated actions proceed.
5. Export: compile public-safe or handoff-ready packets without scraping chat
   history.
6. Contract history: record which Gestaltian Contract version changed, what git
   commit contains it, and where the diff can be viewed.

The ledger records approval requests and approvals, but it does not route
approval requests. Hermes routes approval requests through the configured
communication channel. WEAVE records them, displays them, verifies procedure,
and can block or return feedback when required fields or approvals are missing.

### 8.4 Versioned Gestaltian Contract

Each app has its own versioned Gestaltian Contract:

```text
<weave-root>/apps/<app_id>/contract/gestaltian-contract.md
```

Rules:

1. Hermes owns the semantic contract update.
2. The contract file is tracked in git.
3. Each accepted contract update creates or references a git commit.
4. The ledger records the previous version, new version, commit id, authoring
   agent, owner feedback that caused the change, and diff path.
5. Status commands and REST output show the current contract version and let
   the user inspect the diff caused by their feedback.
6. Contract diffs are not hidden in chat history; they are first-class review
   artifacts.

Example event:

```json
{
  "schema": "weave-event/v0.1",
  "type": "contract.updated",
  "app_id": "local-repair-tracker",
  "contract_path": "contract/gestaltian-contract.md",
  "previous_version": "0.2",
  "new_version": "0.3",
  "git_commit": "<local-commit-id>",
  "diff_path": "contract/diffs/0.2-to-0.3.patch",
  "reason": "Owner clarified that slash commands are status, not the communication channel."
}
```

### 8.5 Why WEAVE Owns Ledger Mechanics

The ledger cannot be owned only by Hermes because:

1. Slash commands need local low-latency state even between Hermes messages.
2. The user needs recovery after process or channel failure.
3. Append-only audit should not depend on model memory.
4. External approval gates need deterministic records.
5. Public-safe export requires a mechanical redaction and validation boundary.
6. Multiple communication channels may exist, but the app needs one durable
   local record.

The ledger should be boring infrastructure: append events, validate schemas,
index current state, expose read APIs, and never reinterpret Hermes' meaning.

### 8.6 Event Types

Minimum event families:

- `app.created`
- `hermes.initialized`
- `communication.channel_configured`
- `lifecycle.stage_registered`
- `artifact.created`
- `artifact.updated`
- `gap.classified`
- `assumption.recorded`
- `evidence.added`
- `approval.requested`
- `approval.resolved`
- `execution.handoff_compiled`
- `execution.started`
- `execution.completed`
- `validation.completed`
- `contract.updated`
- `contract.diff_recorded`
- `artifact.reference_recorded`
- `ingestion.failed`
- `procedure.violation`
- `procedure.feedback_sent`

## 9. WEAVE Runtime REST API

The WEAVE runtime should expose its abilities through a REST API so local or
remote clients can inspect and control the runtime without using the CLI as the
only entrypoint.

The CLI should be one client of this API, not the only controller.

Minimum API surface:

```text
GET  /health
GET  /runtime/status
POST /runtime/stop
POST /runtime/restart-hermes
GET  /apps
GET  /apps/{app_id}/state
GET  /apps/{app_id}/events
GET  /apps/{app_id}/artifacts
POST /apps/{app_id}/events
POST /apps/{app_id}/procedure-feedback
GET  /telegram/commands
```

API responsibilities:

- expose runtime and Hermes health
- expose app state derived from the ledger
- accept structured Hermes events
- stop or restart local runtime components
- return procedure feedback when Hermes omits required fields or gates
- expose the deterministic Telegram command catalog

API boundaries:

- The API does not decide lifecycle meaning.
- The API does not route approval requests to the user.
- The API does not perform production-impacting actions without recorded
  approval.
- Remote access requires an explicit transport and authentication policy.
- Public docs must not include private hostnames, private IPs, credential
  paths, or access procedures.

Example remote-control UX:

```bash
curl -X POST <runtime-api>/runtime/stop
```

This allows stopping Hermes or another runtime component without opening a new
CLI session, while preserving the same audit and permission boundaries.

## 10. Communication Channel

The user should be able to talk to Hermes after setting up a communication
channel. WEAVE should support this without forcing communication through a
separate dashboard.

The first supported channel is Telegram.

Future channels may include a local terminal/TUI session, a configured Hermes
endpoint, or another owner-approved channel. Status commands are not a
communication channel.

WEAVE's role:

- verify that a channel exists
- show channel health
- link the current app workspace to the channel
- ingest Hermes lifecycle and artifact events
- provide a fallback "channel not configured" state

WEAVE should not become the chat product. Slash commands may show
communication-channel health and event-derived summaries, but the user talks to
Hermes in the configured channel.

## 11. UX Contract

The Telegram status surface should reduce cognitive load by following these
rules.

### 11.1 Progressive Disclosure

Show one primary focus at a time:

1. Current stage
2. Why this stage
3. Missing ingredients
4. Next action

Details such as raw logs, full event history, and artifact diffs stay behind
explicit commands or links.

### 11.2 Recognition Over Recall

The user should not need to remember the lifecycle. `/apps` and `/app
<app_id>` should show the active stage for each app, blocked stages, and the
next action.

### 11.3 Chunking

Information should be grouped into stable regions:

- App and runtime status
- Lifecycle stage
- Changes per app
- Current packet
- Missing ingredients
- Evidence
- Approval queue
- Next action

Avoid mixing logs, files, lifecycle state, and approvals in one undifferentiated
stream. Do not turn slash-command output into chat.

### 11.4 Cognitive Offloading

The system should hold:

- open questions
- assumptions
- blockers
- owner approvals
- evidence refs
- next actions

The user should not have to reconstruct these from chat history.

### 11.5 Signal Over Volume

Default view should prioritize:

- stage
- app list with stage per app
- latest changes per app
- blocker
- next required user decision
- current artifact readiness
- runtime health

Raw logs, full transcripts, and detailed evidence should be secondary.

### 11.6 Error Legibility

Failures should say:

- what failed
- what still works
- whether Hermes or WEAVE owns the fix
- what the user can do next

Bad example:

```text
Runtime error.
```

Good example:

```text
Hermes channel is not configured. The runtime ledger is available, but Telegram
commands cannot be delivered until the channel is configured.
```

### 11.7 Calm Defaults

Telegram status output should avoid decorative density. It should use clear
status language, short labels, stable sections, and explicit empty states.

The user should feel oriented, not impressed.

## 12. Component Contracts

### CLI

Purpose: predictable local entrypoint.

Inputs:

- command
- app id or workspace path
- runtime profile

Outputs:

- process status
- command availability
- diagnostics
- non-zero exit code on failure

Acceptance test:

```text
Given no active WEAVE process, when the user runs weave start, then the wrapper
starts the runtime and reports Telegram command availability or a precise
blocker.
```

### Local Wrapper

Purpose: deterministic local process and state shell.

Inputs:

- CLI request
- runtime profile
- app workspace
- Hermes events

Outputs:

- running API and command handler
- appended ledger events
- deterministic state projection
- procedure feedback for Hermes
- health snapshot

Acceptance test:

```text
Given a valid Hermes lifecycle event, when the wrapper receives it, then it
validates the schema, appends it to events.jsonl, and exposes it to slash
commands.
```

### Hermes Adapter

Purpose: connect WEAVE to real Hermes runtime semantics.

The adapter is not a second agent. It is the translation and transport boundary
between WEAVE's deterministic runtime and Hermes' actual communication/runtime
surface.

It does these concrete jobs:

1. Check that Hermes is reachable through the configured Telegram channel or
   runtime surface.
2. Provide Hermes with the active app inventory, current contract version,
   relevant lifecycle artifacts, allowed capabilities, and required output
   schemas.
3. Receive or poll Hermes-produced structured events and artifacts.
4. Normalize Hermes outputs into WEAVE event schemas.
5. Post validated events to the WEAVE runtime API.
6. Return structured procedure feedback when Hermes omits required fields,
   approval gates, artifact refs, or contract traceability.
7. Refuse to translate approval-gated actions into execution unless the ledger
   contains the required approval record.

It does not decide lifecycle meaning, route approvals, write app code by
itself, or reinterpret the Gestaltian Contract.

Inputs:

- Hermes communication channel
- WEAVE package
- Gestalt Runtime Pack
- custom skills
- app state
- capability registry

Outputs:

- structured lifecycle events
- artifacts
- gap classifications
- approval requests
- handoff packets

Acceptance test:

```text
Given a raw app intent and configured Hermes runtime, when Hermes processes the
intent, then it emits a Gestalt Kernel artifact and a lifecycle stage event.
```

### Ledger

Purpose: append-only durable local memory for the app workspace.

Inputs:

- validated events
- artifact refs
- approval records
- procedure feedback records

Outputs:

- current state projection
- event history
- exportable public-safe packet
- deterministic artifact-readiness facts

Acceptance test:

```text
Given a process restart, when WEAVE resumes the app, then slash commands
reconstruct the current stage and packet readiness from the ledger.
```

### Telegram Status Commands

Purpose: low-clutter projection of Hermes-led work through deterministic
Telegram output.

Inputs:

- current state projection
- event history summary
- artifact refs
- approval queue

Outputs:

- legible stage view
- missing ingredients view
- evidence binder
- approval records and statuses
- next action
- latest changes per app
- owner-visible status change

Acceptance test:

```text
Given an app blocked on one missing field, when the owner sends `/blockers`,
then the missing field and next user action are visible without opening logs.
```

Command-output edit acceptance test:

```text
Given the user reports confusing command output through Telegram, when Hermes
creates a Build-Ready Handoff Packet for the command fix, then the fix happens
in a tracked worktree and the ledger records the changed runtime artifact and
validation result.
```

### REST API

Purpose: remote and local control plane for the WEAVE runtime.

Inputs:

- authenticated API request
- app id
- runtime component target
- structured event payload

Outputs:

- runtime health
- app state
- event history
- procedure feedback
- stop/restart result

Acceptance test:

```text
Given the WEAVE runtime is already running, when a client calls POST
/runtime/stop with valid authorization, then the runtime stops the targeted
component and records the action in the ledger.
```

## 13. Deterministic Lifecycle Projection

Hermes owns lifecycle meaning, but the WEAVE runtime may display a stage when
that stage is mechanically proven by artifacts and ledger events.

Examples:

- Kernel stage is complete when
  `lifecycle/02-kernel/artifacts/kernel.md` exists, validates against the
  kernel schema, and has a matching `artifact.created` event.
- Contract stage is complete when
  `lifecycle/03-contract/artifacts/gestaltian-contract.md` exists, includes
  the required sections, and has a matching Hermes-authored event.
- QA stage is active when a Build-Ready Handoff Packet exists, implementation
  artifacts exist, and validation artifacts are being written under
  `lifecycle/07-qa/artifacts/`.

Rules:

1. Deterministic projection must be labeled as derived state.
2. Status output must show the artifact rules that caused the derived stage.
3. Hermes can correct or refine the semantic stage with a valid stage event.
4. WEAVE can block a gated action when deterministic checks prove required
   procedure was not followed.
5. WEAVE feedback should be structured so Hermes can repair the event or
   missing artifact.

This gives the user reliable visible state without making WEAVE a competing
reasoning agent.

## 14. First Vertical Slice

Build:

```text
setup + CLI launch + runtime API + Telegram command status + app workspace ledger + Hermes event ingestion contract
```

Included:

- `weave setup`
- `weave start`
- local wrapper
- REST API server
- deterministic Telegram command route
- Telegram channel configuration
- git-tracked WEAVE root
- app registry with multiple app support
- `<weave-root>/apps/<app_id>/ledger/events.jsonl`
- Hermes root folder organization
- Hermes initialization event schema
- lifecycle stage registration event schema
- deterministic stage projection for at least one artifact rule
- one sample raw intent reaching Gestalt Kernel
- `/apps` app list with stage per app
- `/app <app_id>` current-stage and missing-ingredients projection
- versioned Gestaltian Contract and diff recording for one update

Excluded:

- production deploy
- paid jobs
- external sends
- provider mutation
- credential loading
- full implementation executor
- real app deployment
- multi-user sync
- web UI or message composer

Success proof:

1. User runs `weave setup`.
2. Setup creates or verifies a git-tracked WEAVE root and Telegram channel
   configuration.
3. User starts WEAVE from CLI or calls the runtime API directly.
4. Runtime API is available.
5. `/apps` shows all known apps with stage per app.
6. User sends or has sent a raw intent to Hermes through Telegram.
7. Hermes emits a stage event and Kernel artifact.
8. Ledger persists both.
9. Slash commands mirror both without inventing semantic state.
10. Runtime can derive at least one stage from artifact criteria and label it as
   derived state.
11. A Gestaltian Contract update is git tracked and its diff is visible from
    deterministic status or REST output.
12. API can report status or stop the runtime without opening the CLI.
13. Restart reconstructs the same state.

## 15. Decisions And Open Questions

Decisions from owner feedback:

1. First Hermes communication channel: Telegram.
2. Slash-command communication: deterministic status only, not chat.
3. Multi-app support: required in slice one.
4. Export format priority: markdown first.
5. Storage model: always git tracked, even when not published to a remote host.
6. Work review model: worktrees and pull-request-like review records are part
   of the app workspace.
7. REST API security direction: loopback plus generated bearer token by
   default; non-local access requires explicit owner-approved transport and
   auth policy.

Blocking before implementation:

1. What is the minimum real Hermes invocation/API surface available to the
   adapter?
2. What exact Telegram integration path will Hermes expose for structured
   event output?
3. Should the first implementation create one top-level WEAVE root repo that
   contains all app metadata, or one root repo plus separate app repos linked
   by inventory?

Non-blocking for this contract:

1. Event-derived transcript summaries are probably useful if they remain
   secondary to stage, blockers, artifacts, and next action.
2. Public-safe exports can add JSON later, but markdown is the first readable
   format.

Assumptions for now:

1. Hermes can emit or be wrapped to emit structured JSON events.
2. WEAVE local state is private by default and exported intentionally. This
   means it is git tracked locally but not automatically published or copied to
   public artifacts, because app contracts, approvals, evidence, and repo
   inventories may contain unpublished operating details.
3. The first status surface is Telegram slash commands.
4. The first slice prioritizes clarity and durability over automation breadth.

## 16. Premortem

Likely failure: WEAVE duplicates Hermes and becomes a second planner.

Mitigation: CLI and wrapper contracts forbid semantic lifecycle decisions.

Likely failure: slash commands become noisy log dumps.

Mitigation: default commands show stage, why, missing ingredients, and next
action; logs stay behind explicit inspection commands.

Likely failure: ledger ownership confuses semantic authority.

Mitigation: document the split: Hermes owns meaning, WEAVE owns persistence.

Likely failure: the system claims runtime readiness before Hermes is real.

Mitigation: keep runtime proof as a blocking audit requirement.

Likely failure: implementation starts before a Build-Ready Handoff Packet.

Mitigation: commands and adapter must show handoff readiness as locked until
Hermes emits the packet.

Likely failure: slash commands become a second communication channel and create
split attention.

Mitigation: slash commands remain deterministic status; conversation stays in
the configured Hermes channel.

Likely failure: folder sprawl makes future agents lose app context.

Mitigation: Hermes environment root and per-app folder rules are part of
runtime readiness.

Likely failure: remote API becomes an unsafe control surface.

Mitigation: first REST API requires explicit auth and transport policy before
non-local use.

## 17. Contract Update Rule

After the first implementation slice, update this contract with:

- actual Hermes channel used
- actual event schema changes
- actual ledger path
- UX findings from using Telegram slash commands
- validation results
- remaining blockers
- next slice recommendation

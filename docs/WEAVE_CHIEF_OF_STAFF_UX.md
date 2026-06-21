# WEAVE Chief of Staff UX

Status: implementation planning contract
Date: 2026-06-21

## Simple Model

WEAVE is not a new place to work. WEAVE is an operating layer that augments the
agent environment a user already has: Codex, Hermes, or both.

When WEAVE is active, the user keeps working in the same chat, but the chat now
has a durable desk:

- a pinned Chief of Staff home;
- a list of apps under operation;
- a lifecycle rail for each app;
- a task queue;
- a proof tray;
- a blocker tray;
- update notices from the WEAVE source package;
- safe worker spawning through Codex or Hermes.

The user should always be aware that WEAVE is active. Every meaningful response
from a WEAVE Chief of Staff starts with a compact state line.

```text
WEAVE | Home=Chief of Staff | App=Punch Compute | Stage=Build | State=Blocked | Next=QA proof
```

This line is the smallest visual cockpit. It works in Codex, Hermes, terminals,
and copied transcripts.

## Core Nouns

- **Home:** the local WEAVE workspace and pinned Chief of Staff conversation.
- **App:** a product or operational workstream managed through WEAVE.
- **Task:** a durable unit of work with a stage, state, packet, proof, and
  review record.
- **Stage:** the app's lifecycle position.
- **State:** what can happen now.
- **Packet:** the bounded instruction envelope for a worker or controller.
- **Proof envelope:** structured evidence tied to a claim and acceptance check.
- **Review:** controller judgment that accepts proof, sends work back, or blocks.
- **Snapshot:** generated decision surface from local WEAVE state.
- **Mirror:** optional external representation in Linear, GitHub, or another
  tracker.
- **Update inbox:** public WEAVE updates waiting for review.

Stage and state are deliberately separate:

```text
Stage=Build
State=WORKING
```

```text
Stage=Review
State=READY_FOR_REVIEW
```

```text
Stage=DeployReadiness
State=BLOCKED
```

WEAVE v0.1 is local-first. Local task and proof state is authoritative unless
the user explicitly chooses another source of truth. External systems may be
mirrors, but mirror conflicts become local warnings rather than silent updates.

## Product Promise

Install or port WEAVE once. The user gets a durable Chief of Staff agent that can
run app operations without forcing a new primary UI.

The Chief of Staff:

1. detects whether it is running in Codex, Hermes, or an unsupported agent
   surface;
2. creates or guides creation of a pinned Chief of Staff home;
3. asks a small set of owner and workspace questions;
4. stores public-safe preferences and app state in a standard WEAVE home;
5. creates Linear issues when Linear is available, or local tasks when it is not;
6. tracks every app through lifecycle stages;
7. spawns Codex threads or Hermes agents as workers when useful;
8. records proof, blockers, and review states;
9. checks for WEAVE updates on a cadence;
10. surfaces useful updates when the user returns to the Chief of Staff.

The user can still open other chats. WEAVE makes one chat the stable operational
home.

## Primary User Journey

### 1. Get WEAVE

The user tells an agent to install, create, or activate the WEAVE skill.

WEAVE first determines the environment:

- **Codex:** create or instruct creation of a pinned Chief of Staff thread.
- **Hermes:** create or mark a dedicated Chief of Staff Hermes agent.
- **Other agent:** create local WEAVE state and print exact manual pinning
  instructions.

WEAVE then says:

```text
This is your WEAVE Chief of Staff.
Use this chat for app operations this week. You can keep using other chats, but
this one tracks apps, lifecycle stages, tasks, proof, blockers, workers, and
WEAVE updates.
```

### 2. Answer Once

The Chief of Staff asks a compact first-run questionnaire:

- What should I call you?
- How should I speak to you?
- Do you want direct proof-first updates, detailed reasoning, or a lighter mode?
- What apps or projects should I know about?
- Is Linear connected?
- Is GitHub connected?
- Where should local WEAVE state live?
- Should WEAVE auto-update, notify before update, or stay pinned?
- Which actions always require approval?

The answers are stored in text and JSON files that the user can inspect.

### 3. Start An App

The user says what they want to create or operate.

WEAVE creates an app record and starts the lifecycle:

```text
WEAVE | App=New App | Stage=Intent | State=Needs owner context | Next=answer intent questions
```

The Chief of Staff asks only the questions needed for the current stage. If the
user jumps ahead, WEAVE explains the missing gate:

```text
You are asking for Deployment, but this app has no QA proof yet.
To enter Deployment I need: version, test result, deploy target, capability
boundary, and rollback plan.
```

### 4. Run Work

When work is ready, WEAVE creates a standard worker packet.

Worker packet fields:

- app;
- lifecycle stage;
- goal;
- deliverable;
- allowed surfaces;
- forbidden surfaces;
- acceptance checks;
- proof path;
- stop boundary;
- owner decision boundary.

Codex workers handle code, files, tests, repo changes, and local apps.
Hermes workers handle long-running chat/runtime coordination when connected.
Both report into the same proof and blocker model.

### 5. See Progress

The Chief of Staff keeps the state visible:

- current app;
- lifecycle stage;
- worker lanes;
- blockers;
- proof;
- review queue;
- next action.

For milestones, WEAVE creates a visual state artifact. The first release may use
HTML or an image; it does not require a hosted dashboard.

### 6. Receive Updates

WEAVE checks its source package once per day by default.

When the user returns to the Chief of Staff, it can say:

```text
WEAVE update available: v0.2 adds agent blocker sharing.
Current mode: notify before update.
Recommended action: apply because you manage multiple worker lanes.
```

If auto-update is enabled, safe prompt/schema/doc updates may apply and be
reported. Behavior-changing updates require confirmation.

## UX Principles

- Same environment, augmented.
- One Chief of Staff home.
- App state is always visible.
- Lifecycle stage is always visible.
- Stage and operational state are not overloaded.
- Missing gates are named, not guessed.
- Worker spawning is standard and reviewable.
- Proof is a first-class object.
- A proof path is not proof unless it is tied to a claim and acceptance check.
- Done is impossible without a proof envelope and controller review.
- Updates surface where the user already works.
- The public package never commits secrets or private topology.

## Failure UX

Good WEAVE UX is mostly failure UX. The system must make these states visible:

- stale packet;
- missing proof;
- mirror conflict;
- blocked at stop boundary;
- update available;
- review overdue;
- worker output rejected;
- local-only mode.

The desk metaphor must map to behavior:

- envelope means task or worker packet;
- clock means stale or aging indicator;
- queue means ordered next actions;
- state label means operational status;
- proof path means reviewable artifact reference;
- inbox means public updates or review requests;
- desk snapshot means generated HTML overview.

## Non-Goals For This Release

- No new hosted control plane.
- No required login.
- No required cloud sync.
- No live deployment without separate approval.
- No public posting or external sends.
- No raw secret handling.
- No claim that Hermes is live unless a runtime has been verified.

## Done State For The UX

The UX contract is satisfied when a reviewer can read the docs and understand:

- how WEAVE starts in Codex or Hermes;
- what the Chief of Staff home is;
- what state gets stored;
- how an app moves through lifecycle stages;
- how workers are spawned;
- how proof and blockers are shown;
- how updates are checked and surfaced;
- where the system must stop before live effects.

The v0.1 build target is local tasks, bounded packets, proof envelopes, review
gate, and HTML snapshot. Hosted control planes, bidirectional tracker sync,
autonomous worker spawning, raw-log proof, and auto-publish/deploy are outside
this release.

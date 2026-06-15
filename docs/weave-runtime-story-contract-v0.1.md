# WEAVE Runtime Story Contract v0.1

Date: 2026-05-30
Status: story contract for review
Purpose: describe the WEAVE/Hermes operating system as a readable metaphor
before compiling it into a technical contract.

## 1. The Whole Story

I want an agent to help me create and manage multiple applications properly.

The agent is like a man in a box. I talk to him by sending messages on a
cellphone. He is good at executing, but only when the work is framed correctly.
He needs precise instructions, and he needs the right character. He also has a
limited model of the world. Unless he is given tools, news, app state, project
artifacts, and feedback, he is partly disconnected from reality.

This means the first problem is not "how does he build the app?"

The first problem is "how do we set up the man, the phone, the room, the
folders, the recording machine, and the status window so that the man can do
good work repeatedly?"

The system should help me create many apps over time. Each app should have its
own place, its own documents, its own lifecycle, its own git history, and its
own evidence. The man should be able to work across these apps, but the system
must keep each app legible.

## 2. Characters And Objects

### The Owner

The owner is me. I provide intent, taste, constraints, approval, feedback, and
corrections. I am not expected to remember every detail. The system should hold
important context for me and show it clearly.

### The Man In The Box

The man in the box is Hermes.

Hermes is the primary agent. He talks with me through the configured cellphone
channel. In the first version, the cellphone is Telegram.

Hermes can execute, reason, ask questions, and follow methodology, but he must
be shaped before important work. He needs:

- a character document
- an owner understanding document
- a method for turning intent into artifacts
- an app workspace
- a versioned project contract
- access to relevant evidence
- clear allowed capabilities
- a procedure for approvals

### The Cellphone

The cellphone is the communication channel between me and Hermes.

First channel: Telegram.

Slash commands are not the cellphone conversation. They are a status window
inside Telegram: I talk to Hermes with normal messages, and I inspect WEAVE
state with commands such as `/status`, `/apps`, `/app`, `/blockers`,
`/changes`, and `/next`.

### The Recording Machine

The recording machine is the WEAVE runtime ledger.

It writes down important things Hermes does:

- app created
- owner profile updated
- Hermes character updated
- project contract updated
- lifecycle stage registered
- artifact created
- artifact reused by a later stage
- assumption recorded
- blocker recorded
- approval requested
- approval resolved
- procedure violation detected
- feedback sent to Hermes
- validation completed

The machine is not the agent. It does not think for Hermes. It records,
verifies, reconstructs, and shows.

### The Status Window

The status window is the WEAVE Telegram slash-command surface.

It is quiet deterministic output. It shows:

- all apps
- the lifecycle stage of each app
- the selected app
- what Hermes believes
- what is missing
- what is blocked
- what artifacts exist
- what changed in the contract
- what approvals exist
- what the next action is

It is not model chat. It should reduce cognitive clutter, not become another
place where context is split. If the command output is confusing, Hermes can
propose a tracked runtime change through the same contract, branch/worktree,
review, validation, and ledger process as other app changes.

### The House And Shelves

The house is the WEAVE root.

Everything important should live under a clear root folder that is git tracked.
Even if nothing is published to a remote host, local git history is required.

Inside the house there are shelves:

- general artifacts shelf
- one app room per app
- runtime shelf
- logs shelf
- profiles shelf

Each app room contains:

- app identity
- app inventory
- app context
- repos
- worktrees
- pull-request-like review records
- versioned contract
- lifecycle shelves
- evidence
- approvals
- ledger
- exports

The app context is important because every app has different background, users,
domain assumptions, product taste, constraints, and reality sources. Lifecycle
work should load the app context before it interprets any artifact in that app.

### The Inspector

The inspector is the deterministic part of WEAVE.

It can check whether files exist, whether schemas validate, whether git history
contains a contract update, whether a lifecycle stage has the required
artifacts, and whether an approval-gated action has the needed approval record.

The inspector can say:

"Hermes, this procedure is not complete. You said QA is ready, but the QA
artifact is missing. Repair this."

The inspector cannot say:

"I understand the user's whole vision better than Hermes."

### The Remote Control

The remote control is the WEAVE REST API.

It lets authorized clients inspect or control the runtime without starting a
CLI session. For example, a client can ask whether Hermes is running, list apps,
read app state, or stop a runtime component.

The first safe shape is local-only, loopback-bound, protected by a generated
token. Remote access requires a separate explicit transport and auth decision.

## 3. The Setup Story

Before the man can help me build apps, we set up the room.

I run:

```bash
weave setup
```

The setup process creates or verifies:

1. A git-tracked WEAVE root.
2. The folder structure for general artifacts, apps, runtime files, profiles,
   logs, and exports.
3. Telegram as the first cellphone channel.
4. A local REST API token.
5. Hermes runtime profile.
6. The WEAVE company package.
7. The Gestalt Runtime Pack.
8. The custom skills Hermes needs.
9. The app registry.
10. The rules for where artifacts and repos belong.

After setup, the house exists. Hermes may be active through Telegram even if
WEAVE's deterministic status commands are not being checked.

Setup also creates the unskippable foundation gate. This gate runs before
Hermes performs serious app work. It checks whether Hermes has enough context
to proceed with high confidence.

The gate checks:

- `soul.md`: how Hermes should think and behave
- `owner-profile.md`: who the owner is and how to help them
- app context: what is true and important for this app
- current app contract
- lifecycle state
- available capabilities
- current blockers

If the gate cannot prove that the needed context exists and is good enough,
Hermes must ask the owner through Telegram before continuing. This should happen
proactively at the beginning of the Hermes work session, not only after the
owner asks for a task.

Then I run:

```bash
weave start
```

This does not create only one app. It starts the runtime status layer. It
indexes all known app rooms. `/apps` shows every app and what stage each one is
in. If Hermes worked while WEAVE was not running, WEAVE should sync or import
the structured artifacts and events Hermes produced.

## 4. The First Conversation: Shaping Hermes

Before Hermes helps me with real work, he should stop me.

He says:

```text
Let me stop you there. To help you best in your tasks, we need to have a
discussion about how my thinking and character should be. Once we have this
discussion, I will infer how I need to be to help you best and create a
soul.md document that codifies it.
```

Then we discuss:

- how he should think
- how direct he should be
- what standards he should hold
- how he should handle uncertainty
- when he should challenge me
- when he should ask questions
- when he should proceed with assumptions
- what failure modes he is prone to
- how he should correct himself

At the end, Hermes writes:

```text
<weave-root>/artifacts/general/soul.md
```

This is the character document. It is versioned. When I give feedback that
changes the character Hermes should have, the file changes and the diff is
recorded.

Failure if skipped: Hermes remains too plastic. He may become whatever the last
prompt accidentally shaped him to be.

## 5. The Second Conversation: Understanding The Owner

Then Hermes stops me again.

He says:

```text
I still do not know enough about you. To help you well, I need to understand
your style, constraints, goals, decision patterns, and what kind of help is
actually useful to you. I will ask questions, you will answer, and then I will
create a document I can consult before important work.
```

Then we discuss:

- what I am trying to build over time
- how I think
- what kind of explanations help me
- what kind of answers frustrate me
- how much detail I want
- what I consider good judgment
- what I consider overclaiming
- how I prefer approvals and decisions
- what risks I care about
- what should never be hidden from me

At the end, Hermes writes:

```text
<weave-root>/artifacts/general/owner-profile.md
```

This is not a personality quiz. It is operating context. It helps Hermes serve
me better without making me repeat myself.

Failure if skipped: Hermes may technically follow a task but miss my taste,
style, risk tolerance, or desired level of rigor.

## 6. The Third Conversation: Creating An App Room

Now I can tell Hermes about an app I want to build.

Hermes says:

```text
Now it is a good time. I will ask questions about your project so I can infer
and write the first project contract. This contract will preserve what the app
is supposed to become before we break it into tasks.
```

Then Hermes asks only useful questions. He does not ask a giant questionnaire.
He tries to understand the whole.

The first app setup creates:

```text
<weave-root>/apps/<app_id>/
```

Inside that room:

```text
app.weave.json
context/
  app-context.md
  user-context-for-this-app.md
  domain-context.md
  reality-briefs/
  decisions.md
inventory/
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
  02-kernel/
  03-contract/
  04-premortem/
  05-handoff/
  06-implementation/
  07-qa/
  08-kpi-setup/
  09-marketing/
  10-iteration/
  11-analysis/
ledger/
  events.jsonl
```

Every app is git tracked. If the app has code, that code lives in a repo or
worktree. Work should move through branches and pull-request-like review
records, even if the repo is private and never published.

The app context is loaded throughout the lifecycle. Intent, Kernel, Contract,
Premortem, Handoff, Implementation, QA, Deployment, KPI Setup, Marketing,
Iteration, and Analysis all use it. When the context changes, Hermes records
what changed and why.

Failure if skipped: apps become anonymous folders, context scatters, and future
agents cannot recover what happened.

## 7. The Method Hermes Must Follow

Hermes uses the `gestalt-to-artifact` method.

The story version:

```text
whole vision
  -> essence of the app
  -> contract for the app
  -> premortem
  -> build-ready packet
  -> implementation
  -> validation
  -> contract update
```

The purpose is not to make paperwork. The purpose is to prevent the man in the
box from rushing into tasks before he understands the app as a whole.

## 8. The Lifecycle Story

### Intent

Hermes listens to what I want.

He asks enough questions to understand the app's purpose, user, constraints,
and desired transformation.

The recording machine writes:

- intent artifact created
- assumptions
- open questions
- owner corrections

### Kernel

Hermes writes the compact essence of the app.

This is the app's Gestalt Kernel. It answers:

- what transformation should exist
- what the finished state feels like
- what must always remain true
- what done means
- what wrong means
- what the smallest living version is

The status window can show the kernel path and whether review is needed.

### Contract

Hermes turns the kernel into the app's Gestaltian Contract.

This contract is versioned and git tracked:

```text
<weave-root>/apps/<app_id>/contract/gestaltian-contract.md
```

When I give feedback, Hermes updates the contract. The recording machine writes
the event. Git records the diff. `/changes` shows me what changed.

This matters because I want to see how my feedback changes the app's contract.

### Premortem

Hermes attacks the contract before building.

He asks:

- how could this pass tests but feel wrong?
- where could I misunderstand the owner?
- what approvals are missing?
- what data is missing?
- what could break in the real world?
- what would make this unsafe, noisy, or incoherent?

`/blockers` shows blockers and safe assumptions.

### Handoff

Hermes compiles a Build-Ready Handoff Packet.

This packet says what can be built now, why it supports the whole, what not to
build, what tests are required, and what approvals are needed.

No serious implementation starts before this packet exists.

### Implementation

Hermes executes or directs execution through the approved tools and repos.

Work happens in branches and worktrees. Review records are kept. The recording
machine writes what happened.

If Hermes tries to skip the packet, the inspector blocks or sends feedback.

### QA

Hermes validates through three lenses:

1. Functional: does it work?
2. Failure: does it behave correctly when things are missing, ambiguous, or
   broken?
3. Gestalt: does it still embody the original whole?

The QA lifecycle shelf owns the QA artifacts. If QA uses the contract artifact,
it stores a reference JSON pointing to the contract rather than duplicating it.

### Deployment

Hermes prepares staging or production deployment only after QA has reviewable
proof. Provider credentials, DNS changes, public writes, and production
mutations stay behind capability and owner-approval gates.

If deployment is unavailable, the lifecycle records a blocked deployment plan
instead of pretending KPI or marketing can observe production reality.

### KPI Setup

Hermes identifies what signals should prove the app is working after deployment
or use.

This does not mean public reporting or production tracking is automatically
enabled. It means the app has a measurement plan.

### Marketing

Hermes can prepare distribution artifacts, but external sends, ads, publishing,
payments, provider mutation, DNS changes, and production deploys stay
approval-gated.

Hermes routes approval requests through Telegram. WEAVE records the request and
approval state.

### Iteration And Analysis

After evidence arrives, Hermes analyzes it, proposes contract updates, and
plans the next iteration.

The contract changes when reality teaches us something. `/changes` shows the
diff reference.

## 9. Artifact Rules

Every important artifact belongs to a lifecycle shelf.

If an artifact first belongs to Contract, it lives under:

```text
lifecycle/03-contract/artifacts/
```

If QA later needs that artifact, QA does not copy it. QA stores a reference:

```text
lifecycle/07-qa/refs/<artifact-id>.json
```

The reference says:

- artifact id
- canonical path
- source lifecycle stage
- using lifecycle stage
- why it is reused
- checksum

This prevents artifact duplication and lets the system know which lifecycle
stage created the artifact and which later stages depend on it.

## 10. What The Status Window Must Show

Telegram slash commands should answer quickly:

- what apps exist
- what stage each app is in
- what app is selected
- what Hermes is currently doing
- what Hermes needs from me
- what is blocked
- what assumptions are active
- what approvals exist
- what evidence exists
- what contract version is active
- what changed in the latest contract diff
- what lifecycle artifacts exist
- what action is next

It should not show everything at once.

The default command set should be calm:

1. `/apps`: app list with stage per app
2. `/app <app_id>`: selected app summary
3. `/app <app_id>`: current lifecycle shelf
4. `/blockers` and `/next`: current blocker or next action
5. `/changes [app_id]`: contract diff/status and recent changes
6. `/status`: runtime health and aggregate state

Logs, raw events, transcript summaries, and file details are secondary.

The status window should also show what changed in each app:

- latest contract diff
- latest app context diff
- latest artifact added or changed
- latest lifecycle stage change
- latest approval change
- latest owner-visible status change

## 11. What The REST API Does In The Story

The REST API is the remote control for the machine.

It lets authorized clients:

- check health
- list apps
- read app state
- read events
- read artifact lists
- stop the runtime
- restart Hermes
- post structured events
- send procedure feedback

It does not become a second Hermes. It does not route approvals. It does not
decide the meaning of the app.

First security shape:

- local loopback by default
- generated bearer token
- token not stored in public artifacts
- remote access only after explicit transport and auth approval

## 12. Failure Modes The Story Reveals

### Failure: Hermes has no stable character

Symptom: Hermes changes style and standards based on the latest prompt.

Prevention: `soul.md` exists, is versioned, and is loaded before important
work.

### Failure: Hermes does not know the owner

Symptom: Hermes technically executes but misses taste, desired rigor, or
decision style.

Prevention: `owner-profile.md` exists, is versioned, and is loaded before
important work.

### Failure: Hermes starts building too early

Symptom: code appears before the app contract and handoff packet exist.

Prevention: inspector blocks implementation unless the required lifecycle
artifacts exist.

### Failure: slash commands become a second phone

Symptom: the owner starts using slash commands for conversation, or Hermes
answers deterministic commands with model-generated text.

Prevention: normal messages go to Hermes; WEAVE slash commands return
deterministic runtime state with `llm_used: false`.

### Failure: Hermes cannot improve the status output

Symptom: the user dislikes command output, but Hermes cannot repair the
operator status surface.

Prevention: command output is treated as an editable runtime artifact. Hermes
can change it through the same contract, branch/worktree, review, validation,
and ledger flow used for other artifacts.

### Failure: Hermes starts without foundation context

Symptom: Hermes accepts a task before it knows how it should behave, who the
owner is, or what app context matters.

Prevention: the foundation gate is unskippable. If `soul.md`,
`owner-profile.md`, app context, contract, lifecycle state, or capability
context is missing or low-confidence, Hermes must ask through Telegram and
update the relevant document before continuing.

### Failure: apps become mixed together

Symptom: artifacts, repos, and evidence from different apps are hard to
separate.

Prevention: one app room per app, app registry, app list with stage per app.

### Failure: contract changes are invisible

Symptom: I give feedback, Hermes changes direction, but I cannot see exactly
what changed.

Prevention: git-tracked Gestaltian Contract, contract diffs, ledger
`contract.updated` events, and command-visible diff references.

### Failure: artifacts duplicate across lifecycle stages

Symptom: QA, Handoff, and Contract shelves contain different copies of the same
artifact.

Prevention: first lifecycle shelf owns the artifact; later shelves store
reference JSON.

### Failure: Hermes routes approvals but WEAVE cannot verify them

Symptom: approval-gated action proceeds without a durable approval record.

Prevention: Hermes routes approval through Telegram; WEAVE records approval
events and blocks gated procedure when records are missing.

### Failure: Hermes works while WEAVE is not running and state is lost

Symptom: Telegram conversation contains work that WEAVE status commands cannot
show.

Prevention: Hermes writes structured events/artifacts into the git-tracked app
workspace, and `weave start` syncs/imports offline work.

### Failure: the REST API becomes unsafe

Symptom: remote control exists before auth and transport are clear.

Prevention: loopback-only first; bearer token; explicit transport/auth packet
before remote exposure.

### Failure: the man in the box lacks reality

Symptom: Hermes makes confident claims based on stale or missing context.

Prevention: Hermes must label uncertainty, request evidence, use approved
research tools when needed, and record evidence refs in the ledger.

## 13. Story-To-Technical Mapping

| Story object | Technical primitive |
|---|---|
| Owner | Human operator |
| Man in the box | Hermes agent |
| Cellphone | Telegram communication channel |
| House | Git-tracked WEAVE root |
| App room | Git-tracked app workspace |
| Shelves | Folder structure and lifecycle stage directories |
| Recording machine | WEAVE ledger and runtime event store |
| Status window | WEAVE Telegram slash commands, not model chat |
| Status repair | Command-output change through app workflow |
| Inspector | Deterministic WEAVE runtime verifier |
| Remote control | WEAVE REST API |
| Character paper | `soul.md` |
| Owner paper | `owner-profile.md` |
| App context shelf | `context/` |
| App paper | Gestaltian Contract |
| App paper diff | Git diff plus contract update event |
| Work desk | App repo/worktree |
| Review folder | Pull-request-like review record |
| Permission slip | Approval event |
| Reused document pointer | Artifact reference JSON |

## 14. Story Acceptance Checks

This story contract is acceptable when:

1. The owner can understand the whole system without reading code.
2. The story makes clear that Hermes is the agent and WEAVE is the machine
   around him.
3. The story explains why `soul.md`, `owner-profile.md`, and app contracts
   exist.
4. The story supports multiple apps from the beginning.
5. The story explains setup before start.
6. The story explains what happens if Hermes works while WEAVE is not open.
7. The story includes lifecycle shelves and artifact references.
8. The story includes git-tracked contracts, worktrees, review records, and
   visible contract diffs.
9. The story includes Telegram slash commands, ledger, inspector, REST API,
   Telegram conversation, and approval routing.
10. The story exposes failure modes before implementation.

## 15. Next Step After Review

After this story is reviewed and corrected, compile it into a technical
Gestaltian Contract with:

- exact file schemas
- exact event schemas
- exact setup commands
- exact REST API contract
- exact Telegram slash-command information architecture
- exact Hermes adapter contract
- exact first Build-Ready Handoff Packet

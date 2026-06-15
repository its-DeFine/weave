# WEAVE V1 Product Contract

Status: owner alignment contract before implementation.

This contract defines the completed WEAVE v1 product. It exists to prevent the
same failure mode from happening again: a useful implementation slice, test run,
or merged PR must not be treated as completion of the full owner intent.

## 1. Simple Product Model

WEAVE v1 is a terminal-first product lifecycle cockpit where a human and one or
more agents create, validate, build, QA, and prepare an app for launch.

The user should not feel like they are running scripts. The user should feel
inside a focused chat-like operating surface where WEAVE always makes the next
stage, next question, available choices, artifacts, blockers, and proof visible.

Codex is the first v1 executor. Hermes, Telegram, remote agents, Composio, and
live business operations remain later or gated capabilities unless explicitly
authorized.

## 2. Non-Collapse Rule

The active WEAVE v1 goal is not complete when:

- code exists;
- a PR is merged;
- CI passes;
- local deterministic artifacts are produced;
- Codex can be called once;
- a demo app is generated;
- the TUI displays lifecycle stage names.

Those are milestones. They are not the goal.

The goal is complete only when a fresh operator can open WEAVE, move naturally
from first run through QA in the TUI/chat surface, see agents do real work,
review artifacts and files, give feedback, resume later, and inspect proof that
the app and lifecycle behavior worked.

## 3. V1 Scope

V1 must include:

- a polished interactive TUI as the primary surface;
- chat-like stage prompts and user replies;
- keyboard-native operation with visible choices;
- first-run environment detection;
- owner profile capture;
- app creation or app selection;
- intent capture and sufficiency validation;
- research plan review and research artifact review;
- selection option comparison, edit, and approval;
- business, engineering, QA, KPI, deployment, marketing, and iteration planning;
- Codex-backed engineering execution;
- generated app file and artifact browsing;
- file-specific feedback;
- QA plan authorization;
- surface-aware QA through at least website, CLI/TUI, backend/API, and mixed lanes;
- revision loops when the user is not satisfied or QA fails;
- resumable app/session state;
- an event/artifact ledger and current world model;
- visual proof captures, tests, CI, and dogfood through QA.

V1 may include gated representations of deployment, KPI, marketing, iteration,
and analysis. It must not execute live external effects without separate
authorization.

## 4. Stop Boundaries

WEAVE v1 must stop before:

- credential collection or raw secret handling;
- domain purchase;
- staging or production deployment;
- production analytics writes;
- public posting, messaging, or email sends;
- paid advertising spend;
- destructive infrastructure actions;
- live third-party mutation.

The TUI can ask about preferences and produce plans for these areas. It must
store only public-safe, non-secret planning information.

## 5. Completed User Experience

The completed first screen is the cockpit, not a report.

Persistent regions:

- Header: app, session, current stage, control mode, executor, proof boundary.
- Lifecycle rail: first run, owner profile, app, intent, research, selection,
  plan, engineering, QA, deployment, KPI, marketing, iteration, analysis.
- Chat/work pane: current agent prompt, user reply area, options, stage status.
- Evidence pane: artifacts, files, QA evidence, event ledger, world model.
- Review queue: owner decisions, failed checks, blocked actions, revision asks.
- Command footer: visible keyboard actions and guided next action.

The operator must be able to complete the happy path without memorizing hidden
commands. Power commands can exist, but visible choices are the source of truth.

## 6. Conversation Primitive

Every lifecycle stage must behave like a guided conversation:

1. WEAVE states the stage and why it matters.
2. WEAVE asks the concrete question for this stage.
3. The user can answer naturally, select an option, or ask to inspect evidence.
4. The agent uses the answer and produces or updates artifacts.
5. WEAVE presents the result, proof, and non-claims.
6. The user can approve, revise, attach feedback, or continue.
7. WEAVE records the event and moves only when the stage gate passes.

The current `weave>` command prompt is not enough. The v1 surface must make the
conversation and the lifecycle state the same experience.

## 7. Lifecycle Contract

Each lifecycle stage must define:

- user action;
- visible UI;
- agent action;
- backstage system behavior;
- artifacts written;
- state transition;
- proof shown;
- failure or revision lane;
- hard stop boundary.

### 7.1 First Run And Environment Detection

User journey:

- User starts `bin/weave tui`.
- WEAVE detects local state, available Codex, possible Hermes surfaces, and any
  prior sessions.
- WEAVE asks whether to attach local, create local, connect remote, or continue
  local-only.

Done evidence:

- session state is created;
- detected environment is visible;
- unsupported remote lanes show honest blockers;
- no hidden live effect occurs.

### 7.2 Owner Profile

User journey:

- WEAVE asks the user about engineering/product experience.
- WEAVE asks the user to describe themselves and preferred collaborator style.
- The user saves, edits, or skips.

Done evidence:

- owner profile artifact exists;
- later stage prompts can cite the profile;
- no raw secrets or private topology are stored.

### 7.3 App Creation Or Selection

User journey:

- User creates a new app or selects an existing app.
- WEAVE shows active app, app state, prior artifacts, blockers, and next action.

Done evidence:

- app registry is updated;
- active app state is visible;
- switching apps preserves session context.

### 7.4 Intent

User journey:

- WEAVE presents a structured intent surface.
- User describes app purpose, users, flows, constraints, libraries, deployment
  posture, region, budget, examples, and non-goals.
- Agent validates sufficiency against WEAVE intent axioms.
- User approves, edits, asks what is missing, or adds feedback.

Done evidence:

- intent artifact exists;
- sufficiency result is visible;
- missing information is shown instead of invented;
- approval advances to research only when gate passes.

### 7.5 Research

User journey:

- WEAVE turns the approved intent into a research plan.
- User accepts, edits, adds questions, removes questions, or asks for revision.
- Agent performs authorized research and produces artifacts.
- User reviews research and chooses enough, continue, or correct.

Done evidence:

- research plan artifact exists;
- research synthesis and source log exist when public-web research is authorized;
- missing live research is clearly labeled when not authorized;
- sufficiency gate controls transition to selection.

### 7.6 Selection

User journey:

- WEAVE examines research artifacts and presents options.
- User selects an option, asks for more, discusses/edits an option, or creates a
  new option.
- Agent re-presents the selected direction for approval.

Done evidence:

- option comparison artifact exists;
- selected option is recorded;
- rationale links to research artifacts;
- no transition to plan without selected direction.

### 7.7 Plan

User journey:

- WEAVE converts intent, research, and selection into a full plan.
- The plan includes business, engineering, QA, deployment, KPI, marketing,
  iteration, risk, timeline, repository, provider, and capability tracks.
- User can edit business plan, edit engineering plan, add feedback, remake plan,
  inspect artifacts, or approve.

Done evidence:

- business plan artifact exists;
- engineering plan artifact exists;
- QA plan draft exists;
- KPI, deployment, marketing, and iteration drafts exist;
- credentials are represented as capability requirements, not collected.

### 7.8 Engineering

User journey:

- WEAVE starts the approved engineering plan.
- Codex executes work as the first v1 agent executor.
- TUI shows task progress, changed files, generated artifacts, agent status,
  blockers, and hard decisions.
- User can inspect files, attach feedback, approve for QA, or request changes.

Done evidence:

- executor manifest exists;
- generated app files exist;
- changed/generated files are browsable;
- file-specific feedback is stored and consumed by the next agent run;
- hands-on mode stops for consequential direction changes;
- handoff mode continues until a hard gate or failure.

### 7.9 QA

User journey:

- WEAVE presents a QA plan adapted to the app surface.
- User approves, edits, adds scenarios, or asks for revision.
- Agent runs QA and produces proof.
- User reviews app behavior, QA method, failed checks, videos/screenshots when
  relevant, logs, and source evidence.
- User approves, sends feedback to engineering, or asks QA to rerun.

Done evidence:

- QA plan artifact exists;
- QA result artifact exists;
- QA adapts to website, CLI/TUI, backend/API, and mixed apps;
- failures route to engineering or QA-plan revision honestly;
- at least one dogfood app passes through QA with real Codex execution;
- screenshots or terminal captures prove the visual journey.

### 7.10 Deployment Gate

User journey:

- WEAVE explains deployment needs after QA passes.
- User can record provider/domain preferences or mark credentials unavailable.
- WEAVE blocks live deployment until separately authorized.

Done evidence:

- deployment plan artifact exists;
- credential requirements are stored as capability refs;
- production and staging are not mutated in v1 without separate approval.

### 7.11 KPI Setup

User journey:

- WEAVE proposes 3 to 5 starter KPIs based on current app truth.
- User edits, adds, removes, or marks blocked by deployment.

Done evidence:

- KPI artifact exists;
- local vs production instrumentation boundary is visible;
- production analytics remains gated.

### 7.12 Marketing

User journey:

- WEAVE asks whether there is a marketing budget and which channels are allowed.
- WEAVE creates organic and paid-channel plans.
- Organic drafts and paid plans remain gated before public sends or spend.

Done evidence:

- marketing plan artifact exists;
- budget posture is recorded;
- recurring marketing heartbeat is represented as a gated job;
- no public post, email, or paid spend occurs.

### 7.13 Iteration

User journey:

- WEAVE aggregates feedback, QA findings, analytics placeholders, and owner
  comments into proposed issues.
- User approves or rejects iteration items.
- Approved items route back to engineering and QA.

Done evidence:

- iteration plan artifact exists;
- issue candidates are shown in review queue;
- accepted item can start a staged engineering/QA loop;
- live schedules remain gated.

### 7.14 Analysis

User journey:

- WEAVE summarizes feedback, competitors, sentiment, and improvement candidates.
- User edits cadence/sources or approves analysis plan.

Done evidence:

- analysis plan artifact exists;
- improvement candidates link to evidence;
- external scanning waits for explicit authorization.

## 8. State And Evidence Model

WEAVE v1 must keep these surfaces distinct:

- local app state;
- current session state;
- lifecycle stage state;
- world model;
- event ledger;
- conversation transcript;
- artifacts;
- generated files;
- executor manifests;
- QA proof;
- gated capability requirements.

The UI must show enough of these surfaces that the operator can understand what
is true without reading raw JSON first.

## 9. Visual Product Contract

The TUI must be visually designed, not merely text output.

Required qualities:

- strong color hierarchy;
- focused action card for current question;
- lifecycle rail with state indicators;
- dense but readable panes;
- clear review queue;
- active agent/task status;
- file and artifact browser;
- visible command footer;
- graceful empty states;
- graceful Ctrl-C and interruption handling;
- no traceback as normal user experience;
- no hidden state transitions without visible evidence.

The visual acceptance gate requires screenshots or terminal captures of the
major states. Unit tests alone are not enough.

## 10. Codex Executor Contract

Codex v1 integration must:

- run from the current app and stage context;
- receive the relevant intent, research, selection, and plan artifacts;
- produce or modify files in the app workspace;
- write an executor manifest;
- show running, failed, complete, and blocked states in the TUI;
- preserve output summaries without leaking secrets;
- route failed work to review or engineering revision;
- be dogfooded through QA on a real example app.

Using `codex exec` is acceptable for v1 if it is reliable and visible enough.
Later work can replace it with lower-level programmatic primitives.

## 11. QA Contract

QA must test the product surface being built.

Examples:

- website: source checks, browser/DOM proof, responsive visual proof, SEO tags,
  disabled external effects, user-flow checks;
- CLI/TUI: command behavior, visual readability, resume, interruption, output
  bounds, keyboard flow;
- backend/API: request/response checks, schema checks, error paths, auth boundary
  if relevant and authorized;
- mixed app: all relevant surfaces, not browser-only proof.

QA must also test the WEAVE journey itself, not only the generated app.

## 12. Work Process Contract

Future work must use one large WEAVE v1 goal. PRs are implementation milestones
inside that goal.

Each milestone PR must state:

- which part of this contract it advances;
- which acceptance rows it proves;
- which acceptance rows remain unproven;
- screenshots/captures if the milestone changes UI;
- tests and dogfood evidence;
- non-claims.

The top-level goal can close only when the completion matrix in this contract is
fully proven.

## 13. Completion Matrix

| Area | Required proof before done |
| --- | --- |
| Product contract | This document exists and is kept current |
| Visual TUI | screenshots/captures prove polished cockpit states |
| Natural flow | fresh run moves first-run through QA without hidden commands |
| Stage fidelity | every lifecycle stage has visible ask, choices, artifacts, proof, failure lane |
| Codex work | Codex executes app work from WEAVE context and writes files |
| Artifacts | user can browse artifacts and generated files |
| Feedback | stage and file feedback are recorded and consumed by reruns |
| QA | surface-aware QA passes or fails honestly |
| Resume | app/session can be closed and resumed |
| Stop boundaries | no credentials, deployment, public send, paid spend, or live mutation occurs |
| Docs | operator guide explains how to run, resume, inspect, and test |
| CI | automated tests pass |
| Dogfood | a substantial example app completes through QA with evidence |

## 14. Owner Acceptance

The owner should be able to say yes to all of these:

- I understand what WEAVE is.
- I can use it without guessing hidden commands.
- I can see which lifecycle stage I am in.
- I can see what the agent is asking me.
- I can answer naturally.
- I can inspect artifacts and files.
- I can give stage or file feedback.
- I can watch Codex do work or see its state.
- I can review QA proof.
- I can resume the same app later.
- I can see what is blocked and why.
- I can trust that live risky actions did not happen.

If any answer is no, WEAVE v1 is not done.

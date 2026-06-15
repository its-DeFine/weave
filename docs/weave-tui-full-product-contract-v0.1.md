# WEAVE TUI Full Product Contract

Status: active completion contract for ATM-254.

This document is the completion target for the WEAVE interactive terminal
product surface. It exists to prevent the work from collapsing into a narrow
demo, one-shot script, or deterministic proof runner. A PR may improve one part
of this contract, but the full goal is complete only when every acceptance item
below has current evidence.

## 1. Product Definition

WEAVE TUI is an ongoing operator cockpit for creating and advancing an app
through the WEAVE lifecycle with an agent. It is not a landing page, not a
scripted demo, and not a read-only dashboard.

The first usable screen must put the operator inside the working cockpit. The
operator should be able to see where they are, what app/session is active, what
the last agent/user actions were, what stage is next, what requires review, and
what commands are available without reading a manual.

## 2. Completion Rule

The work is complete only when the current repo proves all of these:

- The TUI is resumable and stateful.
- The TUI has a polished visual hierarchy suitable for sustained operator use.
- The TUI supports interactive navigation, not only scripted output.
- The operator can create or select an app, enter owner profile data, and enter
  a substantial app intent.
- Lifecycle stages expose review, edit, approve, continue, and revision loops.
- Artifacts and generated files can be listed, inspected, and referenced.
- The operator can attach file-specific feedback to the active agent workflow.
- Codex execution is integrated as an ongoing agent action surface, not only a
  single hidden subprocess.
- Generated app source and QA evidence are created and linked into lifecycle
  state.
- QA adapts to the app surface and fails honestly.
- Stop boundaries are enforced before credentials, deployment, public sends,
  paid spend, destructive actions, and live third-party mutations.
- Docs explain how to operate and resume the cockpit.
- Tests and dogfood prove the full flow through QA.

## 3. Non-Goals For This Contract

These are explicitly outside the first full TUI product completion unless
separately authorized:

- Provider credential collection.
- Deployment to production or staging providers.
- Public posting, messaging, or marketing sends.
- Paid advertising spend.
- Live third-party mutation.
- Browser/web app replacement for the terminal cockpit.

The TUI may display these future stages, collect non-secret planning
preferences, and create gated artifacts. It must not execute the live action.

## 4. Core UX Model

The cockpit has four persistent regions:

- Header: active app, active session, lifecycle stage, mode, executor, and stop
  boundary.
- Navigation rail: apps, stages, inbox/review queue, artifacts, files, agent,
  jobs, and proof.
- Work pane: the current stage, question, artifact, file, or agent task.
- Command bar: visible actions with stable keys and short labels.

The command model must support both direct keyboard commands and guided
prompts. The operator should be able to continue work by opening the TUI again
without remembering the last command.

## 4.1 Blueprint Fidelity Rule

The TUI must implement the service blueprint as a user-visible operating flow,
not merely as internal lifecycle state. A completion claim is invalid if the
operator cannot see the stage, understand what is being asked, choose from the
expected options, provide free-form feedback, and return to the same work later.

This product must not become a clone of Codex CLI. Codex CLI is an executor and
conversation primitive. WEAVE TUI is the product-lifecycle cockpit around that
executor. It should expose stage state, artifacts, decisions, review loops, and
proof boundaries in a domain-specific interface.

Every guided stage must answer these questions in the visible UI:

- What is happening now?
- Why is this stage needed?
- What did the agent prepare?
- What are my choices?
- What happens if I choose yes?
- What happens if I choose no or revise?
- Where can I inspect the supporting artifacts/files?
- What stop boundary applies?
- What is the next safe action?

## 4.2 Interaction Primitives

The first full product must support these visible primitives:

- Action card: a focused prompt with a short title, explanation, status, and
  available actions.
- Yes/no confirmation: used for approvals, sufficiency gates, and plan
  acceptance.
- Option picker: used when selecting app, environment, research plan choice,
  selection option, control mode, QA route, or next action.
- Free-form feedback box: used when the operator wants revision or additional
  instruction.
- Artifact/file picker: used to inspect a supporting artifact or generated file.
- File-specific feedback: used to attach feedback to a selected file or
  artifact.
- Stage transition animation or visible transition state: used when moving from
  one lifecycle stage to the next.
- Review queue: shows pending owner decisions, failed checks, revision requests,
  and blocked agent tasks.
- Command bar: shows available keyboard commands and guided actions.

The operator must never need to remember hidden command names to complete the
happy path. Commands may exist for speed, but the visible action model is the
source of truth.

## 4.3 User-Visible Stage Scripts

These scripts are acceptance requirements. The exact words can improve, but the
visible intent and reply options must exist.

### First Run And Environment Detection

The TUI shows:

- "I found these local environments."
- "Would you like to attach to one of these, connect a remote environment, or
  create a new local Hermes/agent environment?"

Required actions:

- Attach existing.
- Create local.
- Connect remote.
- Skip setup and use local WEAVE state only.
- Inspect detected environment.

If no environment exists, the TUI must say so and offer create-local or
connect-remote. Remote support may be marked deferred if not implemented, but it
must be visible as a product lane with a clear blocker.

### Owner Profile

The TUI asks:

- "What is your engineering/product experience?"
- "Tell me about yourself so I can help better."
- "Imagine the best coworker for this project. What style should they have?"

Required actions:

- Save profile.
- Edit answers.
- Skip for now.

The saved profile becomes context for later stage wording and agent prompts.

### Intent

The TUI shows a structured intent form and asks the operator to describe:

- desired app;
- imagined user flows;
- target users;
- preferred libraries or "let agent research";
- local vs hosted/deployed preference;
- deployment region;
- budget or hard constraints;
- known examples or non-goals.

Required actions:

- Submit intent.
- Continue editing.
- Ask agent to validate sufficiency.
- Inspect saved intent artifact.

After the agent validates, the TUI asks:

- "I checked this against the WEAVE intent axioms. Is this intent ready to use?"

Required actions:

- Yes, continue to research.
- No, I want to edit.
- Ask agent what is missing.
- Add feedback.

### Research

The TUI shows:

- "We are ready to start research."
- "I created this research plan. Would you like to change it?"

Required actions:

- Accept research plan.
- Edit plan.
- Add research questions.
- Remove research questions.
- Ask agent to revise plan.
- Start research.

When research completes, the TUI shows artifacts and asks:

- "Do we have enough research, or should we continue/correct it?"

Required actions:

- Enough research, continue.
- Continue research.
- Correct with feedback.
- Inspect artifacts.

### Selection

The TUI shows a transition into selection and then:

- "Based on the research artifacts, I found these options."
- "Which option do you prefer?"

Required actions:

- Select option A/B/C.
- Create my own option.
- Ask agent for more options.
- Discuss/edit selected option.
- Proceed with selected option.

If the operator creates a new option, the TUI asks for the desired shape, sends
that to the agent, and returns with updated options.

### Plan

The TUI says:

- "I have the intent, research, and selected option. I will produce business and
  engineering plans."

The TUI must show at least these tracks:

- business plan;
- engineering plan;
- repository/deployment plan;
- domain/provider needs;
- QA plan;
- KPI plan;
- marketing plan;
- iteration/analysis plan;
- capability and credential requirements without collecting secrets.

Required actions:

- Approve plan.
- Edit business plan.
- Edit engineering plan.
- Add feedback.
- Ask agent to remake plan.
- Inspect artifacts.

### Engineering

The TUI shows:

- active agent task;
- current files changed/generated;
- pending decisions;
- hands-on or handoff mode;
- hard boundary reminders.

Required actions:

- Start/continue engineering.
- Inspect generated files.
- Attach feedback to a file.
- Approve current build for QA.
- Request changes.
- View agent prompt/executor manifest.

Hands-on mode must notify the operator when a high-level decision changes
intent, scope, architecture, public boundary, credential need, or cost. Handoff
mode may let local-safe work proceed, but must still stop at hard gates.

### QA

Before QA runs, the TUI shows:

- "Here is the QA plan for this app surface."
- "Do you authorize this QA run?"

Required actions:

- Run QA.
- Edit QA plan.
- Add scenario.
- Inspect app/files before QA.

After QA, the TUI shows:

- pass/fail summary;
- failed checks;
- route: owner review, engineering, or QA plan revision;
- artifacts, screenshots/video when available and relevant;
- generated files tested.

Required actions:

- Accept QA.
- Send feedback to engineering.
- Ask agent to improve QA.
- Inspect artifacts.
- Rerun QA.

QA must adapt to website, CLI/TUI, backend/API, or mixed surfaces. Browser-only
QA is insufficient for non-browser apps.

### Deployment Planning

The TUI shows:

- deployment target options;
- domain/provider requirements;
- staging plan;
- credential requirements as placeholders only;
- hard stop before live provider mutation.

Required actions:

- Save deployment plan.
- Add provider/domain preference.
- Mark credentials unavailable.
- Stop before live setup.

No secrets are collected in this contract.

### KPI

The TUI shows 3-5 initial KPIs derived from the product and deployment plan.

Required actions:

- Accept KPI plan.
- Edit KPI.
- Add KPI.
- Remove KPI.
- Mark instrumentation blocked until deployment/provider access.

### Marketing

The TUI asks:

- "Do you have a marketing budget?"
- "Which channels or auth surfaces can the agent use later?"

Required actions:

- No budget: organic only.
- Budget exists: record non-secret budget plan.
- Add channel.
- Remove channel.
- Stop before public send/spend.

The TUI must distinguish one-time plan artifacts from future recurring jobs.

### Iteration And Analysis

The TUI shows:

- feedback inbox;
- proposed iteration issues;
- recurring analysis jobs planned;
- stage or environment where work would happen.

Required actions:

- Approve issue for agent work.
- Reject issue.
- Add feedback.
- Inspect evidence.
- Send to engineering loop.

Iteration and marketing can continue in parallel after launch planning, but live
actions remain gated.

## 5. Visual Contract

The terminal UI must use visual design to reduce comprehension load:

- Stage state uses consistent color/status symbols.
- Review-required items are visually distinct from completed or blocked items.
- Current selection is obvious.
- Long text is wrapped and clipped intentionally, not dumped raw.
- Dense state is grouped into sections, tables, or panes.
- Errors are red/actionable and include next safe action.
- Blocked/gated actions are yellow and state the stop boundary.
- Success states are green but never overclaim.
- Artifact/file lists are scan-friendly with kind, stage, status, and relative
  path.

The UX may use plain ANSI rendering first. It can later move to a richer TUI
library, but the user-visible result must feel like an application, not a shell
script transcript.

## 6. Resume And Session Continuity

The TUI must persist enough local state to resume:

- active app id;
- active session id;
- active stage;
- selected pane or last location;
- recent commands/actions;
- pending review cards;
- latest agent task status;
- latest artifact and file refs;
- last failure and next safe action.

Evidence surface:

- a persisted session file under the WEAVE state root;
- a resume command that opens the same app/stage/session;
- tests proving a second invocation reads previous state and shows last actions.

## 7. Lifecycle Stage Contract

The TUI must expose these lifecycle lanes as first-class stages:

1. First run and owner profile.
2. Intent.
3. Research.
4. Selection.
5. Plan.
6. Engineering.
7. QA.
8. Deployment planning and gated setup.
9. KPI setup.
10. Marketing planning and gated jobs.
11. Iteration and analysis.

For each stage, the TUI must show:

- stage purpose;
- current state;
- required artifacts;
- reviewable agent output;
- operator actions;
- next transition;
- stop boundary;
- evidence refs.

## 8. Review/Edit/Approve Loop

Every lifecycle stage that produces a decision or artifact must support this
loop:

1. Agent proposes artifact or plan.
2. TUI shows the artifact summary and evidence refs.
3. Operator can approve, ask for revision, inspect artifacts/files, or add
   feedback.
4. Revision feedback is recorded as a structured review item.
5. Agent can continue from the review item.
6. Stage only advances after the relevant gate passes.

Evidence surface:

- review item records;
- conversation/event ledger entries;
- artifact refs;
- tests for approve and revise paths.

## 9. Artifact And File Inspection

The TUI must support inspecting:

- lifecycle artifacts;
- generated source files;
- QA reports;
- agent prompts/executor manifests;
- event/conversation ledgers;
- pending jobs and blockers.

Minimum first implementation:

- list artifacts by stage;
- list generated files under the app workspace;
- open a selected artifact/file in the work pane;
- show relative path, kind, size, checksum when available;
- attach feedback to the selected artifact/file.

The TUI does not need to edit files directly in the first implementation. It
must support targeted feedback that the agent can use.

## 10. File-Specific Feedback

The operator must be able to say, effectively:

> For this file/artifact, change or investigate this.

This must create a structured feedback item with:

- app id;
- session id;
- stage;
- selected file/artifact ref;
- operator feedback text;
- created timestamp;
- status;
- target agent/executor;
- resulting agent task ref if launched.

Evidence surface:

- feedback ledger JSONL or JSON artifact;
- TUI display in review queue;
- test that feedback on a file is persisted and visible on resume.

## 11. Codex Agent Execution Contract

Codex execution must be a visible agent action surface:

- The TUI shows when Codex is available, running, failed, or complete.
- Operator can start an allowed Codex task from the current stage.
- Prompt packets are saved as public-safe artifacts.
- Executor manifests are saved and linked.
- Required output files/artifacts are verified.
- Failure returns non-zero in scripted mode and visible failure in interactive
  mode.
- Raw stdout/stderr is not blindly persisted if it can include private paths or
  noisy local machine details.

The current `--executor codex` app-builder path is a foundation. It is not yet
the full agent workflow because it is hidden inside scripted stage execution and
does not provide ongoing session controls.

## 12. QA Contract

QA must adapt to the app surface:

- Website: local static serving or equivalent, HTML/SEO/source checks, JS
  syntax/safety checks, runtime route checks.
- CLI/TUI: command execution, output readability, resume behavior, failure
  behavior.
- Backend/API: request/response behavior, schema checks, error handling.
- Mixed: relevant checks from each surface.

QA completion requires:

- real checks against generated files or runtime behavior;
- failed checks routed to engineering or QA plan revision;
- video/screenshot artifacts only when the surface requires visual proof and a
  renderer is available;
- no claim of production, live users, provider auth, or deployment unless those
  were explicitly exercised.

## 13. Service Blueprint

| Phase | User action | Visible TUI | Backstage system | Agent action | Evidence | Failure lane |
| --- | --- | --- | --- | --- | --- | --- |
| First run | Start TUI | Cockpit welcome, environment detection, app/create choices | Detect WEAVE state, Hermes/Codex surfaces, previous session | None or readiness probe | session state, owner profile | show missing runtime/setup choices |
| Owner profile | Enter experience and coworker preference | Guided profile pane | Persist owner preferences | None | owner profile artifact | validation error, editable profile |
| Create/select app | Choose existing or create new | App list and active app header | Load/create app state | None | app metadata, active app ref | no app selected |
| Intent | Fill substantial intent | Intent editor/review pane | Persist draft and review request | Validate intent sufficiency | intent artifact, review item | ask for missing details |
| Research | Review research plan and output | Research plan, progress, artifacts | Persist plan/output | Research public-safe sources if enabled | research artifacts | revise plan or continue research |
| Selection | Pick/edit option | Option comparison pane | Persist decision | Analyze research and propose options | selection artifact | request new option |
| Plan | Review business/technical/QA/KPI/marketing plans | Multi-track plan pane | Persist plans and approvals | Produce plan and revise on feedback | plan artifacts | revise plan |
| Engineering | Start/monitor agent work | Agent task pane, generated files, decisions | Save prompt/executor/source manifests | Codex builds/edits files | generated files, executor manifest | route failed build to engineering |
| QA | Authorize/run QA | QA plan, live status, failed checks | Run surface-adapted checks | Fix or rerun if authorized | QA manifest, artifacts | engineering or QA-plan revision |
| Deployment plan | Review gated setup | Gated checklist | Persist non-secret plan only | None unless authorized | deployment plan artifact | stop before credentials/live deploy |
| KPI | Review metrics plan | KPI definitions and instrumentation plan | Persist plan | None unless authorized | KPI plan artifact | blocked on deployment/provider |
| Marketing | Review campaign plan/jobs | Gated jobs list | Persist planned recurring jobs | None unless authorized | marketing artifacts | stop before public send/spend |
| Iteration/analysis | Review feedback/issues | Feedback inbox, proposed issues | Persist recurring analysis plan | Suggest improvements | iteration artifacts | approval required before work |

The table above is not enough by itself. The user-visible scripts in section
4.3 are part of the contract and must be implemented or explicitly marked
deferred with a failing gap before completion.

## 14. Completion Evidence Matrix

| Requirement | Required evidence |
| --- | --- |
| Formal contract exists | this document is committed and referenced by docs/tests |
| Gap map exists | current-state gap map committed and updated |
| Blueprint fidelity | tests or dogfood show visible prompts and reply choices from section 4.3 |
| User choices | tests cover yes/no, option picker, free-form feedback, and inspect actions |
| Resumable TUI | test invokes TUI twice and second run shows persisted session state |
| Polished visual hierarchy | snapshot/golden output tests cover header/nav/work pane/command bar |
| Navigation | tests cover moving between stages/artifacts/files/review queue |
| Review loop | tests cover approve and revise paths with persisted review items |
| File-specific feedback | test persists feedback on selected file and shows it on resume |
| Codex ongoing agent surface | test or dogfood launches Codex task from session state and records manifest |
| Generated app artifacts | generated source files and source manifest exist |
| QA through QA | real app QA manifest passes for dogfood app |
| Honest failure | tests cover Codex failure and QA failure without false success |
| Docs | quickstart/runtime docs explain interactive and scripted use |
| CI | GitHub checks green on final PR |
| Dogfood | substantial app intent run through QA with proof artifact summary |

## 15. Definition Of Done

The full goal can be marked complete only after:

1. The completion evidence matrix is all proven by current artifacts, tests, or
   CI.
2. The current TUI can be used interactively as an ongoing cockpit, not only via
   `--scripted-demo`.
3. A fresh dogfood runtime can create or resume an app, collect intent, run
   through engineering and QA with Codex, inspect files/artifacts, record
   feedback, and preserve session continuity.
4. All stop boundaries remain intact.
5. The final PR body records local proof, runtime/live proof, non-claims,
   failing-check disposition, and owner/project criteria.

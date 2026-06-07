# WEAVE Telegram Slash Commands

Status: public-safe command contract

WEAVE uses Telegram for Hermes conversation and for deterministic runtime
status. There is no dashboard/UI in this phase. Normal messages go to Hermes
only after normal Hermes setup has been confirmed. Messages that begin with a
WEAVE slash command are intercepted by the gateway and answered from the local
WEAVE runtime state without model-generated text.

Every WEAVE slash-command response uses this contract:

```yaml
schema: weave-telegram-command/v0.1
deterministic: true
llm_used: false
communication_channel: telegram
```

Telegram supports bot command messages as ordinary updates. The deterministic
behavior is not automatic; the WEAVE gateway must route the slash command to
the runtime command handler before Hermes sees it.

## Commands

| Command | Purpose |
|---|---|
| `/start` | Show the deterministic WEAVE command surface. |
| `/help` | List deterministic WEAVE commands. |
| `/autonomy` | Show autonomy mode and hard approval gates. |
| `/status` | Show the WEAVE wall: agent profile, active app, product app portfolio, attention items, runtime source state, and next action. |
| `/status <app_id>` | Show the app wall: summary, lifecycle, current-stage requirements, missing inputs, tasks, decisions, recent work, blockers, agent profile, and next action. |
| `/sources` | Show the runtime source map: canonical root, history surfaces, active/stale/missing state, and next unification action. |
| `/apps` | List product apps, lifecycle stage per app, and attention state. System/tooling apps are hidden by default. |
| `/apps --all` | Include system/tooling apps for maintenance review. |
| `/app <app_id>` | Show one app wall. |
| `/create_app <name>` | Create and select a product app workspace after Hermes/user confirmation. |
| `/switch_app <app_id>` | Select the active product app for the Telegram UX. |
| `/lifecycle [app_id]` | Show lifecycle rows, current-stage gate state, missing evidence, and next action. Defaults to the active app. |
| `/stage [app_id]` | Show the current lifecycle stage and lifecycle row state. Defaults to the active app. |
| `/requirements [app_id]` | Show current-stage requirements, missing inputs, questions, and credential blockers. Defaults to the active app. |
| `/approve_stage [app_id] [stage] [--defer-credentials]` | Record owner approval for a lifecycle stage after foundation, prior-stage, artifact, blocker, and credential gates pass. |
| `/advance [app_id]` | Advance to the next lifecycle stage after the current stage is owner-approved. |
| `/blockers` | Show apps that need owner or Hermes action. |
| `/changes [app_id]` | Show latest recorded changes for one app or all apps. |
| `/transcript [app_id]` | Show recent raw app conversation turns: owner message, Hermes reply, rationale summary, artifact refs, event refs, lifecycle transition, and next action. Defaults to the active app. |
| `/next` | Show the next deterministic owner-visible action. |

## Accessing App Status

Use `/status` when you need the full WEAVE wall:

```text
WEAVE Status

Agent
- model=gpt-5.5; reasoning=xhigh; adapter=codex; prompt_pack=hermes-gestalt-runtime-pack
- autonomy=yolo

Hermes Setup
- state: operator_confirmed_ready
- normal_chat_assumed_ready: true
- route_verification_owner: hermes

Apps
- active_app: visual-novel
- product_apps: 1
- system_apps_hidden: 1
- blocked_apps: 1
- stage_gate_blocked_apps: 1
- Visual Novel (visual-novel): plan / collecting; foundation=passed

Attention
- visual-novel: owner questions

System
- runtime_home: runs/runtime-home
- state_root: runs/runtime-home/weave-state
- root_ready: true
- sources: 7
- canonical_source: weave-root

Next
- Hermes should continue eliciting missing context or drafting the current stage packet.
```

Use `/apps` when you need the compact product portfolio view:

```text
WEAVE product apps:
- Demo App (demo-app): intent / collecting; foundation=blocking
- Production App (production-app): qa / ready_for_review; foundation=passed
```

Use `/status <app_id>` or `/app <app_id>` when you need the state of one app:

```text
WEAVE App Status: Demo App (demo-app)

Summary
- type: product
- stage: intent
- state: collecting
- foundation: blocking: soul.md, owner-profile.md

Lifecycle
- intent: collecting
- research: not_started
- selection: not_started
- plan: not_started

Needs You
- soul.md
- owner-profile.md

Next
- Hermes should ask focused foundation questions and update the required documents.
```

Use `/blockers` and `/next` when you want the lowest-cognitive-load answer to
"what needs attention now?"

Use `/transcript [app_id]` when you need to audit what actually happened in the
chat flow:

```text
WEAVE Transcript: Demo App (demo-app)
- turns: 2
- source: apps/demo-app/ledger/conversation-turns.jsonl
- event_source: apps/demo-app/ledger/conversation-events.jsonl
- review_export: apps/demo-app/exports/conversation/conversation-review.html

Recent Turns
1. 2026-06-06T12:00:00Z [intent]
   owner: Make a short visual novel about a crow learning to ask for water.
   hermes: I captured the intent and created the first intent artifact for review.
   rationale: Foundation documents were complete and the intent artifact now exists.
   transition: intent/collecting -> intent/ready_for_review
   artifacts: 1; events: 1
   next: Owner reviews the intent artifact, then may approve the intent stage.
```

Each row is stored as `weave-conversation-turn/v0.1` in
`apps/<app_id>/ledger/conversation-turns.jsonl`. The row records:

- `operator_message`: what the owner or operator sent.
- `agent_reply`: what Hermes replied.
- `agent_rationale`: an owner-reviewable rationale summary, gate questions,
  missing information, and decision basis. It does not capture hidden model
  chain-of-thought.
- `gate_checks`: deterministic checks Hermes considered before moving.
- `artifact_refs`: files created or updated as a result of the reply.
- `event_refs`: append-only ledger events connected to the turn.
- `state_transition`: lifecycle or stage-state change proposed or initiated
  from the turn.
- `next_action`: the immediate owner-visible next action.

The canonical raw review stream is stored separately as
`weave-conversation-event/v0.1` rows in
`apps/<app_id>/ledger/conversation-events.jsonl`. The runtime can export the
review bundle to `apps/<app_id>/exports/conversation/`:

- `conversation.events.jsonl`: portable event stream.
- `conversation-review.html`: primary human review artifact. It escapes raw
  message content so Markdown fences, tables, and literal HTML in agent replies
  do not break the review surface.
- `conversation-report.json`: paths, counts, checksums, renderer, and policy.

Use the HTML review artifact for owner review and the event JSONL as the source
of truth. Markdown renderings are optional convenience exports only.

Transcript capture is mandatory for app work. A Hermes app-work reply is not
complete until the structured turn has been appended, or Hermes explicitly
reports that transcript sync is blocked. Lifecycle approval and advance use the
current-stage transcript capture gate, so a stage with artifacts can still be
blocked if no current-stage conversation turn links the owner message, Hermes
reply, artifact/event evidence, and proposed state transition.

Use `/stage` and `/requirements` when Hermes says it is missing information and
you want the deterministic reason why lifecycle progress is blocked or still
collecting.

Use `/lifecycle`, `/approve_stage`, and `/advance` when reviewing stage
movement:

```text
WEAVE Lifecycle: Visual Novel (visual-novel)
- current_stage: intent
- state: ready_for_review
Stages:
- intent: ready_for_review; artifacts=1
- research: not_started
Gate:
- missing: none
Next: Owner review is needed; /approve_stage can mark this lifecycle stage approved.
```

Approval and advance are intentionally separate:

```text
/approve_stage visual-novel
Approved stage: visual-novel / intent
Recorded: owner approval and stage gate evidence.
Next: /advance can move to the next lifecycle stage.

/advance visual-novel
Advanced app: visual-novel
- from: intent
- to: research
Next: Hermes should collect or produce evidence for the new stage.
```

If a stage is missing evidence, prior approval, required input, owner answers,
or required credential capability, `/approve_stage` returns a deterministic
blocked response. For KPI, Marketing, and Analysis, the owner can explicitly use
`--defer-credentials` to record that the stage is continuing with a reviewed
credential deferral.

Use `/autonomy` to see whether the gateway is in `yolo` mode and which gates
still require owner authorization through the Telegram LLM conversation.

Use `/sources` when runtime state feels split across multiple places. The
response is deterministic and names which surfaces are active, stale, missing,
or historical. Sensitive entries are represented as references and never expose
secret values.

## Autonomy Mode

Gateway setup defaults to `WEAVE_AUTONOMY_MODE=yolo`. In yolo mode Hermes does
not ask for routine confirmation before non-gated local work, such as
inspection, local app workspace edits, tests, validation, formatting, and
append-only ledger updates.

Yolo mode is not blanket approval. Hermes must ask the owner through the
Telegram LLM conversation before hard-gated actions, including secrets or auth
changes, public sends, paid or metered work, production/service changes, and
destructive work.

## Gateway Rule

The gateway must treat a WEAVE slash command as a deterministic status request.
It should call the WEAVE runtime command handler and return the resulting
`text` field to Telegram. It should not ask Hermes to compose or reinterpret
the answer.

Non-command messages remain Hermes conversation. This keeps the communication
channel simple: chat for intent and app work, slash commands for state. If
normal Hermes setup has not been confirmed, normal messages should return
guided setup instructions rather than a vague setup error, while `/status`,
`/apps`, and `/help` should continue to work.

When information is missing, Hermes should not dead-end the conversation. It
should enter an elicitation loop: explain what is missing, why it matters, ask
focused questions, and keep the owner moving. WEAVE may still show the stage as
`collecting` or `blocked` until required information is recorded and the owner
approves stage completion.

When Hermes performs app work after a normal message, it should submit the
structured transcript form to `POST /apps/<app_id>/conversation`. Runtime or
gateway code should fill deterministic fields where possible, including app id,
current lifecycle stage, timestamps, known artifacts, ledger event refs, and
gate status. Hermes fills the reviewable rationale, missing information,
decision basis, transition reason, and next action. If the gateway cannot
auto-capture an after-reply hook, Hermes must call the conversation endpoint
directly before claiming the turn is complete.

Hermes can fetch the deterministic form from
`GET /apps/<app_id>/conversation/form`. The form tells Hermes which fields are
runtime-filled or runtime-verified, and which fields Hermes must complete.

## REST Parity

The runtime exposes REST-equivalent control paths for deterministic clients:

| REST path | Equivalent |
|---|---|
| `POST /telegram/dispatch` with `{ "text": "/status" }` | Telegram command dispatch without using the model. |
| `GET /apps/<app_id>/lifecycle` | `/lifecycle <app_id>` payload. |
| `GET /apps/<app_id>/conversation` | Full app conversation-turn ledger. |
| `GET /apps/<app_id>/conversation/form` | Deterministic transcript-capture form for Hermes to complete. |
| `GET /apps/<app_id>/conversation/events` | Canonical conversation event stream. |
| `POST /apps/<app_id>/conversation/export` | Materialize the review bundle under `exports/conversation/`. |
| `POST /apps/<app_id>/conversation` | Append a public-safe conversation turn after Hermes replies. |
| `POST /apps/<app_id>/approve-stage` | `/approve_stage <app_id>`. |
| `POST /apps/<app_id>/advance` | `/advance <app_id>`. |

The local runtime smoke and lifecycle rehearsal verify that Telegram-command
dispatch and direct REST lifecycle paths agree on stage state.

## Lifecycle Vocabulary

The product-facing lifecycle names are:

```text
intent -> research -> selection -> plan -> engineering -> qa -> kpi -> marketing -> iteration -> analysis
```

Internal Gestalt artifacts may still appear inside artifact files, but command
output and app folders use product lifecycle language so humans and future
agents can inspect the runtime without translating internal terms.

# WEAVE Telegram Slash Commands

Status: public-safe command contract

WEAVE uses Telegram for Hermes conversation and for deterministic runtime
status. There is no dashboard/UI in this phase. Normal messages go to Hermes
only after provider auth is verified. Messages that begin with a WEAVE slash
command are intercepted by the gateway and answered from the local WEAVE runtime
state without model-generated text.

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
| `/stage [app_id]` | Show the current lifecycle stage and lifecycle row state. Defaults to the active app. |
| `/requirements [app_id]` | Show current-stage requirements, missing inputs, questions, and credential blockers. Defaults to the active app. |
| `/blockers` | Show apps that need owner or Hermes action. |
| `/changes [app_id]` | Show latest recorded changes for one app or all apps. |
| `/next` | Show the next deterministic owner-visible action. |

## Accessing App Status

Use `/status` when you need the full WEAVE wall:

```text
WEAVE Status

Agent
- model=gpt-5.5; reasoning=xhigh; adapter=codex; prompt_pack=hermes-gestalt-runtime-pack
- autonomy=yolo

Provider Auth
- state: verified
- chat_ready: true
- provider: nous
- model: anthropic/claude-sonnet-4

Apps
- active_app: visual-novel
- product_apps: 1
- system_apps_hidden: 1
- blocked_apps: 1
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

Use `/stage` and `/requirements` when Hermes says it is missing information and
you want the deterministic reason why lifecycle progress is blocked or still
collecting.

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
provider auth is missing or unverified, normal messages should return guided
setup instructions rather than a vague provider error, while `/status`, `/apps`,
and `/help` should continue to work.

When information is missing, Hermes should not dead-end the conversation. It
should enter an elicitation loop: explain what is missing, why it matters, ask
focused questions, and keep the owner moving. WEAVE may still show the stage as
`collecting` or `blocked` until required information is recorded and the owner
approves stage completion.

## Lifecycle Vocabulary

The product-facing lifecycle names are:

```text
intent -> research -> selection -> plan -> engineering -> qa -> kpi -> marketing -> iteration -> analysis
```

Internal Gestalt artifacts may still appear inside artifact files, but command
output and app folders use product lifecycle language so humans and future
agents can inspect the runtime without translating internal terms.

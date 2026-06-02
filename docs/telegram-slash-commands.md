# WEAVE Telegram Slash Commands

Status: public-safe command contract

WEAVE uses Telegram for Hermes conversation and for deterministic runtime
status. Normal messages go to Hermes. Messages that begin with a WEAVE slash
command are intercepted by the gateway and answered from the local WEAVE
runtime state without model-generated text.

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
| `/status` | Show runtime readiness, app count, blocked app count, and next action. |
| `/sources` | Show the runtime source map: canonical root, history surfaces, active/stale/missing state, and next unification action. |
| `/apps` | List apps, lifecycle stage per app, and foundation gate state. |
| `/app <app_id>` | Show one app's stage, foundation gate, contract version, artifact count, and latest categorized changes. |
| `/blockers` | Show apps that need owner or Hermes action. |
| `/changes [app_id]` | Show latest recorded changes for one app or all apps. |
| `/next` | Show the next deterministic owner-visible action. |

## Accessing App Status

Use `/apps` when you need the full portfolio view:

```text
WEAVE apps:
Demo App (demo-app): stage=intent; foundation=blocking
Production App (production-app): stage=qa; foundation=passed
```

Use `/app <app_id>` when you need the state of one app:

```text
Demo App (demo-app)
stage: intent (derived)
foundation: blocking: soul.md, owner-profile.md
contract_version: 0.1-template
artifacts: 0
```

Use `/blockers` and `/next` when you want the lowest-cognitive-load answer to
"what needs attention now?"

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
channel simple: chat for intent and app work, slash commands for state.

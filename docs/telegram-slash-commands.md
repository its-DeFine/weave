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
| `/status` | Show runtime readiness, app count, blocked app count, and next action. |
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

## Gateway Rule

The gateway must treat a WEAVE slash command as a deterministic status request.
It should call the WEAVE runtime command handler and return the resulting
`text` field to Telegram. It should not ask Hermes to compose or reinterpret
the answer.

Non-command messages remain Hermes conversation. This keeps the communication
channel simple: chat for intent and app work, slash commands for state.

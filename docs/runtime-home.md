# WEAVE Runtime Home

Status: public-safe architecture contract
Audience: operators, reviewers, and agents

WEAVE uses one durable local runtime home as the source of truth for app work.
The container, gateway process, and optional local API are replaceable process
surfaces. The runtime home is what must survive restart, review, migration, and
future model upgrades.

## Contract

Default layout:

```text
runs/runtime-home/
  runtime-profile.json
  weave-state/
    artifacts/general/
    apps/
    ledger/
    runtime/
      hermes-gateway/
      logs/
      profiles/
      source-map.json
      tokens/
  hermes-home/
    config.yaml
    .env                  # local secret-bearing file, never exported by default
    weave-hermes-setup.json # non-secret Hermes setup readiness status
    plugins/weave-runtime/
```

The names are intentional:

| Path | Owner | Purpose |
|---|---|---|
| `runtime-home/` | WEAVE CLI/runtime | Durable parent for all local state. |
| `runtime-profile.json` | setup backend | Reviewable setup profile, model/profile info, runtime image, and authority boundaries. |
| `weave-state/` | WEAVE runtime state | Apps, lifecycle shelves, ledgers, source map, deterministic command state. |
| `hermes-home/` | Hermes runtime | Hermes config, gateway environment, plugin install, and session-facing local state. |
| container | WEAVE CLI | Replaceable Hermes process runner. It should not own durable state. |

`weave-state/` still uses the legacy schema name `weave-root/v0.1` for
compatibility with existing app and lifecycle contracts. The parent layout is
`weave-runtime-home/v0.1`.

## Services

The current first slice has no dashboard UI.

Runtime surfaces:

- `bin/weave onboard`: guided setup. Builds or selects the Hermes runtime,
  creates the runtime home, writes foundation onboarding context, records
  whether normal Hermes setup has been confirmed, and configures Telegram
  gateway credentials when the owner supplies them.
- `bin/weave hermes status`: reports non-secret Hermes setup readiness.
- `bin/weave hermes confirm-ready`: records that Hermes itself has already been
  installed, authenticated, and verified for normal chat by the operator.
- `bin/weave start`: starts the containerized Hermes gateway from the generated
  gateway workdir.
- `bin/weave stop`: stops the gateway container.
- `bin/weave status`: prints deterministic runtime-home, container, app, and
  next-action state.
- Telegram slash commands: deterministic status from `weave-state/` with
  `deterministic: true` and `llm_used: false`.
- `scripts/weave_runtime_api.py`: optional loopback-only REST skeleton for
  remote-compatible state access. It is not a production service in this slice.

Hermes owns the LLM conversation and app work. WEAVE owns deterministic state
projection, local ledger primitives, setup boundaries, and process control that
Hermes cannot safely delegate to itself.

## Status UX

Use Telegram commands for operator state:

- `/status`: the WEAVE wall, including model/profile, active app, app counts,
  Hermes setup state, blockers, runtime home, source count, ledger count, and
  next action.
- `/apps`: compact product app portfolio.
- `/status <app_id>` or `/app <app_id>`: one app wall with lifecycle row,
  current requirements, missing inputs, decisions, recent work, blockers, and
  next action.
- `/transcript [app_id]`: recent app conversation turns, including the owner
  message, Hermes reply, rationale summary, artifact refs, event refs,
  lifecycle transition, and next action.
- `/sources`: source-of-truth map for active, missing, stale, or historical
  runtime state.

Use `bin/weave status` when the gateway may be down. It does not require the
container to be running; it reports the runtime home and then reports container
state when the container engine is available.

## Migration

WEAVE migration is state-first:

```bash
bin/weave export-runtime --out runtime-export.tar.gz
bin/weave import-runtime runtime-export.tar.gz --runtime-home runs/runtime-home
bin/weave verify-runtime --runtime-home runs/runtime-home
```

Export includes reviewable runtime state and excludes raw secret material by
default:

- `hermes-home/.env`
- `weave-state/runtime/tokens/*`
- temporary Telegram token files
- key-like files such as `.pem`, `.key`, `.p12`, `.pfx`, and `.secret`

After import, `weave verify-runtime` reports whether credential relinking is
required. This is deliberate: app context, ledgers, lifecycle artifacts, source
maps, and profiles can move; raw gateway credentials must be relinked in the
new environment. Hermes setup readiness must also be reconfirmed unless the
runtime is explicitly put into slash-only mode.

## Review Rules

Human review should be able to answer:

- What apps exist?
- Which app is active in the Telegram UX?
- What lifecycle stage is each app in?
- What changed recently in each app?
- What did the owner send, what did Hermes reply, what artifacts/events were
  produced, and what lifecycle transition resulted?
- What is missing before Hermes can continue?
- Which model, reasoning effort, adapter, prompt pack, and skills were active?
- Is normal Hermes setup confirmed, slash-only, or blocked?
- Which files are canonical state versus runtime process state?
- Is the gateway running, missing, or only configured?
- Are credentials linked, or is relinking required?

If a status surface cannot answer those questions, it is incomplete.

Conversation review is state-first. App exchanges are stored in
`apps/<app_id>/ledger/conversation-turns.jsonl` as
`weave-conversation-turn/v0.1` rows. These rows preserve the raw owner/operator
message and Hermes reply, but record only an owner-reviewable rationale summary
instead of hidden model chain-of-thought. Artifacts and state transitions should
be referenced from the turn so a reviewer can move from chat, to file, to
ledger event, to lifecycle state without reconstructing the run from memory.

Transcript capture is mandatory for lifecycle movement. A lifecycle stage
cannot be approved or advanced unless the current stage has a transcript row.
When stage artifacts exist, that row must link to a stage artifact, ledger
event, or state transition. This prevents local artifact creation or chat-only
claims from bypassing the app conversation record.

## QA Path

Minimum repo QA:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/runtime_smoke.py
git diff --check
```

Minimum runtime-home QA:

1. Run `bin/weave onboard --dry-run` and confirm the one-command setup flow is
   understandable before token entry.
2. Run `bin/weave onboard` in a disposable runtime home and confirm token input
   is hidden and not printed.
3. Run `bin/weave status` before starting the gateway and confirm local state
   is visible.
4. Run `bin/weave export-runtime`, `bin/weave import-runtime`, and
   `bin/weave verify-runtime` on a fresh runtime home.
5. Start the gateway only after credentials are intentionally linked.
6. Use Telegram `/start`, `/status`, and `/apps` to confirm deterministic
   replies from the expected bot.

The QA artifact should show process state and deterministic command output, but
must not show raw token values.

## Non-Goals In This Slice

This slice does not add:

- a web dashboard
- production deployment
- host autostart services
- credential export
- multi-agent parallel app UX in Telegram
- remote tunnel or private network instructions
- a full container compose stack

Those can be added later when the runtime-home contract is stable.

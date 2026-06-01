# Hermes Runtime Setup

Status: public-safe setup contract
Audience: builders configuring WEAVE locally

WEAVE defaults to Hermes for the runtime agent and keeps Local Fallback as an
explicit fallback. The public repository can set up the WEAVE-side runtime
profile, provision the real upstream Nous Hermes Agent into ignored local
state, and configure the owner-approved Telegram gateway environment from a
token file when explicitly given gateway flags. It does not install services,
mutate shell startup files, start a gateway daemon, or place secrets in tracked
state.

## What Setup Does

Run:

```bash
python3 scripts/setup_runtime.py
```

The command:

- reads `packages/weave-tool/COMPANY.md`
- selects `hermes-default`
- loads `packages/weave-tool/agents/ceo-hermes/AGENTS.md`
- checks whether a Hermes executable is already on `PATH`
- writes `runs/runtime-profile.json`
- creates or verifies the ignored local WEAVE root
- creates or verifies a foundation app workspace
- writes `runtime/profiles/foundation-gate-<app-id>.json`
- writes a generated Hermes gateway workdir with `AGENTS.md`, `SOUL.md`, and
  `weave-gateway-context.json`
- when gateway flags are supplied, writes Hermes `terminal.cwd` and
  `agent.system_prompt` so gateway sessions load the foundation onboarding
  context even when Hermes starts from another directory
- records Local Fallback as the fallback runtime
- records that Telegram gateway setup is required

The generated `runs/` directory is ignored by git.

The generated gateway workdir is the enforcement bridge. Gateway setup points
Hermes at the printed `foundation_gateway_workdir` path through `terminal.cwd`
and also writes a runtime system prompt. If the foundation gate is not passing,
Hermes must ask the owner through Telegram, ask at most three blocking
questions at once, update the canonical WEAVE documents, and stop before app
work until the gate can pass.

## Real Hermes Provisioning

To install the pinned upstream Hermes Agent for WEAVE:

```bash
python3 scripts/setup_runtime.py --install-hermes
```

This calls `scripts/provision_hermes.py`, which performs explicit reviewed
steps instead of running the upstream `curl | bash` installer:

- clones `https://github.com/NousResearch/hermes-agent.git`
- checks out pinned commit `5921d667855880b0aa2083a50f001748aed52f3e`
- verifies the checkout exposes the `hermes` console script
- creates `runs/hermes-agent/venv`
- installs the package with the `cli` extra
- writes `runs/hermes-agent/bin/hermes`
- writes `runs/hermes-agent/profile.json`
- writes `runs/runtime-profile.json` with the Hermes proof attached

The setup profile only records local proof. It does not start Hermes, run
`hermes setup`, pair Telegram or any other gateway, write provider credentials,
or enable autostart.

## Telegram Gateway Dependency Install

Telegram setup has two required parts. First, Hermes must be installed with the
gateway dependencies available:

```bash
python3 scripts/setup_runtime.py --install-hermes --require-runtime-binary --hermes-extras cli,messaging
```

This still writes only ignored local runtime state. It does not pair Telegram.

Second, configure the Hermes Telegram environment from the same setup command
by passing an owner-approved token file and allowlist:

```bash
python3 scripts/setup_runtime.py \
  --install-hermes \
  --require-runtime-binary \
  --hermes-extras cli,messaging \
  --gateway-token-file <owner-approved-token-file> \
  --gateway-allowed-users <numeric-telegram-user-id>
```

This writes the token and allowlist only into the local Hermes `.env` file,
sets private file permissions, configures the generated foundation gateway
context, and prints a redacted setup summary. With exactly one allowed Telegram
user and no explicit `--gateway-home-channel`, setup also uses that direct chat
as the home channel. It does not print the token, install a service, start a
daemon, contact Telegram, or send messages.

The default gateway autonomy is `--autonomy-mode yolo`. Hermes can continue
without routine confirmation for non-gated local work, but must ask the owner
through the Telegram LLM conversation before hard-gated actions: secrets or
auth changes, public sends, paid or metered work, production/service changes,
or destructive work. Use `--autonomy-mode confirm_everything` to restore
manual confirmation for non-trivial work.

If the numeric Telegram user id is not known yet, a temporary discovery setup
can be used:

```bash
python3 scripts/setup_runtime.py \
  --gateway-token-file <owner-approved-token-file> \
  --gateway-allow-all-users
```

Replace discovery mode with `--gateway-allowed-users` immediately after the
owner id is captured. Do not write tokens into tracked files, command
transcripts, issue comments, pull requests, or setup artifacts.

The narrower `scripts/setup_gateway.py` helper remains available for runtimes
that already completed Hermes installation and only need gateway environment
configuration.

After configuration, verify the gateway path:

```bash
hermes status
hermes gateway status
cd <foundation-gateway-workdir>
hermes gateway run
```

The owner must still send the first Telegram message to the bot before Hermes
can learn the owner chat target.

After provisioning, this stricter check should pass:

```bash
python3 scripts/setup_runtime.py --require-runtime-binary
```

## Strict Binary Check

To require a local Hermes executable:

```bash
python3 scripts/setup_runtime.py --require-runtime-binary
```

This fails if none of these executables are on `PATH`:

- `hermes`
- `hermes-agent`
- `nous-hermes`

Use `--runtime-binary <name-or-path>` when your local binary has a different
name.

## Local Fallback Profile

To write a Local Fallback profile:

```bash
python3 scripts/setup_runtime.py --runtime local-fallback
```

This checks for `local-fallback` on `PATH` and writes the fallback profile locally.

## Boundaries

The default setup command does not:

- download runtime binaries
- run package managers
- install launch services, cron jobs, or service units
- read existing `.env` files during default runtime setup
- load credentials during default runtime setup
- contact private gateways
- mutate hosted runtime state
- claim a remote runtime or production service exists

The `--install-hermes` path does clone upstream source and install Python
packages into `runs/hermes-agent/venv`, but it keeps the same service, secret,
gateway, shell-startup, and production boundaries.

The `--gateway-token-file` setup path is the approval-gated gateway setup
step. It may read the owner-supplied token file and write Hermes local
environment state, but it still does not start the gateway, install autostart,
or perform external sends.

Runtime pairing, gateway live-run approval, autostart, production deploys,
paid jobs, credential changes, public posts, and external sends remain separate
approval gates.

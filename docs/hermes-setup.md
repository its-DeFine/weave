# Hermes Runtime Setup

Status: public-safe setup contract
Audience: builders configuring WEAVE locally

WEAVE defaults to Hermes for the runtime agent and keeps Local Fallback as an
explicit fallback. The public repository can set up the WEAVE-side runtime
profile, build a pinned Hermes container, provision the real upstream Nous
Hermes Agent into ignored local state for host-local fallback, record
non-secret Hermes setup readiness, and configure the owner-approved Telegram
gateway environment from a token file when explicitly given gateway flags. It
does not install services, mutate shell startup files, start a gateway daemon
during setup, or place secrets in tracked state.

The default durable layout is documented in
[WEAVE Runtime Home](runtime-home.md). In short: `runs/runtime-home` owns
reviewable local state, `weave-state/` owns apps and ledgers, `hermes-home/`
owns Hermes config and gateway environment, and the container is replaceable.

## What Setup Does

For the human setup path, run:

```bash
bin/weave onboard
```

This presents a guided ASCII flow that first requires normal Hermes setup
confirmation or an explicit slash-only choice. After that gate passes, it builds
the pinned Hermes container image, creates the local WEAVE root, explains the
dedicated Telegram bot requirement, hides token input, and calls the same
public-safe setup backend without printing secrets.

For CI or non-interactive operator setup, run the backend directly:

```bash
python3 scripts/setup_runtime.py
```

The command:

- reads `packages/weave-tool/COMPANY.md`
- selects `hermes-default`
- loads `packages/weave-tool/agents/ceo-hermes/AGENTS.md`
- checks whether a Hermes executable or runtime container image is available
- writes `runs/runtime-home/runtime-profile.json`
- creates or verifies the ignored local runtime home
- creates or verifies `runs/runtime-home/weave-state`
- creates or verifies a foundation app workspace
- writes `runtime/profiles/foundation-gate-<app-id>.json`
- writes a generated Hermes gateway workdir with `AGENTS.md`, `SOUL.md`, and
  `weave-gateway-context.json`
- when gateway flags are supplied, writes Hermes `terminal.cwd` and
  `agent.system_prompt` so gateway sessions load the foundation onboarding
  context even when Hermes starts from another directory
- records Local Fallback as the fallback runtime
- records Hermes setup state as confirmed, blocked, or slash-only without
  printing credentials
- records that Telegram gateway setup is required

The generated `runs/` directory is ignored by git. The profile records the
runtime-home layout, container image, model/profile metadata, autonomy mode,
and the secret migration policy.

The generated gateway workdir is the enforcement bridge. Gateway setup points
Hermes at the printed `foundation_gateway_workdir` path through `terminal.cwd`
and also writes a runtime system prompt. If the foundation gate is not passing,
Hermes must ask the owner through Telegram, ask at most three blocking
questions at once, update the canonical WEAVE documents, and stop before app
work until the gate can pass.

## Default Container Provisioning

The recommended human path is:

```bash
bin/weave onboard
```

By default this builds `weave-hermes-runtime:local` from
`container/hermes/Dockerfile`. The image clones the upstream Hermes Agent
source at pinned commit `5921d667855880b0aa2083a50f001748aed52f3e` and installs
the `cli,messaging` dependency set inside the image. The runtime profile records
that Hermes is supplied by that container image.

After onboarding, run the gateway with:

```bash
bin/weave start
bin/weave status
bin/weave stop
```

`weave start` mounts the local WEAVE root, Hermes home, and repository into the
container, starts `hermes gateway run --replace`, and applies Docker's
`unless-stopped` restart policy. It does not install host services or autostart
units.

`weave status` reads the runtime home first. It can report missing profile,
state root, Hermes home, gateway env, app counts, active app, and next action
even when the gateway container is not running.

## Runtime Migration

Reviewable state can be exported and imported:

```bash
bin/weave export-runtime --out runtime-export.tar.gz
bin/weave import-runtime runtime-export.tar.gz --runtime-home runs/runtime-home
bin/weave verify-runtime --runtime-home runs/runtime-home
```

The export is intentionally credential-blind. It excludes Hermes `.env`, local
API tokens, temporary Telegram token files, and key-like files. After import,
`verify-runtime` reports whether credentials need to be relinked before the
gateway can run. This keeps migration useful without turning exports into
secret bundles.

## Host-Local Hermes Provisioning

To install the pinned upstream Hermes Agent on the host as a fallback:

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
- writes `runs/runtime-home/runtime-profile.json` with the Hermes proof attached

The setup profile only records local proof. It does not start Hermes, run
`hermes setup`, pair Telegram or any other gateway, write provider credentials,
or enable autostart.

## Hermes Setup Gate

Hermes owns provider authentication, model selection, and provider-route
verification. WEAVE does not collect provider credentials, run provider test
prompts, or inspect provider outputs. WEAVE only records whether the operator has
confirmed that normal Hermes setup already works, or whether the runtime is
intentionally slash-only for deterministic commands.

Run normal Hermes setup first:

```bash
HERMES_HOME=runs/runtime-home/hermes-home hermes setup --portal
```

Select or verify the model with Hermes:

```bash
HERMES_HOME=runs/runtime-home/hermes-home hermes model
```

After Hermes itself can chat, record that readiness for WEAVE:

```bash
bin/weave hermes confirm-ready
```

`bin/weave hermes status` reports non-secret setup state, route verification
ownership, whether normal chat is assumed ready, and whether a Hermes binary
was found. It does not print API keys, OAuth payloads, or provider outputs.

If the operator intentionally wants only deterministic Telegram slash commands
for setup or QA, use:

```bash
bin/weave onboard --slash-only
```

In slash-only mode, `/status`, `/apps`, and `/help` can work while normal
Hermes chat remains blocked.

## Telegram Gateway Dependency Install

The recommended human path remains:

```bash
bin/weave onboard
```

The guided command builds the Hermes image with the messaging dependency set,
then asks for a dedicated Telegram bot token and numeric Telegram user id. It
writes the token only into the local Hermes `.env` file with private file
permissions.

For host-local fallback, use:

```bash
bin/weave onboard --local --install-hermes
```

The scriptable path has two required parts. First, Hermes must be installed
with the gateway dependencies available:

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

After default container configuration, verify the gateway path:

```bash
bin/weave status
bin/weave start
```

For host-local fallback, verify with:

```bash
hermes status
hermes gateway status
cd <foundation-gateway-workdir>
hermes gateway run
```

The owner must still send the first Telegram message to the bot before Hermes
can learn the owner chat target.

After host-local provisioning, this stricter check should pass:

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

The profile-only backend command without container build, host install, or
gateway flags does not:

- download runtime binaries
- run package managers
- install launch services, cron jobs, or service units
- read existing `.env` files during default runtime setup
- load credentials during default runtime setup
- contact private gateways
- mutate hosted runtime state
- claim a remote runtime or production service exists

The default guided container path does clone upstream source and install Python
packages inside the Docker image build. The host-local `--install-hermes` path
does the same inside ignored local runtime state. Both paths keep the same
service, secret, gateway, shell-startup, and production boundaries.

The `--gateway-token-file` setup path is the approval-gated gateway setup
step. It may read the owner-supplied token file and write Hermes local
environment state, but it still does not start the gateway, install autostart,
or perform external sends.

Runtime pairing, gateway live-run approval, autostart, production deploys,
paid jobs, credential changes, public posts, and external sends remain separate
approval gates.

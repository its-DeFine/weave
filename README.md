# WEAVE

![WEAVE runtime hero](assets/weave-hero.png)

WEAVE is a runtime and agent-company package for building applications from
agent-run product lifecycle work.

## Quickstart

Clone the repo and follow [docs/quickstart.md](docs/quickstart.md) to validate
the package, run the test suite, execute a lifecycle dry-run, and configure the
approval-gated Telegram gateway. The base validation path needs no API keys and
no network calls; guided onboarding builds a pinned Hermes container when Docker
is available. See [docs/runtime-home.md](docs/runtime-home.md) for the durable
runtime-home contract.

## Version

Current public package version: `2026.05.13-console`.
Intended release tag: `v2026.05.13-console`.

## Missions

A WEAVE mission is a scoped unit of work dispatched to an agent, tracked
through the lifecycle plus the post-KPI growth loop, and settled with a credit
grant on verified completion. See
[docs/missions/MISSION_TEMPLATE.md](docs/missions/MISSION_TEMPLATE.md) for the
mission format, required fields, and a worked example.

The current release shape is deliberately narrow:

- WEAVE is a standalone repository.
- Hermes is the active runtime and CEO agent dependency.
- WEAVE supplies the company package, lifecycle, primitives, adapter boundaries,
  agent skill contracts, and validation tests.

## Repository Layout

```text
docs/                  Public documentation and replication architecture.
packages/weave-tool/   Hermes-default WEAVE company package.
scripts/               Local validation, smoke, runtime, and gateway scripts.
tests/                 Public-safe validation tests.
```

## Validate

Validate the WEAVE company package:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
```

Run the public-safe test suite:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Run the lifecycle and deterministic Telegram command smoke:

```bash
python3 scripts/runtime_smoke.py
```

Run guided onboarding:

```bash
bin/weave onboard
```

The guided command first checks whether normal Hermes setup has already been
confirmed. After that gate passes, it builds a pinned Hermes container, creates
the ignored `runs/runtime-home` layout, prepares the Hermes gateway context,
explains the dedicated Telegram bot requirement, hides token input, and
configures the deterministic command plugin without printing secrets. It does
not start the gateway, install autostart, or perform external sends.

Normal Hermes chat is owned by Hermes. Configure providers and verify chat
through the normal Hermes setup flow first, then tell WEAVE that Hermes is
ready:

```bash
HERMES_HOME=runs/runtime-home/hermes-home hermes setup --portal
HERMES_HOME=runs/runtime-home/hermes-home hermes model
bin/weave onboard --hermes-ready
```

To complete setup for deterministic slash commands only, use:

```bash
bin/weave onboard --slash-only
```

After onboarding, run the containerized gateway:

```bash
bin/weave start
bin/weave status
bin/weave stop
```

Move reviewable local state without exporting credentials:

```bash
bin/weave export-runtime --out runtime-export.tar.gz
bin/weave import-runtime runtime-export.tar.gz --runtime-home runs/runtime-home
bin/weave verify-runtime --runtime-home runs/runtime-home
```

For a host-local fallback instead of the default container, install the real
pinned upstream Hermes Agent into ignored local state:

```bash
bin/weave onboard --local --install-hermes
```

For CI and operator automation, the backend script remains available:

```bash
python3 scripts/setup_runtime.py \
  --gateway-token-file <owner-approved-token-file> \
  --gateway-allowed-users <numeric-telegram-user-id>
```

Gateway setup defaults to `--autonomy-mode yolo`. In this mode Hermes proceeds
without routine confirmation for non-gated local work, while hard-gated actions
still require Hermes to ask for owner authorization through the Telegram LLM
conversation before acting.

Validate the public-safe workstation context sync sample:

```bash
python3 scripts/context_sync_contract_smoke.py
```

Expected package shape:

```text
valid WEAVE company package: weave
version: 2026.05.13-console
agents: 7
tasks: 9
skills: 13
primitives: 9
prompt_packs: 1
```

## Runtime Model

WEAVE is packaged as an importable AI-operated company:

```text
WEAVE repo
  -> packages/weave-tool
  -> Hermes CEO/runtime agent
  -> WEAVE lifecycle tasks, skills, and primitives
  -> deterministic Telegram slash commands for state
```

The durable state lives in a runtime home:

```text
runs/runtime-home/
  runtime-profile.json
  weave-state/
  hermes-home/
```

The container and gateway process are replaceable. App work, lifecycle
artifacts, ledgers, profiles, source maps, and reviewable Hermes configuration
live in the runtime home. Raw gateway secrets are not exported by default.

The first-slice REST skeleton can be served locally with:

```bash
python3 scripts/weave_runtime_api.py
```

It binds to loopback, requires the ignored generated local token, and delegates
to the same root, app, ledger, foundation, and stage-derivation primitives used
by the tests.

This proves a local instantiation path for the lifecycle runtime. It does not
claim that a VM service, hosted runtime, paid model route, or production
deployment is installed.

Telegram is the operator surface for this release. Normal Telegram messages go
to Hermes only after normal Hermes setup has been confirmed. WEAVE slash
commands are intercepted by the gateway and answered from deterministic local
runtime state with `deterministic: true` and `llm_used: false`.

Available commands:

| Command | Purpose |
|---|---|
| `/start` | Show the deterministic WEAVE command surface. |
| `/help` | List deterministic WEAVE commands. |
| `/status` | Show runtime readiness, app count, blocked app count, and next action. |
| `/sources` | Show runtime source map, history surfaces, and active/stale/missing state. |
| `/apps` | List apps, lifecycle stage per app, and foundation gate state. |
| `/app <app_id>` | Show one app's stage, foundation gate, contract version, artifact count, and latest changes. |
| `/blockers` | Show apps that need owner or Hermes action. |
| `/changes [app_id]` | Show latest recorded changes for one app or all apps. |
| `/next` | Show the next deterministic owner-visible action. |

See [docs/telegram-slash-commands.md](docs/telegram-slash-commands.md) for the
full command contract and response shape.

Hermes carries a public prompt/spec package at
`packages/weave-tool/prompts/hermes-gestalt-runtime-pack/`. That pack is the
reviewable contract for moving a user from raw app idea to Gestalt Kernel,
Gestaltian Contract, Premortem, Build-Ready Handoff Packet, bounded
implementation, validation, and Contract Update.

Use `bin/weave onboard` for the human setup flow. It builds a local Docker
image from `container/hermes/Dockerfile` at pinned upstream Hermes commit
`5921d667855880b0aa2083a50f001748aed52f3e`, then records the image in
`runs/runtime-home/runtime-profile.json`. Use `scripts/setup_runtime.py` for
automation, CI, and non-interactive runtime profiles. Add
`--local --install-hermes` to clone the real upstream Nous Hermes Agent into an
isolated venv under
`runs/hermes-agent/`, install the CLI package there, and attach that proof to
the runtime profile. These install paths use outbound network access, but they
do not install services, read secrets outside the explicit Telegram token flow,
contact private gateways, pair Telegram without owner input, or claim that a
hosted runtime exists.

For Telegram, guided onboarding asks for a dedicated bot token and numeric
Telegram user id. Token input is hidden and copied only into local Hermes
environment state. Provider credentials and route verification stay inside
Hermes; WEAVE records only non-secret setup readiness state with
`bin/weave hermes status`. It does not start the gateway, install autostart, or
place secrets in tracked files and public artifacts. The narrower
`scripts/setup_gateway.py` helper is available when Hermes is already
installed and only gateway environment configuration is needed.

The public workstation context sync contract in
`docs/workstation-context-sync.md` shows how completed local work can be
recorded into a runtime ledger as evidence and decisions. The included sample
uses public-safe paths only and performs no network writes.

The main lifecycle is:

1. Intent.
2. Research.
3. Selection.
4. Plan.
5. Engineering.
6. QA.
7. KPI Setup.
8. Marketing.

After KPI Setup, the growth loop can run under Marketing:

- Iteration: build, deploy, and record feedback-driven changes.
- Analysis: read usage and feedback, then recommend the next iteration.

Research starts only after Intent is explicit. Engineering starts only after
Selection and Plan are recorded. Marketing and the local growth loop both start
from KPI Setup; external distribution remains approval-gated.

## Boundaries

This repository intentionally does not include:

- private WEAVE operating substrate
- private payment, custody, funding, or accounting material
- VM, SSH, VPN, private-network, or host-specific proof details
- API keys, gateway tokens, OAuth tokens, private keys, or seed material
- generated private proof logs
- claims that Livepeer-native output is proven before output evidence exists

## Replication

Start with [WEAVE Replication Architecture](docs/replication-architecture.md).

## License

MIT. See [LICENSE](LICENSE).

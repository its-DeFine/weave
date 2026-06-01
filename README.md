# WEAVE

![WEAVE runtime hero](assets/weave-hero.png)

WEAVE is a runtime and agent-company package for building applications from
agent-run product lifecycle work.

## Quickstart

Clone the repo and follow [docs/quickstart.md](docs/quickstart.md) to validate
the package, run the test suite, execute a lifecycle dry-run, and configure the
approval-gated Telegram gateway. The base validation path needs no API keys and
no network calls; the optional real Hermes provisioning path fetches the pinned
upstream Hermes source and Python packages.

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
operator-ui/           Public-safe local operator console sample.
packages/weave-tool/   Hermes-default WEAVE company package.
scripts/               Local validation, smoke, and UI serving scripts.
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

Run the lifecycle and operator UI smoke:

```bash
python3 scripts/runtime_smoke.py
```

Set up the local Hermes runtime profile:

```bash
python3 scripts/setup_runtime.py
```

Setup also creates an ignored WEAVE root and a Hermes gateway workdir containing
generated `AGENTS.md`/`SOUL.md` enforcement files. Start the Telegram gateway
from the generated `foundation_gateway_workdir` path printed by setup so Hermes
loads the unskippable foundation onboarding gate before app work. When gateway
flags are supplied, setup also writes Hermes `terminal.cwd` and a runtime system
prompt so gateway sessions use that context.

Provision the real pinned upstream Hermes Agent into ignored local state:

```bash
python3 scripts/setup_runtime.py --install-hermes
```

Configure the Telegram gateway from an owner-approved token file:

```bash
python3 scripts/setup_runtime.py \
  --gateway-token-file <owner-approved-token-file> \
  --gateway-allowed-users <numeric-telegram-user-id>
```

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
  -> operator-ui
  -> Hermes CEO/runtime agent
  -> WEAVE lifecycle tasks, skills, and primitives
```

The operator UI is a static public-safe console that reads
`operator-ui/sample-runtime.json`. Run it locally with:

```bash
python3 scripts/run_operator_ui.py
```

The first-slice REST skeleton can be served locally with:

```bash
python3 scripts/weave_runtime_api.py
```

It binds to loopback, requires the ignored generated local token, and delegates
to the same root, app, ledger, foundation, and stage-derivation primitives used
by the tests.

This proves a local instantiation path for the lifecycle console. It does not
claim that a VM service, hosted runtime, paid model route, or production
deployment is installed.

Hermes carries a public prompt/spec package at
`packages/weave-tool/prompts/hermes-gestalt-runtime-pack/`. That pack is the
reviewable contract for moving a user from raw app idea to Gestalt Kernel,
Gestaltian Contract, Premortem, Build-Ready Handoff Packet, bounded
implementation, validation, and Contract Update.

Use `scripts/setup_runtime.py` to write an ignored local runtime profile and to
check whether a Hermes executable is already on `PATH`. Add `--install-hermes`
to clone the real upstream Nous Hermes Agent at pinned commit
`5921d667855880b0aa2083a50f001748aed52f3e`, create an isolated venv under
`runs/hermes-agent/`, install the CLI package there, and attach that proof to
`runs/runtime-profile.json`. This optional install path uses outbound network
access, but it does not install services, read secrets, contact private
gateways, pair Telegram, or claim that a hosted runtime exists.

For Telegram, install Hermes with `--hermes-extras cli,messaging`, then run
`scripts/setup_runtime.py` with `--gateway-token-file` and either an explicit
numeric user allowlist or temporary discovery mode. This writes only local
Hermes environment state and does not start the gateway, install autostart, or
place secrets in tracked files and public artifacts. The narrower
`scripts/setup_gateway.py` helper is also available when Hermes is already
installed.

The public workstation context sync contract in
`docs/workstation-context-sync.md` shows how completed local work can be
recorded into a runtime ledger as evidence and decisions. The included sample
uses public-safe paths only and performs no network writes.

The console includes an app selector, draft app creation, lifecycle stage
track, a parallel iteration-analysis loop below Marketing, Plan/Review/Execute
cards, blocker map, evidence binder, open decisions, KPI snapshot, append-only
event view, foundation gate view, changes per app, REST health, and transcript
summary. It uses sample data only, performs no network writes, and is not a
communication surface.

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

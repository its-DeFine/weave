# WEAVE

![WEAVE runtime hero](assets/weave-hero.png)

WEAVE is a runtime and agent-company package for building applications from
agent-run product lifecycle work.

## Quickstart

Clone the repo and follow [docs/quickstart.md](docs/quickstart.md) to validate
the package, run the test suite, and execute a lifecycle dry-run — no API keys
or network access required.

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
- OpenClaw remains the explicit fallback runtime adapter.
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
skills: 12
primitives: 9
```

## Runtime Model

WEAVE is packaged as an importable AI-operated company:

```text
WEAVE repo
  -> packages/weave-tool
  -> operator-ui
  -> Hermes CEO/runtime agent
  -> OpenClaw fallback runtime adapter
  -> WEAVE lifecycle tasks, skills, and primitives
```

The operator UI is a static public-safe console that reads
`operator-ui/sample-runtime.json`. Run it locally with:

```bash
python3 scripts/run_operator_ui.py
```

This proves a local instantiation path for the lifecycle console. It does not
claim that a VM service, hosted runtime, paid model route, or production
deployment is installed.

The public workstation context sync contract in
`docs/workstation-context-sync.md` shows how completed local work can be
recorded into a runtime ledger as evidence and decisions. The included sample
uses public-safe paths only and performs no network writes.

The console includes an app selector, draft app creation, lifecycle stage
track, a parallel iteration-analysis loop below Marketing, runtime-agent
message drafts, Plan/Review/Execute cards, blocker map, evidence binder, open
decisions, KPI snapshot, and command preview. It uses sample data only and
performs no network writes.

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

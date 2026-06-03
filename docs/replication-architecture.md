# WEAVE Replication Architecture

Status: public-safe architecture note
Audience: builders who want to reproduce the current WEAVE setup
Current recommendation: standalone WEAVE repository, Hermes as the default runtime agent

## Short Answer

WEAVE is a standalone agent-company package and runtime toolkit operated by
Hermes, with Local Fallback preserved as a fallback runtime. WEAVE supplies the
business lifecycle, agent roles, primitives, tasks, evidence contracts, and
future Livepeer adapter boundaries.

The current public package version is `2026.05.13-console`, intended to be
tagged as `v2026.05.13-console`.

The current architecture is:

```text
WEAVE repo
  -> weave-tool package
  -> Hermes CEO/runtime agent
  -> WEAVE lifecycle tasks, skills, and primitives
```

## What Each Layer Owns

| Layer | Owned By | Responsibility |
|---|---|---|
| Hermes | Default runtime dependency | Gestalt-to-Artifact app guidance, agent execution, approved tools, memory/session behavior, command-bus coordination, and operator workflow. |
| Local Fallback | Fallback runtime dependency | Legacy or owner-directed recovery execution when Hermes is unavailable. |
| WEAVE | This repository | Company package, lifecycle, primitive registry, application tasks, evidence gates, public docs, and adapter boundaries. |
| Livepeer or PymtHouse gateways | External capability layer | Future paid or live media pipeline execution after funding, credential, and output-evidence gates. |

## Runtime Boundary

WEAVE should depend on the Hermes default runtime path for this release. The
public repository provides the package, prompt/spec pack, and operating layer.

| Area | WEAVE Scope |
|---|---|---|
| Product shape | AI-operated application business focused on agent-run product lifecycle work. |
| Company content | A concrete WEAVE company with CEO, research, engineering, QA, growth, and analytics roles. |
| Lifecycle | Defines Intent -> Research -> Selection -> Plan -> Engineering -> QA -> KPI Setup -> Marketing, with Iteration and Analysis as a parallel growth loop under Marketing. |
| Primitives | Ships a primitive registry and deterministic Telegram status path that can later map to adapter execution. |
| Runtime agent | Uses Hermes as the CEO/runtime agent directly, with Local Fallback as fallback. |
| Evidence | Requires lifecycle-stage evidence, omission records, boundary notes, and acceptance gates. |
| Livepeer integration | Treated as an external adapter boundary with payment and output proof gates. |

## Recommended Repository Shape

The public WEAVE repository should remain standalone:

```text
weave/
  docs/
    replication-architecture.md
    month1/
  weave-tool/
    COMPANY.md
    agents/
    projects/
    skills/
    primitives/
    scripts/
  scripts/
```

For a public release, `weave-tool/` is the minimum reproducible package.
Telegram slash commands are the public-safe operator status surface. Private
runner implementations can be published only after private paths,
host-specific scripts, secrets, generated runs, and internal evidence are
scrubbed.

## Replication Path

The public replication path should be:

1. Clone the WEAVE repository.
2. Validate the WEAVE company package.
3. Run the runtime smoke.
4. Run `bin/weave onboard` to build the pinned Hermes container and prepare
   local WEAVE/Hermes state.
5. Configure the dedicated Telegram gateway when live communication is needed.
6. Start the containerized gateway with `bin/weave start`.
7. Use deterministic slash commands to inspect app status.
8. Run or inspect the Hermes CEO/runtime agent instructions and Gestalt Runtime Pack.
9. Run the first lifecycle wedge: Research admits one opportunity before Engineering starts.

The WEAVE repository should never require committed secrets. Local credentials
belong in the user's secret store, environment, or Hermes profile.

## Minimum Public Commands

These commands are intentionally local and non-secret.

Validate the WEAVE company package:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
```

Run the runtime smoke:

```bash
python3 scripts/runtime_smoke.py
```

Expected shape:

```text
valid WEAVE company package: weave
version: 2026.05.13-console
agents: 7
tasks: 9
skills: 13
primitives: 9
prompt_packs: 1
telegram command smoke: ok
smoke: ok
```

Run the public test suite:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Public Release Boundaries

Allowed to include:

- `weave-tool/` package files
- public docs under `docs/`
- deterministic Telegram slash-command status primitives
- validators and tests that do not require private infrastructure
- non-secret examples for Hermes configuration

Keep out of the public release:

- API keys, gateway tokens, OAuth tokens, private keys, and seed material
- hostnames, private IPs, SSH jump details, and local machine paths
- generated run logs that may contain environment details
- funding instructions that assume a private account or custody setup
- claims that Livepeer pipeline output is proven before output evidence exists

## Acceptance Standard For Replication

A builder has replicated the current setup when all of these are true:

- WEAVE validates as a company package.
- The runtime smoke passes.
- Telegram slash commands return deterministic local state.
- Hermes is configured as the CEO/runtime agent.
- Intent is the first active lifecycle gate.
- Engineering work starts only after Research, Selection, and Plan are recorded.

That is the current reproducible baseline. Persistent scheduling, public
deployment, paid gateway jobs, funding, and Livepeer-native output are separate
approval and evidence gates.

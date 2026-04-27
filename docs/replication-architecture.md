# WEAVE Replication Architecture

Status: public-safe architecture note
Audience: builders who want to reproduce the current WEAVE setup
Current recommendation: standalone WEAVE repository, Paperclip as upstream dependency, OpenClaw as runtime agent

## Short Answer

WEAVE is not a Paperclip fork.

WEAVE is a standalone agent-company package and runtime toolkit that can be
imported into Paperclip. Paperclip supplies the company control plane. OpenClaw
supplies the agent execution runtime. WEAVE supplies the business lifecycle,
agent roles, primitives, tasks, evidence contracts, and future Livepeer adapter
boundaries.

The current architecture is:

```text
WEAVE repo
  -> weave-tool package
  -> Paperclip company import
  -> openclaw_gateway adapter
  -> OpenClaw CEO/runtime agent
  -> WEAVE lifecycle tasks and primitives
```

## What Each Layer Owns

| Layer | Owned By | Responsibility |
|---|---|---|
| Paperclip | Upstream dependency | Company model, agents, projects, issues, routines, approvals, budgets, activity, secrets, and adapter contracts. |
| OpenClaw | Runtime dependency | Codex-backed agent execution, tools, memory/session behavior, gateway invocation, and operator workflow. |
| WEAVE | This repository | Company package, lifecycle, primitive registry, application tasks, evidence gates, public docs, and adapter boundaries. |
| Livepeer or PymtHouse gateways | External capability layer | Future paid or live media pipeline execution after funding, credential, and output-evidence gates. |

## How WEAVE Differs From Paperclip

WEAVE should not change Paperclip core behavior for the first open-source
release. The difference is in the package and operating layer.

| Area | Paperclip | WEAVE |
|---|---|---|
| Product shape | General AI-operated company runtime. | AI-operated application business focused on realtime media primitives. |
| Company content | Generic importable companies. | A concrete WEAVE company with CEO, research, engineering, QA, growth, and analytics roles. |
| Lifecycle | Provides issues, projects, routines, and policies. | Defines Research -> Engineering -> QA -> Outreach -> KPI/Analytics -> Iteration. |
| Primitives | Does not define WEAVE product primitives. | Ships a primitive registry and browser-native runtime path that can later map to Livepeer pipelines. |
| Runtime agent | Supports adapters. | Uses OpenClaw as the CEO/runtime agent through `openclaw_gateway`. |
| Evidence | Provides logs and activity surfaces. | Requires lifecycle-stage evidence, omission records, boundary notes, and acceptance gates. |
| Livepeer integration | Out of scope for Paperclip core. | Treated as an external adapter boundary with payment and output proof gates. |

## Recommended Repository Shape

The public WEAVE repository should remain standalone:

```text
weave/
  docs/
    replication-architecture.md
    month1/
  weave-tool/
    COMPANY.md
    .paperclip.yaml
    agents/
    projects/
    skills/
    primitives/
    scripts/
  weave-visual-mvp/
  agent-lab/
```

For a public release, `weave-tool/` is the minimum reproducible package.
`weave-visual-mvp/` is the local browser-native application/runtime surface.
`agent-lab/` can be published only after private paths, host-specific scripts,
secrets, generated runs, and internal evidence are scrubbed.

## Why We Should Avoid A Paperclip Fork Now

A fork is useful only when WEAVE needs to change Paperclip core semantics. The
current proof does not require that.

Keeping Paperclip upstream gives WEAVE a cleaner open-source story:

- builders can update Paperclip independently
- WEAVE remains focused on company logic and application primitives
- adapter fixes can be upstreamed or kept as a small bridge
- the release does not inherit responsibility for maintaining a general company runtime

Forking becomes reasonable later only if one of these becomes true:

- WEAVE needs a Paperclip feature that upstream will not accept
- the OpenClaw adapter contract must change in a way that cannot be expressed as a plugin or compatibility bridge
- WEAVE requires a stable embedded Paperclip runtime for distribution
- release users need one binary/container with Paperclip vendored inside

## Current Compatibility Bridge

The current private proof uses a loopback-only compatibility bridge between
Paperclip and OpenClaw.

Purpose:

- keep Paperclip and OpenClaw source trees unmodified
- translate the current Paperclip `openclaw_gateway` payload into the shape the OpenClaw gateway accepts
- preserve WEAVE task context in the prompt
- keep gateway tokens outside the repository

This bridge should be treated as release scaffolding until one of these happens:

- Paperclip adjusts the adapter payload
- OpenClaw accepts the additional metadata field
- WEAVE publishes a small dedicated adapter package
- WEAVE vendors the bridge as a documented local-only component

## Replication Path

The public replication path should be:

1. Install or clone Paperclip from its upstream repository.
2. Install OpenClaw and authenticate the model provider in the local runtime.
3. Clone the WEAVE repository.
4. Validate the WEAVE company package.
5. Start Paperclip in a local/private mode.
6. Import `weave-tool/` as a Paperclip company package.
7. Configure Paperclip's `openclaw_gateway` adapter with a local OpenClaw gateway URL and token.
8. Run a marker issue proof: Paperclip wakes the OpenClaw CEO, OpenClaw posts the marker, and the issue closes.
9. Run the first lifecycle wedge: Research admits one opportunity before Engineering starts.

The WEAVE repository should never require committed secrets. Local credentials
belong in the user's secret store, environment, Paperclip secret storage, or
OpenClaw profile.

## Minimum Public Commands

These commands are intentionally local and non-secret.

Validate the WEAVE company package:

```bash
python3 weave-tool/scripts/validate_company_package.py weave-tool
```

Expected shape:

```text
valid WEAVE company package: weave
agents: 6
tasks: 6
primitives: 9
```

Run the local test suite if `agent-lab/` is included in the release:

```bash
python3 -m unittest discover -s agent-lab/tests -p 'test_*.py'
```

Run a syntax check for the Paperclip/OpenClaw proof harness if it is included:

```bash
node --check agent-lab/library/paperclip_openclaw_gateway_e2e.mjs
```

## Public Release Boundaries

Safe to include:

- `weave-tool/` package files
- public docs under `docs/`
- browser-native runtime primitives
- validators and tests that do not require private infrastructure
- non-secret examples for Paperclip and OpenClaw configuration

Keep out of the public release:

- API keys, gateway tokens, OAuth tokens, private keys, and seed material
- hostnames, private IPs, SSH jump details, and local machine paths
- generated run logs that may contain environment details
- funding instructions that assume a specific treasury or private account
- claims that Livepeer pipeline output is proven before output evidence exists

## Acceptance Standard For Replication

A builder has replicated the current setup when all of these are true:

- WEAVE validates as a company package.
- Paperclip imports the WEAVE package with six `openclaw_gateway` agents.
- OpenClaw is configured as the CEO/runtime agent.
- A marker issue can be assigned from Paperclip and completed by OpenClaw.
- Research is the first active lifecycle gate.
- Engineering work starts only after Research admits one opportunity.

That is the current reproducible baseline. Persistent scheduling, public
deployment, paid gateway jobs, funding, and Livepeer-native output are separate
approval and evidence gates.

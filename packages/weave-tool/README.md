# WEAVE Tool Company Package

Status: public package skeleton
Target runtime: OpenClaw solo
CEO agent: OpenClaw

This directory packages WEAVE as an AI-operated business that can be imported
or translated into an agent runtime.

Current public package version: `2026.05.13-console`.
Intended release tag: `v2026.05.13-console`.

The package keeps three layers separate:

- OpenClaw-first runtime shape: company, agents, projects, tasks, and lifecycle gates.
- OpenClaw execution identity: the CEO/operator agent and lifecycle instructions.
- WEAVE domain logic: lifecycle gates, primitive registry, evidence boundaries, and future Livepeer adapter mapping.

This package validates as an OpenClaw-first lifecycle package. Legacy
runtime import hints are outside this public package. The package does not
contain gateway URLs, tokens, API keys, private keys, funding instructions, or
production service configuration.

Agent skills are public capability contracts. A private runtime may map those
contracts to concrete tools, but those tool mappings stay outside this package.

## Validate

From the repository root:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
```

The repository-level runtime smoke also checks the public-safe operator UI
sample:

```bash
python3 scripts/runtime_smoke.py
```

Expected output:

```text
valid WEAVE company package: weave
version: 2026.05.13-console
agents: 6
tasks: 9
skills: 11
primitives: 9
```

## Current Package Contents

- `COMPANY.md`: WEAVE company definition.
- `agents/ceo-openclaw/AGENTS.md`: OpenClaw CEO identity and operating rules.
- `agents/*/AGENTS.md`: lifecycle role shells that report to the CEO.
- `projects/askuno-runtime-proof/PROJECT.md`: first admitted application project.
- `projects/askuno-runtime-proof/tasks/*/TASK.md`: starter lifecycle task graph.
- `skills/*/SKILL.md`: portable development and lifecycle skill contracts
  referenced by agents and tasks.
- `primitives/registry.json`: local primitive catalog and future adapter mapping.
- `scripts/validate_company_package.py`: local package validator.

## Runtime Boundary

Allowed now:

- edit package files
- validate package completeness
- map lifecycle stages to tasks and routines
- keep primitive registry aligned with the operator-console runtime
- run the OpenClaw-first lifecycle package locally
- inspect the public-safe operator UI sample from the repository root

Approval-gated later:

- OpenClaw gateway pairing
- adding gateway URLs or gateway credentials
- paid Livepeer/PymtHouse jobs
- public marketing or external sends
- funding, top-ups, swaps, or production deploys

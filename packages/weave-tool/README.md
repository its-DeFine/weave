# WEAVE Tool Company Package

Status: public package skeleton
Target runtime: Hermes default
CEO agent: Hermes

This directory packages WEAVE as an AI-operated business that can be imported
or translated into an agent runtime.

Current public package version: `2026.05.13-console`.
Intended release tag: `v2026.05.13-console`.

The package keeps three layers separate:

- Hermes-default runtime shape: company, agents, projects, tasks, and lifecycle gates.
- Hermes execution identity: the CEO/operator agent and Gestalt Runtime Pack.
- WEAVE domain logic: lifecycle gates, primitive registry, evidence boundaries, and future Livepeer adapter mapping.

This package validates as a Hermes-default lifecycle package. Legacy fallback
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

The repository-level runtime smoke also checks the first-slice local root/app
contract and deterministic Telegram slash-command output:

```bash
python3 scripts/runtime_smoke.py
```

To run the guided local onboarding flow from the repository root:

```bash
bin/weave onboard
```

This also writes a generated Hermes gateway workdir under ignored local state.
Run the live Telegram gateway from that workdir so Hermes loads the
unskippable foundation onboarding gate before app work. Gateway setup also
writes Hermes `terminal.cwd` and a runtime system prompt when gateway flags are
supplied.

To provision the real pinned upstream Hermes Agent into ignored local state:

```bash
bin/weave onboard --install-hermes
```

For CI or operator automation, the backend setup script remains available:

```bash
python3 scripts/setup_runtime.py \
  --gateway-token-file <owner-approved-token-file> \
  --gateway-allowed-users <numeric-telegram-user-id>
```

Gateway setup defaults to `--autonomy-mode yolo`: Hermes proceeds on non-gated
local work without routine confirmation, while hard-gated actions still require
owner authorization through the Telegram LLM conversation.

Expected output:

```text
valid WEAVE company package: weave
version: 2026.05.13-console
agents: 7
tasks: 9
skills: 13
primitives: 9
prompt_packs: 1
```

## Current Package Contents

- `COMPANY.md`: WEAVE company definition.
- `agents/ceo-hermes/AGENTS.md`: Hermes CEO identity and operating rules.
- `agents/ceo-fallback/AGENTS.md`: Local Fallback fallback identity and operating rules.
- `agents/*/AGENTS.md`: lifecycle role shells that report to the CEO.
- `projects/askuno-runtime-proof/PROJECT.md`: first admitted application project.
- `projects/askuno-runtime-proof/tasks/*/TASK.md`: starter lifecycle task graph.
- `skills/*/SKILL.md`: portable development and lifecycle skill contracts
  referenced by agents and tasks.
- `prompts/hermes-gestalt-runtime-pack/*`: Hermes prompt/spec package for
  raw idea to contract, handoff, implementation, validation, and contract
  update.
- `primitives/registry.json`: local primitive catalog and future adapter mapping.
- Repository `bin/weave`: human-facing CLI launcher.
- Repository `scripts/weave_cli.py`: guided onboarding CLI backed by the
  public-safe runtime setup scripts.
- `scripts/validate_company_package.py`: local package validator.
- Repository `scripts/setup_runtime.py`: local runtime profile and ignored
  WEAVE root setup, generated Hermes foundation onboarding workdir, and opt-in
  pinned Hermes provisioning.
- Repository `scripts/setup_gateway.py`: narrow approval-gated Telegram
  gateway environment helper used by repository setup when gateway flags are
  supplied.
- Repository `scripts/provision_hermes.py`: explicit local Nous Hermes Agent
  clone, pinned checkout, venv install, wrapper, and proof profile.
- Repository `scripts/weave_runtime_slice.py`: public-safe first-slice runtime
  primitives for root setup, app registry, ledger, foundation gate, stage
  derivation, REST dispatch, and Telegram slash-command status.
- Repository `scripts/weave_runtime_api.py`: loopback-only REST skeleton that
  requires the ignored generated local token.

## Runtime Boundary

Allowed now:

- edit package files
- validate package completeness
- map lifecycle stages to tasks and routines
- keep primitive registry aligned with the deterministic runtime status surface
- run the Hermes-default lifecycle package locally
- provision pinned upstream Hermes locally under ignored `runs/`
- configure Hermes Telegram gateway environment from an owner-approved token
  file outside tracked state
- inspect app status through deterministic Telegram slash commands

Approval-gated later:

- Hermes runtime pairing
- gateway live-run approval, autostart, or service installation
- Local Fallback gateway pairing
- adding gateway URLs or gateway credentials to tracked package files
- paid Livepeer/PymtHouse jobs
- public marketing or external sends
- funding, top-ups, swaps, or production deploys

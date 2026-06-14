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

To try the full local conversation-to-app workflow that creates a concrete app
artifact, use the repository-level dogfood runner:

```bash
mkdir -p runs/full-conversation-app-dogfood
python3 scripts/full_conversation_app_dogfood.py \
  --report-out runs/full-conversation-app-dogfood/report.json \
  --output-dir runs/full-conversation-app-dogfood/artifacts \
  --transcript-out runs/full-conversation-app-dogfood/transcript.md
```

It generates the `Pocket Orchard` static app and review artifacts locally. This
is scripted local proof, not live Hermes/Telegram proof.

To run the guided local onboarding flow from the repository root:

```bash
bin/weave onboard
```

Recommended first inspection commands:

```bash
bin/weave help
bin/weave doctor
bin/weave eval --list
bin/weave onboard --dry-run
bin/weave command /status
```

WEAVE now has four explicit setup modes: managed container, existing-Hermes
attach, slash-only deterministic commands, and host-local fallback. The default
managed-container path builds the pinned Hermes image, writes a generated Hermes
gateway workdir under ignored local state, and configures the deterministic
Telegram command plugin. If Hermes already exists and can chat, use
`bin/weave onboard --existing-hermes --hermes-ready` or
`bin/weave attach-hermes --hermes-ready` to attach only the deterministic WEAVE
state/plugin/config without installing Hermes or mutating provider auth. Start
the live Telegram gateway with `bin/weave start` so Hermes loads the
unskippable foundation onboarding gate before app work. Gateway setup also
writes Hermes `terminal.cwd` and a runtime system prompt when gateway flags are
supplied.

To inspect or stop the containerized gateway:

```bash
bin/weave status
bin/weave stop
```

For a host-local fallback instead of the default container, provision the real
pinned upstream Hermes Agent into ignored local state:

```bash
bin/weave onboard --local --install-hermes
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
eval_contracts: 11
```

## Current Package Contents

- `COMPANY.md`: WEAVE company definition.
- `agents/ceo-hermes/AGENTS.md`: Hermes CEO identity and operating rules.
- `agents/ceo-fallback/AGENTS.md`: Local Fallback fallback identity and operating rules.
- `agents/*/AGENTS.md`: lifecycle role shells that report to the CEO.
- `projects/askuno-runtime-proof/PROJECT.md`: historical/starter worked
  example. It is not the current Month 1 deliverable-review anchor.
- `projects/askuno-runtime-proof/tasks/*/TASK.md`: starter lifecycle task
  graph kept for package-shape continuity, not a claim that Askuno mirrors every
  current review artifact.
- `skills/*/SKILL.md`: portable development and lifecycle skill contracts
  referenced by agents and tasks.
- `prompts/hermes-gestalt-runtime-pack/*`: Hermes prompt/spec package for
  raw idea to contract, handoff, implementation, validation, and contract
  update.
- `primitives/registry.json`: cross-application lifecycle primitive catalog and
  future adapter mapping. It is consumed by package validation and review docs;
  it is not an Askuno app manifest and should not be expected to mirror Askuno's
  product surface.
- Repository `bin/weave`: human-facing CLI launcher.
- Repository `scripts/weave_cli.py`: guided onboarding CLI backed by the
  public-safe runtime setup scripts.
- Repository `scripts/weave_eval.py`: evidence-bound lifecycle and
  release-readiness eval runner.
- `evals/lifecycle/*.yaml` and `evals/release_readiness.yaml`: stage-specific
  hard gates, rubric dimensions, and decision contracts.
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

The repository-level `container/hermes/Dockerfile` is used only by the managed
container setup path (`bin/weave onboard --hermes-ready`, then
`bin/weave start`). Existing-Hermes attach, slash-only deterministic mode, and
host-local fallback do not build or require that image.

## Runtime Boundary

Allowed now:

- edit package files
- validate package completeness
- map lifecycle stages to tasks and routines
- keep primitive registry aligned with the deterministic runtime status surface
- run the Hermes-default lifecycle package locally
- run pinned upstream Hermes through the default container image
- provision pinned upstream Hermes locally under ignored `runs/` as a fallback
- configure Hermes Telegram gateway environment from an owner-approved token
  file outside tracked state
- start, stop, and inspect the containerized gateway with `bin/weave`
- inspect app status through deterministic Telegram slash commands

Approval-gated later:

- Hermes runtime pairing
- gateway live-run approval, autostart, or service installation
- Local Fallback gateway pairing
- adding gateway URLs or gateway credentials to tracked package files
- paid Livepeer/PymtHouse jobs
- public marketing or external sends
- funding, top-ups, swaps, or production deploys

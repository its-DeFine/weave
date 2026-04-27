# WEAVE Tool Company Package

Status: public package skeleton
Target runtime: Paperclip-compatible agent company
CEO agent: OpenClaw

This directory packages WEAVE as an AI-operated business that can be imported
or translated into a company runtime.

The package keeps three layers separate:

- Paperclip-compatible company shape: company, agents, projects, tasks, and routines.
- OpenClaw execution identity: the CEO/operator agent and lifecycle instructions.
- WEAVE domain logic: lifecycle gates, primitive registry, evidence boundaries, and future Livepeer adapter mapping.

This package has been validated against a temporary local Paperclip import and
OpenClaw marker proof. It is not yet deployed into a persistent public or
production Paperclip server. It does not contain gateway URLs, tokens, API keys,
private keys, funding instructions, or production service configuration.

## Validate

From the repository root:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
```

Expected output:

```text
valid WEAVE company package: weave
agents: 6
tasks: 6
primitives: 9
```

## Current Package Contents

- `COMPANY.md`: WEAVE company definition.
- `agents/ceo-openclaw/AGENTS.md`: OpenClaw CEO identity and operating rules.
- `agents/*/AGENTS.md`: lifecycle role shells that report to the CEO.
- `projects/live-visual-studio/PROJECT.md`: first admitted application project.
- `projects/live-visual-studio/tasks/*/TASK.md`: starter lifecycle task graph.
- `skills/*/SKILL.md`: portable skills referenced by agents and tasks.
- `primitives/registry.json`: local primitive catalog and future adapter mapping.
- `.paperclip.yaml`: non-secret runtime hints for routines and import mapping.
- `scripts/validate_company_package.py`: local package validator.

## Runtime Boundary

Allowed now:

- edit package files
- validate package completeness
- map lifecycle stages to tasks and routines
- keep primitive registry aligned with the browser-native runtime

Approval-gated later:

- Paperclip import into a live server
- OpenClaw gateway pairing
- adding gateway URLs or gateway credentials
- paid Livepeer/PymtHouse jobs
- public outreach or external sends
- funding, top-ups, swaps, or production deploys

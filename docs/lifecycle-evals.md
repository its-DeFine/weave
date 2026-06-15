# WEAVE Lifecycle Evals

WEAVE evals are stage contracts, not loose vibes-based reviews. Each lifecycle
stage has its own contract under `packages/weave-tool/evals/`.

A contract combines four things:

1. **Required inputs** — the artifact types a stage is expected to provide.
2. **Hard gates** — deterministic checks or target-surface proof requirements
   that can veto advancement.
3. **Rubric dimensions** — stage-specific quality scores.
4. **Decision policy** — the explicit result: `advance`, `revise`, `blocked`,
   `needs_gate_execution`, `needs_agent_review`, or `needs_human_approval`.

Hard gates win over rubric scores. A high rubric score cannot advance a stage if
required tests, scans, or proof gates fail.

## Runtime-agent QA contract

For features that depend on Hermes agents, MCP tools, gateway routing,
A2A/XMTP transport, or isolated containers/profiles, Plan and QA must use the
runtime contract in `docs/runtime-agent-qa-contract.md`.

That contract forces the missing specifics before the work is treated as
provable: isolated topology, model/provider parity, credential references,
toolsets, MCP server/tool inventory, peer identities, communication scenarios,
parallel test lanes, sender/receiver readback, teardown, and the exact allowed
claim boundary.

Without that contract, the allowed state is only `plan-only` or
`harness-built`; WEAVE must not claim live transport or runtime-agent proof.

## Commands

List available contracts:

```bash
bin/weave eval --list
```

Inspect a stage without running command gates:

```bash
bin/weave eval engineering
```

Generate the review packet an evaluator agent or human must fill:

```bash
bin/weave eval engineering --review-template > engineering-review.json
```

Run command gates and validate an evidence-bound review:

```bash
bin/weave eval engineering --run-gates --review-file engineering-review.json
```

Run the release-readiness gate before push/release:

```bash
bin/weave eval release-readiness --run-gates --review-file release-review.json
```

Use `--strict` in CI if the process should exit non-zero unless the contract can
advance. Release readiness can still return `needs_human_approval` after all
gates and rubric checks pass, because public release and push decisions stay
owner-gated.

## Review file shape

`--review-template` prints the canonical shape:

```json
{
  "schema": "weave.eval-review/v0.1",
  "stage": "Engineering",
  "reviewer": "agent-or-human-name",
  "artifact": "describe artifact or path",
  "scores": {
    "correctness": {
      "score": 4,
      "evidence": ["tests: unit suite passed"],
      "notes": ""
    }
  },
  "overall_notes": ""
}
```

Every scored dimension must include evidence. Evidence should be concrete:
command output, file path, artifact ID, source reference, runtime proof, or
review packet reference. Unsupported scores are treated as revision-required.

## Lifecycle contract files

- `packages/weave-tool/evals/lifecycle/intent.yaml`
- `packages/weave-tool/evals/lifecycle/research.yaml`
- `packages/weave-tool/evals/lifecycle/selection.yaml`
- `packages/weave-tool/evals/lifecycle/plan.yaml`
- `packages/weave-tool/evals/lifecycle/engineering.yaml`
- `packages/weave-tool/evals/lifecycle/qa.yaml`
- `packages/weave-tool/evals/lifecycle/deployment.yaml`
- `packages/weave-tool/evals/lifecycle/kpi-setup.yaml`
- `packages/weave-tool/evals/lifecycle/marketing.yaml`
- `packages/weave-tool/evals/lifecycle/iteration.yaml`
- `packages/weave-tool/evals/lifecycle/analysis.yaml`
- `packages/weave-tool/evals/release_readiness.yaml`

The files use JSON-compatible YAML so the CLI can parse them with Python's
standard library. If a future contract needs broader YAML syntax, the eval runner
can use PyYAML when it is installed.

## Agent evaluator rule

Agents may judge rubric dimensions, but they are evidence-constrained judges:

- no score without evidence;
- no advancing past failed hard gates;
- no public claim beyond verified product state;
- no release/push without the release-readiness contract and owner approval.

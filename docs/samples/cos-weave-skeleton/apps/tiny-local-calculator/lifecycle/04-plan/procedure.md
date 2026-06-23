# Plan Procedure

Use this deterministic procedure after context compaction, model changes, or worker handoff.

## Stage-Entry Contract

Before planning or executing this lifecycle stage, infer the active or requested stage from owner intent and app state, then load these contracts:

- eval: `packages/weave-tool/evals/lifecycle/plan.yaml`
- home procedure: `procedures/lifecycle/04-plan.md`
- app-local procedure: `apps/tiny-local-calculator/lifecycle/04-plan/procedure.md`
- primitive registry: `packages/weave-tool/primitives/registry.json` entry where `lifecycleStage` is `plan`
- relevant skills:
- `packages/weave-tool/skills/cos-weave/SKILL.md`
- `packages/weave-tool/skills/weave-lifecycle/SKILL.md`
- `packages/weave-tool/skills/evidence-packet/SKILL.md`
- `packages/weave-tool/skills/implementation-planning/SKILL.md`

Record the consulted contracts in proof and readback. If any contract is missing or contradicts the requested work, return `REVISE` or `BLOCKED` before acting.

## Inputs

- current app record
- lifecycle-state.json
- blockers and proof tray
- owner constraints and hard gates

## Steps

1. Observe current `plan` state, artifacts, blockers, and prior proof.
2. Validate the requested claim against lifecycle scope and non-claims.
3. Govern hard gates before any external, public, paid, credential, or destructive action.
4. Review worker output or local artifacts before accepting completion.
5. Sync readback files, proof tray, blockers, and next action.

## Review Loop

`observe -> validate -> govern -> review -> sync` is mandatory before a lifecycle step can be accepted.

## Forbidden Defaults

- do not claim full lifecycle completion from this stage alone
- do not mutate trackers, deploy, send public messages, spend money, or touch credentials without approval
- do not require hidden orchestration for default first-run WEAVE behavior

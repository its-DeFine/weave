# Research Procedure

Use this deterministic procedure after context compaction, model changes, or worker handoff.

## Stage-Entry Contract

Before planning or executing this lifecycle stage, infer the active or requested stage from owner intent and app state, then load these contracts:

- eval: `packages/weave-tool/evals/lifecycle/research.yaml`
- home procedure: `procedures/lifecycle/02-research.md`
- app-local procedure: `apps/tiny-local-calculator/lifecycle/02-research/procedure.md`
- primitive registry: `packages/weave-tool/primitives/registry.json` entry where `lifecycleStage` is `research`
- relevant skills:
- `packages/weave-tool/skills/cos-weave/SKILL.md`
- `packages/weave-tool/skills/weave-lifecycle/SKILL.md`
- `packages/weave-tool/skills/evidence-packet/SKILL.md`
- `packages/weave-tool/skills/primitive-market-research/SKILL.md`

Record the consulted contracts in proof and readback. If any contract is missing or contradicts the requested work, return `REVISE` or `BLOCKED` before acting.

Research is not only technical feasibility. When product uncertainty exists, a Research packet must make product research, alternatives, substitutes, competitors, antagonists, disconfirming evidence, and decision readiness visible before Selection.

## Inputs

- current app record
- lifecycle-state.json
- blockers and proof tray
- owner constraints and hard gates
- allowed public/local sources and source-refresh needs
- primitive-market-research output when product, user, customer, pricing, competitor, substitute, or antagonist uncertainty is material

## Required Research Outputs

- product-market facts
- target users and use cases
- customer or audience segment
- alternatives and substitutes
- competitors and antagonists
- disconfirming evidence and reasons the app may not matter
- constraints and risk gates
- technical feasibility evidence
- source list
- facts, assumptions, and opinions separated clearly
- decision readiness for Selection

## Claim Readback Buckets

Record each material claim in exactly one bucket so readback can separate proof from interpretation:

- sourced_facts
- assumptions
- opinions

Facts need source references or explicit observed evidence. Assumptions need the condition that would confirm or falsify them. Opinions need an owner/agent attribution and must not be presented as facts.

## Steps

1. Observe current `research` state, artifacts, blockers, prior proof, and product uncertainty.
2. Validate product-market facts, target users, use cases, customer or audience segment, alternatives, substitutes, competitors, antagonists, constraints, risks, and technical feasibility evidence.
3. Use `primitive-market-research` before Selection when product, user, customer, pricing, competitor, substitute, or antagonist uncertainty is material.
4. Identify disconfirming evidence and reasons the app may not matter; park attractive alternatives explicitly.
5. Separate sourced facts, assumptions, and opinions in readback and proof artifacts.
6. Govern hard gates before any external, public, paid, credential, or destructive action.
7. Review worker output or local artifacts before accepting completion.
8. Sync readback files, proof tray, blockers, and next action.

## Review Loop

`observe -> validate -> govern -> review -> sync` is mandatory before a lifecycle step can be accepted.

## Cannot Pass

- technical feasibility evidence alone when product, user, customer, alternative, substitute, competitor, antagonist, or value uncertainty is still central
- uncited pricing, competitor, API, or capability claims presented as facts
- unlabeled assumptions or opinions
- missing source list for material factual claims

## Forbidden Defaults

- do not claim full lifecycle completion from this stage alone
- do not mutate trackers, deploy, send public messages, spend money, or touch credentials without approval
- do not require hidden orchestration for default first-run WEAVE behavior
- do not require exhaustive industry reports for trivial internal tools where product fit is not part of the decision

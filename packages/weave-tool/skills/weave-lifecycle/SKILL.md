---
name: weave-lifecycle
description: Operate the WEAVE application lifecycle in stage order with explicit gates and evidence.
---

# WEAVE Lifecycle

## Use When

Use this skill when operating a WEAVE company, project, or task.

## Inputs

- target app
- current lifecycle stage
- prior stage evidence
- capability context snapshot
- open gates
- owner constraints

## Outputs

- current stage verdict
- next stage or blocker
- evidence requirement
- source refresh requirement
- approval requirement
- overwrite record when returning to an earlier stage

## Rules

- On every lifecycle entry or transition, infer the active or requested stage
  from owner intent and app state before acting. Do not ask the owner to
  classify the lifecycle stage manually.
- Load the stage-entry contract bundle before planning or executing:
  `packages/weave-tool/evals/lifecycle/<stage>.yaml`, the generated home-level
  or app-local lifecycle procedure, the matching
  `packages/weave-tool/primitives/registry.json` entry, and the relevant
  `packages/weave-tool/skills/*/SKILL.md` files.
- Record the consulted eval, procedure, primitive registry entry, and selected
  skills in proof and readback.
- Missing or contradictory stage-entry contracts return `REVISE` when locally
  fixable or `BLOCKED` when source access or an external dependency is
  unavailable. Do not proceed from memory or a vague stage label.
- Intent unlocks Research.
- Research unlocks Selection.
- Selection unlocks Plan.
- Plan unlocks Engineering.
- Engineering unlocks QA.
- QA unlocks KPI Setup.
- KPI Setup unlocks Marketing.
- KPI Setup also unlocks the local Iteration and Analysis growth loop under
  Marketing.
- Missing live stages must be emitted as unavailable or omitted with a reason.
- Volatile API, pricing, model, or capability claims require a current
  source check before stage completion.
- Approval-gated actions must stop before execution.
- Returning to an earlier stage requires an overwrite record that names the
  reason and affected downstream stages.

## Stop Conditions

- A requested stage skip lacks evidence.
- A stage regression lacks an overwrite record.
- A public or external action lacks owner approval.

## Verification

The stage state is valid when the dependency chain, evidence, and next review
action are all explicit.

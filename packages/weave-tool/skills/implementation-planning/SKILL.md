---
name: implementation-planning
description: Convert a lifecycle goal into a bounded work packet with acceptance checks and approval gates.
---

# Implementation Planning

## Use When

Use this skill before Engineering, QA, KPI Setup, Marketing, Iteration, or
Analysis work that changes artifacts, makes claims, or requests owner approval.

## Inputs

- lifecycle stage
- target app
- goal
- prior evidence
- known blockers
- allowed and forbidden areas
- local files, tools, or external surfaces involved, if any

## Outputs

- work packet
- scoped task list
- acceptance checks
- approval gates
- risk and rollback notes
- expected evidence packet shape

## Rules

- Keep one active wedge and park adjacent work.
- Name the smallest deliverable that advances the current lifecycle stage.
- Include explicit acceptance checks before execution starts.
- Mark external, paid, production, credential, and custody actions as gated.
- If a request mixes strategy and execution, split the plan before acting.
- Do not let nearby files or fixture output satisfy a live/public claim. Name
  the exact proof surface that QA must exercise.

## Stop Conditions

- Approval-gated action lacks an owner approval record.
- The goal conflicts with the current stage and no overwrite record exists.
- The requested work cannot be made public-safe.

## Verification

The plan is ready when another agent can execute it without guessing the target,
scope, boundaries, or checks.

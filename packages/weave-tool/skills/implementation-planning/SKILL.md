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
- runtime/tool/transport surfaces involved, if any

## Outputs

- work packet
- scoped task list
- acceptance checks
- runtime-agent QA contract when the work depends on Hermes agents, MCP tools,
  gateways, A2A/XMTP transport, containers, or profile-isolated runtimes
- approval gates
- risk and rollback notes
- expected evidence packet shape

## Rules

- Keep one active wedge and park adjacent work.
- Name the smallest deliverable that advances the current lifecycle stage.
- Include explicit acceptance checks before execution starts.
- Mark external, paid, production, credential, and custody actions as gated.
- If a request mixes strategy and execution, split the plan before acting.
- For agent-runtime work, include the isolated QA topology before Engineering:
  container/worktree/profile count, model/provider parity, credential reference
  shape, toolsets, MCP servers, peer identities, communication scenario,
  parallel test lanes, expected artifacts, teardown, and allowed claim boundary.
- Do not let a local queue, fixture, or direct file-copy scenario satisfy a live
  transport claim. Name the exact proof surface that QA must exercise.

## Stop Conditions

- Approval-gated action lacks an owner approval record.
- The goal conflicts with the current stage and no overwrite record exists.
- The requested work cannot be made public-safe.

## Verification

The plan is ready when another agent can execute it without guessing the target,
scope, boundaries, or checks. For runtime-agent features, readiness also requires
an explicit runtime QA contract; see `docs/runtime-agent-qa-contract.md`.

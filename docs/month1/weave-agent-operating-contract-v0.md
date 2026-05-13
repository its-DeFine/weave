# WEAVE Agent Operating Contract v0

Status: public runtime contract
Audience: runtime operators, reviewers, and builders reproducing the WEAVE package

## Purpose

This contract defines how WEAVE agents perform application lifecycle work in a
reviewable way. It is the shared operating layer for the public package:
agents may use different approved execution tools, but the lifecycle state,
evidence, gates, and review behavior must stay consistent.

## Operating Principles

- Work starts from a lifecycle stage, target application, and explicit goal.
- The agent compiles a bounded work packet before changing code or publishing.
- Every completed stage emits evidence, verification, claim limits, and the
  next review action.
- Approval-gated actions stop before execution and produce an owner review
  request.
- Missing inputs become blockers with a named missing item and proposed next
  action.
- Public claims must match the evidence attached to the stage.

## Work Packet

Before medium-risk or external-facing work, the runtime should compile:

- `goal`
- `target_app`
- `lifecycle_stage`
- `repo_or_package_area`
- `deliverable`
- `constraints`
- `allowed_areas`
- `forbidden_areas`
- `approval_gates`
- `acceptance_checks`
- `environment_class`: `local_only`, `cloud_safe`, or `hybrid`
- `deadline_or_window`

For low-risk local inspection, the packet can be brief. For production,
publishing, credentials, paid jobs, or external sends, the packet must be
explicit enough for owner review.

## Execution Loop

1. Load the current app, lifecycle stage, prior evidence, open gates, and
   owner constraints.
2. Compile the work packet and identify missing or contradictory inputs.
3. Select the smallest useful action that can move the current stage forward.
4. Use only skills and tools allowed by the stage and approval boundary.
5. Execute the bounded change or produce the review/blocker artifact.
6. Run the acceptance checks for the stage.
7. Emit an evidence packet.
8. Request review, advance the stage, or keep the stage blocked with a reason.

## Evidence Packet

Each completed or blocked action should produce:

- `target_app`
- `lifecycle_stage`
- `objective`
- `inputs_used`
- `actions_taken`
- `artifacts_changed`
- `verification_commands`
- `verification_result`
- `claim_limits`
- `approval_status`
- `blockers`
- `next_action`

Evidence packets should be concise enough for review and specific enough that a
new agent can reproduce the state without reading a private transcript.

## Stage Movement

Stages advance in this order:

Intent -> Research -> Selection -> Plan -> Engineering -> QA -> KPI Setup ->
Marketing -> Iteration.

Returning to an earlier stage is allowed only through an explicit overwrite
record. The overwrite record must name the reason, the evidence being replaced,
the downstream stages affected, and whether owner approval is required.

Examples:

- New market evidence can reopen Selection after Research is updated.
- A failed QA result can reopen Engineering.
- A changed public claim can reopen KPI Setup or Marketing.

Silent stage regression is not allowed.

## Approval Gates

Agents must stop before:

- public posts, external sends, or ad launches
- paid jobs or metered external calls
- credential, auth, or account changes
- production deployments
- custody, payment, or funding actions
- service autostart or supervisor enablement
- runtime pairing with a private operator service

The correct output for a gated action is an approval request with the intended
action, blast radius, evidence, rollback or stop condition, and exact command or
surface that would be used after approval.

## Skill Access Model

The public package declares skill contracts. A private runtime may map those
contracts to concrete tools, but the public package should not expose private
tool names, paths, credentials, or infrastructure.

Each skill must define:

- when to use it
- inputs it expects
- outputs it must emit
- rules and stop conditions
- verification expectations

## Runtime Bridge

The operator UI or workstation-facing agent may send messages into the runtime
only as structured command drafts or review notes. Bridge events should include
the target app, lifecycle stage, message intent, approval status, and whether
the payload is safe for persistence.

Bridge events should not include secrets, raw credentials, private transcripts,
or host-specific paths.

## Quality Bar

An agent should not mark a task complete unless:

- the acceptance checks were run or an omission was recorded
- changed artifacts are named
- public claims are constrained by evidence
- the next action is clear
- repeated blockers are not retried without a new input or changed plan


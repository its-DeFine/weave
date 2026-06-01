# WEAVE Runtime Document Templates v0.1

Date: 2026-05-30
Status: template contract
Purpose: define the documents Hermes needs before it can operate with high
confidence.

## 1. Template Rules

These templates are written for an agent that is capable but has limited world
model understanding. The documents must therefore make hidden context explicit,
name assumptions, define wrong behavior, and tell Hermes when to stop and ask.

Every template should be:

- git tracked
- versioned when semantically important
- loaded before relevant lifecycle work
- updated when owner feedback changes the operating reality
- referenced from the ledger when changed

## 2. `soul.md`

Location:

```text
<weave-root>/artifacts/general/soul.md
```

Purpose: define how Hermes should think and behave across all work.

Template:

```markdown
# Hermes Soul

Version:
Last updated:
Owner:

## Role

What Hermes is here to be:

What Hermes is not:

## Operating Character

Default tone:

Decision style:

Level of rigor:

How direct Hermes should be:

When Hermes should challenge the owner:

When Hermes should proceed with assumptions:

When Hermes must stop and ask:

## Known Weaknesses

World model limits:

Reasoning limits:

Context limits:

Overclaiming risks:

Drift risks:

## Required Habits

Before important work Hermes must:
1.
2.
3.

During work Hermes must:
1.
2.
3.

After work Hermes must:
1.
2.
3.

## Confidence Policy

Hermes may act when:

Hermes may suggest when:

Hermes must ask when:

Hermes must refuse or stop when:

## Failure Modes To Watch

Failure:
Symptom:
Correction:

## Update Rules

What kind of owner feedback should change this document:

How changes are approved:

Where diffs are recorded:
```

## 3. `owner-profile.md`

Location:

```text
<weave-root>/artifacts/general/owner-profile.md
```

Purpose: tell Hermes who it is helping and how to help them well.

Template:

```markdown
# Owner Profile

Version:
Last updated:
Owner:

## Working Style

How the owner thinks:

How the owner makes decisions:

Preferred level of detail:

Preferred communication style:

What feels helpful:

What feels annoying or wasteful:

## Taste And Standards

Quality bar:

Design taste:

Engineering taste:

Documentation taste:

Risk tolerance:

## Operating Preferences

When to be concise:

When to go deep:

When to ask questions:

When to infer:

When to push back:

## Recurring Constraints

Security:

Privacy:

Public vs private boundaries:

Budget:

Time:

Attention:

## Approval Preferences

Actions that require explicit approval:

How approval should be requested:

What information must be shown before approval:

## Known Context

Projects:

People or organizations:

Tools:

Important history:

## Update Rules

Owner feedback that should update this:

Where diffs are recorded:
```

## 4. App Context

Location:

```text
<weave-root>/apps/<app_id>/context/app-context.md
```

Purpose: define the app-specific reality Hermes needs for lifecycle work.

Template:

```markdown
# App Context

App id:
Version:
Last updated:

## App Summary

What this app is:

Who it is for:

Why it exists:

What success feels like:

## Current Reality

Current stage:

Current repos:

Current deployed surfaces:

Current users or testers:

Current blockers:

Current evidence:

## Domain Context

Domain:

Important concepts:

Important constraints:

Market or ecosystem facts:

Reality sources:

What Hermes must not assume:

## Product Taste

Desired user experience:

What should feel wrong:

Visual or interaction preferences:

Performance expectations:

## Technical Context

Primary stack:

Data model:

Integrations:

Runtime constraints:

Testing expectations:

Deployment model:

## Authority Boundary

Hermes may do:

Hermes must request approval before:

Hermes must never do:

## Update Rules

What changes this context:

Where changes are recorded:
```

## 5. App Inventory

Location:

```text
<weave-root>/apps/<app_id>/inventory/app-inventory.md
```

Purpose: list the concrete resources for the app.

Template:

```markdown
# App Inventory

App id:
Last updated:

## Repositories

Repository:
Purpose:
Local path:
Remote:
Default branch:
Worktree policy:

## Worktrees

Worktree:
Branch:
Purpose:
Status:
Review record:

## Artifacts

Artifact:
Canonical path:
Lifecycle stage:
Owner:
Consumers:

## External Systems

System:
Purpose:
Access status:
Authority boundary:

## Capabilities

Capability:
Purpose:
Allowed actions:
Approval required:
Secret handling:

## Known Blockers

Blocker:
Owner:
Resolution path:
```

## 6. App Gestaltian Contract

Location:

```text
<weave-root>/apps/<app_id>/contract/gestaltian-contract.md
```

Purpose: versioned project contract that changes when owner feedback or reality
changes the app.

Minimum template:

```markdown
# Gestaltian Contract

Project:
Version:
Date:
Owner:
Current lifecycle stage:

## Raw Vision

## Gestalt Kernel

## Finished-State Narrative

## Definition Of Done

## Definition Of Wrong

## System Boundary

## Actors And External Systems

## App Context Required

## Workflows

## Decisions

## Rules And Invariants

## Components

## Failure Modes

## Approval Loops

## Acceptance Tests

## Lifecycle Artifact Map

## Current Build-Ready Handoff Packet

## Open Questions And Assumptions

## Traceability Map

## Contract Update Log
```

## 7. Lifecycle Artifact Manifest

Location:

```text
<weave-root>/apps/<app_id>/lifecycle/<stage>/artifacts/manifest.json
```

Purpose: state what artifacts a lifecycle stage owns.

Template:

```json
{
  "schema": "weave-lifecycle-artifact-manifest/v0.1",
  "app_id": "",
  "stage": "",
  "artifacts": [
    {
      "artifact_id": "",
      "path": "",
      "type": "",
      "created_by": "hermes",
      "created_at": "",
      "contract_version": "",
      "checksum": "sha256:"
    }
  ]
}
```

## 8. Artifact Reference

Location:

```text
<weave-root>/apps/<app_id>/lifecycle/<stage>/refs/<artifact_id>.json
```

Purpose: reference an artifact owned by an earlier lifecycle stage without
copying it.

Template:

```json
{
  "schema": "weave-artifact-ref/v0.1",
  "artifact_id": "",
  "canonical_path": "",
  "source_stage": "",
  "used_by_stage": "",
  "reason": "",
  "checksum": "sha256:"
}
```

## 9. Approval Record

Location:

```text
<weave-root>/apps/<app_id>/approvals/<approval_id>.json
```

Purpose: durable proof that Hermes requested approval and the owner resolved it.

Template:

```json
{
  "schema": "weave-approval/v0.1",
  "approval_id": "",
  "app_id": "",
  "requested_by": "hermes",
  "requested_at": "",
  "channel": "telegram",
  "action": "",
  "reason": "",
  "risk_level": "",
  "information_shown_to_owner": [],
  "decision": "approved | rejected | deferred",
  "decided_at": "",
  "decision_by": "owner",
  "conditions": [],
  "ledger_event_id": ""
}
```

## 10. Procedure Feedback

Location:

```text
<weave-root>/apps/<app_id>/ledger/procedure-feedback/<feedback_id>.json
```

Purpose: tell Hermes what procedure was missing or malformed.

Template:

```json
{
  "schema": "weave-procedure-feedback/v0.1",
  "feedback_id": "",
  "app_id": "",
  "target_event_id": "",
  "severity": "blocking | warning",
  "problem": "",
  "required_repair": "",
  "evidence": [],
  "created_at": ""
}
```

## 11. Window Change Record

Location:

```text
<weave-root>/apps/<app_id>/lifecycle/06-implementation/artifacts/window-change-<id>.md
```

Purpose: record changes Hermes makes to the viewing window.

Template:

```markdown
# Window Change Record

Change id:
App id:
Contract version:
Branch or worktree:

## User Feedback

## Problem

## Intended UX Change

## Files Changed

## Validation

Functional:

Failure:

Gestalt:

## Diff Reference

## Ledger Events
```

---
name: codebase-orientation
description: Inspect a target repository or package area and produce a concise implementation map before planning or editing.
---

# Codebase Orientation

## Use When

Use this skill at the start of Engineering, QA, or handoff work when the agent
needs to understand an application, package, or runtime surface before acting.

## Inputs

- target app or package area
- current lifecycle stage
- goal or question
- known constraints
- files or directories already identified by the operator

## Outputs

- relevant entrypoints
- test and smoke commands
- data/config surfaces
- public/private boundary notes
- likely change areas
- unknowns that block execution

## Rules

- Read the existing source of truth before proposing changes.
- Prefer repository-local docs, scripts, tests, and package manifests.
- Keep the orientation short enough to be used as execution context.
- Separate confirmed facts from inferences.
- Do not expose private paths or credentials in public artifacts.

## Stop Conditions

- The target repo or app cannot be identified.
- The next step would require credentials, production access, or an external
  write.
- The codebase shape contradicts the requested lifecycle stage.

## Verification

Name the files inspected and the command or path that would verify the next
action.


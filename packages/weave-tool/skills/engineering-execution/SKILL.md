---
name: engineering-execution
description: Make bounded code or package changes, run the agreed checks, and record changed artifacts.
---

# Engineering Execution

## Use When

Use this skill after Intent, Research, Selection, and Plan have admitted a
bounded implementation wedge.

## Inputs

- approved or local-only work packet
- target files or package area
- acceptance checks
- claim limits
- allowed and forbidden areas

## Outputs

- changed files
- implementation summary
- checks run and results
- known omissions
- next review action

## Rules

- Follow existing repository patterns before adding abstractions.
- Keep edits scoped to the planned package area.
- Preserve unrelated user or runtime changes.
- Add or update tests when behavior or validation changes.
- Run the agreed checks before marking work complete.
- Record any check that could not be run and why.

## Stop Conditions

- The change needs credentials, paid calls, production deploy, or external send.
- Required context is missing and cannot be inferred safely.
- Tests reveal a failure outside the planned scope that changes the claim.

## Verification

The output must include the exact verification commands and whether they passed.


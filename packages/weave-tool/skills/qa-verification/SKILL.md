---
name: qa-verification
description: Verify package, file-state, UI, and lifecycle claims with checks, evidence, and failure boundaries.
---

# QA Verification

## Use When

Use this skill before promoting a lifecycle stage, publishing a package, or
claiming that a lifecycle surface works.

## Inputs

- target app or package area
- changed artifacts
- claimed behavior
- acceptance checks
- public/private boundary

## Outputs

- verification commands
- pass/fail result
- failure cases checked
- visual or local evidence when relevant
- claim limits
- release verdict

## Rules

- Verify the claim that will be made publicly.
- Separate local dry-run proof from hosted or live service proof.
- Check both happy path and at least one meaningful failure boundary when the
  feature has user-facing risk.
- Nearby artifacts, fixture packets, or local file copies are not enough to
  prove a live or public surface.
- Treat unrun checks as omissions, not as passes.
- Keep screenshots or UI evidence public-safe when attached.

## Stop Conditions

- A claimed production or hosted surface cannot be verified.
- Evidence contains private paths, credentials, or internal infrastructure.
- A failed check changes the release verdict.

## Verification

QA is complete when the release verdict names what passed, what remains
unverified, and what claim is allowed.

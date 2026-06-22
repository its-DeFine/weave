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
- external-agent QA contract, when the claim depends on external agents,
  tool bridges, network transport, or isolated profiles
- public/private boundary

## Outputs

- verification commands
- pass/fail result
- failure cases checked
- isolated topology, launched scenario, and per-agent readback when
  external-agent behavior is claimed
- visual or local evidence when relevant
- claim limits
- release verdict

## Rules

- Verify the claim that will be made publicly.
- Separate local dry-run proof from hosted or live service proof.
- Check both happy path and at least one meaningful failure boundary when the
  feature has user-facing risk.
- For external-agent features, QA must launch or attach the specified isolated
  agents, read back model/provider/tool configuration from each agent,
  run the communication scenario, collect evidence from both sender and
  receiver, and label the exact proof surface.
- One-sided logs, parent-session tool calls, fixture packets, or local file-copy
  loops are not enough to prove a communication transport.
- Treat unrun checks as omissions, not as passes.
- Keep screenshots or UI evidence public-safe when attached.

## Stop Conditions

- A claimed production or hosted surface cannot be verified.
- An external-agent claim lacks an executable QA contract or cannot launch the
  isolated topology it names.
- Evidence contains private paths, credentials, or internal infrastructure.
- A failed check changes the release verdict.

## Verification

QA is complete when the release verdict names what passed, what remains
unverified, and what claim is allowed. For external-agent claims, QA is not
complete until sender and receiver readback artifacts match the declared
scenario.

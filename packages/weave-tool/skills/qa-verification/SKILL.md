---
name: qa-verification
description: Verify runtime, UI, package, and lifecycle claims with checks, evidence, and failure boundaries.
---

# QA Verification

## Use When

Use this skill before promoting a lifecycle stage, publishing a package, or
claiming that a runtime surface works.

## Inputs

- target app or package area
- changed artifacts
- claimed behavior
- acceptance checks
- runtime-agent QA contract, when the claim depends on Hermes agents, MCP,
  gateway routing, A2A/XMTP transport, containers, or isolated profiles
- public/private boundary

## Outputs

- verification commands
- pass/fail result
- failure cases checked
- isolated runtime topology, launched scenario, and per-runtime readback when
  runtime-agent behavior is claimed
- visual or local evidence when relevant
- claim limits
- release verdict

## Rules

- Verify the claim that will be made publicly.
- Separate local dry-run proof from hosted or live service proof.
- Check both happy path and at least one meaningful failure boundary when the
  feature has user-facing risk.
- For runtime-agent features, QA must launch or attach the specified isolated
  runtimes, read back model/provider/tool/MCP configuration from each runtime,
  run the communication scenario, collect evidence from both sender and
  receiver, and label the exact proof surface.
- One-sided logs, parent-session tool calls, fixture packets, or local file-copy
  loops are not enough to prove a communication transport.
- Treat unrun checks as omissions, not as passes.
- Keep screenshots or UI evidence public-safe when attached.

## Stop Conditions

- A claimed production or hosted runtime cannot be verified.
- A runtime-agent claim lacks an executable QA contract or cannot launch the
  isolated topology it names.
- Evidence contains private paths, credentials, or internal infrastructure.
- A failed check changes the release verdict.

## Verification

QA is complete when the release verdict names what passed, what remains
unverified, and what claim is allowed. For runtime-agent claims, QA is not
complete until sender and receiver readback artifacts match the scenario in
`docs/runtime-agent-qa-contract.md`.


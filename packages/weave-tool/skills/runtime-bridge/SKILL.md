---
name: runtime-bridge
description: Shape safe command drafts and review notes between Telegram, workstation agents, and WEAVE runtime.
---

# Runtime Bridge

## Use When

Use this skill when a human operator, local agent, or Telegram gateway needs to send
stage context, a command draft, or a review note into the WEAVE runtime.

## Inputs

- target app id
- lifecycle stage
- operator message or agent note
- command intent
- approval status
- persistence safety flag

## Outputs

- structured command draft
- target app and lifecycle stage
- approval requirement
- sanitized summary
- evidence or review link when available
- runtime response expectation

## Rules

- Store structured summaries, not raw private transcripts.
- Include whether the payload is safe to persist.
- Keep secrets, credentials, private paths, and host-specific details out of
  bridge events.
- Owner-gated commands must remain drafts until approval exists.
- Runtime responses should be visible through deterministic status commands as
  state, evidence, blocker, or next action.

## Stop Conditions

- The message asks for a gated action without approval.
- The message contains credentials or private operational details.
- The target app or lifecycle stage is unknown.

## Verification

The bridge output is valid when it can be rendered by deterministic Telegram
status commands and replayed by a runtime worker without needing private chat
context.

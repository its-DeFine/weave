---
name: evidence-packet
description: Produce concise, reviewable evidence packets for completed, blocked, or owner-gated lifecycle work.
---

# Evidence Packet

## Use When

Use this skill whenever an agent completes work, blocks on a missing input,
requests owner approval, or hands off to another runtime lane.

## Inputs

- target app
- lifecycle stage
- work packet
- actions taken
- artifacts changed
- verification output
- blockers or approval gates

## Outputs

- target app and stage
- objective
- inputs used
- changed artifacts
- checks run and result
- claim limits
- blockers
- owner approval request if needed
- next action

## Rules

- Evidence should be reproducible from files and commands, not private chat
  memory.
- Keep the packet short enough to review quickly.
- Link or name artifacts instead of pasting long logs.
- State omissions plainly.
- Do not mark owner-gated work complete until approval evidence exists.

## Stop Conditions

- The evidence would require publishing private logs, credentials, or paths.
- The verification result contradicts the intended claim.
- The next action is ambiguous.

## Verification

A reviewer should be able to answer: what changed, how it was checked, what is
still blocked, and what happens next.


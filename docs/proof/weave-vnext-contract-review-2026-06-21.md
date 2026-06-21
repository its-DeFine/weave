# WEAVE vNext Contract Review

Date: 2026-06-21
Reviewer: COS controller
Artifact: `docs/WEAVE_VNEXT_GROUND_ZERO_CONTRACT.md`

## Verdict

READY_FOR_CONTROLLER_REVIEW as a contract artifact, not as an implementation
claim.

## Why The Previous Contract Was Not Enough

- It led with generic COS governance instead of identity-first app-company flow.
- It did not make `owner-profile.md`, `soul.md`, and `agent.md` the first hard
  gate.
- It did not make app-to-monetization the product spine early enough.
- It mixed proof discipline with product identity, making WEAVE look like a
  task router instead of an application-company agent.
- It did not give a concrete service blueprint a future agent could execute.

## Review Roles Applied

| Role | Finding | Resolution |
| --- | --- | --- |
| Product architect | Product center must be onboarding -> identity -> app -> monetization. | Rewrote one-screen contract and product flow around that spine. |
| UX/service blueprint reviewer | A normal user needs clear first-run behavior and visible state. | Added first-run flow, state line, durable home, and service blueprint. |
| Implementation architect | The architecture must stay small enough to build. | Reduced architecture to one surface, one home, one state file, cards, envelopes, packets, gates. |
| Evaluation/governance reviewer | Improvement needs measurable events and scorecards. | Added required events, scorecard dimensions, governance rules, and black-box tests. |
| Skeptical future-agent user | The contract must prevent generic "done" claims. | Added proof-surface separation, non-claim rules, and definition of done. |

## Key Changes

- Defined WEAVE vNext as an identity-first application-company Chief of Staff.
- Made Codex the first required surface and Hermes a later/proven integration.
- Added the first-run identity gate before any app work.
- Added a durable home model with a small `state.json`.
- Added executable intent-truth fields.
- Added app lifecycle stages through monetization and usage/revenue learning.
- Added a service blueprint with user actions, visible responses, backstage
  actions, artifacts, proof/readback, and failure modes.
- Added proof-surface separation and a proof-envelope schema.
- Added observability events, scorecard dimensions, governance rules, and
  black-box acceptance tests.
- Added a repo reset matrix for keep/rewrite/archive/delete categories.

## Residual Non-Claims

- This does not prove the current code implements the contract.
- This does not prove Codex black-box runtime behavior.
- This does not prove live Hermes behavior.
- This does not archive, delete, push, publish, or deploy anything.
- This does not prove public website, payment, or revenue behavior.

## Controller Acceptance Basis

The contract is acceptable for controller review because a future agent can now
execute from it without needing the owner to restate the philosophy:

1. Start or resume WEAVE.
2. Form identity.
3. Ask for app intent.
4. Move through app lifecycle gates.
5. Dispatch workers only with packets.
6. Accept claims only with proof envelopes.
7. Stop at live/payment/destructive boundaries.
8. Keep state and owner mental model synchronized.

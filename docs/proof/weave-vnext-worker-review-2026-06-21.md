# WEAVE vNext Worker Contract Review

Date: 2026-06-21
Reviewer: visible WEAVE contract smoke-review worker
Artifacts:
- `docs/WEAVE_VNEXT_GROUND_ZERO_CONTRACT.md`
- `docs/proof/weave-vnext-contract-review-2026-06-21.md`

## Verdict

READY_FOR_CONTROLLER_REVIEW after targeted contract revisions.

## Adversarial Checks

| Risk | Result |
| --- | --- |
| First-run Codex user flow executable, not just described | Pass after adding the Codex first-run state machine and minimum `state.json` shape. |
| Identity gate non-skippable | Pass after making `identity_state != accepted` a mechanical block on app cards, workers, engineering, launch, and monetization. |
| App-to-monetization lifecycle complete and not generic task routing | Pass after requiring lifecycle-card fields and stating that WEAVE tasks must advance app-company stages or maintain the stage system. |
| Proof surfaces and non-claims stop overclaiming | Pass. The proof-surface table, proof envelope, non-claim fields, and governance rules are adequate as contract requirements. |
| Observability, eval, governance, stale-worker cleanup actionable | Pass after adding the public-safe event schema and explicit stale-worker cleanup decisions. |
| Future agent can use contract without owner philosophy restatement | Pass. The contract now gives activation prompts, state transitions, artifacts, gates, lifecycle stages, proof rules, and cleanup decisions. |
| Architecture simple enough to implement without old TUI/Textual baggage | Pass. The architecture remains one COS chat, one durable home, one state file, events, cards, proof envelopes, worker packets, and review gates. |

## Residual Non-Claims

- This review does not prove the repository implements the contract.
- This review does not prove Codex black-box behavior.
- This review does not prove Hermes behavior.
- This review does not prove launch, payment, public website, analytics, usage,
  or revenue behavior.
- This review did not push, deploy, delete, run long tests, or inspect secrets.

## Proof

- Contract patch: `docs/WEAVE_VNEXT_GROUND_ZERO_CONTRACT.md`
- Independent review note: `docs/proof/weave-vnext-worker-review-2026-06-21.md`
- Required checks: `git diff --check` and targeted whitespace checks on edited
  files.

# WEAVE Harness Engineering Adoption

WEAVE adopts harness-engineering discipline by making every agent claim
testable, bounded, and resumable.

## Harness Principles In WEAVE

- Convert raw intent into an explicit contract.
- Keep the target surface narrow.
- Define stop boundaries before execution.
- Produce proof artifacts instead of relying on chat confidence.
- Run adversarial review before acceptance.
- Sync the human mental model with the system state.

## Default Harness Packet

```text
current_model: COS WEAVE file skeleton
expected_change: <files or app state to change>
proof_path: <proof files or commands>
exit_condition: ACCEPT_FOR_SCOPE | REVISE | BLOCKED | NEEDS_OWNER_ACTION
owner_decision_boundary: public, paid, credentialed, destructive, or tracker-changing work
```

## What This Prevents

- claiming done from partial local work;
- losing app state after context compaction;
- asking the owner to classify lifecycle manually;
- repeating the same missing-proof mistake;
- hiding blocked state inside prose;
- letting old repository surfaces define the current product.

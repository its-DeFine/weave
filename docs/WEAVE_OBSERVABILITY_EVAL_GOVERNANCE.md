# WEAVE Observability, Evaluation, and Governance

Status: public-safe contract
Date: 2026-06-21

WEAVE must make agent work observable, evaluable, and governed before it can
claim that a task is done. The goal is not to collect more raw logs. The goal is
to turn every app or runtime loop into a reviewable control system: what was
asked, what changed, what proof exists, what is blocked, and what can improve
next time.

## Simple model

- **Observability** records the shape of the run without exposing private data.
- **Evaluation** judges the run against evidence, not vibes.
- **Governance** decides what is allowed to advance, what must stop, and what
  requires owner approval.

If a WEAVE task lacks any one of these, it can still be a draft or rehearsal,
but it must not be marked `DONE`.

## Evidence surfaces

WEAVE uses sanitized evidence surfaces by default:

- task id, app id, lifecycle stage, state, and owner decision boundary;
- worker or runtime label, without internal hostnames or private topology;
- state transitions with timestamps;
- proof paths, checksums, or reviewer-visible artifact references;
- tool/runtime surfaces used;
- cost, token, latency, and tool-call counters when available;
- blocker and owner-action records;
- cleanup or archive state for disposable runtime work;
- explicit non-claims.

WEAVE does not require raw chat transcripts, raw logs, cookies, browser session
values, private keys, API tokens, credential paths, or private infrastructure
names to evaluate a task.

## Required proof boundary labels

Every meaningful claim should carry one of these labels:

- `SELF_REPORTED`: an agent said it happened; not accepted as done.
- `TOOL_VERIFIED_LOCAL`: deterministic local command, file, screenshot, or
  readback verifies the claim.
- `TARGET_SURFACE_VERIFIED`: the intended runtime, browser, service, or external
  target was exercised and read back.
- `HUMAN_APPROVED`: an authorized human accepted a gate or reviewed an artifact.
- `EXTERNAL_SIDE_EFFECT`: public, production, billing, custody, user-facing, or
  third-party state changed and was read back.
- `SANITIZED_SUMMARY`: raw private evidence was intentionally withheld and
  replaced with a safe summary.
- `BLOCKED_PENDING_INPUT`: the next step needs owner input or unavailable access.
- `REVIEW_REQUIRED`: work appears complete but cannot become `DONE` until
  controller or human review.

## DONE gate

`DONE` is blocked unless all of the following are true:

1. The task has a clear lifecycle stage and expected change.
2. The claim has a proof boundary label.
3. A reviewer-visible artifact or summary exists.
4. The proof path is bound to an acceptance check.
5. Hard gates for secrets, private topology, production, public sends, billing,
   custody/value transfer, and destructive actions were respected.
6. Any external side effect has explicit approval and target-surface readback.
7. Any missing proof is named as a non-claim, blocker, or follow-up.
8. The controller review or evaluator result says the work can advance.

## Evaluation contract

The special eval contract is available as:

```bash
bin/weave eval observability-governance
bin/weave eval observability-governance --review-template
```

It checks six dimensions:

- traceability;
- evaluation quality;
- governance strength;
- learning loop;
- public-safe boundary;
- operational measurement.

Hard gates win over rubric scores. A high-quality writeup cannot advance if the
sanitized evidence ledger, evaluator review, governance gates, or proof boundary
labels are missing.

## Runtime-agent rule

When Hermes or another runtime agent is involved, this contract complements
`docs/runtime-agent-qa-contract.md`.

Runtime proof must say exactly which surface is proven:

- local rehearsal;
- attached runtime one-shot;
- container mesh;
- live transport;
- external-write verified.

If the runtime proof comes from a private operator surface, public artifacts must
describe it generically and keep internal identifiers in ignored proof bundles.

## Chief-of-Staff loop

A WEAVE Chief-of-Staff response should be able to answer:

- What stage are we in?
- What state is the task in?
- What proof exists?
- What is still unproven?
- What hard gate blocks progress?
- What owner action, if any, is truly needed?
- What did we learn that should change the next packet?

This is the difference between a chat that produces artifacts and an operating
system that improves.

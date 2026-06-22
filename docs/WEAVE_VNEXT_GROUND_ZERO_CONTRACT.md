# WEAVE vNext Ground Zero Contract

WEAVE vNext is a COS-first repository skeleton. It is not a terminal cockpit,
not a private operations bridge, and not a hidden service mesh. A Codex thread
can become COS WEAVE by reading this repository and creating visible state under
`runs/cos-weave-home/`.

## Product Thesis

People lose track of what an agent promised, what it actually did, and what is
still unproven. WEAVE fixes that by making every app effort a small operating
company folder with intent, lifecycle state, todos, proofs, blockers, worker
packets, review decisions, and readback state.

## Acceptance Bar

A fresh Codex thread should be able to:

1. Receive a WEAVE repo URL/path and ordinary app intent.
2. Read the repo contract.
3. Emit the WEAVE state line before meaningful work.
4. Create or load `runs/cos-weave-home/`.
5. Infer intent truth without asking the user to classify the task.
6. Create app folders and lifecycle state.
7. Decide the next safe lifecycle slice.
8. Create worker packets when parallel execution is useful.
9. Run local validation and review loops.
10. Report proof, non-claims, blockers, and next actions.

## Non-Claims

Default COS WEAVE proof does not prove:

- production deployment;
- public posting or sending;
- paid calls, billing, or transfers;
- credential access;
- live tracker mutation;
- any lifecycle stage that was not explicitly executed and reviewed.

## Lifecycle Handling

Each lifecycle stage has:

- entry condition;
- questions to ask only if missing information changes action;
- expected artifact;
- validation command or manual proof rule;
- review rubric;
- exit condition;
- non-claims.

The lifecycle exists to prevent overclaiming. A narrow calculator artifact can
be accepted for Intent + Engineering + QA without pretending Deployment,
Marketing, KPI, Iteration, or Analysis happened.

## Review Loop

Every meaningful change follows:

```text
observe -> validate -> govern -> review -> sync
```

- Observe: record what changed and where.
- Validate: run checks or produce bounded proof.
- Govern: compare against scope, stop boundaries, and non-claims.
- Review: decide `ACCEPT_FOR_SCOPE`, `REVISE`, `BLOCKED`, or
  `NEEDS_OWNER_ACTION`.
- Sync: update lifecycle, todos, proof, blockers, and readback.

## Repository Shape

Keep current product code small:

- `bin/weave`: local helper entrypoint.
- `scripts/weave_cli.py`: helper CLI.
- `scripts/weave_cos_skeleton.py`: file skeleton creation/readback.
- `scripts/weave_eval.py`: lifecycle eval and review loop.
- `packages/weave-tool/`: portable skill package and lifecycle contracts.
- `docs/`: current COS WEAVE contract, UX, service blueprint, and proof rules.
- `tests/`: unit and contract tests.

Anything that does not support this shape should be removed or moved out of the
review surface.

# WEAVE Intent Truth And Completion Contract

Status: active product contract
Date: 2026-06-21

## Simple Model

The user should not manually classify work. The user talks to the WEAVE Chief of
Staff in normal language. WEAVE must infer the current case, record why that
case is the best interpretation, and derive the lifecycle slice, proof needs,
and completion boundary from that interpretation.

This contract is the missing layer between conversation and task state. It
answers:

- what is the user really asking for;
- what kind of work is this right now;
- what lifecycle stages are required for this slice;
- what stages are explicitly not required yet;
- what proof is necessary before a done claim;
- what claim is forbidden even if the output looks polished.

## Core Rule

No WEAVE task can close from prose alone.

A closeout is valid only when these three objects agree:

1. **Intent truth:** the inferred user goal, current case, uncertainties, and
   scope.
2. **Required-stage matrix:** every in-scope lifecycle stage has evidence; every
   out-of-scope stage has a reason.
3. **Proof envelope:** the final claim, proof path, acceptance check, and review
   state match the active slice.

If those objects disagree, the correct state is `REVISION_REQUIRED`,
`BLOCKED`, or `DONE_FOR_SCOPE_ONLY`, never full `DONE`.

## Intent Truth Object

Every app record should contain an `intent_truth` object:

```json
{
  "schema": "weave-intent-truth/v0.1",
  "state": "unresolved",
  "intent_frame": {
    "user_goal": "capture owner intent and acceptance checks",
    "best_current_case": "intent_discovery",
    "case_confidence": "low_until_owner_answers",
    "target_outcome": "clear app/task contract before worker dispatch"
  },
  "scope_lattice": {
    "active_slice": "intent_capture",
    "required_stages": ["intent"],
    "not_required_stages": [
      {"stage": "build", "reason": "not required until intent and acceptance checks are recorded"}
    ],
    "full_lifecycle_claim": false
  },
  "completion_contract": {
    "allowed_done_state": "DONE_FOR_SCOPE_ONLY",
    "controller_review_required": true
  }
}
```

The object is public-safe. It summarizes intent and proof boundaries. It does
not require raw transcripts, raw logs, private topology, credentials, cookies,
or browser sessions.

## State Line

Every meaningful WEAVE response should expose the truth boundary:

```text
WEAVE | Home=Chief of Staff | App=Punch Compute | Stage=Intent | Scope=Intent Capture | FullLifecycle=not_claimed | Truth=unresolved | State=NEW | Next=answer intent questions
```

This makes partial work obvious. A calculator test can be marked
`DONE_FOR_SCOPE_ONLY` for an engineering slice without implying deployment,
marketing, publish, or full app lifecycle completion.

## Non-Gameable Done Gate

WEAVE must reject a completion claim when any of these are true:

- the active slice is missing;
- the final claim exceeds the active slice;
- a required stage has no proof envelope;
- a not-required stage has no reason;
- the proof path exists but does not name a claim and acceptance check;
- controller review is missing;
- a mirror tracker says done but local WEAVE proof state does not.

The rejection should be explicit:

```text
State=REVISION_REQUIRED
Reason=claim exceeds active slice
Allowed=the engineering slice can close after local QA proof
NotAllowed=full lifecycle done, published, production ready
```

## Compaction Survival

After context compaction or model handoff, a fresh agent must reconstruct truth
from durable state:

- `state.json`
- `apps/<app_id>/intent-truth.json`
- `apps/<app_id>/lifecycle.json`
- `tasks/<task_id>/packet.md`
- `tasks/<task_id>/proof.json`
- generated snapshot HTML
- optional Linear/GitHub mirror comments

Raw chat memory is useful context, not the source of truth.

## Eval Contract

The checkable eval is:

```bash
bin/weave eval intent-truth
bin/weave eval intent-truth --review-template
```

The eval requires an evidence-bound review of intent fidelity, case resolution,
scope precision, completion truth, anti-gaming strength, owner visibility, and
compaction survivability.

## Done State For This Contract

This contract is satisfied for a WEAVE app when:

- the app has an `intent_truth` object;
- the state line exposes `Scope`, `FullLifecycle`, and `Truth`;
- the lifecycle matrix separates required and not-required stages;
- worker packets include the truth boundary;
- proof envelopes include the claim boundary;
- `bin/weave eval intent-truth` can be used before any broad done claim.

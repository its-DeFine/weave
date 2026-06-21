# WEAVE Review Loop Process

Status: active product contract
Date: 2026-06-21

## Simple Model

WEAVE should not create artifacts and then move on. Every meaningful output goes
through a loop:

```text
Create -> Observe -> Validate -> Govern -> Review -> Sync
```

This loop is how WEAVE avoids vibe-coded progress. It gives the agent a default
behavior when the user points out a process weakness: stop adding surface area,
fix the loop, then continue.

## The Three Principles

### Observability

A reviewer must be able to see:

- what changed;
- why it changed;
- what claim is being made;
- what proof exists;
- what proof does not exist;
- where the proof artifact lives;
- what state changed after review.

Raw logs, raw transcripts, credentials, cookies, private topology, and browser
sessions are not observability artifacts. Use sanitized proof envelopes,
summaries, state files, and review records.

### Validation

The claim must be tested against the right surface:

- code claims need tests, lint, smoke, or diff checks;
- UX claims need generated snapshots, screenshots, or user-flow proof;
- runtime claims need target runtime proof;
- tracker claims need tracker readback;
- partial-slice claims need scope and non-claim checks.

If validation cannot run, the state is `BLOCKED` or `NEEDS_OWNER_ACTION`, not
done.

### Governance

The loop must block:

- raw secrets, credentials, cookies, private keys, and browser sessions;
- private topology or raw internal dumps in public artifacts;
- production deploys, public sends, billing, custody, or value transfer without
  exact approval;
- broad completion claims without proof;
- local-only proof being presented as live runtime proof.

## Default Review Decisions

Controller review has four allowed outcomes:

- `ACCEPT_FOR_SCOPE`: the artifact is good enough for the active slice only.
- `REVISE`: the artifact is useful but below the bar or missing evidence.
- `BLOCKED`: a stop boundary or unavailable surface prevents completion.
- `NEEDS_OWNER_ACTION`: the next step truly requires owner choice or auth.

There is no unqualified `DONE` unless the active scope is the full lifecycle and
all required proof exists.

## Proactive Reprioritization Rule

When the owner says the process itself is failing, especially around governance,
observability, validation, stale workers, owner attention, or fake completion,
WEAVE must reprioritize the loop fix before continuing feature work.

The correct response is:

1. state what is missing;
2. patch the durable rule or test if inside scope;
3. run focused verification;
4. return to the product task with the loop strengthened.

This is an operating rule, not a suggestion.

## Chief-Of-Staff Home Contract

Every generated Chief-of-Staff home writes:

- `review-loop.json`
- `review-loop.md`
- proof envelopes with `review_loop_state`
- worker packets that name the loop
- snapshots with a Review Loop section

The loop state is local and public-safe. It does not prove live Hermes, live
deployment, public posting, or tracker updates by itself.

## Eval Contract

Run:

```bash
bin/weave eval review-loop
bin/weave eval review-loop --review-template
```

The eval checks whether observability evidence, validation, governance gates,
controller review, and state sync are all present.

## Done State For This Contract

The loop is implemented when:

- generated homes include the review-loop state;
- the loop is visible in snapshots;
- worker packets tell agents to run through the loop;
- proof envelopes record review loop state;
- `bin/weave eval review-loop` exists and blocks without evidence;
- tests prevent the loop from disappearing.

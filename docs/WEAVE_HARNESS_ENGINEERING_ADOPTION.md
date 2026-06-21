# WEAVE Harness Engineering Adoption

Status: design contract
Date: 2026-06-21

## Source

This document adapts the public OpenAI article "Harness engineering:
leveraging Codex in an agent-first world" for WEAVE vNext.

The article's useful lesson for WEAVE is that agent success depends less on
larger prompts and more on a harness: a repo-local system of record,
agent-legible runtime surfaces, mechanical invariants, review loops, and
garbage collection that let agents correct themselves without spending owner
attention.

## WEAVE Translation

WEAVE is not only a Chief of Staff chat. WEAVE must become a small harness that
makes app-company work legible and executable for Codex first, and Hermes later.

When a WEAVE run fails, the controller must not simply retry the same request.
It must classify the failure as one of:

- missing source-of-truth document;
- missing state or event field;
- missing lifecycle procedure;
- missing proof surface;
- missing eval or validator;
- missing worker-packet field;
- missing architecture boundary;
- stale or conflicting documentation;
- serious owner decision boundary.

If the failure is not a serious owner boundary, WEAVE records or patches the
missing harness capability before repeating the work.

## Harness Principles

### 1. Repository Knowledge Is The System Of Record

WEAVE must keep durable product and operating knowledge inside the repository or
the WEAVE home, not only in chat memory.

`AGENTS.md` remains a short map. It should point agents to current docs instead
of becoming a giant manual. Deep rules belong in focused documents:

- product and lifecycle contract;
- service blueprint;
- implementation packet;
- observability, evaluation, and governance;
- quality scorecard;
- security and public-safety rules;
- active and completed execution plans;
- known technical debt and garbage-collection notes.

Every meaningful design decision must have a repo-local artifact or a recorded
non-claim.

### 2. Progressive Disclosure Beats Prompt Bulk

WEAVE agents should begin from a small stable entry point, then navigate to the
specific source of truth required by the current lifecycle stage.

The first prompt should not inject every WEAVE document. It should identify:

- active app;
- active lifecycle stage;
- active proof claim;
- required source-of-truth documents;
- missing context;
- stop boundary.

### 3. Runtime Surfaces Must Be Agent-Legible

WEAVE cannot rely only on local files to prove behavior. For each app, the plan
must name which target surfaces can be inspected by the agent:

- local files;
- unit or smoke tests;
- local runtime;
- browser page, DOM snapshot, screenshot, or navigation flow;
- logs;
- metrics;
- traces;
- tracker state;
- public/live surface;
- payment or revenue surface.

If a surface is not available, WEAVE records the missing surface as a non-claim
instead of accepting nearby proof.

### 4. Feedback Loops Are Product Features

Every meaningful WEAVE task follows:

```text
state -> reproduce or inspect -> create -> observe -> validate -> govern ->
review -> patch harness if needed -> sync
```

If validation fails, WEAVE asks: "what capability is missing from the harness?"
The answer must become a document, eval, validator, worker-packet field, or
state transition before the same failure is allowed to repeat.

### 5. Architecture And Taste Need Mechanical Checks

Prose is not enough. WEAVE must encode important rules in checks where possible:

- public-safe repository scan;
- secret scan;
- package/company validator;
- lifecycle/eval schemas;
- proof-envelope validator;
- stale-worker scanner;
- doc index and freshness scanner;
- architecture-boundary checks for any implementation package;
- black-box Codex/Hermes behavior tests.

Check failures should include remediation instructions that are useful to an
agent, not only a human.

### 6. Throughput Changes Review

The owner should not be the default reviewer for every safe, local, reversible
change. WEAVE should use cheap agent correction loops and controller review for
ordinary implementation quality, while preserving hard owner gates for:

- public sends;
- production deploys;
- billing, payment, wallet, signer, or value transfer;
- raw secrets, cookies, private keys, session values, private data;
- destructive or irreversible changes;
- unclear account/project choice;
- objective changes.

### 7. Entropy Requires Garbage Collection

Agent systems copy local patterns. WEAVE therefore needs recurring cleanup:

- stale documentation scan;
- obsolete file and old-TUI/Textual residue scan;
- conflicting source-of-truth scan;
- proof-without-claim scan;
- claim-without-proof scan;
- stale worker cleanup;
- quality-score update;
- targeted refactor packet generation.

Garbage collection is not cosmetic. It is how WEAVE prevents the same mistakes
from compounding.

## Implementation Requirements

WEAVE implementation should add or preserve these artifacts:

| Artifact | Purpose |
| --- | --- |
| `AGENTS.md` | Short public-safe map and hard repo rules. |
| `docs/WEAVE_VNEXT_GROUND_ZERO_CONTRACT.md` | Product and lifecycle source of truth. |
| `docs/WEAVE_HARNESS_ENGINEERING_ADOPTION.md` | Harness engineering adaptation and implementation requirements. |
| `docs/WEAVE_REVIEW_LOOP_PROCESS.md` | Create/observe/validate/govern/review/sync process. |
| `docs/WEAVE_OBSERVABILITY_EVAL_GOVERNANCE.md` | Evaluation, governance, scorecard, and proof rules. |
| `docs/WEAVE_SKILL_AUDIT_AND_ARCHIVE_PLAN.md` | Garbage collection for stale skills/docs. |
| `packages/weave-tool/evals/*.yaml` | Black-box and lifecycle eval definitions. |
| `scripts/weave_eval.py` | Local evaluator and review-loop runner. |

## Acceptance Checks

A WEAVE change has incorporated harness engineering only when:

- a future agent can find the correct source of truth without chat history;
- lifecycle progress is backed by target-surface proof or explicit non-claims;
- repeated failures create a harness improvement item, not another retry;
- at least one mechanical check enforces the rule when practical;
- stale docs/workers/proofs are visible and cleanable;
- owner attention is reserved for true judgment boundaries.

## Non-Claims

This document does not prove the current WEAVE implementation satisfies the
harness. It defines the design target and repository requirements that the
implementation must satisfy.

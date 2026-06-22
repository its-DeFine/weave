# Compound Engineering

Status: design contract
Date: 2026-06-22

## Source

This document adapts the operating pattern from Peter Yang's interview,
"How This Non-Technical Founder Mastered Agentic Engineering in 50 Minutes |
Matt Van Horn".

The useful topics are:

- plans are for AI, not for the owner to read line by line;
- compound engineering as the core loop;
- non-technical operators can build by orchestrating agents and proof;
- Printing Press-style tooling turns products/websites into agent-usable CLIs;
- local indexed context lets agents reason over durable evidence;
- CLI plus skill can be more reliable than a fragile direct integration;
- open-source contribution requires value, tests, and maintainer fit;
- strong agents must be asked to critique, benchmark, and sometimes kill their
  own ideas;
- launch fear is real, so readiness must be separated from psychology.

## Definition

Compound engineering is WEAVE's agentic engineering loop:

```text
intent -> plan for agents -> capability/tooling -> execution workers ->
adversarial review -> target-surface proof -> PR/launch/readback -> learn
```

The owner should not need to inspect every plan or implementation detail. The
owner sees:

- current lifecycle stage;
- key decision;
- proof surface;
- blockers;
- rejected options;
- next safe action.

The detailed plan is an agent coordination artifact. The controller reads or
audits it only where quality, safety, or direction depends on it.

## Core Rules

### 1. Plans Are Agent Artifacts

The plan must be structured enough for workers to execute, but owner-facing
readback stays compressed. The owner should see the one or two decisions that
matter, not every internal step.

### 2. One Sharp Question Beats Full Plan Review

Before execution, WEAVE asks the smallest question that could prevent wasted
work. If the plan is safe and directionally clear, WEAVE proceeds and proves.

### 3. Build Or Print Capabilities Before Brute-Forcing Work

If agents struggle with a surface, WEAVE should ask whether a capability is
missing:

- local CLI;
- local database/index;
- browser/DOM/screenshot tool;
- source map;
- API wrapper;
- fixture or simulator;
- evaluator;
- stale-state scanner.

When useful, WEAVE creates a "capability printer" packet: build the smallest
local tool that makes the target surface agent-legible.

### 4. Local Context Beats Repeated Fetching

For repeated work, WEAVE should create durable local context:

- source snapshot;
- SQLite or JSON index;
- persona/user model;
- API/source inventory;
- known constraints;
- previous proof and failures.

No local context artifact may contain raw secrets, private sessions, cookies,
raw transcripts, raw logs, or private topology.

### 5. CLI Plus Skill Is A Preferred Shape

When an agent needs to operate a domain repeatedly, a small CLI plus a skill is
often better than an opaque integration. The CLI exposes actions and state; the
skill explains when and how to use them.

### 6. Adversarial Review Is Mandatory

After a worker produces an answer, WEAVE asks a reviewer to attack it:

- What would make this fail?
- What would a maintainer reject?
- What benchmark disproves this?
- What surface was not tested?
- What is slower, riskier, or uglier than before?
- Should this be killed rather than shipped?

Bad work is a successful outcome if the loop proves it should stop.

### 7. Open-Source PR Mode Requires Extra Governance

External PRs are public and reputation-bearing. WEAVE must not spam maintainers
or submit shallow AI output.

Before claiming an open-source PR is ready or tested, WEAVE needs:

- PR URL or branch;
- problem statement and maintainer value;
- reproduction or evidence that the issue exists;
- exact files changed;
- local test command and result, or explicit non-claim;
- CI status, if available;
- maintainer feedback, if any;
- risk that the change is unwanted, noisy, or out of project taste.

If a PR is already open but testing is unknown, the state is
`needs_test_evidence`, not `done`.

### 8. Launch Readiness And Launch Nerves Are Separate

A project can be technically ready while the owner is hesitant. WEAVE should
name this clearly:

- product readiness;
- proof readiness;
- public-launch approval;
- psychological/positioning blocker.

The fix for launch fear is a smaller reversible launch, not pretending the work
is unfinished.

## WEAVE Lifecycle Mapping

| WEAVE stage | Compound engineering behavior |
| --- | --- |
| Identity | Learn how much detail the owner wants and which actions require approval. |
| App Intent | Convert vague ambition into a concrete engineering or contribution objective. |
| Product Brief | Define target user, maintainer, repo, buyer, or operator value. |
| Research | Inspect allowed sources, prior issues/PRs/docs, examples, APIs, and local evidence. |
| Selection | Choose between direct edit, generated CLI, local index, wrapper, skill, or no-op. |
| Plan | Produce an agent-readable packet, not a verbose owner essay. |
| Engineering | Build in a bounded worktree or local slice with exact proof target. |
| QA | Run target-surface checks; reject nearby proof. |
| Deployment/PR Gate | Ask approval for public PR, deploy, send, billing, or value-transfer action. |
| Launch Readback | Verify PR/CI/live surface after public action. |
| Iteration | Fold feedback, CI failures, maintainer comments, and owner critique into the harness. |

## Standard Compound Engineering Procedure

1. **Receive intent.** Preserve the full owner intent in plain language.
2. **Infer lifecycle stage.** Do not ask the user to classify the task.
3. **Produce agent plan.** Keep owner readback short.
4. **Ask one sharp question.** Only if it changes direction or safety.
5. **Check missing capability.** Decide whether to build a CLI/index/eval first.
6. **Dispatch workers.** Use visible pinned workers for durable work.
7. **Validate target surface.** Run local tests, browser checks, CI checks, or
   explicit non-claims.
8. **Adversarial review.** Ask whether to accept, revise, block, or kill.
9. **Public gate.** PRs, deploys, sends, payments, or public posts require exact
   approval.
10. **Read back.** Show state, proof, non-claims, rejected options, and next
    action.
11. **Improve the harness.** If failure repeats, add a doc, skill, check,
    index, or capability printer.

## Owner-Facing Summary Template

```text
WEAVE | App=<app> | Stage=<stage> | State=<state> | Proof=<surface> | Next=<action>

Decision:
<one sentence>

Proof:
- <target surface and result>

Rejected or killed:
- <option and reason>

Still not proven:
- <non-claims>

Next:
- <safe next action>
```

## Worker Packet Addendum

For compound engineering tasks, worker packets must include:

```text
Compound engineering mode: true
Objective: <what value should exist after this>
Target surface: <repo/app/browser/PR/CLI/etc>
Capability question: <is a CLI/index/tool/eval needed first?>
Allowed sources: <explicit sources>
Forbidden sources: <secrets/private sessions/raw logs/public sends/etc>
Plan audience: agent/controller, not owner
Proof required: <exact target-surface check>
Adversarial review question: <what would make us kill or revise this?>
Public gate: <none, PR approval, deploy approval, send approval, payment approval>
Non-claims: <what this slice does not prove>
```

## Symfony/Open-Source PR Testing Rule

If the owner says a Symfony, Python, Go, Zed, or other external PR is "out",
WEAVE must verify which PR is meant before making claims.

Minimum readback:

- PR URL;
- open/closed/merged state;
- local tests run, if any;
- CI status, if available;
- maintainer feedback;
- what is still untested.

Without that, WEAVE says: `PR exists, test proof unknown`.

## Safety

WEAVE may research public docs, public issues, public PRs, and local repo files.
WEAVE must not scrape private sessions, expose cookies, sniff private traffic,
or reverse-engineer hidden APIs unless the owner has explicitly authorized the
surface and the action is legal, safe, and public-safe to describe.

## Done State

Compound engineering is adopted when:

- the owner can give vague intent and WEAVE produces a stage, plan, worker
  packet, proof target, and next action;
- repeated work produces reusable tools/indexes/evals;
- bad ideas are killed with proof instead of shipped;
- open-source PRs are not called tested without test or CI evidence;
- launch blockers are separated from product readiness;
- the harness improves after repeated failure.

## Continuous Skill

The reusable package skill lives at
`packages/weave-tool/skills/compound-engineering/SKILL.md`. Use it whenever
WEAVE work involves agent orchestration, missing capability/tooling decisions,
target-surface proof, PR readiness, launch readback, or repeated harness
failures.

For WEAVE-to-Symphony adapter work, the standing compound-engineering plan is
`docs/WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md`.

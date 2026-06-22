# COS WEAVE Repo Skeleton

COS WEAVE uses a simple file/folder skeleton as its product surface. The
skeleton is intentionally boring: it must be easy for any Codex agent to create,
inspect, validate, and resume.

## Default Home

```text
runs/cos-weave-home/
  state.json
  owner-profile.md
  owner-profile.json
  apps/
    registry.json
    <app-id>/
      app.json
      intent.md
      intent.json
      intent-truth.json
      lifecycle.json
      lifecycle/
        lifecycle-state.json
        01-intent/
        02-research/
        03-selection/
        04-plan/
        05-engineering/
        06-qa/
        07-deployment/
        08-kpi-setup/
        09-marketing/
        10-iteration/
        11-analysis/
      todos.md
      tasks.json
      tasks/
        tasks.json
        worker-packets/
      worker-packets/
        WP-0001.md
      proof/
        proof-tray.json
      blockers/
        blocker-tray.json
      review/
        review-queue.json
      updates/
        readback.json
  procedures/lifecycle/
  tasks/
  proof/
  blockers/
  review/
  inbox/
  updates/readback.json
```

## File Roles

- `owner-profile.md`: non-secret preferences, collaboration style, useful
  constraints, and open questions.
- `registry.json`: list of known apps and active app IDs.
- `state.json`: WEAVE home state and active app pointer.
- `owner-profile.json`: machine-readable draft owner profile.
- `app.json`: app metadata, intent truth, current lifecycle pointer, gates, and
  non-claims.
- `intent.md` and `intent.json`: owner words plus normalized intent truth
  inferred from the user's language.
- `intent-truth.json`: resumable truth/completion boundary for the active slice.
- `lifecycle.json`: stage state, gates, proofs, blockers, and non-claims.
- `lifecycle/`: per-stage procedure and state files matching the canonical
  lifecycle vocabulary.
- `todos.md`: next actions split by agent, owner, and blocked items.
- `tasks.json` and `tasks/`: local task ledger and worker packet references.
- `worker-packets/`: packets that a COS WEAVE thread can give to pinned worker
  threads when parallel execution is useful.
- `proof/`: command output summaries, artifact pointers, and review evidence.
- `blockers/`: exact blocker, owner action if any, and safe alternatives.
- `review/`: review-loop decisions and revision requests.
- `updates/readback.json`: concise resumable state for the next thread turn.

## Lifecycle States

The default lifecycle stages are:

1. Intent
2. Research
3. Selection
4. Plan
5. Engineering
6. QA
7. Deployment
8. KPI Setup
9. Marketing
10. Iteration
11. Analysis

The durable slug for KPI Setup is `kpi-setup`. The CLI may accept `kpi` as a
short alias, but generated files, eval contracts, and primitives use
`kpi-setup`.

Not every task uses every stage. A narrow task can be accepted for its stated
scope, but the agent must explicitly say which stages were not attempted.

## Core Rule

Missing owner preferences are questions and todos, not a hard blocker. The
agent should create useful state immediately, mark assumptions, and continue
until a real boundary appears.

## Optional Extensions

Optional orchestration backends may be added later, but they are not required
for the default product. The review-ready repo must work with only Codex, this
repository, and local files.

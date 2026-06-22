# COS WEAVE Repo Skeleton

COS WEAVE uses a simple file/folder skeleton as its product surface. The
skeleton is intentionally boring: it must be easy for any Codex agent to create,
inspect, validate, and resume.

## Default Home

```text
runs/cos-weave-home/
  owner-profile.md
  apps/
    registry.json
    <app-id>/
      app.json
      intent.md
      lifecycle.json
      todos.md
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
```

## File Roles

- `owner-profile.md`: non-secret preferences, collaboration style, useful
  constraints, and open questions.
- `registry.json`: list of known apps and active app IDs.
- `app.json`: app metadata and current lifecycle pointer.
- `intent.md`: normalized intent truth inferred from the user's language.
- `lifecycle.json`: stage state, gates, proofs, blockers, and non-claims.
- `todos.md`: next actions split by agent, owner, and blocked items.
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
4. Planning
5. Engineering
6. QA
7. Deployment
8. KPI
9. Marketing
10. Iteration
11. Analysis

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

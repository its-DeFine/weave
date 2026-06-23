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
      deployment-gates.json
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
- `deployment-gates.json`: provider-specific launch prerequisites. It records
  provider name, required capabilities, proof state, safe validation path,
  forbidden actions until validation, and non-claims without raw secrets.
- `intent.md` and `intent.json`: owner words plus normalized intent truth
  inferred from the user's language.
- `intent-truth.json`: resumable truth/completion boundary for the active slice.
- `lifecycle.json`: stage state, gates, proofs, blockers, and non-claims.
- `lifecycle/`: per-stage procedure and state files matching the canonical
  lifecycle vocabulary. Each stage state includes the stage-entry contract
  refs that must be loaded before acting: eval YAML, generated procedure,
  primitive registry entry, and relevant skills.
- `todos.md`: next actions split by agent, owner, and blocked items.
- `tasks.json` and `tasks/`: local task ledger and worker packet references.
- `worker-packets/`: packets that a COS WEAVE thread can give to pinned worker
  threads when parallel execution is useful.
- `proof/`: command output summaries, artifact pointers, and review evidence.
- `blockers/`: exact blocker, owner action if any, and safe alternatives.
- `review/`: review-loop decisions and revision requests.
- `updates/readback.json`: concise resumable state for the next thread turn.

## Deployment Provider Gates

Every app folder includes structured deployment prerequisites as local state.
The default gates model Cloudflare DNS/domain authority and Vercel hosting or
deploy target access. Each provider entry starts as `not_validated`, names the
safe validation path through an approved connector, MCP, or brokered access
validator, and records only proof state, proof references, public-safe labels,
and `secret_ref` values when needed.

Local intent, planning, and engineering can continue without provider access.
Deployment, launch, DNS mutation, domain attachment, billing, public traffic,
and provider access claims stay blocked until the relevant provider gate is
validated. Additional providers can be added by using the same required fields:
provider, required capabilities, proof state, safe validation path, forbidden
actions until validation, and non-claims.

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

## Stage-Entry Contracts

Before a COS WEAVE agent plans or executes any lifecycle entry or transition,
it infers the stage from owner intent and app state, loads the matching
`packages/weave-tool/evals/lifecycle/<stage>.yaml`, reads the generated
home-level or app-local procedure, checks the stage entry in
`packages/weave-tool/primitives/registry.json`, and selects relevant
`packages/weave-tool/skills/*/SKILL.md` files.

The generated lifecycle state, stage procedure, proof tray, worker packet, and
readback record those consulted contracts. Missing or contradictory contracts
produce `REVISE` or `BLOCKED`; they are not permission for the agent to
improvise from memory. The owner still does not need to name lifecycle stages.

## Core Rule

Missing owner preferences are questions and todos, not a hard blocker. The
agent should create useful state immediately, mark assumptions, and continue
until a real boundary appears.

## Optional Extensions

Optional orchestration backends may be added later, but they are not required
for the default product. The review-ready repo must work with only Codex, this
repository, and local files.

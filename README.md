# WEAVE

![WEAVE repo skeleton hero](assets/weave-hero.png)

Current release: `v0.1.0`.

WEAVE is a Chief-of-Staff mode for Codex: paste the public repo URL plus an
ordinary app idea, and the Codex thread becomes COS WEAVE, a local-file
operating skeleton for app intent, lifecycle state, worker packets, proof,
blockers, review, deployment prerequisite gates, and readback.

WEAVE does not require a terminal UI, external orchestrator, tracker, deployment
account, credentials, or manual lifecycle classification for first contact.

## First Contact

Normal user prompt:

```text
Use WEAVE release v0.1.0 from https://github.com/its-DeFine/weave.git. I want to build <ordinary app intent>.
```

The first meaningful response must begin with:

```text
WEAVE | Home=<repo>/runs/cos-weave-home | App=<app-or-pending> | Stage=<stage> | Scope=local-file-skeleton | State=<state> | Next=<next action>
```

The WEAVE state line must appear before any execution packet. Do not start with `Execution packet`.

Example:

```text
Use WEAVE release v0.1.0 from https://github.com/its-DeFine/weave.git. I want to build a tiny local calculator app.
```

If the Codex thread is projectless and only has the public Git URL, use this
stronger launcher prompt instead. It tells the agent to read the repo contract
before sending a generic execution packet:

```text
Before any commentary or execution packet, open or clone this repository and read COS_WEAVE_FIRST_CONTACT.md, AGENTS.md, and docs/COS_WEAVE_BOOTSTRAP.md. Obey the COS WEAVE first-contact contract from those files: your first meaningful response must start with the WEAVE state line.

Use WEAVE release v0.1.0 from https://github.com/its-DeFine/weave.git. I want to build <ordinary app intent>. Work locally only unless I explicitly approve another surface.
```

## What Happens Next

1. The Codex agent opens or clones the public repository.
2. It reads `COS_WEAVE_FIRST_CONTACT.md`, `AGENTS.md`, and
   `docs/COS_WEAVE_BOOTSTRAP.md`.
3. It announces itself with the `WEAVE | ...` state line.
4. It creates or loads `runs/cos-weave-home/` inside the repo workspace.
5. It infers the app and lifecycle slice from ordinary words.
6. It writes app state, lifecycle state, todos, worker packets, proof,
   blockers, review queue, and readback files.
7. It asks only the owner questions needed for safe local progress.
8. It reports what is proven, what is not proven, and the next safe action.

The user provides: the repo URL, ordinary app intent, answers to any lightweight
clarifying questions, and explicit approval for any external surface.

The agent does automatically: repo reading, local WEAVE home creation, app
folder creation, lifecycle inference, proof/readback writing, and local
validation. The user should not need to run CLI commands to start WEAVE.

## Default File-Skeleton State

Then the agent should create or load:

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
      todos.md
      tasks.json
      tasks/
        tasks.json
        worker-packets/
      worker-packets/
      proof/
      blockers/
      review/
      updates/readback.json
  procedures/lifecycle/
  tasks/
  proof/
  blockers/
  review/
  inbox/
  updates/readback.json
```

These developer commands are not the user-facing first-run path.

## Deployment Gates

Cloudflare and Vercel are useful and expected deployment surfaces when an app
reaches a deployment stage, but they are not required for intent capture,
planning, or local engineering. COS WEAVE must stop before DNS changes,
provider mutations, production deploys, paid actions, or public release unless
the owner explicitly approves the target surface and the proof required.

Do not paste raw Cloudflare, Vercel, DNS, OAuth, API, or service credentials
into chat. Use an approved local secret manager or brokered execution path only
after the deployment gate is intentionally opened.

## Visual Model

The user-facing process is shown in:

- [WEAVE v0.1 flow](assets/weave-v0.1-flow.svg)
- [WEAVE v0.1 lifecycle map](assets/weave-v0.1-lifecycle.svg)

The visual model is deliberately simple: one COS WEAVE thread, one visible
WEAVE home, many app folders, and lifecycle state that only advances with
proof and review.

## What WEAVE Does

- Infers the app and lifecycle slice from ordinary user words.
- Creates app state immediately for safe local scope.
- Records what is missing as todos, blockers, or owner questions.
- Records provider-specific deployment prerequisites, including Cloudflare
  DNS/domain authority and Vercel hosting/deploy target access, without raw
  secrets.
- Produces worker packets when a visible worker thread is useful.
- Requires the review loop before accepting meaningful claims:
  `observe -> validate -> govern -> review -> sync`.
- Keeps non-claims explicit so local file proof is not mistaken for live,
  deployed, public, paid, credentialed, or full-lifecycle proof.
- Keeps local intent, planning, and engineering separate from deployment
  readiness; deployment or launch stays blocked until relevant provider access
  is validated through a safe connector, MCP, or brokered access path.
- Records review-ready cleanup scope in
  [docs/WEAVE_REVIEW_READY_COMPOUND_ENGINEERING.md](docs/WEAVE_REVIEW_READY_COMPOUND_ENGINEERING.md).
- Records cleanup proof in
  [docs/WEAVE_REVIEW_READY_CLEANUP_REPORT.md](docs/WEAVE_REVIEW_READY_CLEANUP_REPORT.md).
- Follows the prompt-bootstrap compound engineering contract in
  [docs/COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md](docs/COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md).

## Developer Commands

These commands are internal validation helpers. A normal user should not need to
run them to start WEAVE.

```bash
bin/weave cos-bootstrap --source . --intent "build a tiny local calculator app"
bin/weave readback --home runs/cos-weave-home
bin/weave eval --list
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 scripts/validate_docs_current.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
git diff --check
```

## Current Repository Shape

```text
AGENTS.md                         Public agent rules and first-contact contract.
COS_WEAVE_FIRST_CONTACT.md         Root activation contract.
COS_WEAVE_LAUNCHER.md              Tiny prompt for projectless remote-URL starts.
docs/                              Current contracts, blueprint, review, and eval docs.
packages/weave-tool/               Portable skills, lifecycle evals, and primitive registry.
scripts/weave_cos_skeleton.py       File-skeleton state engine.
scripts/weave_cli.py                Local validation CLI.
scripts/weave_eval.py               Evidence-bound eval runner.
tests/                             Current product and safety checks.
```

## Review Boundary

This repository is ready for review when the checks above pass. The allowed
public claim is:

```text
WEAVE provides a Codex-first, local-file COS skeleton that can bootstrap app
state from ordinary intent, maintain lifecycle/proof/review/readback files, and
avoid overclaiming live or public effects.
```

Not claimed unless separately implemented and proven:

- live worker execution;
- live tracker mutation;
- deployment or public release;
- public sends or marketing posts;
- billing, payments, paid calls, or value transfer;
- credential access or secret handling;
- full lifecycle completion for any app.

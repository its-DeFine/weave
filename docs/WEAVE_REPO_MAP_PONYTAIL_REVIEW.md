# WEAVE Repo Map And Ponytail Review

Status: DONE_FOR_REPO_MAP
Date: 2026-06-22

## Short Verdict

The repository is logically coherent for the current product boundary: COS
WEAVE is a Codex-first, local-file skeleton that records app intent, lifecycle
state, proof, blockers, review, worker packets, and readback.

I would use this repo to build and manage multiple app efforts through COS
WEAVE when the work is local-file-first and proof-bound. I would not treat it
as a live orchestration runtime, tracker bridge, deploy system, billing system,
credential broker, public-send tool, or full lifecycle automation product.

For this minimal goal, SOTA means the shortest reliable path that keeps state
durable after context compaction, lets a new agent resume without guessing, and
prevents local proof from turning into unearned live/public claims. It does not
mean maximum features. It means small, inspectable, validated, public-safe, and
hard to overclaim.

## Cleanup Completed In This Loop

- Lifecycle vocabulary is aligned to the canonical 11 stages:
  `intent`, `research`, `selection`, `plan`, `engineering`, `qa`,
  `deployment`, `kpi-setup`, `marketing`, `iteration`, and `analysis`.
- The generated sample skeleton now matches the real generated output shape,
  including intent truth, task ledgers, lifecycle state, per-stage procedures,
  proof, blockers, review, trays, and readback.
- The Livepeer-specific boundary skill moved out of the generic skill set and
  into `packages/weave-tool/extensions/livepeer/` as an optional domain
  extension.
- Runtime-agent governance was removed from the default lifecycle eval and
  skill surface so the current package does not imply required orchestration.
- Tests were added or updated to catch lifecycle vocabulary drift, package
  boundary drift, and sample/generated skeleton drift.

## Repo Map By Purpose

### Root Product Contract

| Item | Purpose | Usefulness | Ponytail judgment |
| --- | --- | --- | --- |
| `README.md` | First public explanation, first-contact trigger, skeleton shape, commands, non-claims. | keep | Minimum public entrypoint. It repeats critical first-contact behavior so agents and reviewers do not need hidden context. |
| `AGENTS.md` | Agent rules, source-of-truth order, safety boundary, required checks. | safety-critical | Repetition is tolerated because first-contact behavior depends on repo instructions being discovered early. |
| `COS_WEAVE_FIRST_CONTACT.md` | Root activation contract for `Use this repo as COS WEAVE`. | keep | Small dedicated contract; avoids burying the state-line rule in long docs. |
| `COS_WEAVE_LAUNCHER.md` | Copy-paste launcher for projectless remote-URL starts. | keep | Exists only because a URL-only thread cannot obey repo instructions before reading the repo. |
| `LICENSE` | MIT license. | keep | Required public package hygiene. |
| `VERSION` | Current package/repo version marker. | keep | One-line version is cheaper than deriving release identity from prose. |
| `requirements.txt` | Declares no third-party Python runtime dependency. | keep | Useful negative proof: stdlib-first product. |
| `.gitignore` | Keeps local runtime artifacts, envs, caches, and generated runs out of the repo. | safety-critical | Prevents private or noisy local state from becoming public. |
| `.dockerignore` | Keeps Docker/build contexts public-safe if used later. | keep | Boring guardrail; tiny cost, useful if packaging is tested. |

### GitHub And CI

| Item | Purpose | Usefulness | Ponytail judgment |
| --- | --- | --- | --- |
| `.github/` | GitHub-specific public review automation. | keep | One folder; no extra platform abstraction. |
| `.github/PULL_REQUEST_TEMPLATE.md` | Forces proof boundary, command ledger, and merge criteria in PRs. | safety-critical | Prevents vague PRs; not removable without losing governance. |
| `.github/workflows/public-safe-ci.yml` | Runs package validation, tests, secret scan, public-safe scan, diff check, and PR proof ledger. | safety-critical | CI mirrors the repo claim. No deploy/publish job is included. |

### Assets And Entry Point

| Item | Purpose | Usefulness | Ponytail judgment |
| --- | --- | --- | --- |
| `assets/` | Static public assets. | keep | Small, inspectable asset folder. |
| `assets/weave-hero.png` | README hero image. | simplify-later | Not core logic. Keep while it helps public orientation; delete if it becomes branding clutter. |
| `bin/` | User-facing local command entrypoints. | keep | Single shim folder is enough. |
| `bin/weave` | Shell wrapper choosing `.venv/bin/python` or `python3`. | keep | Minimal portable CLI entrypoint; no packaging/install ceremony required. |

### Current Docs

| Item | Purpose | Usefulness | Ponytail judgment |
| --- | --- | --- | --- |
| `docs/` | Public docs and review artifacts. | keep | Docs are part of the product because agents read them as operating instructions. |
| `docs/README.md` | Docs index and default reading order. | keep | Prevents stale docs from becoming accidental source of truth. |
| `docs/quickstart.md` | Short user/developer quickstart. | keep | Shortest path for local validation. |
| `docs/COS_WEAVE_BOOTSTRAP.md` | Prompt-first bootstrap contract and done boundary. | safety-critical | Core behavior contract; must stay explicit. |
| `docs/COS_WEAVE_REPO_SKELETON.md` | Canonical file/folder skeleton and lifecycle vocabulary. | safety-critical | Current structure source of truth. |
| `docs/COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md` | Acceptance slices for prompt bootstrap and first-run behavior. | keep | Tolerated complexity because it binds behavior to tests and prevents checklist-only proof. |
| `docs/WEAVE_VNEXT_GROUND_ZERO_CONTRACT.md` | Product boundary and non-claims for vNext. | keep | Keeps old product ambitions from defining the current repo. |
| `docs/WEAVE_SERVICE_BLUEPRINT.md` | Frontstage/backstage service model. | keep | Small enough and useful for owner mental model. |
| `docs/WEAVE_CHIEF_OF_STAFF_UX.md` | COS WEAVE user experience contract. | keep | Explains user-visible behavior without adding UI code. |
| `docs/WEAVE_INTENT_TRUTH_AND_COMPLETION_CONTRACT.md` | Intent truth, required-stage matrix, and completion boundary. | keep | More complex than the skeleton, but tolerated because it blocks false done claims. |
| `docs/WEAVE_OBSERVABILITY_EVAL_GOVERNANCE.md` | Proof and governance principles. | keep | Supports review discipline; no runtime feature creep. |
| `docs/WEAVE_REVIEW_LOOP_PROCESS.md` | `observe -> validate -> govern -> review -> sync`. | safety-critical | Small mandatory loop that keeps proof and state synchronized. |
| `docs/COMPOUND_ENGINEERING.md` | Agentic engineering loop and owner-facing proof model. | keep | Useful as operating philosophy; avoid expanding it into product surface. |
| `docs/WEAVE_HARNESS_ENGINEERING_ADOPTION.md` | Harness packet shape and safety discipline. | keep | Reinforces bounded execution and proof. |
| `docs/WEAVE_REVIEW_READY_COMPOUND_ENGINEERING.md` | Cleanup contract for the review-ready pruning. | keep | Historical proof of scope; delete only after release notes replace it. |
| `docs/WEAVE_REVIEW_READY_CLEANUP_REPORT.md` | Cleanup proof report and non-claims. | keep | Review artifact; useful for controller traceability. |
| `docs/lifecycle-evals.md` | Eval contract guide. | keep | Small bridge between CLI and eval files. |
| `docs/pr-proof-ledger.md` | PR proof-ledger reference. | keep | Supports CI and reviewer expectations. |
| `docs/WEAVE_REPO_MAP_PONYTAIL_REVIEW.md` | This file: durable repo map and usefulness review. | keep | Closes the original owner request without adding code. |

### Generated Sample Skeleton

| Item | Purpose | Usefulness | Ponytail judgment |
| --- | --- | --- | --- |
| `docs/samples/` | Public sample area. | generated-sample | Kept because the product is a file skeleton; reviewers need to inspect a real example. |
| `docs/samples/cos-weave-skeleton/` | Sanitized generated sample of `runs/cos-weave-home/`. | generated-sample | Tolerated file volume because parity tests catch drift and the sample demonstrates compaction-survivable state. |
| `docs/samples/cos-weave-skeleton/README.md` | Explains the sample is generated and public-safe. | keep | Prevents reviewers from mistaking sample paths for private local state. |
| `docs/samples/cos-weave-skeleton/state.json` | Home state and active app pointer. | generated-sample | Machine-readable proof of home shape. |
| `docs/samples/cos-weave-skeleton/owner-profile.md` and `owner-profile.json` | Draft owner profile surfaces. | generated-sample | Shows identity is a todo, not a hard blocker. |
| `docs/samples/cos-weave-skeleton/apps/registry.json` | App registry and active app pointer. | generated-sample | Required for multi-app resume. |
| `docs/samples/cos-weave-skeleton/apps/tiny-local-calculator/` | Example app workspace. | generated-sample | One app is enough to demonstrate structure without inventing demo apps. |
| `app.json`, `intent.md`, `intent.json`, `intent-truth.json` | App metadata and intent truth boundary. | generated-sample | Tolerated duplication because Markdown is owner-readable and JSON is resumable. |
| `lifecycle.json` and `lifecycle/lifecycle-state.json` | Lifecycle state and canonical stage rows. | generated-sample | Duplication tolerated for simple top-level read and nested lifecycle folder parity. |
| `lifecycle/01-intent/` through `lifecycle/11-analysis/` | Per-stage procedure and state files. | generated-sample | Verbose but intentionally generated; proves every canonical stage has durable state. |
| `todos.md` | Owner/agent next actions. | generated-sample | Human-readable minimal task surface. |
| `tasks.json`, `tasks/tasks.json`, `tasks/worker-packets/WP-0001.md` | Local task ledger and worker packet reference. | generated-sample | Tolerated compatibility duplication; simplify only after consumers settle. |
| `worker-packets/WP-0001.md` | Human-visible worker packet. | generated-sample | Useful when pinned workers exist; harmless local file when they do not. |
| `proof/proof-tray.json`, `blockers/blocker-tray.json`, `review/review-queue.json`, `updates/readback.json` | App-level proof, blocker, review, and readback trays. | generated-sample | Safety-critical surfaces for not overclaiming. |
| `procedures/lifecycle/*.md` | Home-level stage procedures. | generated-sample | Tolerated because generated agents need deterministic restart instructions. |
| `tasks/worker-packets.json`, `proof/tray.json`, `blockers/tray.json`, `review/queue.json`, `inbox/review-queue.json`, `updates/readback.json`, `updates/events.jsonl`, `cos-bootstrap/latest.json` | Home-level indexes, trays, readback, event, and bootstrap proof. | generated-sample | Useful resumability and proof envelope; keep while the sample parity test covers shape. |

### Portable Package

| Item | Purpose | Usefulness | Ponytail judgment |
| --- | --- | --- | --- |
| `packages/` | Portable package root. | keep | One package folder; no multi-package architecture. |
| `packages/weave-tool/` | Public behavior layer for skills, evals, primitives, and validator. | keep | Small package surface aligned to COS skeleton. |
| `packages/weave-tool/COMPANY.md` | Package identity, version, and boundary. | keep | Required for portable package validation. |
| `packages/weave-tool/README.md` | Package contents and validation command. | keep | Minimal package-specific orientation. |
| `packages/weave-tool/primitives/registry.json` | Lifecycle primitive map. | keep | Useful compact index; no code needed. |
| `packages/weave-tool/scripts/validate_company_package.py` | Package shape validator. | safety-critical | Keeps package contents deliberate. Stdlib-only and strict. |
| `packages/weave-tool/skills/` | Generic COS WEAVE skills. | keep | Skills are docs-as-capability; no runtime dependency. |
| `skills/cos-weave/SKILL.md` | Activation behavior. | safety-critical | Core package skill. |
| `skills/compound-engineering/SKILL.md` | Agentic engineering loop. | keep | Useful operating pattern; keep bounded. |
| `skills/weave-lifecycle/SKILL.md` | Lifecycle dependency rules. | keep | Keeps stage order explicit. |
| `skills/implementation-planning/SKILL.md` | Bounded work packet planning. | keep | Prevents scope drift before implementation. |
| `skills/engineering-execution/SKILL.md` | Scoped implementation behavior. | keep | Useful for worker consistency. |
| `skills/qa-verification/SKILL.md` | Verification behavior and claim limits. | safety-critical | Keeps tests tied to claims. |
| `skills/evidence-packet/SKILL.md` | Reviewable evidence packet shape. | keep | Short enough and proof-focused. |
| `skills/security-release-review/SKILL.md` | Public release safety review. | safety-critical | Public repo needs this. |
| `skills/codebase-orientation/SKILL.md` | Repo orientation before edits. | keep | Helps workers avoid blind changes. |
| `skills/primitive-market-research/SKILL.md` | Research stage support. | simplify-later | Useful for lifecycle completeness; delete if real usage stays engineering-only. |
| `packages/weave-tool/evals/` | Lifecycle and release eval contracts. | keep | Eval contracts are lightweight JSON-compatible YAML, not a framework. |
| `evals/lifecycle/*.yaml` | Intent through Analysis stage review rubrics. | safety-critical | Prevents stage advancement by prose alone. |
| `evals/release_readiness.yaml` | Repo release/readiness gate. | safety-critical | Mirrors the public review claim. |
| `packages/weave-tool/extensions/` | Optional domain extensions outside the generic package surface. | optional-extension | Keeps domain context without polluting the default package. |
| `extensions/livepeer/skills/livepeer-adapter-boundary/SKILL.md` | Livepeer-specific proof boundary skill. | optional-extension | Useful context preserved, but intentionally not required by the generic validator. |

### Scripts

| Item | Purpose | Usefulness | Ponytail judgment |
| --- | --- | --- | --- |
| `scripts/` | Repo-local validation and skeleton helpers. | keep | Small stdlib scripts instead of service/runtime dependency. |
| `scripts/weave_cli.py` | Local CLI router for bootstrap, readback, eval. | keep | Thin command surface; no speculative CLI commands. |
| `scripts/weave_cos_skeleton.py` | File skeleton generator/readback engine. | safety-critical | Largest script because it owns generated state; tolerated because it is deterministic, stdlib-only, and tested. |
| `scripts/weave_eval.py` | Evidence-bound eval runner. | safety-critical | More complex than a shell script, but needed for hard gates, reviews, and score binding. |
| `scripts/check_no_secrets.py` | Secret/private value scanner. | safety-critical | Public repo guardrail. False positives are acceptable. |
| `scripts/public_safe_repo_scan.py` | Scanner for private paths, topology, and legacy surfaces. | safety-critical | Prevents stale/private product surfaces from leaking back in. |
| `scripts/validate_docs_current.py` | Docs-currentness validator for lifecycle vocabulary, product boundary, optional extension boundary, repo-map gates, and non-claims. | safety-critical | Small stdlib lint gate that catches stale docs without adding a parser framework. |
| `scripts/validate_pr_proof_ledger.py` | PR body proof-boundary checker. | safety-critical | Keeps public PRs evidence-backed without GitHub API calls. |

### Tests

| Item | Purpose | Usefulness | Ponytail judgment |
| --- | --- | --- | --- |
| `tests/` | Unit and contract tests. | safety-critical | Tests are the smallest durable proof that docs, code, package, sample, and scanners agree. |
| `test_weave_cli.py` | CLI bootstrap/readback/help/lifecycle alignment tests. | safety-critical | Catches command-surface drift. |
| `test_cos_weave_bootstrap_contract.py` | Prompt-first contract, docs, sample, and sample-parity tests. | safety-critical | Prevents a checklist-only repo from passing review. |
| `test_cos_weave_prompt_bootstrap_ce.py` | Compound-engineering bootstrap contract tests. | keep | Ensures the prompt-first acceptance bar remains visible. |
| `test_weave_eval.py` | Eval runner tests for gates, reviews, aliases, scoring, and evidence. | safety-critical | Protects the proof engine. |
| `test_weave_company_package.py` | Package validator and package boundary tests. | safety-critical | Catches accidental skill/eval/primitive drift. |
| `test_check_no_secrets.py` | Secret scanner behavior tests. | safety-critical | Prevents scanner regressions. |
| `test_public_safe_repo_scan.py` | Public-safe scanner behavior tests. | safety-critical | Keeps private/stale surface detection explicit. |
| `test_validate_docs_current.py` | Docs-currentness validator tests. | safety-critical | Ensures docs stay aligned to the current COS-first local-file skeleton. |
| `test_validate_pr_proof_ledger.py` | PR proof-ledger validator tests. | safety-critical | Keeps CI proof checks predictable. |

## What Is Missing

### Required Before External Review

- Local validation must pass in this worktree, including docs-currentness,
  package, unit, secret, public-safe, and diff checks.
- Controller diff review must inspect the full patch set and decide whether
  the public review claim is acceptable.
- Integration/commit into the intended branch must happen before any external
  review claim is final.
- Push/PR update must happen before remote reviewers can inspect the final
  branch.
- GitHub CI must pass on the PR or target branch before claiming the remote
  review surface is green.

### Required Before Real Users

- Use `docs/WEAVE_CONCEPT_CHANGE_MAINTAINER_PLAYBOOK.md` when the default
  concept changes, including the sample refresh command for
  `docs/samples/cos-weave-skeleton/`.
- Clearer owner-facing examples for multi-app resume and for moving from
  Intent to Plan/Engineering without implying full lifecycle completion.
- More failure-path examples for blocked source path, URL-only local CLI, and
  owner-gated external actions.
- A small compatibility decision on duplicate generated files such as
  `tasks.json` plus `tasks/tasks.json`, and root worker packet plus nested task
  worker packet.

### Future Extension Only

- Live worker creation or thread pinning.
- Tracker or Linear mutation.
- Deployment and public launch flows.
- Public sends or marketing posts.
- Billing, payments, paid calls, or value transfer.
- Credential access, secret brokers, browser sessions, or private runtime
  topology.
- Hosted UI or terminal cockpit.
- Domain extension packages beyond the optional Livepeer boundary.

## Code Quality Review

- Scripts: relevant and well-made for the stated goal. They are stdlib-only,
  command-line friendly, deterministic, and bounded. `weave_cos_skeleton.py`
  is the only large script because it writes the full state surface.
- Tests: strong for a local-file skeleton. They cover bootstrap discovery,
  sample parity, lifecycle vocabulary, eval behavior, package validation,
  safety scans, and PR proof rules.
- Evals: useful and intentionally strict. They avoid needing a service while
  still requiring evidence before advancement.
- Package validator: relevant and well-scoped. It keeps the generic package
  surface deliberate and leaves domain work in `extensions/`.
- Sample skeleton: useful because it matches generated shape and is sanitized.
  File count is tolerated because the product itself is a file skeleton.
- Docs: coherent now. Some docs are governance-heavy, but that complexity is
  accepted because proof boundaries are the product's value.
- CI: appropriate for public review. It validates package, tests, secrets,
  public-safe surfaces, diff hygiene, and PR proof ledger. It does not deploy.

## Non-Claims

This repo map and the current local checks do not prove:

- live worker execution;
- live tracker or Linear mutation;
- production deploy;
- public send or marketing post;
- billing, payment, paid call, custody, or value transfer;
- credential access or secret handling;
- full lifecycle completion for a real app.

## Proof Commands

Current required proof state for this patch set: PASS.

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validate_docs_current.py
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
git diff --check
```

Additional proof used by the repo quality loop:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
bin/weave cos-bootstrap --source . --intent "build a tiny local calculator app"
bin/weave readback --home runs/cos-weave-home
python3 -m unittest tests.test_cos_weave_bootstrap_contract.CosWeaveBootstrapContractTests.test_repo_skeleton_sample_matches_generated_file_shape
```

Observed state: all pass locally in this worktree.

## Owner-Facing Statement

DONE_FOR_REPO_MAP.

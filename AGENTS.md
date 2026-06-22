# WEAVE Public Repository Agent Rules

This repository is public. Treat every commit, branch, pull request, log, and
artifact as publishable by default.

## Source-Of-Truth Map

Keep this file short. It is a public-safe map, not the full operating manual.
For durable WEAVE/COS decisions, read the focused source document:

- `docs/WEAVE_VNEXT_GROUND_ZERO_CONTRACT.md` for product, lifecycle, proof, and
  done-state rules.
- `docs/WEAVE_HARNESS_ENGINEERING_ADOPTION.md` for harness-engineering rules:
  repo-local knowledge, progressive disclosure, agent-legible validation
  surfaces, feedback loops, mechanical checks, and garbage collection.
- `docs/COMPOUND_ENGINEERING.md` for the agentic engineering loop: plans for
  agents, capability printers, CLI plus skill, adversarial review, PR testing
  governance, and launch-readiness separation.
- `docs/WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md` for the methodical WEAVE-to-Symphony
  adapter plan, data contracts, test ladder, proof boundaries, and continuous
  compound-engineering use.
- `docs/WEAVE_OBSERVABILITY_EVAL_GOVERNANCE.md` for eval, governance, and
  scorecard rules.
- `docs/WEAVE_REVIEW_LOOP_PROCESS.md` for create/observe/validate/govern/
  review/sync.

## Confidential Topology Boundary

Do not commit or mention private operating details, including:

- internal device nicknames, workstation names, runtime host names, or service names
- overlay-network vendor names, VPN product names, private route names, private
  IPs, or private DNS names
- runtime isolation names, container names, host-specific usernames, home
  directories, SSH key paths, or operator shell commands
- credential locations, auth payloads, refresh tokens, API keys, secrets,
  Keychain item names, or secret manager object names
- private repo names, unpublished runbooks, private deployment topology, or
  owner-specific access procedures

Use generic language such as `remote runtime`, `owner-approved transport`,
`private runtime address`, and `private runtime home` when a public artifact
needs to describe a capability boundary.

## Required Checks

Before committing or pushing public changes, run:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/runtime_smoke.py
git diff --check
```

If any check fails, fix the source artifact and amend the relevant commit. Do
not add a follow-up cleanup commit for confidential-info removal on an open PR.

## COS Anti-Repeat Guardrail

WEAVE/COS agents must treat owner prompts as normal-user intent, not as test
scripts. If a claim is about Codex, Hermes, worker spawning, pinned threads,
onboarding, lifecycle routing, or owner-facing behavior, local CLI artifacts are
supporting evidence only. The claim cannot be accepted until the target surface
is exercised or the missing target-surface proof is recorded as a non-claim.

Before claiming `READY_FOR_REVIEW` or `DONE`, check:

- prior context and memory-derived failure patterns were considered without raw
  transcripts, raw logs, secrets, or private topology;
- the tested user flow did not depend on the owner using WEAVE vocabulary or an
  explicit test checklist;
- proof is bound to the actual claim and acceptance check;
- assumptions, missing surfaces, and non-claims are visible;
- completion state, proof state, and owner mental model have been synced.

For WEAVE/COS changes, run the `cos-runtime-truth` eval or explain why it is not
applicable. Explicit prompt compliance is not enough to prove WEAVE works.

## Visible Worker Rule

For COS-managed durable work, "create an agent" means create a visible pinned
Codex instance/thread with a task packet and proof path. Hidden helper workers
may be used only as disposable support, must be labeled as such, and must not be
presented as the owner-visible COS agent.

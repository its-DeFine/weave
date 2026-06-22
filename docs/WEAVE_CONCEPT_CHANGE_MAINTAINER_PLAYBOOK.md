# WEAVE Concept Change Maintainer Playbook

Status: ACTIVE_MAINTAINER_GUIDE
Date: 2026-06-22

## Purpose

Use this playbook when the default WEAVE concept changes. A concept change is
not done when one document or command is updated. It is done when the public
docs, package boundary, generated sample, tests, validators, and non-claims all
describe the same product.

The current default concept is COS WEAVE: a Codex-first, local-file skeleton
that records app intent, lifecycle state, tasks, worker packets, proof,
blockers, review, and readback. Optional or future capabilities must stay
clearly labeled as optional or future-only.

## When To Update Each Surface

Update docs when the owner-facing model, first-contact behavior, lifecycle
vocabulary, proof boundary, command list, package contents, sample shape, or
non-claims change.

Update code when the file skeleton, CLI behavior, readback shape, eval runner,
package validator, scanner behavior, or generated sample shape must change to
make the new concept real.

Update the generated sample when generator output, lifecycle stage names,
folder layout, proof/blocker/review/readback trays, task ledgers, or app
metadata change. The sample is product evidence, not decorative documentation.

Update tests when a change should be guarded from regressing. At minimum, add
or adjust tests for first-contact behavior, lifecycle vocabulary, generated
sample parity, package boundary, scanners, eval contracts, and docs-currentness
when those surfaces move.

Update `scripts/validate_docs_current.py` when a new public source-of-truth doc
is added, a stale vocabulary class is discovered, a non-claim becomes mandatory,
the optional-extension boundary changes, or the canonical lifecycle vocabulary
changes.

## Change Procedure

1. Name the concept change in one sentence using default-product language.
2. Identify the owner-facing claim that will be allowed after validation.
3. Update source-of-truth docs first: `README.md`, `AGENTS.md`, `docs/README.md`,
   `docs/COS_WEAVE_BOOTSTRAP.md`, `docs/COS_WEAVE_REPO_SKELETON.md`, and
   `docs/WEAVE_VNEXT_GROUND_ZERO_CONTRACT.md` when applicable.
4. Update package docs, skills, evals, primitives, and validators only where
   the concept change needs machine-checkable behavior.
5. Regenerate or update `docs/samples/cos-weave-skeleton/` if the generator
   shape changed.
6. Add or update tests before claiming the concept is protected.
7. Run the command ledger below and fix the source artifact that caused any
   failure.
8. Record non-claims for surfaces that are still not proven.

## Sample Refresh Command

Use this only when the committed sample should move with the generator shape:

```bash
bin/weave cos-bootstrap --source . --home docs/samples/cos-weave-skeleton --intent "build a tiny local calculator app" --app-id tiny-local-calculator --app-name "Tiny Local Calculator" --json
```

Then inspect `git status --short` and remove any deliberately obsolete sample
files as a separate reviewed change. The parity test below proves file-shape
agreement with a fresh generated home.

## Required Command Ledger

Run these before claiming a concept/currentness change is review-ready:

```bash
python3 scripts/validate_docs_current.py
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
git diff --check
```

Useful focused checks while iterating:

```bash
python3 -m unittest tests.test_cos_weave_bootstrap_contract.CosWeaveBootstrapContractTests.test_repo_skeleton_sample_matches_generated_file_shape
python3 -m unittest tests.test_validate_docs_current
```

## What The Docs-Currentness Validator Proves

`scripts/validate_docs_current.py` can prove that:

- canonical lifecycle stage files and IDs are present and old stage IDs are not
  still used in text surfaces it scans;
- core public docs and generic package docs avoid default-language references
  to non-default product surfaces;
- the optional extension boundary stays outside the generic package surface;
- the repo map contains external-review gates and does not overclaim;
- mandatory non-claims remain visible in the public docs.

It cannot prove:

- the concept change is the right product decision;
- every sentence in every document is semantically complete;
- another worktree, branch, pull request, or remote CI run contains the change;
- live workers, live tracker mutation, deployment, public sends, billing,
  credential access, or full lifecycle completion;
- sample content quality beyond the tests and review surfaces that inspect it.

## Stale-Reference Guardrails

Default docs should describe only the current default concept. Previous
functionality belongs in explicit future-only, optional-extension, or non-claim
sections, not in first-contact instructions.

Before closing a concept change:

- search for the old concept name, old stage names, old command names, and old
  proof claims with targeted `rg` commands;
- update the docs index and first-contact docs so a new agent reads the current
  path first;
- remove stale generated sample files when the generator no longer emits them;
- add a validator rule if the stale reference class is likely to recur;
- state what is not integrated or not proven instead of treating local docs as
  remote review proof.

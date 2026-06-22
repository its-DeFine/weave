# WEAVE Review-Ready Cleanup Report

Date: 2026-06-22
State: ACCEPT_FOR_SCOPE for repository review

## What Changed

- Removed legacy application examples, old runtime code, old terminal cockpit
  code, historical proof dumps, obsolete schemas, old prompt packs, and tests
  tied to deleted surfaces.
- Rewrote the public docs around one current product path: COS WEAVE in Codex,
  local file skeleton, lifecycle state, proof, blockers, review, and readback.
- Reduced the package to the current portable skill/eval/primitive set.
- Simplified CI to package validation, unit/contract tests, secret scan,
  public-safe scan, diff hygiene, and PR proof-ledger validation.
- Added a review-ready compound-engineering contract for this cleanup.

## What Remains

- `bin/weave`
- `scripts/weave_cli.py`
- `scripts/weave_cos_skeleton.py`
- `scripts/weave_eval.py`
- `packages/weave-tool/`
- current COS WEAVE docs and sample file skeleton
- current tests and public-safety scanners

These remain because they directly support prompt-first COS WEAVE bootstrap,
local file-backed app state, lifecycle evals, proof boundaries, and repository
review.

## Validation Run

All of these passed locally:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
git diff --check
bin/weave cos-bootstrap --source . --intent "build a tiny local calculator app"
bin/weave readback --home runs/cos-weave-home
bin/weave eval release-readiness --run-gates --strict --review-file runs/release-readiness-review.json
```

Release-readiness eval result:

- hard gates: passed
- rubric score: 24/24
- eval state: verified; approval-gated
- blockers: none

## Still Not Proven

- production deployment
- public posting or sending
- paid actions or value transfer
- credential access
- live tracker mutation
- full lifecycle completion for a real app

Those are intentionally outside this cleanup scope.

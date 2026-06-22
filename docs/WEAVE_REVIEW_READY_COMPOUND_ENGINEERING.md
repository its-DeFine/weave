# WEAVE Review-Ready Compound Engineering Contract

Status: executed cleanup contract
Date: 2026-06-22

## Objective

Make the WEAVE repository review-ready for the current vNext product:
COS-first, Codex-first, repository-skeleton-based, local-file state, deterministic
lifecycle prompts, evidence-bound review, and no legacy product surface in the
public default path.

## Target Surface

- Public GitHub repository and PR branch.
- Local repo files, docs, package skills, eval contracts, scripts, CI, and tests.
- No live deploy, public send, paid call, credential access, or tracker mutation.

## Current Model

WEAVE is one Chief of Staff thread operating over a visible file skeleton:

```text
Codex thread + WEAVE repo URL/path + ordinary app intent
-> COS WEAVE state line
-> runs/cos-weave-home/
-> app folders, lifecycle state, todos, worker packets, proof, blockers, review, readback
```

## Expected Change

Remove or rewrite anything that teaches a different default product. Keep only
surfaces that support:

- prompt-first activation;
- file-backed app state;
- lifecycle contracts;
- worker packets as files;
- proof and blocker trays;
- review-loop decisions;
- public-safe validation.

## Deletion Rule

Delete legacy code, docs, tests, examples, and package surfaces when they are
not needed for the current model. Do not keep obsolete material as "optional"
inside the review path, because that makes the product harder to understand and
harder to validate.

## Proof Path

The cleanup is acceptable only if all pass:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
git diff --check
bin/weave cos-bootstrap --source . --intent "build a tiny local calculator app"
bin/weave readback --home runs/cos-weave-home
```

## Adversarial Review Questions

- Can a new user understand the product from README and docs without knowing
  historical experiments?
- Can a Codex instance become COS WEAVE from repo URL/path plus ordinary intent?
- Does the repo create visible app state instead of depending on hidden context?
- Are lifecycle claims bounded to what was actually run and reviewed?
- Are live/public/paid/credentialed/tracker-changing effects explicitly
  outside the default proof claim?
- Do tests fail if old product surfaces return to public docs or package files?
- Does CI validate the same claims made in the PR?

## Exit Condition

`ACCEPT_FOR_SCOPE` when the repo is tidy, public-safe, test-passing, and clear
about what is proven. `REVISE` if stale surfaces remain. `BLOCKED` only if local
validation or GitHub push/checks are unavailable for reasons outside the repo.

## Allowed Claim After Passing

WEAVE provides a Codex-first, local-file COS skeleton that can bootstrap app
state from ordinary intent, maintain lifecycle/proof/review/readback files, and
avoid overclaiming live or public effects.

## Non-Claims

This cleanup does not prove production deployment, public posting, paid
actions, credential access, live tracker mutation, or full lifecycle completion
for any real app.

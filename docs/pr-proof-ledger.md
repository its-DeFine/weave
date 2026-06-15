# PR Proof Ledger And Merge Criteria

Status: public-safe merge contract.

Every WEAVE PR must record the issue, proof commands, proof boundaries, and
merge criteria in the PR body. The goal is to prevent code merge, local proof,
runtime proof, and live/user-facing proof from being collapsed into one claim.

## Required Local Check Packet

Run these before opening or merging a lifecycle/productization PR:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
python3 scripts/validate_lifecycle_artifacts.py docs/samples/lifecycle-artifacts.example.json
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/runtime_smoke.py
git diff --check
```

When lifecycle fixtures, gates, or stage ordering change, also run:

```bash
python3 scripts/lifecycle_rehearsal_smoke.py --report-out /tmp/weave-lifecycle-rehearsal.json
```

## PR Body Requirements

CI validates PR bodies with:

```bash
python3 scripts/validate_pr_proof_ledger.py
```

The PR body must include:

- Linear issue identifier or link;
- proof ledger with at least one checked proof command;
- local proof boundary;
- runtime/live proof boundary;
- unproven boundaries or non-claims;
- failing checks disposition;
- owner/project criteria disposition.

Unchecked template checkboxes are not allowed to remain in a ready PR.

## Merge Criteria

A PR can merge only when:

- required local checks are recorded in the PR proof ledger;
- GitHub CI is green;
- public-safety/no-secret checks pass;
- any failed, skipped, blocked, or waived check is explicitly documented and
  accepted before merge;
- claims in the PR body do not exceed the strongest proof surface actually
  exercised.

Local deterministic proof does not prove live Hermes/Telegram behavior, deployed
behavior, public-send behavior, analytics, payments, or real-user traction.

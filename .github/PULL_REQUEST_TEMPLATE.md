## Issue
<!-- Include the issue identifier or link, for example ATM-250. -->

## Summary
<!-- What changed? Keep this owner-readable and public-safe. -->

## Proof Boundary
- Local proof:
- Live/public proof:
- Non-claims:

## Proof Ledger
- [ ] `python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool`
- [ ] `python3 -m unittest discover -s tests -p 'test_*.py'`
- [ ] `python3 scripts/check_no_secrets.py`
- [ ] `python3 scripts/public_safe_repo_scan.py`
- [ ] `git diff --check`

## Merge Criteria
- [ ] Failing checks: none, or documented and accepted by the owner/project criteria.
- [ ] Owner/project criteria satisfied.

# PR Proof Ledger

Every review-ready PR must include a proof ledger in the PR body.

Required sections:

- issue or tracker identifier;
- proof boundary or non-claims;
- proof ledger;
- merge criteria.

Required statements:

- local proof;
- live/public proof or explicit non-claim;
- failing checks disposition;
- owner/project criteria disposition;
- at least one executable proof command.

Example:

```markdown
## Proof Boundary
- Local proof: unit tests and public-safe scans.
- Live/public proof: not claimed.
- Non-claims: no deploy, no public send, no paid action.

## Proof Ledger
- [x] `python3 -m unittest discover -s tests -p 'test_*.py'`
```

Validator:

```bash
python3 scripts/validate_pr_proof_ledger.py --body-file <body.md>
```

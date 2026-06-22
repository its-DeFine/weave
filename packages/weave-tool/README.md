# WEAVE Tool Package

Status: public COS WEAVE package

This package is the portable behavior layer for WEAVE vNext. It is intentionally
small: skills, lifecycle evals, primitive registry, and a package validator.

## Validate

From the repository root:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
```

Expected shape:

```text
valid WEAVE package: weave
version: 2026.06.22-cos-skeleton
skills: 11
primitives: 11
eval_contracts: 12
```

## Contents

- `COMPANY.md`: package identity and public boundary.
- `skills/cos-weave/SKILL.md`: how an agent becomes COS WEAVE from repo URL/path.
- `skills/compound-engineering/SKILL.md`: agentic engineering loop.
- `skills/*/SKILL.md`: supporting planning, execution, QA, evidence, and release review skills.
- `evals/lifecycle/*.yaml`: lifecycle evidence contracts.
- `evals/release_readiness.yaml`: review-readiness gate.
- `primitives/registry.json`: lifecycle primitive map.
- `scripts/validate_company_package.py`: public package validator.

## Boundary

This package can be imported by a Codex agent or read directly from the repo.
It does not contain private paths, credentials, service setup, or live
integration instructions. Those belong in a separate approved implementation
packet if ever needed.

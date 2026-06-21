# WEAVE Skill Audit and Archive Plan

Status: audit, no deletions performed
Date: 2026-06-21

## Simple Model

The current skill package is not ready for blind cleanup. The validator requires
many skills explicitly, and every agent has a declared skill list. If files are
deleted without changing those contracts, the package breaks.

The correct cleanup sequence is:

1. classify the current skills;
2. decide the vNext core set from the ground-zero contract;
3. merge or rewrite overlapping skills;
4. update agent skill lists and validator requirements;
5. archive old skills with a reversible commit;
6. run package validation and public-safety checks.

## Current Inventory

| Skill | Agent refs | Current reading |
| --- | ---: | --- |
| `cos-weave` | 7 | Core vNext. Keep and rewrite around natural-language COS behavior. |
| `weave-lifecycle` | 6 | Core vNext. Keep, but align stages to the ground-zero contract. |
| `evidence-packet` | 7 | Core vNext. Keep and make proof envelopes first-class. |
| `implementation-planning` | 4 | Core vNext. Keep and now includes minimum-necessary planning. |
| `engineering-execution` | 1 | Core vNext. Keep and now includes minimum-necessary execution. |
| `qa-verification` | 2 | Core vNext. Keep and connect directly to review loops/evals. |
| `codebase-orientation` | 2 | Keep. Required before editing stale or accreted surfaces. |
| `security-release-review` | 3 | Keep. Public repo release boundary depends on it. |
| `runtime-app-attachment` | 7 | Rewrite. Useful principle, but current wording is runtime-heavy for vNext. |
| `gestalt-runtime` | 1 | Park pending Hermes vNext. Do not delete until Hermes adapter decision. |
| `runtime-bridge` | 3 | Park pending Hermes/transport decision. Likely merge into runtime attachment. |
| `lifecycle-runtime-builder` | 4 | Archive candidate. Looks like legacy local-runtime scaffolding. |
| `livepeer-adapter-boundary` | 4 | Archive or move to optional adapter pack unless Livepeer is active scope. |
| `primitive-market-research` | 4 | Merge candidate. Research belongs in lifecycle, not a standalone default skill. |

## Keep Set for vNext Core

The likely core set after reset is:

- `cos-weave`
- `weave-lifecycle`
- `evidence-packet`
- `implementation-planning`
- `engineering-execution`
- `qa-verification`
- `codebase-orientation`
- `security-release-review`

These map directly to the current WEAVE promise: understand intent, plan the
slice, execute minimally, verify the actual claim, and record public-safe proof.

## Rewrite Set

`runtime-app-attachment` should survive as a concept but not as the current
runtime-heavy default. In vNext it should become a generic target-surface
attachment skill:

- attach to Codex when the claim is about Codex;
- attach to Hermes when the claim is about Hermes;
- attach to browser, tracker, repo, or deployment surface only when claimed;
- record non-claims when the target surface was not exercised.

## Parked Optional Pack

These should not be default skills until the ground-zero contract says they are
needed for the current product:

- `gestalt-runtime`
- `runtime-bridge`
- `livepeer-adapter-boundary`

They may become optional adapter packs instead of core skills.

## Archive Candidates

These are the first cleanup candidates after the contract is accepted:

- `lifecycle-runtime-builder`
- `primitive-market-research`

Reasoning:

- both can be folded into lifecycle/planning/research flow;
- both increase the default surface area;
- neither is necessary for the first Codex COS user journey unless the contract
  admits it explicitly.

## Required Code Changes Before Archiving

Before any archive/delete operation:

- remove archived skills from affected `agents/*/AGENTS.md` frontmatter;
- update `REQUIRED_SKILLS` in `packages/weave-tool/scripts/validate_company_package.py`;
- update tests that assert package skill count or required skill presence;
- add a migration note that maps old skill names to new core responsibilities;
- run package validation, unit tests, secret scan, public-safe scan, and diff
  whitespace checks.

## Stop Boundary

No skill is deleted in this pass. The current output is an audit plan because
deletion before the ground-zero contract would repeat the same failure pattern:
editing the shape before agreeing on what the shape must be.

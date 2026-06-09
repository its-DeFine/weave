# Private App Operating Profile Evaluations

Status: local deterministic evaluation harness

## Purpose

This harness tests whether WEAVE Operating Profiles can produce reviewable app
artifacts for private, non-public products. The point is not marketing or live
traction. The point is to build multiple useful local app proofs in parallel and
make the agent's cognitive model inspectable after the run.

Each scenario uses synthetic private-domain data. The generated apps are static,
local-only, and dependency-free.

## What it proves

- WEAVE can run a deterministic parallel evaluation across several private app
  scenarios.
- Each app output includes source files, a local assessment report, and a
  cognitive artifact bundle.
- The profile makes CWA, DMN, IBIS, ADR, and PROV use reviewable as concrete
  files instead of invisible reasoning claims.
- The aggregate report lets reviewers compare scenario outcomes without reading
  every generated file first.

## What it does not prove

- It is not live Hermes CLI proof.
- It is not Telegram or deployed-gateway proof.
- It is not hosted application proof.
- It is not marketing, analytics, payment, or real-user traction proof.
- It does not process real private customer data.

## Operating profile

The concrete profile lives at:

- `packages/weave-tool/process-profiles/private-app-parallel-assessment.json`

The schema lives at:

- `packages/weave-tool/process-profiles/schemas/operating-profile.schema.json`

Key profile fields:

- `trigger_mode`: `reactive`
- `authority_mode`: `recommend_only`
- `target_surface`: local generated static apps plus deterministic cognitive
  evidence artifacts
- `private_data_policy.real_private_data_allowed`: `false`
- `private_data_policy.synthetic_private_data_allowed`: `true`
- `private_data_policy.external_send_allowed`: `false`
- `evaluation.marketing_included`: `false`

## Cognitive artifacts per app

Every generated app gets:

- `intent-frame.json`
- `profile-selection.json`
- `cwa-work-domain.json`
- `dmn-decision-table.json`
- `ibis-map.json`
- `adr-0001-local-private-first.md`
- `action-intent.json`
- `action-result.json`
- `prov-ledger.jsonl`
- `assessment-report.json`

The aggregate run also writes:

- `aggregate-report.json`
- optional Markdown report if `--report-out` is supplied

## Run it

```bash
mkdir -p runs/private-app-operating-profile-evals
python3 scripts/private_app_operating_profile_eval.py \
  --output-dir runs/private-app-operating-profile-evals/artifacts \
  --report-out runs/private-app-operating-profile-evals/report.md \
  --parallel 4 \
  --force
```

List scenarios:

```bash
python3 scripts/private_app_operating_profile_eval.py --list
```

Run one scenario:

```bash
python3 scripts/private_app_operating_profile_eval.py \
  --scenario runway-ledger \
  --output-dir runs/private-app-operating-profile-evals/runway-ledger \
  --parallel 1 \
  --force
```

## Included private-app scenarios

- `runway-ledger`: weekly cash decision board for private runway assumptions.
- `partner-pulse`: partner-note follow-up priorities and risk tags.
- `cohort-compass`: product activation friction ranking.
- `care-loop`: calm daily care checklist from private routines.
- `decision-deck`: meeting decisions, blockers, and next owners.
- `learning-loop`: private cohort lesson-improvement ranking.

## Review workflow

1. Open `aggregate-report.json` first.
2. Pick any result and inspect its `assessment-report.json`.
3. Inspect `cognitive-artifacts/profile-selection.json` to see the profile
   choice.
4. Inspect `cognitive-artifacts/cwa-work-domain.json` for private-domain
   modeling.
5. Inspect `cognitive-artifacts/dmn-decision-table.json` for deterministic
   routing.
6. Inspect `cognitive-artifacts/ibis-map.json` and
   `adr-0001-local-private-first.md` for contested choices and commitment.
7. Inspect `cognitive-artifacts/prov-ledger.jsonl` for the event trail.
8. Open the generated app's `index.html` locally if browser inspection is needed.

## Proof boundary

The highest proven surface is:

`local deterministic private-app fixture with reviewable cognitive artifacts`

Do not report this as live Hermes, Telegram, deployed gateway, or market proof.

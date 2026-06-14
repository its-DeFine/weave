# Private App Operating Profile Evaluations

Status: local deterministic evaluation harness

## Purpose

This harness tests whether WEAVE Operating Profiles can produce reviewable app
artifacts for private, non-public products. The point is not marketing or live
traction. The point is to generate 10 useful local app proofs in parallel and
prove that the cognitive frameworks are consumed by review gates, not merely
emitted as decorative files.

Each scenario uses synthetic private-domain data. The generated apps are static,
local-only, and dependency-free.

## What it proves

- WEAVE can run a deterministic parallel evaluation across 10 private app
  scenarios.
- Each app output includes source files, a local assessment report, a per-app
  `review.json`/`review.md`, and a framework-gate evidence bundle.
- CWA, DMN, IBIS, ADR, Premortem, and PROV are visible as concrete artifacts and
  as validation gates that can fail from malformed or contradictory content.
- Gestalt is optional/deferred by default for this test; it is not a hard gate.
- The aggregate report lets reviewers compare scenario outcomes without reading
  every generated file first.

## What it does not prove

- It is not live Hermes CLI proof.
- It is not Codex/Hermes autonomous goal-loop proof.
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

- `schema`: `weave-operating-profile/v0.2`
- `trigger_mode`: `reactive`
- `authority_mode`: `recommend_only`
- `target_surface`: local deterministic private-app fixture with generated static
  apps and reviewable framework-gate evidence
- `private_data_policy.real_private_data_allowed`: `false`
- `private_data_policy.synthetic_private_data_allowed`: `true`
- `private_data_policy.external_send_allowed`: `false`
- `evaluation.minimum_app_count`: `10`
- `evaluation.marketing_included`: `false`

## Framework gates per app

Every generated app gets gate-consumed artifacts:

- `intent-frame.json`
- `profile-selection.json`
- `intake-state.json`
- `cwa-work-domain.json`
- `information-requirements.json`
- `missing-information-assessment.json`
- `dmn-routing-table.json`
- `decision-evaluation-log.json`
- `ibis-issue-map.json`
- `open-issues.json`
- `adr-0001-local-private-first.md`
- `decision-register.json`
- `premortem-report.json`
- `risk-to-test-map.json`
- `action-intent.json`
- `action-result.json`
- `proof-boundary-report.json`
- `lifecycle-transition-log.jsonl`
- `prov-ledger.jsonl`
- `assessment-report.json`
- `review.json`
- `review.md`

The aggregate run also writes:

- `.weave-private-app-eval-output-root`
- `aggregate-report.json`
- `aggregate-review.json`
- `aggregate-review.md`
- `cases.jsonl`
- optional Markdown report if `--report-out` is supplied

## Committed artifact boundary

The generated bundle committed under
`docs/month1/artifacts/private-app-operating-profile-evals/` is sample review
evidence. It helps reviewers inspect the shape and volume of the evidence bundle
without running the harness first. It is not required as a byte-for-byte golden
fixture, and it should not be treated as live-agent, hosted-app, Telegram, or
real-user proof.

For normal review, regenerate into `runs/private-app-operating-profile-evals/` or
a temporary directory and compare these stable properties instead of raw bytes:

- schemas and app counts;
- gate names, pass/fail status, and source-artifact references;
- proof-boundary `highest_proven_surface`, `not_proven`, and explicit non-claims;
- generated app source presence and local-only/static constraints.

Regenerated artifacts may differ by timestamp, artifact ordering, run checksum,
or per-file hash/checksum values. Those differences are expected unless a future
version adds a dedicated fixed-clock golden-fixture mode.

## Run it

```bash
mkdir -p runs/private-app-operating-profile-evals
python3 scripts/private_app_operating_profile_eval.py \
  --output-dir runs/private-app-operating-profile-evals/artifacts \
  --report-out runs/private-app-operating-profile-evals/report.md \
  --parallel 4 \
  --force
```

`--force` is guarded. It refuses protected roots, symlink roots,
non-directories, and non-empty unmarked directories. It may delete only an empty
output directory, a root previously marked by this harness with
`.weave-private-app-eval-output-root`, or an explicitly named temporary eval root.
Use a fresh `runs/...` path when unsure.

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
- `grant-radar`: nonprofit grant opportunity and missing-material triage.
- `vendor-vault`: vendor renewal and consolidation risk review.
- `clinic-queue`: clinic operations queue triage without clinical advice.
- `content-calibrator`: local content idea review queue without publishing.

## Review workflow

1. Open `aggregate-review.md` or `aggregate-review.json` first.
2. Inspect failed/warn cases first. If all pass, sample at least two pass cases.
3. For a sampled case, open its `review.md` and `review.json`.
4. Confirm each review gate lists source artifacts.
5. Inspect `cognitive-artifacts/missing-information-assessment.json` for the CWA
   missing-information gate.
6. Inspect `cognitive-artifacts/dmn-routing-table.json`,
   `decision-evaluation-log.json`, and `lifecycle-transition-log.jsonl` for DMN
   routing.
7. Inspect `ibis-issue-map.json`, `open-issues.json`, and
   `adr-0001-local-private-first.md` for contested choices and commitments.
8. Inspect `premortem-report.json` and `risk-to-test-map.json` for failure-mode
   coverage.
9. Inspect `prov-ledger.jsonl` before accepting any proof-surface claim.
10. Open the generated app's `index.html` locally if browser inspection is needed.

## Proof boundary

The highest proven surface is:

`local deterministic private-app fixture with generated static apps and reviewable framework-gate evidence`

Do not report this as live Hermes, Codex/Hermes goal-loop, Telegram, deployed
gateway, hosted app, real-data, or market proof.

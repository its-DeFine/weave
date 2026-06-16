# WEAVE v1 Textual Delivery Summary

This is the review surface for the corrected WEAVE v1 target: a local Textual
TUI product that can be used like a human operator from first run through QA.
WEAVE itself is not a web app and does not need a deployed URL. A URL is only
relevant later for a generated website app after a separate deployment approval.

## Completion Claim

Current claim: the local WEAVE v1 Textual path is proven through QA with all
service-blueprint routes, all operator views, visible Codex running state, and
real Codex CLI execution connected through the backend.

Traceability:

- Linear issue: `ATM-257`
- Git branch: `codex/atm-257-weave-textual-service-blueprint`

Evidence:

- Textual dogfood report: `docs/proof/weave-v1-textual-dogfood.json`
- Textual journey recording: `docs/ux/weave-v1-textual-dogfood/weave-v1-textual-dogfood-recording.svg`
- First-run proof frame: `docs/ux/weave-v1-textual-dogfood/01-first-run.svg`
- Owner profile proof frame: `docs/ux/weave-v1-textual-dogfood/03-owner-profile.svg`
- Codex running proof frame: `docs/ux/weave-v1-textual-dogfood/10-engineering-codex-running.svg`
- Resume proof frame: `docs/ux/weave-v1-textual-dogfood/19-resume-qa.svg`
- Gated later-stage proof frames: `docs/ux/weave-v1-textual-dogfood/14-gated-deployment.svg`
  through `docs/ux/weave-v1-textual-dogfood/18-gated-analysis.svg`
- All-view proof frames: `docs/ux/weave-v1-textual-dogfood/20-view-overview.svg`
  through `docs/ux/weave-v1-textual-dogfood/26-view-resume.svg`
- Backend dogfood report: `docs/proof/weave-v1-backend-dogfood.json`
- Completion matrix: `docs/WEAVE_V1_COMPLETION_MATRIX.md`
- Operator runbook: `docs/WEAVE_V1_TEXTUAL_RUNBOOK.md`

## Proven Journey

The Textual dogfood uses the actual Textual app surface and records a
human-style journey:

1. First run opens the TUI with environment detection.
2. The lifecycle rail is activated by keyboard Enter.
3. App workspace is created.
4. Owner profile and foundation context are saved.
5. App workspace route is shown.
6. Intent prompt packet, proof artifact, evaluation, approval, and advance are
   completed.
7. Research prompt packet, proof artifact, evaluation, approval, and advance are
   completed.
8. Selection prompt packet, proof artifact, evaluation, approval, and advance
   are completed.
9. Plan prompt packet, proof artifact, evaluation, approval, and advance are
   completed.
10. Engineering prepares a prompt packet and invokes real Codex CLI execution.
11. The TUI captures Codex running state before completion.
12. Generated source files, executor manifest, and source manifest are recorded.
13. File-specific feedback on generated source creates an
    `engineering/file_feedback` prompt packet.
14. Engineering evaluation and approval are completed.
15. QA prompt packet, proof artifact, evaluation, and approval are completed.
16. Deployment, KPI, Marketing, Iteration, and Analysis are shown as gated
    planning screens with live-effect boundaries.
17. The TUI is reopened on the same state and resumes at QA.
18. The operator switches through the `overview`, `stages`, `artifacts`,
    `files`, `reviews`, `help`, and `resume` views.

## Current Proof Metrics

From `docs/proof/weave-v1-textual-dogfood.json`:

- `passed`: true
- `reason`: `completed_through_qa_all_views_and_routes_captured`
- approved stages: `intent`, `research`, `selection`, `plan`, `engineering`,
  `qa`
- Textual frames: 26
- required routes captured: `first_run`, `owner_profile`, `app`, `intent`,
  `research`, `selection`, `plan`, `engineering`, `qa`, `deployment`, `kpi`,
  `marketing`, `iteration`, `analysis`
- required views captured: `overview`, `stages`, `artifacts`, `files`,
  `reviews`, `help`, `resume`
- human-style actions: 61
- prompt packets: 8
- generated app source files: 5
- resume stage: `qa`
- Codex executor manifest status: `passed`
- Codex executor process completed: true
- Codex executor required file check: passed
- scrubbed non-reviewable runtime refs: `runtime/tokens/local-api-token`,
  `runtime/tokens/`, `runtime/source-map.json`
- external effects executed: none
- secret value printed: false

## Verification Commands

Latest verification pass included:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python -m unittest tests.test_weave_textual_app tests.test_weave_prompt_orchestration
python3 scripts/runtime_smoke.py
python3 scripts/public_safe_repo_scan.py
python3 scripts/check_no_secrets.py
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
git diff --check
.venv/bin/python scripts/capture_weave_textual_screens.py
.venv/bin/python scripts/weave_v1_textual_dogfood.py --clean --codex-timeout 240
python3 scripts/weave_v1_backend_dogfood.py --report-out docs/proof/weave-v1-backend-dogfood.json --codex-timeout 600
```

All listed checks passed in the latest local run.

## Non-Claims

- WEAVE itself was not deployed and does not need a URL.
- No live Hermes or Telegram gateway proof is claimed here.
- No raw credentials were captured.
- No public messages were sent.
- No paid spend occurred.
- No market validation is claimed.
- Deployment, KPI, marketing, iteration, and analysis remain gated later-stage
  planning surfaces unless separately authorized for live effects.

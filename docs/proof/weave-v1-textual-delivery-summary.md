# WEAVE v1 Textual Delivery Summary

This is the review surface for the corrected WEAVE v1 target: a local Textual
TUI product that can be used like a human operator from first run through QA.
WEAVE itself is not a web app and does not need a deployed URL. A URL is only
relevant later for a generated website app after a separate deployment approval.

## Completion Claim

Current claim: the local WEAVE v1 Textual path is proven through QA with all
operator views captured and real Codex CLI execution connected through the
backend.

Traceability:

- Linear issue: `ATM-256`
- Git branch: `codex/atm-256-weave-v1-textual-completion`

Evidence:

- Textual dogfood report: `docs/proof/weave-v1-textual-dogfood.json`
- Textual journey recording: `docs/ux/weave-v1-textual-dogfood/weave-v1-textual-dogfood-recording.svg`
- Resume proof frame: `docs/ux/weave-v1-textual-dogfood/11-resume-qa.svg`
- All-view proof frames: `docs/ux/weave-v1-textual-dogfood/12-view-overview.svg`
  through `docs/ux/weave-v1-textual-dogfood/18-view-resume.svg`
- Backend dogfood report: `docs/proof/weave-v1-backend-dogfood.json`
- Completion matrix: `docs/WEAVE_V1_COMPLETION_MATRIX.md`
- Operator runbook: `docs/WEAVE_V1_TEXTUAL_RUNBOOK.md`

## Proven Journey

The Textual dogfood uses the actual Textual app surface and records a
human-style journey:

1. First run opens the TUI.
2. App workspace is created.
3. Owner profile and foundation context are saved.
4. Intent prompt packet, proof artifact, evaluation, approval, and advance are
   completed.
5. Research prompt packet, proof artifact, evaluation, approval, and advance are
   completed.
6. Selection prompt packet, proof artifact, evaluation, approval, and advance
   are completed.
7. Plan prompt packet, proof artifact, evaluation, approval, and advance are
   completed.
8. Engineering prepares a prompt packet and invokes real Codex CLI execution.
9. Generated source files, executor manifest, and source manifest are recorded.
10. File-specific feedback on generated source creates an
    `engineering/file_feedback` prompt packet.
11. Engineering evaluation and approval are completed.
12. QA prompt packet, proof artifact, evaluation, and approval are completed.
13. The TUI is reopened on the same state and resumes at QA.
14. The operator switches through the `overview`, `stages`, `artifacts`,
    `files`, `reviews`, `help`, and `resume` views.

## Current Proof Metrics

From `docs/proof/weave-v1-textual-dogfood.json`:

- `passed`: true
- `reason`: `completed_through_qa_and_all_views_captured`
- approved stages: `intent`, `research`, `selection`, `plan`, `engineering`,
  `qa`
- Textual frames: 18
- required views captured: `overview`, `stages`, `artifacts`, `files`,
  `reviews`, `help`, `resume`
- human-style actions: 48
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

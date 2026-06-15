# WEAVE TUI Full Product Dogfood

Status: proof artifact for ATM-254.

Date: 2026-06-15.

## Intent

Validate that the new WEAVE cockpit is not just a scripted demo or generic
Codex wrapper. The dogfood had to enter the cockpit, invoke the real Codex
executor from the `weave>` loop, generate an example website app, expose files
and artifacts in the cockpit, pass local QA, and stop before live external
effects.

## Command Shape

The run used a throwaway runtime home and this command shape:

```bash
printf 'g\nfiles\nartifacts\nreviews\nq\n' | bin/weave tui \
  --runtime-home <throwaway-runtime-home> \
  --app-id codex-dogfood-atm254-rerun \
  --app-name 'Codex Dogfood ATM254 Rerun' \
  --app-surface website \
  --control-mode handoff \
  --executor codex \
  --codex-timeout 900 \
  --loop \
  --no-color \
  --intent 'Build a launch-readiness studio for a small product team...' \
  --target-user 'founder operator validating an agent-built launch workflow' \
  --deployment-region 'United States and European Union planned after local proof' \
  --marketing-budget 'none for local proof; organic planning only'
```

## Result

- Cockpit entered the `weave>` loop and accepted `g`.
- Real Codex executor ran with `live_agent_execution: true`.
- Required generated files were produced:
  - `apps/codex-dogfood-atm254-rerun/repo/primary/index.html`
  - `apps/codex-dogfood-atm254-rerun/repo/primary/src/app.js`
  - `apps/codex-dogfood-atm254-rerun/repo/primary/src/styles.css`
  - `apps/codex-dogfood-atm254-rerun/repo/primary/public/config.json`
  - `apps/codex-dogfood-atm254-rerun/repo/primary/README.md`
- The cockpit `files` pane listed all generated files.
- The cockpit `artifacts` pane listed lifecycle artifacts from Intent through
  gated launch planning.
- Real app QA passed with `check_count: 30`, `failed_count: 0`,
  `route: owner_review`.
- TUI session manifest recorded `executor: codex`, `control_label: handoff`,
  and `external_effects_executed: []`.
- App state stopped at `current_stage: deployment`, `stage_state: blocked`,
  with blocker `launch capabilities deferred`.

## Proof Refs

All refs below are relative to the throwaway runtime root:

- `apps/codex-dogfood-atm254-rerun/lifecycle/05-engineering/artifacts/app-executor-manifest.json`
- `apps/codex-dogfood-atm254-rerun/lifecycle/05-engineering/artifacts/generated-app-manifest.json`
- `apps/codex-dogfood-atm254-rerun/lifecycle/06-qa/artifacts/real-app-qa.json`
- `apps/codex-dogfood-atm254-rerun/lifecycle/06-qa/artifacts/tui-session-manifest.json`
- `apps/codex-dogfood-atm254-rerun/lifecycle/07-deployment/artifacts/launch-ops-manifest.json`

## Failure Found And Fixed

The first real Codex dogfood generated a placeholder canonical URL inside
`src/app.js`. Real app QA correctly failed `js-no-external-url` and routed the
app back to Engineering. The prompt was tightened to keep canonical URL text
only in `index.html`, and a regression test now asserts that prompt rule.

The retry also exposed that `g` was too coarse on an existing app: it tried to
rerun early lifecycle instead of resuming Engineering/QA. The command is now
stage-aware, and a regression test covers failed-QA rerun recovery.

## Still Not Full Product

This proves the cockpit can drive a real Codex app build through local QA and
show the resulting files/artifacts. It does not yet prove rich file previews,
stage-specific research/selection/plan editing, QA-plan drilldown, deployment
execution, live KPI wiring, marketing execution, or recurring iteration jobs.

# WEAVE v1 Textual Service-Blueprint Correction Goal

## Purpose

Fix WEAVE v1 Textual so it behaves like the service-blueprint product flow, not
like a vague backend control panel. The owner must be able to enter the TUI,
complete first-run onboarding, move naturally between lifecycle screens, use
keyboard and mouse activation, see polished visual hierarchy, and continue a
real app lifecycle through QA.

## Current Failure To Fix

Observed owner failure:

- Clicking `First Run` does not open a first-run screen.
- Arrow navigation plus Enter does not activate lifecycle items.
- The visible TUI does not provide the guided onboarding flow from the service
  blueprint.
- Lifecycle movement is not natural; it looks like a generic panel with buttons.
- The TUI can appear frozen during longer actions.
- Visual quality is insufficient: weak color, weak spacing, weak hierarchy, no
  pleasant graphics, no strong focus, no loading/progress animation.

## Deliverable

A merged PR that replaces the current Textual experience with a real
service-blueprint TUI flow and proves it with human-style usage artifacts.

## Required Product Behavior

The operator can run:

```sh
bin/weave tui --textual --app-id my-test-app --app-name "My Test App" --executor codex --control-mode handoff
```

Then the operator can:

1. See an intentional first screen with visual hierarchy and a clear next action.
2. Enter `First Run` by clicking it or focusing it with arrows and pressing Enter.
3. Complete environment detection and choose attach/create/local-only behavior.
4. Enter owner profile and desired coworker style.
5. Create or load an app workspace.
6. Capture and validate intent.
7. Move through `Intent`, `Research`, `Selection`, `Plan`, `Engineering`, and
   `QA` as separate screens with stage-specific choices.
8. Use `Research` to see a research plan, accept/edit/revise, then review
   artifacts.
9. Use `Selection` to see options, choose one, create a custom option, or
   discuss/edit.
10. Use `Plan` to review/edit business and engineering plans.
11. Use `Engineering` to run Codex, inspect generated files, and attach
    file-specific feedback.
12. Use `QA` to authorize QA, see surface-adapted QA proof, and request reruns.
13. See `Deployment`, `KPI`, `Marketing`, `Iteration`, and `Analysis` as real
    gated screens with clear missing capabilities, not dead menu items.
14. Resume the same app state after quitting and reopening.

## UI Requirements

- Use Textual screens/routes instead of one static overview panel.
- Lifecycle list items must be actionable by mouse click and keyboard Enter.
- Arrow keys move focus predictably.
- Tab and Shift-Tab move between major regions predictably.
- Esc/back returns to the previous screen.
- Help explains shortcuts and feedback syntax.
- Long-running Codex/backend actions show running state, spinner/progress, start
  time, elapsed time, and recoverable timeout/failure state.
- Visual style must use clear color hierarchy, bold headings, status badges,
  spacing, separators, focused cards/panels, progress rails, and tasteful motion.
- The screen must make the current stage, user question, available choices,
  proof boundary, next action, and blockers visually obvious.

## Backend And Safety Invariants

- No raw secrets are collected or printed.
- No deployment, public send, paid spend, credential mutation, or destructive
  external action is performed.
- Codex execution remains routed through the backend executor.
- Prompt packets, artifacts, review queue, source manifests, executor manifests,
  world model, stage gates, and transcript turns remain durable.
- Engineering and QA hard gates stay explicit and cannot be silently bypassed.
- The TUI must surface blocked states honestly instead of appearing frozen.

## First Step Before Coding

Run read-only inspection and report:

- `source_files_read`
- `failing_command_or_invariant`
- `planned_touched_files`
- `verification_command`
- `architecture_map`
- `business_logic_invariants`
- `ui_or_flow_invariants`
- `iteration_delta`
- `implementation_brief`

Inspect at minimum:

- `scripts/weave_textual_app.py`
- `scripts/weave_backend.py`
- `scripts/weave_v1_textual_dogfood.py`
- `scripts/capture_weave_textual_screens.py`
- `tests/test_weave_textual_app.py`
- `tests/test_weave_prompt_orchestration.py`
- `docs/WEAVE_V1_PRODUCT_CONTRACT.md`
- `docs/WEAVE_V1_TEXTUAL_RUNBOOK.md`
- `docs/WEAVE_V1_COMPLETION_MATRIX.md`
- `docs/proof/weave-v1-textual-delivery-summary.md`

## Expected Files To Edit

- `scripts/weave_textual_app.py`
- `scripts/weave_backend.py` if richer projection/action state is needed
- `scripts/weave_v1_textual_dogfood.py`
- `scripts/capture_weave_textual_screens.py`
- `tests/test_weave_textual_app.py`
- `docs/WEAVE_V1_TEXTUAL_RUNBOOK.md`
- `docs/WEAVE_V1_COMPLETION_MATRIX.md`
- `docs/proof/weave-v1-textual-delivery-summary.md`

## Acceptance Checks

- Create a Linear issue before coding.
- Manual TUI use works with keyboard and mouse:
  - click/Enter on `First Run` opens first-run onboarding
  - click/Enter on lifecycle stages opens their stage screens
  - Tab/Shift-Tab and Esc/back behave predictably
- Full dogfood captures video/SVG artifacts showing human-style navigation
  through onboarding, all core lifecycle screens, files, artifacts, reviews,
  help, resume, Codex progress, and QA.
- Dogfood reaches QA with a real generated app.
- Unit tests cover keyboard navigation, list activation, route changes,
  onboarding flow, progress state, resume, feedback, and blocked/error states.
- Full verification passes:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/weave_v1_textual_dogfood.py --clean --codex-timeout 240
.venv/bin/python scripts/capture_weave_textual_screens.py
python3 scripts/runtime_smoke.py
python3 scripts/public_safe_repo_scan.py
python3 scripts/check_no_secrets.py
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
git diff --check
```

- Open a PR.
- CI must pass.
- Merge only after CI passes.
- Mark Linear Done only after merge.
- Mark the active goal complete only after merged `main` contains the fix and
  proof artifacts.

## Deadline / Work Window

Work continuously until the above is genuinely done. Intermediate PRs are
allowed only if the parent goal remains open and final acceptance is not claimed
until the full service-blueprint TUI behavior is proven.

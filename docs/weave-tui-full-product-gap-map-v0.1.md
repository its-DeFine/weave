# WEAVE TUI Full Product Gap Map

Status: current-state gap map for ATM-254 after the first cockpit implementation wedge.

This map compares the current repo state after PR #24 with the full TUI product
contract. It records what is already useful, what is missing, and what evidence
is required before completion can be claimed.

## Current Proven Foundation

- `bin/weave tui --executor codex --scripted-demo --write --no-color` can invoke
  `codex exec` for a bounded app-builder task.
- Generated app source files are written under `apps/<app>/repo/primary`.
- Executor, generated-source, SEO, and real-app QA manifests are recorded.
- Real local QA can pass or fail honestly against generated website files.
- Fixture executor is explicitly labeled as deterministic CI/local proof only.
- Failure-path tests cover broken generated source and failed Codex execution.
- `bin/weave tui` now opens a resumable cockpit by default outside
  `--scripted-demo`.
- The cockpit renders the service-blueprint stage scripts, action cards,
  visible choices, command bar, stage state, review queue, artifact list, and
  generated file list.
- The cockpit command loop can create local app state, navigate views, resume a
  saved view, record stage feedback, record file-specific feedback, and invoke
  the local lifecycle executor through QA with `g`/`run`.
- Real Codex dogfood through the cockpit passed local generated-app QA; see
  `docs/weave-tui-full-product-dogfood-v0.1.md`.

This is a foundation slice, not the full product.

## Gap Summary

| Contract area | Current state | Gap | Required next evidence |
| --- | --- | --- | --- |
| Service blueprint fidelity | Stage scripts and choices are now rendered from code | Still needs full stage-by-stage happy path dogfood, not only unit assertions | dogfood showing first-run through QA with operator choices |
| User-visible choices | Action cards expose yes/no, option picker, feedback, inspect, revise, approve primitives | Some choices are visible before all have dedicated handlers | command tests for each active choice or honest blocked message |
| Ongoing cockpit | Default non-scripted TUI opens a resumable command loop with panes and command bar | Visual system is still ASCII-frame based, not final rich TUI polish | screenshot/golden review after layout pass |
| Resume | Session file stores selected view and recent actions | Resume is app-local only; no app switcher yet | multi-app resume/app picker test |
| Visual hierarchy | Header/nav/work pane/command bar are present | Needs stronger styling density and attention guidance | golden output/snapshot for dense cockpit layout |
| Navigation | Commands cover status/stages/artifacts/files/reviews/help/resume | No file open/preview pager yet | artifact/file open commands and tests |
| Review loops | `y`, `n`, and `f` record owner responses/feedback in a review-visible ledger | Approve/revise does not yet drive stage transition or agent re-plan | tests for stage approval/revision affecting lifecycle state |
| Artifact inspection | Artifact pane lists lifecycle artifacts after execution | Does not open/read individual artifacts yet | artifact open command and test |
| File inspection | File pane lists generated app files after execution | Does not open/read individual files yet | file open command and test |
| File-specific feedback | `p <file> <feedback>` records structured file feedback | Feedback is captured but not yet consumed by a re-engineering loop | feedback-to-agent rerun test |
| Codex ongoing agent surface | `g`/`run` invokes the existing local lifecycle executor through QA from the cockpit, including real Codex dogfood | Execution has stage-aware resume but not live task-progress streaming | agent task pane and executor manifest linked to session |
| Research/selection/plan UX | Early lifecycle writes deterministic artifacts and stage scripts are visible | No editable plan form or research/selection re-present loop yet | stage panes with review/revise controls |
| QA UX | Real app QA manifest is written and listed after cockpit run | No visible QA plan authorization, failed-check drilldown, or rerun planning loop | QA pane and failed-check routing test |
| Deployment/KPI/marketing/iteration | Launch ops creates gated artifacts | No cockpit for gated jobs/plans and recurring future work | gated planning panes without live actions |
| Docs | README, quickstart, and runtime docs explain cockpit operation/resume basics | Need full operator manual after stage-specific flows exist | docs updated with final dogfood path |
| Dogfood | Real Codex cockpit dogfood passed through local QA and recorded a proof doc | No owner-visible rich file preview or stage-editing dogfood yet | dogfood report for stage-specific edit/revise flows |

## Blueprint Fidelity Risk

The highest current risk is building an attractive terminal around the wrong
interaction model. The product must not simply recreate Codex CLI with WEAVE
colors. The original service blueprint requires guided stage cards with visible
choices, review loops, editable plans, artifact inspection, and file-specific
feedback.

Before implementing a rich renderer, the next wedge must define and test the
interaction primitives:

- yes/no approval;
- option picker;
- free-form feedback;
- inspect artifact/file;
- revise and re-present;
- approve and transition;
- blocked/gated action.

Without these primitives, a polished shell would still miss the user's intended
experience.

## Current Code Shape

The current TUI implementation is concentrated in `scripts/weave_tui.py`.

Important current functions:

- `collect_inputs`: prompt-based setup collection.
- `run_scripted_or_interactive`: linear orchestration of first-run, early
  lifecycle, engineering scaffold, real app QA, lifecycle QA bundle, and launch
  gates.
- `run_cockpit`: resumable command loop and one-frame cockpit renderer.
- `handle_cockpit_command`: navigation, app creation, feedback, file feedback,
  and local executor command dispatcher.
- `BLUEPRINT_STAGE_SCRIPTS`: code-backed user-visible lifecycle asks/options.
- `render_summary`: final summary output.
- `run_codex_executor`: bounded one-shot Codex app builder.
- `run_real_app_qa`: generated app QA checks.

The session/cockpit layer now exists. Remaining architecture gaps are:

- app switcher and multi-app view;
- artifact/file open previews;
- richer stage-specific execution beyond the current `g`/`run` resume behavior;
- feedback consumption by the next agent execution;
- QA authorization and rerun pane;
- richer visual system and golden output review.

## First Implementation Wedge

The completed first wedge created the cockpit shell without pretending the full
goal is done:

1. Add a persisted `tui-session.json` or equivalent under the app/runtime state.
2. Add a render model with header, navigation rail, work pane, command bar, and
   proof boundary.
3. Add read-only commands for `status`, `stages`, `artifacts`, `files`,
   `reviews`, and `help`.
4. Add a `resume` path that shows the last app/stage/view and recent commands.
5. Add tests proving state persistence and visual output.

The next aligned wedge is to split coarse execution into stage-specific actions:
intent validation, research plan review, selection review, plan review,
engineering task progress, QA plan authorization, QA rerun, and feedback-driven
re-engineering.

## Non-Completion Warning

Do not mark ATM-254 or the active Codex goal complete after the first cockpit
shell. Completion requires the full evidence matrix in
`docs/weave-tui-full-product-contract-v0.1.md`.

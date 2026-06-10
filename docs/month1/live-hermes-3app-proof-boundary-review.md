# Live Hermes 3-App Proof Boundary Review

Status: local review artifact. This documents failed/partial live-Hermes CLI runs and the hardening added to prevent false proof claims.

## Highest proven surface

- Fixture mode: orchestration/reporting proof only.
- Hermes CLI mode: live generated-agent reply behavior only when the CLI invocation completes cleanly and expectations pass.
- Deployed gateway / Telegram: not proven here; requires real adapter send/wait/readback on the deployed target surface.

## Run evidence

### `live-3app-hermes-cli-20260610T001919Z`

Path: `/tmp/weave-scripted-user-live-agent-runs/live-3app-hermes-cli-20260610T001919Z`

Result reported by runner:

```json
{"output_root": "/tmp/weave-scripted-user-live-agent-runs/live-3app-hermes-cli-20260610T001919Z", "passed": false, "run_id": "live-3app-hermes-cli-20260610T001919Z"}
```

Observed blockers:

- Runway Ledger did not complete cleanly under live Hermes CLI; it hit the analysis-timeout class of failure.
- Decision Deck exposed the runtime/schema gap where `live_hermes` event creator was not accepted.
- Partner Pulse could appear pass-like while relying too heavily on generated prose rather than target-surface proof.

### `live-3app-hermes-cli-20260610T010807Z-retry`

Path: `/tmp/weave-scripted-user-live-agent-runs/live-3app-hermes-cli-20260610T010807Z-retry`

Process: `proc_5fdb38fc5a1c` exited `-15` and produced no aggregate report.

Observed state before kill:

- Only `live-runway-ledger-1` existed.
- App reached `current_stage: kpi` with approved stages `intent`, `research`, `selection`, `plan`, `engineering`, and `qa`.
- Required app source files were absent:
  - `index.html`: missing
  - `styles.css`: missing
  - `app.js`: missing
  - `README.md`: missing
- Repo file list under `repo/primary` was empty.

Interpretation: this run demonstrates why lifecycle approval and coherent agent prose must not be accepted as app implementation proof.

### Strict live-Hermes loop

Supervisor log: `/tmp/weave-live-3app-strict-20260610T012148Z/supervisor.log`

Purpose: stricter benchmark with required app-file checks and forbidden max-turn/cap text.

Observed supervisor log:

- `attempt 1 start run_id=live-3app-hermes-cli-strict-20260610T012155Z-a1`
- `attempt 1 done returncode=-15 review_passed=False failures=1`
- `attempt 2 start run_id=live-3app-hermes-cli-strict-20260610T012653Z-a2`

Run path: `/tmp/weave-scripted-user-live-agent-runs/live-3app-hermes-cli-strict-20260610T012653Z-a2`

Aggregate result:

- `passed: false`
- `instance_count: 3`
- all agent replies source-labeled `live_hermes`
- Decision Deck aborted at `engineering: failed_expectations`
- Partner Pulse aborted at `research: failed_expectations`
- Runway Ledger aborted at `engineering: failed_expectations`
- required app source files were still absent in inspected app repos.

Interpretation: this strict loop is useful negative proof. It verifies the harder gates can catch live-Hermes generated-agent work that advances conversation stages without satisfying implementation evidence.

### `live-3app-hermes-cli-goal-loop-20260610T013147Z-a1-mt24`

Path: `/tmp/weave-scripted-user-live-agent-runs/live-3app-hermes-cli-goal-loop-20260610T013147Z-a1-mt24`

Supervisor: `/tmp/weave-live-3app-codex-goal-loop-20260610T013135Z/codex_goal_loop_3app_live.py`

Observed state before stop:

- Supervisor log recorded only `attempt=1 max_turns=24 run_id=live-3app-hermes-cli-goal-loop-20260610T013147Z-a1-mt24 start` before the process was killed.
- Runway Ledger reached `plan`, with `intent`, `research`, and `selection` approved.
- Runway Ledger scenario report: `passed=false`; terminal reason `aborted at plan: timeout`.
- Partner Pulse reached `selection`, with `intent` and `research` approved.
- Decision Deck had no completed scenario directory in this run.
- Required files were absent in inspected app repos.
- No aggregate success summary existed.

Interpretation: bounded autonomous/goal-loop execution was attempted, but it found a hard proof blocker rather than a clean pass.

## Hardening added

- Accept `live_hermes`, `live_agent`, and `deployed_agent` runtime event creators while still rejecting fixture provenance as live event proof.
- Add `app_repo_required_files` expectations so engineering/QA can require concrete source files in the app repo.
- Reject required-file proof for absolute paths, `..` paths, and symlinks.
- Add live-Hermes cap-marker detection via `live_adapter_completed_without_turn_cap`.
- Add live-Hermes timeout floors:
  - `WEAVE_LIVE_HERMES_ANALYSIS_TIMEOUT_SECONDS` for analysis.
  - `WEAVE_LIVE_HERMES_STEP_TIMEOUT_SECONDS` for broader live-Hermes benchmark loops.
- Raise Hermes CLI max-turn defaults and make them env-configurable.
- Update live prompt instructions to require single-invocation completion or explicit inability to verify.
- Update methodology docs with proof-strength labels, required-file proof, and surface boundaries.

## Verification run after hardening

Commands run locally:

```bash
python3 -m unittest tests.test_scripted_user_live_agent_runner tests.test_weave_runtime_slice
python3 -m unittest discover -s tests -p 'test_*.py' -b
python3 scripts/runtime_smoke.py
python3 scripts/check_no_secrets.py .
git diff --check
```

Observed outputs:

- Selected runner/runtime tests: `Ran 42 tests ... OK`.
- Full unittest discovery: `Ran 141 tests in 5.037s ... OK`.
- Runtime smoke: `smoke: ok` plus package validation for `weave` version `2026.05.13-console`.
- Secret scan: exit code `0`, no output.
- Diff whitespace check: exit code `0`, no output.

## Non-claims

- No clean live 3-app Hermes CLI pass is claimed.
- No deployed gateway/Telegram target-surface proof is claimed.
- No external send, deploy, analytics, payment, credential, or customer-facing behavior is claimed.
- Green local tests prove the runner/methodology hardening, not live app quality or deployed behavior.

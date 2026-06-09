# Scripted-User / Live-Agent Runner

Status: MVP runner for local WEAVE scenario execution. Fixture mode is deterministic CI proof; live mode requires a live agent adapter and refuses fixture/replay reply sources as a hard proof-boundary failure.

## Purpose

The full-conversation dogfood proves that a local WEAVE lifecycle fixture can export stage artifacts, gates, and review bundles. It does **not** prove live agent behavior because both sides of that transcript are scripted.

This runner covers the next surface:

- scenario files script only the user/owner turns
- the selected adapter supplies the agent reply
- the runner waits for the reply, enforces timeouts, evaluates predicates, and branches
- multiple scenario instances can run in parallel against isolated WEAVE roots
- every turn is recorded as a runtime conversation turn with source labels
- reports separate live proof from fixture proof
- proof-boundary violations are hard failures: fixture mode cannot impersonate
  live sources, and live mode cannot accept fixture/replay/deterministic sources

## Command Shape

Fixture CI mode uses the fixture adapter only. The runner rejects `--mode fixture`
with any live adapter before an adapter can execute.

```bash
python3 scripts/scripted_user_live_agent_runner.py \
  --scenario docs/month1/examples/scripted-user-live-agent-scenario.example.json \
  --mode fixture \
  --agent fixture \
  --output-dir /tmp/weave-scripted-user-live-agent-runs \
  --run-id example-fixture \
  --force
```

Parallel fixture rehearsal:

```bash
python3 scripts/scripted_user_live_agent_runner.py \
  --scenario docs/month1/examples/scripted-user-live-agent-scenario.example.json \
  --repeat 4 \
  --parallel 4 \
  --output-dir /tmp/weave-scripted-user-live-agent-runs
```

Hermes CLI live-agent mode:

```bash
python3 scripts/scripted_user_live_agent_runner.py \
  --scenario path/to/scenario.json \
  --mode live \
  --agent hermes-cli \
  --hermes-bin hermes \
  --model "$WEAVE_HERMES_MODEL" \
  --provider "$WEAVE_HERMES_PROVIDER_ADAPTER" \
  --max-turns 4 \
  --timeout 180
```

Live mode currently means: the adapter produced a generated reply from a live Hermes CLI process. It is **not** the same as deployed Telegram gateway proof unless the adapter is extended to drive that deployed surface.

## Scenario Shape

Required top-level fields:

- `schema`: `weave-scripted-user-live-agent-scenario/v0.1`
- `scenario_id`: stable scenario label
- `steps`: non-empty list of scripted user turns

Common optional fields:

- `intent`: human-readable app goal
- `app.id_template`: supports `{scenario_id}`, `{run_id}`, `{run_index}`
- `app.name_template`: supports the same template variables
- `foundation`: public-safe seeded context used to satisfy foundation gates
- `max_executed_steps`: loop guard for branches
- `fixture_replies`: deterministic replies for fixture mode only

Each step supports:

- `label`: branch target label
- `stage`: WEAVE lifecycle stage (`intent`, `research`, `selection`, `plan`, `engineering`, `qa`, `kpi`, `marketing`, `iteration`, `analysis`)
- `user_message`: scripted owner/user prompt
- `timeout_seconds`: per-turn timeout
- `cwd`: `weave_root` or `app_repo`
- `expect`: predicates over the reply and runtime state
- `on_pass`, `on_fail`, `on_error`, `on_timeout`, `on_max_stage_messages`: branch actions
- `max_stage_messages`: stage-local message-count failover guard
- `post_actions`: currently `approve_stage` and `advance_stage`

Branch actions:

- `next`: continue to the next step
- `stop`: end the scenario successfully only if the latest executed path has no
  unrecovered non-passing result
- `abort`: end the scenario as failed
- `goto:<label>`: jump to another step

`goto:<label>` can model explicit recovery paths. A later passing recovery step
clears a previous timeout/expectation failure only when the failing branch used
`goto:<label>`; a plain `next` path does not erase a prior non-passing result.
Source-mode violations do not use scenario recovery branches; they abort because
they would corrupt the proof boundary.

Expectation predicates currently include:

- `reply_contains_all`
- `reply_contains_any`
- `reply_not_contains_any`
- `reply_regex_any`
- `reply_min_chars`
- `agent_source_in`
- `turn_count_delta_at_least`
- `stage_in`
- `stage_state_in`
- `stage_message_count_at_most`

Runtime-state predicates such as `stage_in` and `stage_state_in` are evaluated
after successful non-state checks and after `post_actions`, so a step can assert
that an `approve_stage`/`advance_stage` action actually moved the app to the
expected stage.

## Output

Each scenario instance writes an isolated bundle:

- `weave-root/`: local WEAVE runtime root
- `scenario-report.json`: per-instance report
- `conversation-review/`: runtime conversation export
- `app-source-snapshot/`: generated/local app repo snapshot

Each executed agent turn records two reviewable artifacts when expectations are
evaluated: the conversation turn links to a stable `*-agent-reply.md` proof
artifact, and the scenario step result links to a final `*-expectations.md`
artifact. This avoids stale conversation checksums while still allowing final
predicate results to include post-action runtime state.

The run root also writes:

- `aggregate-report.json`: pass/fail summary across all scenario instances

## Proof Labels

Fixture mode proves:

- scenario parsing with explicit schema declaration
- timeout and branch behavior, including explicit `goto` recovery only
- runtime conversation capture
- deterministic source labeling with live-source impersonation rejected
- isolated parallel instance execution
- report generation

Fixture mode does **not** prove:

- live Hermes behavior
- deployed gateway behavior
- Telegram delivery/readback
- external deploys, analytics, payments, credentials, or public sends
- real market demand or user validation

Live Hermes CLI mode proves more than fixture mode, but still needs explicit target-surface evidence before it can be called deployed runtime proof.

## Complexity Assessment

MVP complexity is moderate:

- one runner process can coordinate multiple isolated scenario instances with a thread pool
- each instance creates its own WEAVE root, app workspace, transcript, artifacts, and source snapshot
- fixture mode needs no external infrastructure
- Hermes CLI live mode needs a configured Hermes CLI and model/provider access
- deployed gateway mode is not implemented yet; it needs a target-surface adapter with send/wait/readback proof

For application generation at scale, use narrow scenario batches first: one scenario per app archetype, low `--max-turns`, bounded `--timeout`, and `--parallel` sized to available model/runtime capacity. Treat every generated app as local proof until browser QA, deploy approval, analytics/payment gates, and human review are explicitly added.

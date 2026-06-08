# WEAVE Capability Context Runtime QA

Status: local-runtime QA evidence

This note records the current QA boundary for the WEAVE capability context work.

## What Was Tested

The local loopback runtime smoke now verifies that:

- the context index validates
- the runtime source map exposes `capability-context-index`
- `/sources` shows the capability context index through the deterministic
  command layer
- a sample WIP app can be created through the REST runtime
- a context snapshot event can be appended to that app
- the snapshot records all three app-building paths:
  - existing API
  - gateway capability
  - new orchestrator-run capability

## Commands

```bash
python3 scripts/validate_context_index.py docs/context-sources/livepeer-context-index.sample.json
python3 scripts/context_index_runtime_smoke.py
python3 scripts/runtime_smoke.py
```

The same runtime smoke can test a separate local context repository:

```bash
python3 scripts/context_index_runtime_smoke.py --context-index ../weave-context/context-index.json
```

To preserve an owner-facing proof report:

```bash
python3 scripts/context_index_runtime_smoke.py \
  --context-index ../weave-context/context-index.json \
  --report-out /path/to/context-index-runtime-smoke-report.json
```

The separate context repository can also generate an owner-facing capability
probe:

```bash
cd ../weave-context
python3 scripts/context_probe.py --app "WIP Livepeer application"
```

## What This Proves

This proves that WEAVE can discover the capability context source from runtime
state and can record which context was used for a WIP app.

It also proves that the agent-facing UX has a deterministic source-discovery
answer: `/sources` includes the capability context index.

The context probe additionally checks that a user can see the three decision
paths without reading the raw JSON:

- existing APIs
- gateway-exposed capabilities
- new orchestrator-run capabilities

## What This Does Not Prove

This does not prove:

- a live Hermes Telegram gateway is running
- provider credentials are configured
- a live app has successfully called a metered Livepeer API
- the separate context repo has been published to GitHub
- public KPI or production traffic evidence exists for this context path

Those claims require separate live-runtime or hosted-surface evidence.

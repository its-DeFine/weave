# WEAVE Observability, Evaluation, And Governance

WEAVE exists because chat memory is not enough. Every app effort needs durable
state that a user and a later agent can inspect.

## Observability

Every app folder must expose:

- current lifecycle stage;
- stage status;
- open todos;
- proof paths;
- blockers;
- owner actions;
- non-claims;
- latest readback summary.

The minimum readback is `updates/readback.json`.

## Evaluation

Each lifecycle stage is evaluated against:

- scope fit;
- artifact completeness;
- proof quality;
- risk boundaries;
- owner comprehension;
- next-action clarity.

The helper command is:

```bash
bin/weave eval <stage> --review-template
```

When a stage has hard gates, the agent runs them itself and records proof.

## Governance

Governance means the agent cannot silently convert one kind of proof into
another. Local files do not prove deployment. A draft worker packet does not
prove the worker ran. A plan does not prove engineering. Engineering does not
prove QA.

Before every `ACCEPT_FOR_SCOPE`, the agent must state:

- accepted scope;
- proof produced;
- stages not attempted;
- stop boundaries still active;
- next safe action.

## Improvement Metrics

The repo should help operators measure:

- fewer repeated owner asks;
- faster self-unblock inside approved local scope;
- fewer stale workers;
- higher proof completeness;
- cleaner lifecycle state;
- clearer blocked vs done distinctions;
- fewer claims that depend on hidden context.

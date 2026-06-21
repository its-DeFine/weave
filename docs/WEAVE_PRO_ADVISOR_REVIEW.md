# WEAVE Pro Advisor Review

Status: incorporated into v0.1 implementation
Date: 2026-06-21

## Summary

The advisor agreed the WEAVE v0.1 direction is coherent if it is framed as a
local-first Chief of Staff desk, not a hosted control plane or autonomous
orchestration platform.

Recommended scope:

- local WEAVE home;
- local tasks;
- bounded worker packets;
- proof envelopes;
- controller review gate;
- HTML decision snapshot;
- optional external mirrors without bidirectional sync.

Everything else waits.

## Critical Corrections

- The state line must be generated from local task and proof files, not from
  narrative memory.
- Stage and state must be separate.
- Local WEAVE state is authoritative in v0.1; external trackers are mirrors.
- Workers may return `READY_FOR_REVIEW`, `BLOCKED`, or `NEEDS_PACKET_CHANGE`,
  but cannot mark work `DONE`.
- A proof path is not proof unless it is tied to a claim, acceptance check,
  non-claims, and review.
- Snapshots are decision surfaces, not decorative dashboards.

## Top Failure Modes

- state-line theater;
- mirror ambiguity between local state and external trackers;
- loose worker packets;
- proof-path inflation;
- visual snapshot noise.

## Build Target Adopted

The current implementation adopts the local desk target:

```text
Local tasks + packets + proof envelopes + review gate + HTML snapshot.
```

The CLI slice creates a local Chief of Staff home and renders a snapshot without
credentials, live runtime access, deploys, public sends, or paid actions.

## Deferred

- hosted control plane;
- bidirectional Linear/GitHub sync;
- autonomous worker spawning;
- proof from raw logs or transcripts;
- auto-publish or auto-deploy;
- complex animated desk UI.

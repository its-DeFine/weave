# WEAVE Update Model

Status: implementation planning contract
Date: 2026-06-21

## Simple Model

WEAVE updates should reach the Chief of Staff where the user already works.

The user should not need to check a dashboard. The update mechanism writes a
small local update inbox and the Chief of Staff reports relevant changes the
next time the user returns.

## Modes

| Mode | Meaning |
| --- | --- |
| `pinned` | Do not apply updates. Only report that newer versions exist. |
| `notify` | Default. Report useful updates and ask before applying. |
| `auto-safe` | Apply safe docs/schema additions automatically; ask before behavior changes. |

## Version Files

Local state:

```text
weave-home/weave-version.json
weave-home/updates/inbox.md
weave-home/updates/applied.jsonl
```

Example `weave-version.json`:

```json
{
  "current_version": "0.1.0",
  "source_url": "https://github.com/its-DeFine/weave",
  "mode": "notify",
  "last_checked_at": "2026-06-21T00:00:00Z",
  "last_seen_version": "0.1.0"
}
```

## Daily Check

The update check may run as:

- a Codex heartbeat;
- a Hermes scheduler job;
- a local cron/task runner;
- a manual Chief of Staff command.

It reads only public release metadata or pinned public docs:

- version;
- changelog;
- `WEAVE_PROMPT.md`;
- lifecycle schema;
- update policy.

It must not read or send secrets, private transcripts, private hostnames, or
private runtime state.

## Relevance Filter

An update is relevant if it affects:

- lifecycle stages;
- worker spawning;
- proof rules;
- blocker handling;
- update rules;
- Codex adapter behavior;
- Hermes adapter behavior;
- security or public-safe boundaries;
- visual snapshot generation.

It is not relevant enough to interrupt the user if it only changes prose that
does not affect operation.

## Chief of Staff Surfacing

When the user returns, the Chief of Staff adds one compact update line:

```text
WEAVE update: v0.2 available; useful because it improves worker blocker sharing.
Mode=notify. Say "apply WEAVE update" to update after the current stage.
```

If auto-safe applied something:

```text
WEAVE update applied: v0.1.1 docs/schema clarification. No behavior gates changed.
```

## Hard Boundaries

WEAVE never auto-applies updates that change:

- raw secret handling;
- production deployment behavior;
- public send behavior;
- paid action behavior;
- custody/payment behavior;
- owner approval gates;
- private runtime pairing.

Those updates become review items.

## Update Proof

Every check writes:

```json
{
  "checked_at": "2026-06-21T00:00:00Z",
  "current_version": "0.1.0",
  "latest_version": "0.2.0",
  "mode": "notify",
  "decision": "notify_user",
  "summary": "Adds blocker sharing between worker lanes.",
  "requires_confirmation": true
}
```

## Acceptance Checks

- Updates are visible in the Chief of Staff chat, not hidden in a dashboard.
- Safe and behavior-changing updates are separated.
- Auto-update cannot change serious approval gates.
- The public source URL is stored without private topology.
- Update checks produce proof records.

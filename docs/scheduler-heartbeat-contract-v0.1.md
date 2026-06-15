# WEAVE Scheduler Heartbeat Contract v0.1

Trace: ATM-243

This contract defines how WEAVE represents recurring jobs, heartbeat runs,
owner notifications, pause/resume behavior, and kill switches. It is a
specification layer only. It does not install a scheduler, start background
services, send notifications, perform public actions, or connect live providers.

## Simple Model

Recurring WEAVE work should look like visible operating state, not hidden cron.

The scheduler model has four objects:

1. **Recurring job**: the durable plan for repeated work.
2. **Job run event**: one attempted heartbeat execution.
3. **Owner notification**: the owner-visible attention item created by a job or
   lifecycle gate.
4. **Kill switch**: a stop control that can pause or block jobs by scope.

The corresponding schema files are:

- `schemas/recurring-job.schema.json`
- `schemas/job-run-event.schema.json`
- `schemas/owner-notification.schema.json`
- `schemas/kill-switch.schema.json`

Sample fixtures live at:

- `docs/samples/scheduler-jobs.example.json`

## Required Recurring Job Types

The v0.1 scheduler vocabulary includes:

```text
marketing_engagement
feedback_intake
competitor_scan
staged_implementation
feature_recommendation
analytics_review
owner_followup
capability_health_check
```

The first implementation slice must at least support fixtures for:

- marketing engagement;
- feedback intake;
- competitor or sentiment scan;
- staged implementation.

## Job States

Recurring jobs use this state vocabulary:

```text
draft
pending_owner_approval
active
paused
blocked
kill_switched
completed
cancelled
failed
```

Meaning:

- `draft`: defined but not allowed to run.
- `pending_owner_approval`: ready, but waiting for owner approval.
- `active`: allowed to run according to schedule and capability grants.
- `paused`: intentionally stopped without deleting history.
- `blocked`: cannot run because a dependency, capability, or approval is
  missing.
- `kill_switched`: stopped by a broader safety switch.
- `completed`: one-shot or finite recurring work finished.
- `cancelled`: deliberately retired.
- `failed`: scheduler could not execute or record a required run.

## Run States

Each job heartbeat produces a run event with one of these results:

```text
started
succeeded
blocked
failed
skipped
cancelled
timed_out
needs_owner
```

A job's state can be `active` while a specific run is `blocked`; the run event
records the immediate failure and the job records whether the issue is
persistent.

## Cadence Model

Cadence is declarative:

```text
manual
once
hourly
daily
weekly
cron
event_driven
```

The v0.1 contract may store a cron expression, but execution code must not
assume cron exists. A local product surface can show cadence intent before a
real scheduler is implemented.

## External Effect Boundaries

Every job and run must classify its strongest possible external effect:

```text
none
read_only
local_write
staging_write
production_write
public_send
paid_spend
credential_scope_change
destructive_change
```

The following always require explicit owner approval and an active capability
grant:

```text
production_write
public_send
paid_spend
credential_scope_change
destructive_change
```

Hands-off mode does not bypass these gates.

## Job Contract

Minimum recurring job shape:

```json
{
  "schema": "weave/recurring-job/v0.1",
  "job_id": "job-marketing-engagement-001",
  "app_id": "pocket-orchard",
  "job_type": "marketing_engagement",
  "status": "pending_owner_approval",
  "created_at": "2026-06-15T12:00:00Z",
  "cadence": {
    "kind": "weekly",
    "description": "Review replies and draft engagement suggestions once per week."
  },
  "owner_visible_name": "Marketing engagement heartbeat",
  "purpose": "Track approved channel replies and propose owner-reviewed responses.",
  "lifecycle_stages": ["marketing", "iteration"],
  "capability_refs": ["capability:social-draft-access"],
  "approval_required_for": ["public_send"],
  "external_effect": "read_only",
  "kill_switch_refs": ["kill-switch:public-actions"],
  "evidence_refs": ["artifact:marketing-plan-v1"],
  "public_safe": true
}
```

Jobs are plans, not proof. A job does not prove work happened until run events
exist.

## Run Event Contract

Minimum run event shape:

```json
{
  "schema": "weave/job-run-event/v0.1",
  "run_id": "run-marketing-engagement-20260615",
  "job_id": "job-marketing-engagement-001",
  "app_id": "pocket-orchard",
  "started_at": "2026-06-15T12:00:00Z",
  "finished_at": "2026-06-15T12:01:00Z",
  "result": "needs_owner",
  "external_effect": "read_only",
  "summary": "Drafted two possible replies; owner approval required before send.",
  "evidence_refs": ["artifact:reply-draft-review"],
  "notification_refs": ["notification:marketing-reply-review-001"],
  "claims": ["reply drafts were prepared"],
  "non_claims": ["no public message was sent"],
  "public_safe": true
}
```

Run events are append-only evidence. If a run fails, do not overwrite it; write
a later retry run.

## Owner Notification Contract

Notifications represent owner attention, not background noise.

Minimum shape:

```json
{
  "schema": "weave/owner-notification/v0.1",
  "notification_id": "marketing-reply-review-001",
  "app_id": "pocket-orchard",
  "created_at": "2026-06-15T12:01:00Z",
  "source": "job",
  "severity": "action_required",
  "status": "open",
  "title": "Approve or edit drafted marketing replies",
  "body": "The engagement heartbeat prepared drafts but cannot send publicly.",
  "action_refs": ["decision-card:public-reply-001"],
  "public_safe": true
}
```

Notification statuses:

```text
open
acknowledged
resolved
dismissed
expired
```

Notification severities:

```text
info
review
action_required
blocked
urgent
```

## Kill Switch Contract

Kill switches are durable safety controls. They can block jobs by job id, app,
capability, lifecycle stage, or external effect class.

Minimum shape:

```json
{
  "schema": "weave/kill-switch/v0.1",
  "switch_id": "public-actions",
  "status": "enabled",
  "created_at": "2026-06-15T12:00:00Z",
  "scope": {
    "external_effects": ["public_send", "paid_spend"],
    "job_types": ["marketing_engagement"]
  },
  "reason": "Owner has not approved public sends for this app.",
  "created_by": "owner",
  "public_safe": true
}
```

Kill switch status:

```text
enabled
disabled
expired
superseded
```

When enabled, a kill switch wins over job state, cadence, and capability
availability. The next run event should be `blocked` or `skipped` with the kill
switch reference.

## Pause, Resume, And Cancel

Pause:

- sets job status to `paused`;
- writes an event ledger entry;
- does not delete prior run events;
- stops future scheduled execution until resumed.

Resume:

- requires the job to pass current approval and capability checks;
- writes an event ledger entry;
- leaves old failures visible.

Cancel:

- sets job status to `cancelled`;
- records why it no longer belongs in the operating model;
- keeps history available for analysis.

## Retry Rules

Retries must be explicit:

- each retry writes a new run event;
- retry count and max retry count are recorded;
- failures that cross approval, capability, external-effect, or kill-switch
  boundaries do not auto-retry into action;
- repeated failure should create an owner notification or block the job.

## Observability

A product surface should be able to answer:

- what recurring jobs exist;
- which are active, paused, blocked, or kill-switched;
- what the last run did;
- what evidence exists;
- what owner action is needed;
- what external effect would happen if the job ran;
- what remains unproven.

## Integration With Other Contracts

Recurring jobs should reference:

- lifecycle state for current app/stage;
- world model for current product reality;
- capability grants for brokered actions;
- owner decision cards for approval-required forks;
- event ledger entries for job creation, pausing, cancellation, and proof.

## Acceptance For ATM-243

This spec PR is acceptable when:

- job, run event, notification, and kill-switch contracts are documented;
- schema files exist for those object types;
- sample fixtures cover marketing engagement, feedback intake, competitor scan,
  and staged implementation;
- tests prove schema parseability and fixture coverage;
- no live scheduler, background service, notification send, public send, paid
  spend, or external action is implemented.

# WEAVE Chief of Staff Service Blueprint

Status: implementation planning contract
Date: 2026-06-21

## Simple Model

The visible product is one Chief of Staff chat. The backstage system is a small
WEAVE home plus a repeatable lifecycle and proof protocol.

This blueprint describes what the user sees, what the agent does, what the
system stores, and what proves each phase worked.

## Service Blueprint Table

| Phase | User action | Frontstage WEAVE behavior | Backstage WEAVE behavior | Evidence/state |
| --- | --- | --- | --- | --- |
| Activate | User asks an agent to use WEAVE | Explains WEAVE and checks environment | Detects Codex, Hermes, or unsupported surface | environment detection record |
| Create home | User accepts Chief of Staff setup | Creates or guides pinned COS home | Creates WEAVE home files and folders | `weave-home/README.md`, `weave-version.json` |
| Owner setup | User answers onboarding questions | Asks in plain language, no jargon required | Stores public-safe owner profile and communication mode | `owner-profile.md`, `preferences.json` |
| App setup | User names an app or project | Creates active app card and lifecycle state line | Creates app registry entry and initial lifecycle record | `apps.json`, `apps/<id>/lifecycle.json` |
| Tracker setup | User confirms Linear/GitHub availability | Explains whether tasks will go to Linear or local todo | Creates tracker adapter config without secrets | `tracker.json`, Linear issue refs or `tasks.json` |
| Intent | User explains what they want | Asks only missing intent questions | Records intent artifact and sufficiency check | `intent.md`, `intent-check.json` |
| Requirements | User gives constraints and preferences | Shows what is required before build/deploy | Records business, product, technical, and approval requirements | `requirements.md` |
| Architecture | User approves or revises direction | Shows architecture choices and tradeoffs | Records architecture, app surfaces, and capability needs | `architecture.md`, `capabilities.json` |
| Task breakdown | User asks to proceed | Creates work packets and worker lanes | Creates Linear issues or local tasks with proof paths | `tasks.json`, issue URLs |
| Build | User authorizes local/repo work | Spawns Codex or Hermes worker lanes | Tracks worker state, proof, and blockers | worker packet, proof path |
| Review | Worker returns ready-for-review | Shows proof, changed artifacts, and non-claims | Stores review state separately from done state | `review.md`, `proof-index.md` |
| QA | User asks if it works | Runs or records verification commands | Stores pass/fail, evidence, and claim limits | `qa.md`, test outputs |
| Deploy readiness | User asks to deploy or publish | Lists missing gates before any live effect | Stops before credentials/live mutation unless approved | deploy packet or blocker |
| Publish | User approves exact public action | Executes only the approved public action | Records commit/tag/deploy/video proof | release proof |
| Update check | Daily check or manual command | Announces useful WEAVE changes in COS home | Reads current version and latest source version | `updates/inbox.md` |
| Snapshot | Milestone reached | Shows HTML/image state map | Reads only app/task/proof state | snapshot artifact |
| Closure | User accepts result | Marks done only after acceptance checks | Appends final proof and retrospective | done record |

For v0.1, local WEAVE task/proof state is authoritative. Tracker rows are
mirrors unless the user explicitly selects another authority. Every mirror
record must keep local ID, external ID, last sync time, sync direction, and
conflict state. Bidirectional writes are out of scope for the first public
release.

## First-Run Script

```text
WEAVE detected: Codex.

I can create a pinned Chief of Staff home for app operations. This home will
track apps, lifecycle stages, tasks, proof, blockers, worker lanes, and WEAVE
updates.

You can keep using other chats. This chat becomes the place where app operations
are organized and reviewed.

Before we start:
1. How should I speak to you?
2. Where should I record tasks: Linear, local todo, or both?
3. Should WEAVE auto-update, notify before update, or stay pinned?
4. What app do you want to operate first?
```

## State Files

Default WEAVE home structure:

```text
weave-home/
  README.md
  owner-profile.md
  preferences.json
  weave-version.json
  updates/
    inbox.md
    applied.jsonl
  apps.json
  tasks.json
  blockers.md
  proof-index.md
  apps/
    <app-id>/
      app.md
      lifecycle.json
      intent.md
      requirements.md
      architecture.md
      tasks.json
      proof/
      snapshots/
```

All files must be public-safe by default. Secret values, private hostnames,
private network details, and raw transcripts are not stored.

## Worker Lane Contract

A worker lane is not a random side chat. It is a bounded work packet.

```json
{
  "app_id": "punch-compute",
  "stage": "build",
  "worker_type": "codex",
  "goal": "build demand-capture landing page variant",
  "deliverable": "local implementation plus QA artifact",
  "allowed_surfaces": ["repo", "local_tests"],
  "forbidden_surfaces": ["production_deploy", "public_send", "raw_secrets"],
  "acceptance_checks": ["tests pass", "proof artifact exists"],
  "proof_path": "apps/punch-compute/proof/build-001.md",
  "stop_boundary": "stop before deployment or credential use"
}
```

Workers can return `READY_FOR_REVIEW`, `BLOCKED`, or
`NEEDS_PACKET_CHANGE`. They cannot mark work `DONE`. `DONE` requires a proof
envelope and controller review.

Minimum packet fields:

```text
Task:
Stage:
State:
Objective:
Allowed surfaces:
Forbidden actions:
Expected output:
Proof required:
Stop boundaries:
Return states:
Staleness rule:
```

## Proof Envelope Contract

Proof is claim-bound. A path alone is not proof.

Minimum envelope fields:

```json
{
  "schema": "weave-proof-envelope/v0.1",
  "task_id": "WEAVE-0001",
  "claim": "local Chief of Staff state was generated",
  "artifact": "state.json",
  "acceptance_check": "state file exists and declares no live effects",
  "reviewed_by": "controller",
  "state_effect": "ready_for_review",
  "non_claims": ["does not prove live Hermes chat"],
  "sensitive_surfaces_avoided": true
}
```

Unsupported claims must appear as `UNPROVEN`, not as task status.

## Update Service Blueprint

| Phase | Behavior |
| --- | --- |
| Schedule | Once per day by default |
| Source | Public WEAVE repository release/version metadata |
| Read mode | Version, changelog, prompt/schema docs only |
| Safe auto-apply | typo/docs/schema additions that do not change hard gates |
| Confirm first | prompt behavior, lifecycle stages, worker policy, live-effect gates |
| Never auto-apply | secret handling, deploy behavior, external sends, paid actions |
| User visibility | Next COS interaction shows update state line and summary |

Example notice:

```text
WEAVE update ready: v0.2 adds blocker sharing between worker lanes.
Mode: notify-before-update.
Suggested: apply after current Build stage finishes.
```

## Failure Modes And Safeguards

| Failure mode | Safeguard |
| --- | --- |
| User forgets which chat is WEAVE | Every meaningful reply starts with WEAVE state line |
| State line becomes stale theater | State line is generated from local task/proof files |
| Agent skips lifecycle gates | Stage movement requires proof and acceptance checks |
| Worker side chat gets lost | Worker packet includes proof path and returns to COS home |
| Linear is unavailable | Local `tasks.json` and `proof-index.md` become fallback tracker |
| Tracker mirror conflict | Local warning is created; v0.1 does not auto-resolve or write externally |
| Proof path points to noise | Proof envelope must bind artifact, claim, acceptance check, non-claims, and review |
| Update is invisible | Daily update writes inbox and next COS reply surfaces it |
| Update changes behavior silently | Behavior-changing updates require confirmation |
| Live deployment happens too early | Deploy readiness stage stops before live effects |
| Hermes is assumed live | Hermes adapter must report verified, stub, or unavailable |
| Public repo leaks private topology | Public-safe scan and explicit AGENTS.md rules gate release |

## Minimum Acceptance Checks

- Create one local task and move it from Intent to Review while the state line
  changes from local files.
- Prove `READY_FOR_REVIEW` and `DONE` are distinct.
- Block `DONE` when proof envelope, acceptance check, or review note is missing.
- Render a snapshot with one active task, one blocked task, one review task, and
  one stale packet, then answer the next action within 15 seconds.
- Generate a bounded worker packet with allowed surfaces, forbidden actions,
  expected output, proof path, stop boundary, return states, and staleness rule.
- Run without Linear or GitHub while preserving the full local workflow.
- Run an update check as inbox-only public metadata without auto-apply.

## Blueprint Acceptance Checks

- A new user can understand what happens after activating WEAVE.
- A maintainer can implement first-run files and update checks from this doc.
- Codex and Hermes roles are distinct but use the same lifecycle state.
- The service stops before live effects without exact approval.
- Local fallback works when Linear/GitHub/Hermes are unavailable.

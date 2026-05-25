---
name: runtime-app-attachment
description: Require agents working on WEAVE-managed apps to attach to the runtime, inspect app context, and sync evidence back before finishing.
---

# Runtime App Attachment

## Use When

Use this skill before any non-trivial work on a WEAVE-managed app.

This skill prevents workstation-only or chat-only completion. A WEAVE app task
is complete only when the agent has checked the runtime context and either
synced final evidence back to the runtime or clearly recorded why sync did not
happen.

## Runtime Configuration

Fill these values for your installation. Do not commit secrets.

| Field | Value |
|---|---|
| runtime endpoint | `<WEAVE_RUNTIME_ENDPOINT>` |
| health check | `GET <WEAVE_RUNTIME_ENDPOINT>/health` |
| app context read | `GET <WEAVE_RUNTIME_ENDPOINT>/conversation?app_id=<APP_ID>` |
| evidence sync | `POST <WEAVE_RUNTIME_ENDPOINT>/command` |
| default command types | `record_evidence`, `record_decision` |
| workspace root | `<WEAVE_WORKSPACE_ROOT>` |
| private app repo root | `<APP_REPO_ROOT>` |
| managed app registry | `<WEAVE_MANAGED_APP_REGISTRY_PATH>` |
| context sync helper | `<OPTIONAL_CONTEXT_SYNC_HELPER_PATH>` |
| access method | `<LOCAL_BRIDGE | DIRECT_HTTP | SSH_TUNNEL | OTHER>` |

Public templates should leave the values above as placeholders. Private
installations may fill them with local, non-secret paths and endpoints.

## Inputs

- target app id
- target app name
- lifecycle stage
- runtime endpoint or access method
- managed app registry path
- app repository root
- work packet
- evidence or receipt path
- approval and sync boundaries

## Outputs

- runtime health status
- latest app runtime context summary
- evidence sync command or blocked-sync note
- synced runtime evidence reference
- sync verification result
- final claim limits and next action

## Rules

1. Compile the execution packet.
   - Include `goal`, `repo_or_path`, `deliverable`, `constraints`,
     `allowed_or_forbidden_areas`, `acceptance_checks`,
     `environment_class`, and `deadline_or_window`.
   - Treat deploys, credential changes, payment actions, public posts, runtime
     writes, and service restarts as separate approval-gated work.

2. Attach to runtime before work.
   - Check runtime health.
   - Read the target app conversation/context.
   - Identify latest evidence, open blockers, owner gates, and prior decisions.
   - If the runtime is unreachable, continue only when the packet allows local
     work without runtime sync, and mark the work `runtime_sync_blocked`.

3. Work from authoritative state.
   - Runtime context tells the agent what the app/runtime currently knows.
   - Repository files and live endpoints prove what currently exists.
   - Private chat memory is never enough to override runtime or repo evidence.

4. Produce evidence.
   - Record changed artifacts, checks run, verification result, claim limits,
     blockers, and next action.
   - Keep evidence public-safe unless the runtime lane explicitly allows
     private evidence references.
   - Never include API keys, tokens, private keys, seed phrases, passwords,
     customer secrets, or long-lived credentials.

5. Sync evidence back.
   - Use `record_evidence` for completed, blocked, or advanced work.
   - Use `record_decision` when a product/runtime decision changed.
   - Keep `secret_payload_allowed` set to `false`.
   - If sync is blocked, write a local receipt and include the exact future
     sync step in the final answer.

6. Verify sync.
   - Re-read the target app conversation/context.
   - Confirm the new evidence appears with the current date or run id.
   - Confirm runtime health still passes.

## Required Workflow

Use the rules above as the required workflow for every non-trivial app task.
Do not treat a local repo edit, a chat summary, or a green test as complete
runtime app work until runtime context has been read and sync status is known.

## Runtime Command Shape

Use this generic command shape for evidence sync.

```json
{
  "schema": "weave-agent-command/v0.1",
  "command_id": "cmd-<yyyymmddThhmmssZ>-<short-id>",
  "created_at": "<ISO-8601 UTC timestamp>",
  "sender_agent_id": "<AGENT_ID>",
  "receiver_agent_id": "<RUNTIME_AGENT_ID>",
  "target_app_id": "<APP_ID>",
  "target_app_name": "<APP_NAME>",
  "lifecycle_stage": "<LIFECYCLE_STAGE>",
  "command_type": "record_evidence",
  "authority_scope": "<AUTHORITY_SCOPE>",
  "payload_ref": "<PAYLOAD_REF>",
  "deadline_or_window": "<DEADLINE_OR_WINDOW>",
  "requires_owner_approval": false,
  "ack_status": "pending",
  "result_status": "pending",
  "evidence_ref": "<EVIDENCE_REF>",
  "operator_message": "<PUBLIC_SAFE_SUMMARY>",
  "secret_payload_allowed": false
}
```

## Stop Conditions

Stop before runtime sync when:

- runtime writes are outside the approved packet;
- the evidence summary contains secret-shaped values;
- the requested action is actually a deploy, public post, credential change,
  payment/custody action, domain change, or service restart;
- the app id, endpoint, registry, or access method is unknown;
- runtime health or sync verification fails in a way that weakens the claim.

## Final Answer Requirements

For WEAVE app work, the final answer must state:

- runtime health checked: yes/no;
- app context read: yes/no;
- latest relevant runtime timestamp;
- evidence synced: yes/no;
- sync verification: yes/no;
- local receipt path when sync did not happen;
- remaining blockers or owner-gated actions.

## Verification

The work is complete only when one of these is true:

- runtime context was read, evidence was synced, and the new runtime context was
  verified; or
- sync was explicitly out of scope or blocked, and the final answer names a
  local receipt plus the exact command or packet needed for later sync.

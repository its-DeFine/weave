# Workstation Context Sync

Status: public-safe runtime contract.

Workstation context sync lets a local operator or workstation agent record
completed app work into a WEAVE runtime without granting deployment, payment,
credential, or service-management authority.

## Why It Exists

Some app work happens outside the runtime loop: local repository changes,
hosted health checks, QA notes, screenshots, product decisions, and handover
packets. The runtime can maintain the app only after that work is recorded in
its command, conversation, and evidence ledgers.

## Public Contract

A sync packet is reviewable data, not an execution script.

Required fields:

- `schema`: `weave-workstation-context-sync/v0.1`
- `packet_id`
- `app_id`
- `app_name`
- `lifecycle_stage`
- `summary`
- `work_done`
- `evidence_refs`
- `capabilities`
- `decisions`
- `blockers`
- `stop_boundaries`
- `deadline_or_window`
- `secret_payload_allowed`: `false`

The runtime adapter may transform the packet into append-only records such as:

- `record_evidence`
- `record_decision`
- a runtime conversation message

The adapter must reject secret-like payloads and must not load local env files.

## Authority Boundary

Allowed:

- record sanitized evidence references
- record decisions and blockers
- attach app context to a runtime conversation
- make future runtime maintenance easier

Forbidden:

- deploying or publishing
- changing DNS, accounts, billing, or credentials
- moving funds
- starting paid jobs
- changing runtime services or schedulers
- storing secret values

## Replication Flow

```text
local app work
  -> reviewed sync packet
  -> secret scan
  -> runtime ledger command
  -> runtime conversation entry
  -> owner/operator review
```

See `docs/samples/workstation-context-sync.sample.json` for a public-safe sample.

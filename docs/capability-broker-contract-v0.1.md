# WEAVE Capability Broker Contract v0.1

Trace: ATM-242

This contract specifies how WEAVE represents capabilities, credential
references, owner approvals, grants, audit events, and revocation. It is a
design and schema contract only. It does not implement a vault, connect a
provider, perform external actions, or store raw credentials.

## Simple Model

A capability is an owner-approved way for WEAVE to perform a class of action.
The agent can see the capability's name, status, allowed actions, and proof
boundary. The agent must not see raw secrets.

The broker has three jobs:

1. **Inventory**: tell WEAVE which capabilities exist, are missing, or are
   deferred.
2. **Grant**: issue scoped, owner-approved permission to use a capability for a
   specific app/stage/action.
3. **Audit**: record what was requested, approved, attempted, blocked, used, or
   revoked.

## Schema Files

- `schemas/capability-inventory.schema.json`
- `schemas/capability-grant.schema.json`
- `schemas/capability-audit-event.schema.json`

These schemas are public-safe. They allow references such as `secret_ref` and
`capability_ref`, but they do not allow raw credential material to be required
or represented as agent-visible fields.

## Capability States

Capability status uses this vocabulary:

```text
unavailable
available_unconnected
connection_requested
connected
owner_provided
agent_created_pending_owner
granted
suspended
revoked
deferred
failed
```

Meaning:

- `unavailable`: WEAVE knows the capability is absent.
- `available_unconnected`: the owner or environment could connect it, but it is
  not connected yet.
- `connection_requested`: WEAVE asked the owner to connect or authorize it.
- `connected`: a broker can reference the capability, but no action grant is
  implied.
- `owner_provided`: owner supplied the capability through an approved secure
  path.
- `agent_created_pending_owner`: an agent prepared or initiated setup, but owner
  confirmation is still required before use.
- `granted`: a scoped grant exists for a specific action boundary.
- `suspended`: temporarily unavailable without deleting inventory history.
- `revoked`: deliberately removed or no longer usable.
- `deferred`: owner or stage chose to continue without it.
- `failed`: connection or verification failed.

## Capability Types

Allowed types:

```text
web
email
cloud
domain
analytics
ads
social
repo
task_tracker
messaging
payment
database
storage
runtime
custom
```

The type is descriptive. It does not grant permission. Permission comes only
from a grant.

## Agent Visibility

Agents may receive:

- capability id;
- display name;
- type;
- status;
- lifecycle stages where it may be relevant;
- allowed action names;
- blocked action names;
- whether owner approval is required;
- proof/evidence references;
- capability or secret references that cannot be dereferenced by the model.

Agents must not receive:

- raw tokens;
- provider refresh payloads;
- passwords;
- private keys;
- personal verification codes;
- provider console sessions;
- private endpoints or account-specific operating details.

If a tool execution needs a sensitive value, the execution layer resolves the
reference outside the agent-visible transcript and writes an audit event with
the allowed claim boundary.

## Secret Reference Shape

Secret references are opaque strings. They identify broker-managed material
without exposing the material.

Recommended shape:

```text
secret_ref:<stable-public-safe-id>
```

Examples of acceptable public-safe references:

```text
secret_ref:deployment-provider-prod
secret_ref:analytics-readonly
secret_ref:social-posting-draft-only
```

These are labels, not locations. They must not reveal a private machine,
private path, private account, private endpoint, or actual credential value.

## Grant Model

A grant is a scoped permission packet for a capability. It answers:

- who requested the grant;
- who approved it;
- which app and lifecycle stage may use it;
- what actions are allowed;
- what actions remain blocked;
- whether external effects are allowed;
- when it expires;
- what audit events are required.

Minimum grant shape:

```json
{
  "schema": "weave/capability-grant/v0.1",
  "grant_id": "grant-deploy-staging-001",
  "capability_id": "deployment-provider",
  "app_id": "pocket-orchard",
  "stage": "deployment",
  "status": "active",
  "requested_by": "agent",
  "approved_by": "owner",
  "created_at": "2026-06-15T12:00:00Z",
  "allowed_actions": ["create-staging-deploy", "read-deploy-status"],
  "forbidden_actions": ["production-deploy", "paid-plan-upgrade"],
  "approval_required_for": ["production-deploy", "paid-spend"],
  "external_effect": "staging_write",
  "secret_ref": "secret_ref:deployment-provider-staging",
  "audit_required": true,
  "public_safe": true
}
```

Grant status:

```text
requested
active
denied
suspended
revoked
expired
used
failed
```

## External Effect Classes

Each grant and audit event must classify external effect level:

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

Rules:

- `none`, `read_only`, and `local_write` may be allowed by low-risk local
  workflows if the app's lifecycle policy allows it.
- `staging_write` requires an explicit grant.
- `production_write`, `public_send`, `paid_spend`,
  `credential_scope_change`, and `destructive_change` require explicit owner
  approval and a fresh audit event.

## Approval Gates

These action classes must remain owner-gated even if a technical capability is
connected:

```text
public_send
paid_spend
production_deploy
credential_scope_change
destructive_action
legal_or_regulatory_claim
security_boundary_change
real_user_message
```

Hands-off mode does not remove these gates.

## Capability Lifecycle

```text
discover capability need
-> record inventory status
-> ask owner to connect, create, defer, or proceed without it
-> verify connection without exposing raw secrets
-> request scoped grant
-> approve, deny, defer, or revoke
-> execute through brokered path if active grant exists
-> write audit event
-> update world model and event ledger
```

## Audit Event Contract

Every capability use or blocked attempt writes an audit event.

Minimum shape:

```json
{
  "schema": "weave/capability-audit-event/v0.1",
  "audit_id": "audit-20260615-0001",
  "at": "2026-06-15T12:00:00Z",
  "capability_id": "deployment-provider",
  "grant_id": "grant-deploy-staging-001",
  "app_id": "pocket-orchard",
  "stage": "deployment",
  "actor": "agent",
  "action": "create-staging-deploy",
  "result": "allowed",
  "external_effect": "staging_write",
  "evidence_refs": ["artifact:deployment-log-redacted"],
  "claims": ["staging deploy command was submitted through brokered capability"],
  "non_claims": ["does not prove production deploy"],
  "public_safe": true
}
```

Audit result values:

```text
allowed
blocked
denied
deferred
failed
revoked
expired
```

## Integration With Lifecycle Artifacts

Capability events should update:

- lifecycle state `capability_gaps`;
- world model `capability_gaps`;
- event ledger entries for capability requested/deferred and proof recorded;
- owner decision cards when a missing capability changes the plan;
- scheduler jobs when a recurring job depends on the capability.

## Failure Cases

The broker must make these failures explicit:

- capability missing;
- owner approval missing;
- grant expired;
- grant does not include requested action;
- requested action has higher external effect than grant allows;
- broker cannot resolve secret reference;
- verification failed;
- audit event could not be written;
- revocation happened during queued work.

Failure is a valid lifecycle state. The agent should report the blocked action,
the reason, the requested next owner action, and what remains unproven.

## Acceptance For ATM-242

This spec PR is acceptable when:

- the broker inventory, grant, secret reference, audit, revocation, and approval
  boundary model is documented;
- schema files exist for inventory, grant, and audit events;
- tests prove the schema files are parseable and do not require raw credential
  fields;
- the docs index links the contract;
- no credential storage, provider connection, or live external action is
  implemented.

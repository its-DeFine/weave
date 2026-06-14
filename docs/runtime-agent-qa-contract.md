# WEAVE Runtime Agent QA Contract

WEAVE must not claim that Hermes agents, MCP tools, A2A packets, XMTP adapters, gateways, or containerized runtimes work until the lifecycle contains an explicit runtime QA contract and fresh evidence from the target surface.

## Simple model

- **Hermes** is the worker runtime.
- **MCP/tools** are the hands available to that worker.
- **Containers/worktrees** are isolated rooms where workers cannot accidentally share state.
- **A2A/XMTP/gateway transports** are delivery paths between rooms.
- **WEAVE** is the manager that specifies the rooms, the tools, the scenario, the approval gate, and the evidence needed before saying the thing works.

## When this contract is required

A plan must include this contract before Engineering or QA whenever the claimed feature depends on any of these surfaces:

- multiple Hermes agents communicating;
- MCP server installation, discovery, or tool use;
- gateway routing or messaging adapters;
- A2A/XMTP work-packet delivery;
- containerized or profile-isolated runtime behavior;
- model/provider/token parity across more than one runtime.

If the contract is missing, the Plan stage can still be discussed, but it is not executable enough to advance as runtime proof.

## Required contract fields

A runtime-agent QA contract should be stored as a review artifact with this shape:

```json
{
  "schema": "weave.runtime-agent-qa-contract/v0.1",
  "feature_id": "short-stable-id",
  "target_claim": "the exact claim QA is allowed to prove",
  "runtime_surface": "hermes-cli | hermes-gateway | mcp-server | a2a-transport | xmtp-adapter | mixed",
  "proof_boundary": "local-only | container-mesh | live-transport | external-write-verified",
  "topology": {
    "agent_count": 2,
    "isolation": "container | worktree | profile | mixed",
    "runtime_image_or_source": "pinned image, checkout, or build ref",
    "hermes_home_mode": "fresh-per-agent",
    "model_provider": "same provider for all agents unless variance is intentional",
    "model_id": "same model for all agents unless variance is intentional",
    "credential_source_ref": "owner-approved secret reference, never raw secret text",
    "toolsets": ["terminal", "file", "mcp", "messaging"],
    "mcp_servers": [
      {
        "name": "server-under-test",
        "transport": "stdio | http",
        "installation_scope": "agent-a | agent-b | both",
        "expected_tools": ["tool names or prefixes"]
      }
    ]
  },
  "identities": {
    "agent_a": "stable test identity or profile label",
    "agent_b": "stable test identity or profile label",
    "pairing_method": "explicit invite, configured peer record, or signed handshake",
    "address_exchange_evidence": "artifact path or packet id"
  },
  "scenario_matrix": [
    {
      "id": "happy-path-work-packet",
      "goal": "agent A sends a structured task packet to agent B; B returns evidence",
      "parallelizable": true,
      "expected_evidence": ["A outbox", "B inbox", "approval record", "B evidence", "A receipt"]
    },
    {
      "id": "approval-block",
      "goal": "B receives a task but does not execute before approval",
      "parallelizable": true,
      "expected_evidence": ["pending state", "blocked execution attempt"]
    },
    {
      "id": "replay-duplicate",
      "goal": "duplicate packet does not double execute",
      "parallelizable": true,
      "expected_evidence": ["dedupe record", "single execution record"]
    },
    {
      "id": "malformed-or-secret-payload",
      "goal": "bad schemas and secret-looking payloads are rejected",
      "parallelizable": true,
      "expected_evidence": ["validation error", "no execution", "redacted report"]
    }
  ],
  "parallel_test_lanes": [
    "unit schema validation",
    "integration queue/readback",
    "container mesh communication",
    "MCP tool discovery and allowed-tool call",
    "transport send/receive/readback",
    "public-safe and no-secret scan"
  ],
  "commands": [
    {
      "id": "launch-mesh",
      "command_ref": "script or CLI invocation, with secret refs not raw values",
      "expected_artifacts": ["mesh manifest", "per-agent logs", "per-agent config summaries"]
    },
    {
      "id": "run-scenarios",
      "command_ref": "scenario runner invocation",
      "expected_artifacts": ["scenario report", "transcripts", "packet ledger"]
    },
    {
      "id": "verify-readback",
      "command_ref": "readback verifier invocation",
      "expected_artifacts": ["verifier result", "claim boundary"]
    }
  ],
  "approval_gates": [
    "external transport credentials require owner approval",
    "public writes, payments, custody, deployment, and real-user messages are out of scope unless separately approved"
  ],
  "teardown": {
    "required": true,
    "evidence": ["containers stopped", "temporary homes archived or removed", "secrets not written to artifacts"]
  }
}
```

## Disposable resource lifecycle

Runtime QA resources are disposable rooms, not durable product state. A QA plan must decide how each container, Compose project, temporary profile, Hermes home, and worktree will be phased out before it is created.

Required resource states:

1. **created** — the disposable surface exists and is labeled with the QA run id.
2. **running** — the runtime is active and may execute only the scoped scenario.
3. **completed** — scenario execution is finished and no new scenario work should begin.
4. **teardown_requested** — the run is draining; queues/logs/ledgers are flushed and new work is rejected.
5. **stopped** — containers/gateways/processes are no longer active.
6. **removed** — disposable containers, temporary homes, or worktrees were deleted after archive gates passed.
7. **phased_out** — only durable evidence, sanitized exports, manifests, and checksums remain.

Cleanup policy requirements:

- archive or explicitly mark runtime state ephemeral before deleting a container;
- keep raw credentials out of contracts, logs, archives, and evidence bundles;
- use QA labels such as `weave.qa.disposable=true` and `weave.qa.run_id=<id>` so deletion targets only the test room;
- default Compose cleanup is `docker compose down --remove-orphans`; named volumes are retained unless a sanitized export exists and the policy explicitly allows volume deletion;
- future re-up must come from Docker Compose plus sanitized runtime export/retained volume, then `verify-runtime` and secret relink before any renewed behavior claim.

Claim limits:

- **cleanup-verified** only means disposable resources were stopped/removed and durable evidence remains. It does not prove feature behavior.
- **rehydration-verified** only means the archive/import verified in a fresh runtime. It does not prove live transport still works unless credentials were relinked and scenarios reran.
- A deleted container is not durable state. Only runtime-home exports, retained volumes, manifests, checksums, and evidence bundles are durable.

## QA execution rules

1. Launch fresh isolated runtimes for each participating agent. Do not reuse the parent agent home as proof.
2. Read back the effective provider, model, toolsets, MCP servers, and credential references from each runtime before running scenarios.
3. Install or configure the tool/MCP/transport under test in the runtimes that need it, then prove discovery from inside those runtimes.
4. Pair the test identities explicitly. Pairing proves identity knowledge, not permission to execute.
5. Run happy path and failure path scenarios. A runtime transport proof needs both.
6. Harvest evidence from both sides of the communication. One-sided logs are not enough for a communication claim.
7. Verify duplicate/replay protection and malformed-packet rejection.
8. Label the proof surface honestly: local queue, container mesh, live transport, or external target readback.
9. Teardown or quarantine all temporary runtimes and keep artifacts public-safe.

## XMTP/MCP example acceptance

For an XMTP-shaped MCP/tool test, the minimum acceptable proof is:

1. Agent A and Agent B start in separate isolated runtimes with the same intended model and provider.
2. The MCP server or transport adapter is installed/configured on the correct side and its tools are discovered.
3. Agent A learns Agent B's test identity through the specified pairing method.
4. Agent A sends a structured work packet through the target adapter.
5. Agent B receives the packet, stores it, and refuses execution before approval.
6. Approval is recorded by local policy or owner action.
7. Agent B executes a bounded safe action and emits evidence.
8. Agent B returns an evidence packet through the target path.
9. Agent A records the evidence and can read it back.
10. Duplicate, malformed, and secret-looking packets do not execute.

If any step uses a fixture, mock, local queue, or direct file copy instead of the target adapter, the allowed claim must say so.

## Allowed claims

- **Plan-only:** the scenario is specified but not run.
- **Harness-built:** launch scripts or scenarios exist but were not executed.
- **Container-mesh verified:** isolated runtimes communicated on the configured local/test transport and both sides were read back.
- **Live-transport verified:** the real adapter delivered and both sender and receiver readbacks match.
- **External-write verified:** the intended external target was changed and read back there.
- **Cleanup-verified:** disposable runtime surfaces were stopped/removed and durable evidence/archive remains.
- **Rehydration-verified:** sanitized archive restored into a fresh runtime and runtime verification passed.

Anything weaker must not be reported as live XMTP, live gateway, or production communication proof.

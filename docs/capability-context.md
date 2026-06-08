# WEAVE Capability Context

Status: public contract draft

WEAVE agents need a maintained context source before they can reliably create
applications from Livepeer pipelines, Livepeer APIs, gateway-exposed
capabilities, or new orchestrator-run capabilities.

This document defines the context contract that the WEAVE tool reads. The
recommended operating shape is a separate public GitHub repository for the
context itself, with this repository keeping the schema, lifecycle rule, and
default pointer.

## Repository Split

```text
its-DeFine/weave
  owns: lifecycle, agent rules, context schema, validation, and default pointer

its-DeFine/weave-context
  owns: current capability notes, source freshness, examples, and snapshots
```

Keeping the context in a separate repo avoids coupling fast-changing capability
notes to the WEAVE tool release cycle. The WEAVE repo should still define the
rules for how an agent uses that context.

## Context Index

The context repo should expose a machine-readable index:

```text
https://raw.githubusercontent.com/its-DeFine/weave-context/main/context-index.json
```

The context repo may also expose human-readable Markdown pages and a static docs
site, but the JSON index is the canonical agent entrypoint.

The index tells the agent:

- which sources exist
- what type each source is
- which lifecycle stages need the source
- how fresh the source is
- whether the source must be rechecked before use
- which application paths the source supports

## Three Application Paths

WEAVE should model three distinct ways to build an application.

### Path 1. Existing APIs

Use this path when the application can call an existing API directly.

The agent needs to know:

- API base URL and documentation URL
- auth model and whether credentials are owner-gated
- supported operations
- rate limits, pricing, or usage constraints
- sample request and response shape
- QA method that proves the integration works
- failure modes and fallback behavior

Example source types:

- `api`
- `sdk`
- `documentation`
- `example`

### Path 2. Gateway Capabilities

Use this path when the application should route work through a gateway that
selects available network capabilities.

The agent needs to know:

- gateway documentation and endpoint shape
- how capability discovery works
- what pipelines, models, or operations are exposed
- what the gateway does versus what the orchestrator does
- pricing, latency, reliability, and output-quality limits
- how to test capability availability without overclaiming production readiness

Example source types:

- `gateway`
- `pipeline`
- `capability-discovery`
- `pricing`
- `health`

### Path 3. New Orchestrator-Run Capabilities

Use this path when WEAVE wants to create or package a capability that
orchestrators can run and gateways can expose.

The agent needs to know:

- expected capability interface
- container or runtime boundary
- hardware requirements
- model or workload artifacts
- warm-start and pricing assumptions
- gateway advertisement or discovery requirements
- conformance tests
- deployment and operations risks

Example source types:

- `orchestrator-capability`
- `container`
- `model`
- `hardware`
- `conformance-test`
- `operations`

## Lifecycle Rules

The agent must consult the context index at these points:

- Research: before mapping capabilities or market options
- Selection: before choosing an application wedge
- Plan: before naming tasks, credentials, and gates
- Engineering: before integrating an API, gateway, or capability
- QA: before claiming a source is live or available
- KPI Setup: before naming usage or payment evidence
- Marketing: before public claims about capabilities or availability
- Iteration: before changing direction based on new evidence

If a source has `freshness: verify_before_use`, the agent must recheck the
primary source before making an implementation or public claim.

## Source Evidence Rule

Each app should record the context snapshot it used:

```yaml
context_snapshot:
  index_url: "https://raw.githubusercontent.com/its-DeFine/weave-context/main/context-index.json"
  index_version: "2026-06-06"
  checked_at: "2026-06-06T00:00:00Z"
  sources_used:
    - "livepeer-ai-api"
    - "livepeer-ai-gateway"
```

This lets a reviewer answer: what did the agent know when it selected, built, or
changed the application?

## Public-Safety Rule

The context repo must not contain:

- private endpoints
- private credentials or credential locations
- private hostnames, device names, or operator-specific transport details
- unpublished deployment topology
- private customer or user data

Use references to public documentation, public repositories, public API specs,
or sanitized examples.

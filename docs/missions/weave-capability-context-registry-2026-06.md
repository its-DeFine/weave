---
mission_id: weave-capability-context-registry-2026-06
target_repo: its-DeFine/weave
scope: Add a public, refreshable capability context registry that WEAVE agents can use for Livepeer pipelines, APIs, documentation, KPI sources, and application ideas.
acceptance_criteria:
  - docs/capability-context.md exists and defines the human and machine-readable context contract
  - docs/context-sources/livepeer-context-index.sample.json exists and validates as JSON
  - packages/weave-tool/primitives/registry.json distinguishes pipeline, API, documentation, KPI, and outreach source types
  - package validation exits 0
  - public-safe repository scan exits 0
compute_budget_minutes: 90
credit_reward: 30
value_to_org: Gives Hermes and future WEAVE agents a stable source of current capability context before they research, select, or build applications.
why_compute_conserving: A shared context registry prevents every agent session from rediscovering the same pipeline, API, pricing, limitation, and example information from scratch.
---

# Capability Context Registry

**Scope**

Create the public WEAVE capability context layer. This layer should let an agent
find the canonical context index, inspect available Livepeer pipelines and APIs,
understand source freshness, and cite which context was used before creating or
iterating on an application.

**Acceptance evidence required**

- [ ] `docs/capability-context.md` defines the context contract.
- [ ] `docs/context-sources/livepeer-context-index.sample.json` exists and is valid JSON.
- [ ] The primitive/source registry distinguishes pipeline, API, documentation,
      KPI, and outreach source types.
- [ ] Agent-facing instructions say when context must be refreshed.
- [ ] `python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool` exits 0.
- [ ] `python3 scripts/public_safe_repo_scan.py` exits 0.

**Compute budget:** 90 minutes agent runtime.
**Credit reward:** 30 credits on verified completion.

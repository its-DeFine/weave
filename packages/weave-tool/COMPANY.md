---
schema: agentcompanies/v1
kind: company
slug: weave
name: WEAVE
description: AI-operated application business that turns agent-run product lifecycle work into usable products.
version: "2026.05.13-console"
releaseDate: "2026-05-13"
releaseTag: "v2026.05.13-console"
releaseChannel: public-d1-console
license: MIT
homepage: https://github.com/its-DeFine/weave
runtime: hermes-default
runtimeFallback: local-fallback
goals:
  - Build commercially viable WEAVE applications through the lifecycle.
  - Use Month 1 product proof and conversation-to-app dogfood surfaces as the current review anchors.
  - Keep Askuno Runtime Proof as a historical worked example, not the current deliverable-review anchor.
  - Preserve a clean future swap path to Livepeer-native pipelines.
requirements:
  secrets:
    - hermes_runtime_credentials
    - livepeer_gateway_credentials
metadata:
  lifecycle: weave-eight-stage-plus-growth-loop
  primaryRuntime: hermes-default
  fallbackRuntime: local-fallback
  ceoAgent: ceo-hermes
---

# WEAVE

WEAVE is an AI-operated business runtime for guiding agent-run product work
from intent to shipped application with evidence, gates, KPI setup, marketing,
and a parallel iteration-analysis loop tracked as first-class state.

The company operates in lifecycle order:

1. Research and analysis.
2. Selection.
3. Plan.
4. Engineering and commercial integration.
5. QA and readiness.
6. KPI setup and public/reporting instrumentation.
7. Marketing and distribution.

After KPI setup, the growth loop runs under Marketing instead of after it:

- Iteration: implement feedback or arbitrary product improvements and deploy them.
- Analysis: read analytics and feedback, then recommend the next iteration.

Hermes is the default CEO agent and active runtime for this package. WEAVE
supplies the business logic: primitives, lifecycle gates, application
selection, evidence contracts, agent skill contracts, command-bus boundaries,
and future Livepeer adapter boundaries. Local Fallback remains the explicit fallback
runtime for legacy or owner-directed recovery runs.

## Current Review Anchor

Review the Month 1 WEAVE surfaces as a lifecycle/runtime package, not as an
Askuno-specific launch review. The current reviewer-facing anchors are:

- FableFrame Studio local product proof.
- The full conversation-to-app dogfood artifact bundle.
- The deterministic lifecycle, command, evidence, and prompt-pack contracts.

Askuno Runtime Proof remains a starter project and historical worked example in
this package. It should not be used as the acceptance surface for the current
Month 1 deliverable review unless a separate Askuno review packet is explicitly
requested. Future Livepeer gateway, payment, or compute-warrant adapters must be
connected only after a separate approval and evidence gate.

# WEAVE Application Lifecycle Summary

WEAVE is built around an application lifecycle for agent-run product work.

The important point is that WEAVE is the lifecycle wrapper, not the execution
runtime itself. Hermes and approved local execution tools do the actual work.
WEAVE tracks the target, source context, stage, plan, evidence, review gates,
owner approvals, KPI signals, and iteration history around that work.

For Month 1, the active runtime operator is Hermes. The lifecycle status
surface should expose Hermes' selected app, lifecycle stage state, agent
activity, evidence paths, owner approval gates, and Gestalt Runtime Pack
outputs.

For the formal lifecycle contract, see [WEAVE Lifecycle Contract v0](weave-lifecycle-contract-v0.md).
For the runtime agent behavior contract, see [WEAVE Agent Operating Contract v0](weave-agent-operating-contract-v0.md).

## Stage 1. Intent

Purpose: define the product target, user, constraints, authority boundary, and
owner goal before the runtime starts changing code or publishing work.

This includes:
- who the application is for
- what problem or workflow it targets
- what external actions are approval-gated
- what counts as a truthful proof

## Stage 2. Research

Purpose: understand the Livepeer capability surface and the market opportunity
surface well enough to identify viable applications. The capability surface can
include existing APIs, gateway-exposed capabilities, pipeline documentation, SDKs,
pricing or limit references, and orchestrator-run capability paths.

This includes:
- mapping existing APIs, gateways, pipelines, and what they can do
- assessing quality, uptime, pricing, operators, and operational reliability
- synthesizing capabilities into reusable primitives where useful
- identifying what applications become possible from those primitives or direct
  API/gateway paths
- running competitor analysis and pricing analysis once a serious concept exists
- recording the context sources checked and which sources must be refreshed
  before implementation or public claims

Primitive note:
- a stacked primitive layers multiple pipelines in the same path or modality
- a coordinated primitive uses multiple pipelines together across different paths or modalities inside the same application behavior

## Stage 3. Selection

Purpose: choose the simplest shippable application wedge and state why it is
being selected now.

This includes:
- selecting one application target
- naming deferred alternatives
- recording the smallest credible proof path
- recording known risks or missing data

## Stage 4. Plan

Purpose: translate the selected application into scoped runtime work.

This includes:
- tasks and done criteria
- review gates
- approval boundaries
- evidence expected from the runtime

## Stage 5. Engineering

Purpose: compose the chosen APIs, gateway capabilities, pipelines, or
orchestrator-run capabilities into a working application and wire the payment,
credit, or orchestrator flow correctly where that is in scope.

This includes:
- using the relevant existing APIs, gateways, pipelines, or capability paths
  correctly
- implementing runtime behavior and application assembly
- implementing user payment flow and orchestrator routing
- connecting the runtime to the hosted or documented product surface as needed

## Stage 6. QA

Purpose: test the built application, identify issues, and determine whether it is ready for user exposure.

This includes:
- functional QA
- integration QA
- payment-flow QA
- failure-case QA
- capability-source freshness QA for volatile API, gateway, pricing, or model
  claims
- readiness judgment

## Stage 7. KPI Setup

Purpose: define what will be measured before marketing or distribution starts.

This includes:
- naming the KPI source or reporting surface
- defining public and private metrics
- recording omissions when analytics are not yet available
- setting the interpretation rule for usage, credits, payments, quality,
  onboarding, positioning, or market fit

## Stage 8. Marketing

Purpose: put the application in front of real consumers through a controlled,
reviewable workflow.

This includes:
- creating the marketing workflow
- having the agent operate draft, research, or distribution-support work where
  approved
- advertising or distributing to target users in a controlled way
- keeping human review or approval where a boundary is intentionally retained

## Stage 9. Iteration

Purpose: improve or redirect the product after QA, KPI, marketing, or owner
feedback creates evidence for a change.

This includes:
- making engineering changes
- deploying the changed system
- re-QAing the changed system
- returning to earlier stages as needed
- rejecting, pausing, or reframing when evidence justifies
- refreshing capability context when a source, API, gateway, or orchestrator
  capability has changed

## Stage 10. Analysis

Purpose: read analytics and feedback as they arrive and turn them into the next
iteration recommendation.

This includes:
- summarizing usage, onboarding, payment, quality, or campaign signals
- separating public aggregate metrics from private operational metrics
- recommending continue, change, park, or reject
- naming the evidence that justifies the next implementation pass

## Wrapper versus execution runtime

This distinction matters:
- the execution runtime does the work
- the WEAVE wrapper guides the lifecycle, records evidence, exposes gates, and
  reports public KPIs
- the application output is the shipped product, starting with Askuno in Month 1
- the capability context source tells the runtime which public APIs, gateways,
  pipelines, and orchestrator capability paths are available to inspect

These are related layers, but they should not be collapsed into one object.

# WEAVE Application Lifecycle Summary

WEAVE is built around a six-stage application lifecycle.

The important point is that this lifecycle is primarily operated by the agent. Humans can remain in the loop for steering, review, and approval-gated actions, but the runtime is meant to perform the actual work of researching, building, QAing, distributing, reading feedback, and iterating.

## Stage 1. Research and analysis

Purpose: understand the Livepeer capability surface and the market opportunity surface well enough to identify viable applications.

This includes:
- mapping existing pipelines and what they can do
- assessing quality, uptime, pricing, operators, and operational reliability
- synthesizing pipelines into reusable primitives
- identifying what applications become possible from those primitives
- running competitor analysis and pricing analysis once a serious concept exists

Primitive note:
- a stacked primitive layers multiple pipelines in the same path or modality
- a coordinated primitive uses multiple pipelines together across different paths or modalities inside the same application behavior

## Stage 2. Engineering and commercial integration

Purpose: compose the chosen pipelines into a working application and wire the payment and orchestrator flow correctly.

This includes:
- using the relevant existing pipelines correctly
- implementing runtime behavior and application assembly
- implementing user payment flow and orchestrator routing
- connecting the runtime to the hosted or documented product surface as needed

## Stage 3. QA and readiness

Purpose: test the built application, identify issues, and determine whether it is ready for user exposure.

This includes:
- functional QA
- integration QA
- payment-flow QA
- failure-case QA
- readiness judgment

## Stage 4. Outreach and distribution

Purpose: put the application in front of real consumers through a repeatable workflow.

This includes:
- creating the outreach workflow
- having the agent operate that workflow as the primary actor
- advertising or distributing to target consumers in a controlled way
- keeping human review or approval only where a boundary is intentionally retained

## Stage 5. KPI, feedback, and interpretation

Purpose: read market truth from usage, public KPIs, analytics, and customer responses.

This includes:
- tracking public KPIs
- collecting analytics and customer feedback
- interpreting whether the problem is product, market, pricing, onboarding, quality, or positioning

## Stage 6. Iteration

Purpose: improve or redirect the product based on real-world evidence.

This includes:
- making engineering changes
- re-QAing the changed system
- returning to outreach or earlier stages as needed
- rejecting, pausing, or reframing when evidence justifies

## Tool versus runtime

This distinction matters:
- the WEAVE tool is the open-source capability layer and should be able to support all six lifecycle stages
- the WEAVE runtime is the deployed realization of that same capability layer, where the lifecycle becomes actualized against real users, real applications, real outreach, real analytics, and real iteration

The tool and the runtime are not two unrelated products. The runtime is the live expression of the tool.

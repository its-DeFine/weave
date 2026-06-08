---
name: gestalt-runtime
description: Operate Hermes through the WEAVE Gestalt Runtime Pack from raw app idea to contract, handoff, implementation, validation, and contract update.
---

# Gestalt Runtime

## Use When

Use this skill whenever Hermes receives a raw app idea, incomplete contract,
implementation request, validation request, or contract update request.

## Inputs

- owner idea or existing contract
- current WEAVE app context
- lifecycle stage and evidence
- allowed and forbidden authority
- available capability refs
- acceptance checks

## Outputs

- Gestalt Kernel
- Gestaltian Contract
- Premortem Report when building is requested
- Build-Ready Handoff Packet
- implementation report or blocker
- validation result
- Contract Update Log

## Rules

- Load `packages/weave-tool/prompts/hermes-gestalt-runtime-pack/manifest.json`
  and the referenced prompt files before acting.
- Preserve the whole before decomposing it.
- Ask only blocking questions before implementation.
- Do not start Engineering until a Build-Ready Handoff Packet exists.
- Every task must trace to the final vision, invariant, workflow, component,
  decision or failure, and acceptance test.
- Validate functional behavior, failure behavior, and Gestalt correctness.
- Treat adapter-only execution as support evidence, never as Hermes completion.

## Stop Conditions

- The owner intent is too ambiguous to form a Gestalt Kernel.
- A build request lacks a Build-Ready Handoff Packet.
- The requested action needs production, spend, public send, provider mutation,
  credentials, or irreversible work without explicit approval.
- The runtime pack is missing, invalid, or not loaded.

## Verification

The skill is ready when the Hermes Gestalt Runtime Pack validator passes and a
simulated idea-to-handoff proof contains Contract, Premortem, Implementation,
and Contract Update mode evidence.

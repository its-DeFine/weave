---
name: compound-engineering
description: Plan and execute agentic engineering loops with explicit capability checks, proof surfaces, adversarial review, and non-claims.
---

# Compound Engineering

## Use When

Use this skill when work involves any of:

- turning vague owner intent into agent-executable work;
- WEAVE lifecycle, Chief of Staff, worker orchestration, or Symphony adapter
  changes;
- building or choosing a CLI, local queue, index, fixture, evaluator, browser
  proof, or API wrapper before implementation;
- PR readiness, CI proof, launch readback, or public-safe release work;
- repeated failures where the harness should improve instead of relying on
  memory or manual reminders.

## Inputs

- owner intent in plain language;
- current lifecycle stage, if known;
- target surface: repo, app, browser, queue, tracker, PR, runtime, or dashboard;
- allowed and forbidden sources;
- public gate: none, PR, deploy, send, billing, credential, or live tracker;
- proof required;
- known non-claims;
- previous failures or stale-worker risks.

## Outputs

- compound engineering packet;
- capability decision;
- worker packet or explicit no-worker decision;
- proof target and validation commands;
- adversarial review result;
- non-claims and owner gates;
- closeout state and next safe action.

## Output Packet

Produce this packet before execution:

```text
Compound engineering mode: true
Objective: <value that should exist for the user>
Lifecycle stage: <inferred stage, not owner-classified>
Target surface: <surface that must be proven>
Capability question: <missing CLI/index/queue/eval/wrapper?>
Chosen path: <reuse/build/skip/kill>
Worker packet: <agent-executable task shape>
Proof required: <exact command, artifact, browser state, CI check, or live readback>
Adversarial review: <what would make us revise/block/kill?>
Public gate: <none or exact approval required>
Non-claims: <what this slice does not prove>
```

## Rules

- Treat owner prompts as draft intent, not as complete specifications.
- Infer lifecycle stage and missing information without forcing the owner to use
  WEAVE vocabulary.
- Validate the target surface, not a nearby artifact.
- Prefer reuse before adding a new tool, abstraction, or dependency.
- Add a capability only when it makes future agent work more legible or safer.
- Keep public, live, paid, destructive, credential, and tracker mutations gated.
- Record explicit non-claims whenever a slice proves less than the owner wants.
- If the same class of failure repeats, improve the harness with a check, doc,
  skill, fixture, or evaluator.

## Procedure

1. Preserve the owner's raw intent.
2. Infer the WEAVE lifecycle stage. Do not ask the owner to classify it.
3. Decide whether the work needs a missing capability before implementation.
4. Prefer an existing repo surface or skill before adding new code.
5. If a capability is missing, build the smallest local, testable surface.
6. Execute in a bounded worktree or package area.
7. Validate the target surface, not a nearby artifact.
8. Run adversarial review against overclaim, hidden assumptions, user value, and
   proof quality.
9. Record non-claims and owner gates.
10. Update the harness when a repeated failure pattern appears.

## WEAVE To Symphony Adapter Rule

For WEAVE-to-Symphony work, use
`docs/WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md` as the standing plan.

Required boundary:

- WEAVE owns user intent, lifecycle truth, proof envelopes, owner gates, and
  readback.
- Symphony owns isolated workspaces, Codex app-server execution, retries,
  blocked/running state, and optional operational dashboard surfaces.
- The adapter owns conversion between WEAVE `WorkItem` records and
  Symphony-dispatchable work.

Never claim adapter success until the current slice has target-surface proof.

## Proof Rules

- Local files prove file state only.
- Unit tests prove only tested behavior.
- Runtime smoke proves only local runtime scope.
- Browser proof requires DOM, screenshot, or interaction evidence.
- CI proof requires current CI status for the relevant branch or PR.
- Live tracker proof requires exact approved live tracker surface.
- Public sends, deploys, billing, credentials, and live tracker mutations are
  gated.

## Adversarial Review

Before closeout, answer:

- What would make this fail for the user?
- What target surface was not tested?
- Did we build a capability because it was needed, or because it was convenient?
- Can an agent mark this done without proof?
- Is the state visible after compaction or restart?
- Should this be accepted, revised, blocked, or killed?

## Stop Conditions

- The target surface requires a gated action without recorded approval.
- The plan depends on raw secrets, cookies, private sessions, raw logs, or raw
  transcripts.
- The only proof is a nearby artifact rather than the claimed behavior.
- The owner value is unclear and cannot be inferred from the request.

## Verification

Closeout must include:

- state: `accepted_for_scope`, `revise`, `blocked`, `needs_owner_action`, or
  `killed`;
- files changed;
- exact checks run;
- target surface proven;
- non-claims;
- next safe action.

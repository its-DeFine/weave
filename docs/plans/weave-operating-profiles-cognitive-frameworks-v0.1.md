# WEAVE Operating Profiles for Cognitive Frameworks v0.1

Status: engineering concept contract
Date: 2026-06-09
Source: synthesized from the agent action provenance handoff and WEAVE owner-intent loop discussion

## Purpose

This document crystallizes how WEAVE should turn abstract owner intent into
configurable agent operating loops using structured cognitive/process frameworks.

The goal is not to pick one academic framework and force all agent work through
it. The goal is to let WEAVE agents select, combine, configure, and audit
standard operating profiles so that vague intent can mature into:

1. explicit work-domain understanding;
2. known constraints and forbidden actions;
3. process and decision models;
4. executable specs and handoff packets;
5. bounded action;
6. target-surface verification;
7. structured provenance for future agents.

Short version:

```text
Owner intent
  -> classify work
  -> select operating profile
  -> model context and missing information
  -> mature intent into spec
  -> decide bounded action
  -> record action intent
  -> act within scope
  -> verify target surface
  -> record action result
  -> hand off reliable state
```

## Product thesis

WEAVE should expose **operating profiles**, not just prompts.

An operating profile is a named configuration that tells an agent:

- what kind of work it is doing;
- which framework or framework stack applies;
- what artifacts it must produce before action;
- what evidence is required after action;
- what it must do when information is missing;
- what requires owner approval;
- what future agents may rely on.

The first default profile should be:

```text
hermes-gestalt-lifecycle
```

It should preserve the current WEAVE lifecycle and Hermes Gestalt Runtime Pack,
then add an explicit framework-selection and provenance layer.

## Core distinction

Retrospective human/team analysis usually asks:

```text
Observed action -> infer cognitive process -> explain why
```

WEAVE agent operation should instead ask prospectively:

```text
Goal -> work model -> operating profile -> pre-action rationale
  -> bounded action -> verification -> audit ledger -> downstream handoff
```

The reasoning artifact should exist both before and after action. It should be
structured and reviewable, not a dump of hidden chain-of-thought.

## Trigger model: reactive and proactive work

The current operating-profile idea needs an explicit trigger axis. The same
cognitive frameworks apply differently depending on whether the work starts
from a direct owner request or from an observed signal.

### Reactive tasks

Reactive tasks start from an explicit owner/app/operator request.

Examples:

- "turn this intent into a full implementation";
- "ship the lifecycle proof";
- "review this PR";
- "build the marketing launch packet".

Default behavior:

```text
owner intent -> intent frame -> operating profile -> bounded lifecycle loop
  -> target-surface verification -> action_result -> handoff
```

Reactive work can move aggressively through implementation because the owner
has supplied the initiating authority. The agent still needs proof boundaries,
approval gates, and no-goal capture, but the trigger itself is already valid.

### Proactive tasks

Proactive tasks start from a monitored condition, elapsed time, feedback,
usage data, partner pattern, market signal, operational degradation, or
previously scheduled review point.

Examples:

- one week of application usage reveals a pattern;
- partners repeatedly ask for the same workflow;
- marketing claims are no longer aligned with product evidence;
- KPI data suggests a planned feature should be deferred;
- support/feedback shows a missing onboarding step;
- a launch sequence moves from one-off execution to continuous optimization.

Default behavior:

```text
signal -> source/evidence classification -> CWA/IBIS/DMN assessment
  -> recommendation/no-action/defer packet -> owner gate or bounded action
  -> verification -> updated assumption ledger
```

Proactive work should not mean "the agent just does things." It should mean
the agent can notice, assess, and recommend with structured evidence. It may
act only inside explicitly pre-authorized bounds.

### CEO-agent profile

A CEO-agent or product-operator agent is best modeled as a proactive assessment
profile, not as an unrestricted executor.

It should hold broad context, but its authority should be narrow:

- ingest approved feedback, KPI, support, partner, roadmap, and marketing data;
- detect material changes or repeated patterns;
- run CWA when the operating context has changed;
- run IBIS when interpretation is contested;
- run DMN when rules determine whether a signal is actionable;
- write ADRs when product direction changes;
- produce recommendation, defer, stop, or owner-approval packets;
- execute only pre-approved low-risk local maintenance actions.

It should explicitly support **do not do** decisions. A mature proactive loop is
not just a feature generator; it is also a cancellation, deferral, and risk
control system.

### Continuous work conversion

Some workflows begin reactive and become proactive:

- marketing launch -> marketing monitoring and claim governance;
- KPI setup -> weekly product review;
- support response -> recurring friction-pattern analysis;
- partner onboarding -> partner-pattern roadmap input;
- implementation proof -> release-readiness monitoring.

The process profile should therefore record both:

- `trigger_mode`: `reactive`, `proactive`, or `hybrid`;
- `authority_mode`: `recommend_only`, `bounded_local_action`,
  `approval_required_action`, or `pre_authorized_external_action`.

## Framework stack

WEAVE should use a layered stack:

- **WEAVE Lifecycle Contract**: outer stage machine, gates, evidence, review state.
- **Hermes Gestalt Runtime Pack**: whole-preserving semantic compiler from raw idea to contract, premortem, handoff, implementation, validation, and contract update.
- **CWA**: work-system model for abstract, ambiguous, dynamic, or new territory.
- **Product lifecycle pattern mining**: public artifact ladder for strategic/product work.
- **BPMN / SOP / checklist**: observable workflow for known repeatable procedures.
- **DMN**: deterministic rule and routing decisions.
- **IBIS / hypothesis map**: contested choices, ambiguity, arguments, unresolved questions.
- **ADR / decision record**: consequential decisions that future agents must understand.
- **W3C PROV-inspired event ledger**: entities, activities, agents, generated artifacts, verification, and downstream reliability.
- **Proof gates**: target-surface verification and truthful claim boundaries.

No single framework is enough:

- CWA is strong for discovering the work system, weak as a concrete runtime audit ledger.
- BPMN is strong for observable process, weak for internal reasoning and ambiguity.
- DMN is strong for repeatable rules, weak when variables are not discovered yet.
- IBIS/ADR are strong for rationale, weak as execution engines.
- PROV is strong for lineage, weak for deciding what to do.

WEAVE should compose them.

## Operating profile selection

The agent should start each non-trivial task by selecting one or more profiles.

### CWA Discovery Profile

Use when:

- owner intent is abstract;
- the domain is unfamiliar;
- success criteria are unclear;
- constraints, authorities, tools, or actors are not mapped;
- the agent does not yet know what should be done.

Purpose:

```text
Convert vague intent into a work-domain model before choosing a workflow or action.
```

Required outputs:

- goals and values;
- constraints and forbidden actions;
- actors, tools, artifacts, authorities;
- recurring control tasks;
- missing information;
- plausible strategies;
- risk boundaries;
- recommended next profile.

For WEAVE, CWA is the correct starting layer for **new territories** and
under-specified owner intent. It prevents the agent from jumping straight from a
voice note or broad strategic desire into code.

### Product Lifecycle Pattern Mining Profile

Use when:

- work is product-strategic;
- launch, adoption, support, docs, or market proof matter;
- public lifecycle examples can reduce uncertainty.

Purpose:

```text
Extract public success patterns before turning strategy into a WEAVE plan.
```

Evidence ladder:

```text
intent/problem
  -> spec/RFC/proposal
  -> review/decision
  -> implementation
  -> tests/QA
  -> release notes/changelog/docs
  -> launch narrative
  -> enablement/support/community
  -> operations metrics
  -> next iteration
```

The output must label source-backed facts, same-product inferences,
cross-product inferences, assumptions, and unsupported claims.

### BPMN Execution Profile

Use when:

- the process is known;
- steps and handoffs matter;
- multiple actors or lanes are involved;
- approval or exception paths matter.

Purpose:

```text
Represent what happens, in what order, between whom, with what gates.
```

Required outputs:

- start event;
- tasks;
- gateways;
- actors/swimlanes;
- handoffs;
- exceptions;
- approval gates;
- end state.

### DMN Decision Profile

Use when:

- a repeatable rule determines the answer;
- inputs and thresholds are known or discoverable;
- routing, eligibility, risk gating, or stage movement should be deterministic.

Purpose:

```text
Given inputs and rules, produce a reproducible decision and rule-hit trace.
```

Required outputs:

- required inputs;
- known/missing/assumed input status;
- rules;
- matched rules;
- decision output;
- confidence and missing variables.

### IBIS Deliberation Profile

Use when:

- there are competing interpretations or options;
- evidence is incomplete;
- the agent must explain why one path is preferred;
- disagreement or tradeoff is expected.

Purpose:

```text
Map issue, options, arguments, evidence, unresolved questions, and selected position.
```

Required outputs:

- issue/question;
- options;
- arguments for;
- arguments against;
- evidence;
- unresolved questions;
- preferred option;
- why the option is good enough for the next lifecycle decision.

### ADR Commitment Profile

Use when:

- a choice affects architecture, process, policy, scope, proof boundary, or future work;
- downstream agents need to know why alternatives were rejected.

Purpose:

```text
Record a consequential decision in a compact future-readable form.
```

Required outputs:

- context;
- decision;
- alternatives considered;
- consequences;
- status;
- evidence/references;
- revisit condition.

### PROV Ledger Profile

Use when:

- always.

Purpose:

```text
Preserve lineage across observations, interpretations, decisions, actions, artifacts, verification, and handoffs.
```

Required event types:

- observation;
- interpretation;
- profile_selection;
- decision;
- action_intent;
- action_result;
- verification;
- escalation;
- handoff;
- playbook_update.

## Maturity ladder

WEAVE should track intent maturity explicitly:

```text
M0 Raw Intent
M1 Framed Intent
M2 Work Model
M3 Decision Model
M4 Executable Spec
M5 Action Packet
M6 Verified Result
M7 Reusable Pattern
```

### M0 Raw Intent

The owner gives a desire, task, question, or direction.

Pass condition: the raw input is preserved enough to avoid losing meaning.

### M1 Framed Intent

The agent restates:

- objective;
- target user or beneficiary;
- desired outcome;
- non-goals;
- constraints;
- target proof surface;
- missing information.

Pass condition: the owner intent can be reviewed as a structured frame.

### M2 Work Model

The agent uses CWA or another profile to model the work system.

Pass condition: the agent can state what is known, what is missing, what matters,
what is forbidden, and what strategies are plausible.

### M3 Decision Model

The agent uses DMN, IBIS, ADR, or equivalent structure to resolve routing and
choice.

Pass condition: future agents can see why this path was selected and what was
rejected.

### M4 Executable Spec

The agent produces an implementable WEAVE spec or Build-Ready Handoff Packet.

Pass condition: Engineering can proceed without reinterpreting the owner intent.

### M5 Action Packet

The agent records a pre-action intent event with selected bounded action,
rationale, rejected alternatives, approval requirement, and verification method.

Pass condition: the action can be audited before it happens.

### M6 Verified Result

The action is performed and checked against the actual target surface.

Pass condition: the result has evidence and a precise state label.

### M7 Reusable Pattern

The agent updates a reusable profile, playbook, rule, test, or skill when the
work reveals a durable process improvement.

Pass condition: future agents get a better method without reading the transcript.

## Canonical WEAVE Intent Maturity Loop

```text
0. Receive owner intent.
1. Preserve the raw intent and finished-state intuition.
2. Frame the intent into outcome, non-goals, constraints, proof surface, and missing data.
3. Classify the work as static, dynamic, or hybrid.
4. Select operating profiles.
5. If abstract/new/ambiguous, run CWA before workflow/action.
6. If product-strategic, run lifecycle-pattern mining before Plan.
7. If repeatable/rule-based, run DMN.
8. If process-known, run BPMN/SOP.
9. If contested, run IBIS.
10. If consequential, write ADR.
11. Compile a Build-Ready Handoff Packet or blocker.
12. Record action_intent before any non-trivial action.
13. Act within scope, choosing the smallest useful bounded action.
14. Verify the target surface.
15. Record action_result, verification, state label, claim limits, and downstream reliability.
16. Advance, loop, escalate, or stop.
```

## Work-type routing

### Static work

Static work has stable rules and known procedure.

Use:

- BPMN/SOP;
- DMN;
- checklist;
- evidence packet;
- proof gate.

Behavior:

```text
Follow procedure -> apply rules -> verify -> report evidence and claim limits.
```

### Dynamic work

Dynamic work has uncertainty, changing context, unclear success criteria, or
unmapped constraints.

Use:

- CWA;
- hypothesis testing;
- IBIS;
- ADR;
- provenance ledger;
- escalation gates.

Behavior:

```text
Map situation -> identify uncertainty -> select smallest bounded action
  -> verify -> update model -> loop or escalate.
```

### Hybrid work

Most WEAVE product work is hybrid.

Use:

```text
CWA/product-pattern mining first -> then BPMN/DMN/SOP execution once classification is stable.
```

## Stage-by-stage defaults

### Intent

Default profile stack:

- Gestalt Runtime Pack;
- CWA Discovery;
- PROV Ledger.

Required artifacts:

- intent frame;
- profile selection;
- missing-information list;
- owner gates;
- target proof surface.

### Research

Default profile stack:

- CWA Discovery;
- product lifecycle pattern mining;
- IBIS when competing interpretations exist;
- PROV Ledger.

Required artifacts:

- research brief;
- evidence ladder;
- source/inference labels;
- unresolved questions;
- sufficiency self-check.

### Selection

Default profile stack:

- IBIS Deliberation;
- ADR Commitment;
- DMN when selection criteria are rule-like;
- PROV Ledger.

Required artifacts:

- options;
- decision record;
- deferred alternatives;
- strongest objection;
- revisit condition.

### Plan

Default profile stack:

- BPMN Execution;
- DMN Decision;
- ADR when scope/process choices are consequential;
- PROV Ledger.

Required artifacts:

- Build-Ready Handoff Packet;
- task graph;
- acceptance checks;
- authority boundaries;
- stop/escalation conditions.

### Engineering

Default profile stack:

- BPMN/SOP;
- DMN for risk gates;
- action_intent/action_result events;
- PROV Ledger.

Required artifacts:

- changed files;
- commands run;
- implementation evidence;
- failure handling;
- claim limits.

### QA

Default profile stack:

- BPMN/SOP;
- DMN gates;
- proof-boundary labeling;
- PROV Ledger.

Required artifacts:

- test matrix;
- target-surface proof;
- failure evidence;
- readiness label;
- unverified surfaces;
- proof-strength labels that separate raw captured evidence from agent self-report;
- explicit partial/retry status for timeout, max-turn/tool-cap, or missing raw proof.

A QA pass requires more than an agent-written summary. The gate should attach raw
command output or checksums for CLI checks, rendered/console evidence for browser
checks, and read-back artifacts for export claims. If only a model-written QA
reply exists, label it `agent-self-reported-check` and do not promote it to
`raw-command-captured` or `browser-smoke-captured`.

### Proof calibration ladder

Every lifecycle stage should classify each material claim using this ladder:

1. `source-inspected`: source/artifact read, behavior not executed.
2. `agent-self-reported-check`: agent says it ran a check; raw output missing.
3. `raw-command-captured`: command, cwd, exit code, stdout/stderr or checksums captured.
4. `browser-smoke-captured`: rendered UI, console, and DOM/screenshot evidence captured.
5. `export-readback-captured`: generated export/artifact was read back and parsed.
6. `external-write-verified`: real external target send/deploy/payment/etc. completed with readback.
7. `external-unproven/gated`: external surface remains unproven and requires owner approval.

Rules:

- Artifact existence is not proof validity.
- Implementation proof must check required target files/paths directly. A lifecycle
  runner should fail engineering if named files such as `index.html`, `styles.css`,
  `app.js`, or `README.md` are absent, even when the agent reply sounds plausible.
- A timeout, max-turn cap, or tool-call cap makes the stage `partial` unless all
  required proof predicates already have captured evidence.
- Fixture mode proves orchestration/reporting only.
- Hermes CLI mode proves live generated-agent behavior only; it does not prove
  Telegram or deployed-gateway behavior.
- Deployed gateway proof requires a target-surface adapter that performs
  send/wait/readback against the real destination.

### KPI Setup

Default profile stack:

- DMN for metric eligibility and public/private classification;
- ADR for KPI definitions;
- PROV Ledger.

Required artifacts:

- metrics definition;
- collection boundary;
- privacy/publication boundary;
- feedback loop trigger.

### Marketing

Default profile stack:

- BPMN for launch/support workflow;
- DMN for public-claim gating;
- IBIS for audience/channel/message tradeoffs;
- PROV Ledger.

Required artifacts:

- launch plan;
- verified claim list;
- blocked/deferred claims;
- owner approval request for public sends.

### Iteration and Analysis

Default profile stack:

- CWA for changed operating context;
- IBIS for interpreting feedback;
- ADR for changed direction;
- PROV Ledger.

Required artifacts:

- feedback interpretation;
- contract update;
- next-loop recommendation;
- superseded assumptions.

## Configurability model

WEAVE should make the method configurable without making the agent arbitrary.

Configurable:

- active operating profile;
- stage order;
- stage-to-profile mapping;
- required artifacts by stage;
- evidence depth;
- proof surfaces;
- approval gates;
- iteration caps;
- escalation rules;
- eval contract bindings;
- prompt pack binding.

Not freely configurable without owner/admin approval:

- secret payload policy;
- public-send authority;
- spend/paid action authority;
- credential/auth mutation authority;
- production deployment authority;
- destructive action authority;
- proof-boundary labeling rules.

## Data model: process profile

A process profile is a public-safe package definition or local runtime profile
that binds stages to frameworks, artifacts, gates, and proof surfaces.

```json
{
  "schema": "weave-process-profile/v0.1",
  "id": "hermes-gestalt-lifecycle",
  "framework_id": "hermes-gestalt",
  "version": "2026.06.09",
  "trigger_mode": "hybrid",
  "authority_mode": "approval_required_action",
  "proactive_signal_sources": [
    "feedback",
    "kpi_data",
    "support_patterns",
    "partner_patterns",
    "scheduled_review"
  ],
  "secret_payload_allowed": false,
  "stage_order": [
    "intent",
    "research",
    "selection",
    "plan",
    "engineering",
    "qa",
    "kpi-setup",
    "marketing",
    "iteration",
    "analysis"
  ],
  "stages": [
    {
      "id": "intent",
      "default_profiles": ["gestalt", "cwa_discovery", "prov_ledger"],
      "required_artifacts": ["intent_frame", "profile_selection", "missing_information"],
      "exit_criteria": ["owner_intent_framed", "proof_surface_named"],
      "owner_review_required": true
    }
  ],
  "approval_gates": [
    "public_send",
    "paid_or_metered_work",
    "credential_or_auth_mutation",
    "production_deployment",
    "destructive_or_irreversible_change"
  ]
}
```

## Data model: profile selection record

```json
{
  "schema": "weave-profile-selection/v0.1",
  "task_id": "T-123",
  "owner_intent_summary": "string",
  "lifecycle_stage": "intent",
  "work_type": "static | dynamic | hybrid",
  "abstraction_level": "low | medium | high",
  "uncertainty_level": "low | medium | high",
  "repeatability": "one_off | recurring | unknown",
  "risk_level": "low | medium | high",
  "selected_profiles": ["cwa_discovery", "prov_ledger"],
  "rationale": [
    {
      "profile": "cwa_discovery",
      "reason": "Owner intent is abstract and the work domain is not yet mapped."
    }
  ],
  "next_artifact": "cwa_work_domain",
  "stop_if_missing": ["authority boundary", "target proof surface"]
}
```

## Data model: intent frame

```json
{
  "schema": "weave-intent-frame/v0.1",
  "task_id": "T-123",
  "owner_intent": "string",
  "agent_restatement": "string",
  "desired_outcome": "string",
  "target_user_or_beneficiary": "string",
  "success_signal": "string",
  "target_proof_surface": "string",
  "scope": {
    "in_scope": ["string"],
    "out_of_scope": ["string"]
  },
  "constraints": ["string"],
  "forbidden_actions": ["string"],
  "known_facts": [
    {
      "claim": "string",
      "source": "string",
      "status": "observed | inferred | assumed | verified"
    }
  ],
  "missing_information": ["string"],
  "initial_work_type": "static | dynamic | hybrid"
}
```

## Data model: CWA work domain

```json
{
  "schema": "weave-cwa-work-domain/v0.1",
  "task_id": "T-123",
  "domain": "string",
  "goals": ["string"],
  "values": ["string"],
  "constraints": ["string"],
  "forbidden_actions": ["string"],
  "actors": ["string"],
  "tools": ["string"],
  "artifacts": ["string"],
  "authorities": ["string"],
  "control_tasks": ["diagnose", "classify", "prioritize", "recover", "escalate"],
  "unknowns": ["string"],
  "strategy_options": [
    {
      "strategy": "string",
      "pros": ["string"],
      "cons": ["string"],
      "risks": ["string"]
    }
  ],
  "recommended_next_profile": "bpmn_execution | dmn_decision | ibis_deliberation | adr_commitment | action_packet"
}
```

## Data model: action intent

```json
{
  "schema": "weave-action-intent/v0.1",
  "event_type": "action_intent",
  "task_id": "T-123",
  "agent_id": "agent-name",
  "lifecycle_stage": "plan",
  "goal": "string",
  "profile_context": ["cwa_discovery", "dmn_decision"],
  "current_state": "string",
  "evidence": [
    {
      "claim": "string",
      "source": "string",
      "status": "observed | inferred | assumed | verified | missing"
    }
  ],
  "constraints": ["string"],
  "candidate_actions": ["string"],
  "selected_action": "string",
  "rationale_summary": "string",
  "rejected_alternatives": [
    {
      "action": "string",
      "reason": "string"
    }
  ],
  "risk_level": "low | medium | high",
  "approval_required": false,
  "verification_method": "string",
  "downstream_expected_impact": "string"
}
```

## Data model: action result

```json
{
  "schema": "weave-action-result/v0.1",
  "event_type": "action_result",
  "task_id": "T-123",
  "agent_id": "agent-name",
  "lifecycle_stage": "engineering",
  "action_taken": "string",
  "target_surface": "local_file | cli | test | pr | live_agent | browser | deployed_service | public_surface",
  "proof_strength": "source-inspected | agent-self-reported-check | raw-command-captured | browser-smoke-captured | export-readback-captured | external-write-verified | external-unproven/gated",
  "interruption_state": "none | timeout | max_turns | tool_cap | cancelled",
  "observed_result": "string",
  "evidence": [
    {
      "source": "string",
      "summary": "string"
    }
  ],
  "state_label": "planned | staged | local-only | verified | blocked | delivered | external-write-verified",
  "assumptions_confirmed": ["string"],
  "assumptions_falsified": ["string"],
  "new_risks": ["string"],
  "downstream_reliability": {
    "safe_to_rely_on": ["string"],
    "not_safe_to_rely_on": ["string"],
    "requires_validation": ["string"]
  },
  "next_recommended_action": "string"
}
```

## Downstream handoff contract

Every handoff should include:

```text
Reliable for downstream:
- verified facts;
- actions actually taken;
- artifacts created or changed;
- active constraints;
- target-surface proof.

Not reliable yet:
- assumptions;
- inferences;
- planned but unexecuted actions;
- unchecked target surfaces;
- stale or superseded evidence.

Recommended next move:
- safest next bounded action;
- profile to use next;
- gate or approval required before action.
```

## Engineering architecture

### Package definitions

Add package-level definitions once the runtime-generated first slice is stable:

```text
packages/weave-tool/cognitive-frameworks/registry.json
packages/weave-tool/cognitive-frameworks/hermes-gestalt.json
packages/weave-tool/process-profiles/hermes-gestalt-lifecycle.json
```

These files should define framework ids, default prompt pack, process profile,
secret policy, stage mappings, default artifact obligations, and eval bindings.

### Runtime local state

Generate or copy the active profile into local runtime state:

```text
runtime/profiles/process-profile.json
```

The local runtime profile should include:

- process profile id;
- framework id;
- version;
- hash;
- source;
- selected stage order;
- prompt pack;
- secret payload policy.

### App snapshot

Each new app should snapshot the process profile in its app metadata so that
future agents know which method governed the work.

Suggested fields:

```json
{
  "cognitive_framework_id": "hermes-gestalt",
  "process_profile_id": "hermes-gestalt-lifecycle",
  "process_profile_version": "2026.06.09",
  "process_profile_hash": "sha256:..."
}
```

### Runtime surface

Add read-only inspection first:

```text
/runtime/process-profile
```

Optional deterministic Telegram command later:

```text
/process
/profile
```

The first slice should be read-only. Runtime mutation of process profiles should
come later and should be owner/admin-gated.

## Minimal engineering slice

The smallest safe implementation should not immediately move every lifecycle
constant into config. First create the profile substrate from existing behavior.

### Slice 1: Generated process profile from current code

Files:

- `scripts/weave_runtime_slice.py`
- `tests/test_weave_runtime_slice.py`

Work:

1. Add `PROCESS_PROFILE_SCHEMA = "weave-process-profile/v0.1"`.
2. Add helpers:
   - `process_profile_path(root)`;
   - `default_process_profile(root)`;
   - `validate_process_profile(profile)`;
   - `write_process_profile(root, profile)`;
   - `ensure_process_profile(root)`.
3. Build the default profile from existing lifecycle constants and requirements.
4. Call `ensure_process_profile(root)` inside root setup.
5. Add process profile summary to deterministic status output.
6. Add process profile id/hash to the agent profile.
7. Snapshot process profile id/hash into new app metadata.
8. Add read-only REST dispatch for `/runtime/process-profile`.
9. Add tests for setup, validation, app snapshot, and REST readback.

Acceptance:

```text
A fresh WEAVE root deterministically records the active process profile without changing lifecycle behavior.
```

### Slice 2: Package-level profile files

Files:

- `packages/weave-tool/process-profiles/hermes-gestalt-lifecycle.json`
- `packages/weave-tool/cognitive-frameworks/hermes-gestalt.json`
- `packages/weave-tool/cognitive-frameworks/registry.json`
- `packages/weave-tool/scripts/validate_company_package.py`
- `tests/test_weave_company_package.py`

Work:

1. Move the default profile into package definitions.
2. Validate schemas, ids, stage coverage, eval bindings, prompt pack reference,
   and `secret_payload_allowed: false`.
3. Ensure all canonical lifecycle stages have profile mappings.
4. Update package summary and tests.

Acceptance:

```text
The WEAVE company package validates with cognitive framework and process profile definitions included.
```

### Slice 3: Stage profile obligations

Files:

- `scripts/weave_runtime_slice.py`
- `scripts/weave_eval.py`
- `tests/test_weave_runtime_slice.py`
- `tests/test_weave_eval.py`

Work:

1. Bind each stage to required profile artifacts.
2. Expose missing artifacts in lifecycle/status output.
3. Make eval contracts aware of profile obligations.
4. Add blocked/needs-agent-review outcomes when required artifacts are missing.

Acceptance:

```text
A stage cannot claim readiness when its configured profile artifacts are missing.
```

### Slice 4: Action provenance events

Files:

- `scripts/weave_runtime_slice.py`
- `tests/test_weave_runtime_slice.py`
- docs under `docs/month1/` if public review artifacts need updates.

Work:

1. Add `action_intent` and `action_result` event writers.
2. Append events to the app ledger.
3. Project downstream reliability into status/evidence output.
4. Add tests for event append, projection, and overclaim prevention.

Acceptance:

```text
A future agent can read the ledger and reconstruct what was intended, done, verified, and safe to rely on.
```

### Slice 5: User-visible profile inspection

Files:

- `scripts/weave_runtime_slice.py`
- `integrations/hermes/weave-runtime/__init__.py`
- `tests/test_weave_runtime_slice.py`
- `tests/test_weave_runtime_http.py`

Work:

1. Add deterministic `/process` or `/profile` command.
2. Register it in the Hermes plugin command map.
3. Ensure output is concise and public-safe.
4. Include active framework id, profile id, stage profile, proof boundary, and
   whether mutation is allowed.

Acceptance:

```text
The owner can inspect which operating profile governs the runtime without asking the model to infer it.
```

## Acceptance criteria for the whole feature

### Concept acceptance

- WEAVE defines agents as using selectable operating profiles, not one generic loop.
- CWA, BPMN, DMN, IBIS, ADR, and PROV each have a clear role.
- CWA is the default first profile for abstract or under-specified owner intent.
- The framework stack distinguishes discovery, process, decision, deliberation,
  commitment, provenance, and proof.
- Hidden chain-of-thought is not the audit mechanism.

### Runtime acceptance

For every non-trivial lifecycle task, the runtime can show:

- owner intent frame;
- work type;
- selected profile(s);
- why those profiles were selected;
- missing information;
- constraints and forbidden actions;
- selected action;
- rejected alternatives;
- verification method;
- actual result;
- downstream reliability.

### Proof acceptance

- Fixture mode proves orchestration/reporting only.
- Hermes CLI live-agent proof proves generated-agent behavior only.
- Deployed gateway/Telegram proof requires its own target-surface adapter.
- Public claims cannot exceed attached proof.

## Non-goals

This feature should not:

- turn WEAVE into a second semantic planner competing with Hermes;
- expose hidden chain-of-thought;
- store secrets or private transcripts as audit artifacts;
- allow arbitrary runtime profile mutation without owner/admin approval;
- claim deployed gateway behavior from local fixture or CLI proof;
- force all tasks through heavyweight CWA/BPMN/DMN artifacts.

## Blunt design rule

Do not make frameworks decorative.

If WEAVE says an agent used CWA, BPMN, DMN, IBIS, ADR, or PROV, there must be a
corresponding structured artifact, gate, or ledger event that future agents can
read. Otherwise it is just methodology theater.

The first implementation should therefore prove one narrow thing:

```text
The active process profile is deterministic, inspectable, snapshotted onto app work, and tied to stage artifact obligations.
```

Only after that should WEAVE support multiple configurable profiles.

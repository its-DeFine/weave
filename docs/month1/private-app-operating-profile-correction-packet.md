# Private App Operating Profile Correction Packet

Status: owner-confirmed correction; included in this PR update as proof-boundary review evidence

## Blunt correction

The current private-app operating-profile slice should be described as a deterministic fixture/test harness, not as the intended live product-building agent loop.

It currently proves that WEAVE can generate reviewable local static-app artifacts and cognitive evidence from hard-coded synthetic scenarios. It does not prove that live Hermes agents can take owner intent through the full lifecycle from requirements to execution, ask for missing specialized data, coordinate one or more agents through the defined cognitive/process loop, and iterate until acceptance or a bounded stop condition.

## Owner-confirmed target

The intended test target is a **live Hermes-agent lifecycle**:

> A live agent takes an owner request from intent to execution across the full lifecycle, except lifecycle steps that cannot be honestly evaluated in this slice, such as real post-launch iteration and marketing.

This means the real proof target is not merely generated fixture files. The replies and actions must come from one or more agents run through Hermes/Codex/Hermes-managed agent execution, with reviewable evidence that they followed the lifecycle and cognitive framework.

## Current packet interpretation

Current artifact set:

- `scripts/private_app_operating_profile_eval.py`
- `packages/weave-tool/process-profiles/private-app-parallel-assessment.json`
- `docs/month1/private-app-operating-profile-evals.md`
- `docs/month1/private-app-operating-profile-eval-sample-report.md`
- `tests/test_private_app_operating_profile_eval.py`
- `docs/month1/artifacts/private-app-operating-profile-evals/`
- `docs/month1/private-app-operating-profile-correction-packet.md`

Correct interpretation:

- `scripts/private_app_operating_profile_eval.py` contains pre-baked synthetic app scenarios.
- Each scenario is a whole benchmark fixture, not a live agent lifecycle.
- The scenario data is generic and synthetic, not owner-provided specialized requirements.
- The harness emits static app files plus CWA/DMN/IBIS/ADR/PROV artifacts.
- The harness does not run a live model or autonomous coding loop.
- The harness does not ask clarifying questions when required input is missing.

## Proven surface today

Highest currently proven surface:

`local deterministic private-app fixture with generated static apps and reviewable framework-gate evidence`

What this means:

- orchestration and report generation are exercised locally;
- parallel scenario execution is exercised locally;
- privacy/authority boundaries are represented as deterministic artifacts;
- generated output is reviewable as files;
- fixture behavior can help test deterministic expectations and mock-data behavior.

## Non-claims today

Do not claim that the current PR proves:

- live Hermes-agent lifecycle behavior;
- Codex/Hermes goal-loop execution until acceptance;
- Telegram/deployed-gateway adapter behavior;
- hosted/private-app runtime behavior;
- real user requirement intake;
- specialized private data handling;
- clarifying-question behavior;
- production/customer/market validation.

## Confirmed input model

The intended system should support multiple ways of inputting specialized data. These are different intake surfaces, not different products:

- structured JSON/YAML requirement packet;
- conversational transcript;
- direct Telegram/owner messages;
- fixture/mock-data packets for deterministic regression tests.

The same lifecycle contract should normalize these into a reviewable requirement/intake state before the agent proceeds.

## Confirmed scenario model

Scenarios should not be defined by a fixed number of owner turns. Real lifecycle work may require a variable number of turns.

Instead, the process should define bounded lifecycle step loops:

- Each lifecycle step has explicit acceptance criteria.
- Each step may take multiple turns or agent passes.
- The loop may set a maximum number of unresolved agent attempts.
- If the step is still unresolved after the limit, the process pauses and asks the owner for manual feedback.
- The system must not proceed to the next lifecycle step until the current step is accepted, blocked, or explicitly waived.

Example rule:

```text
while intake_step is not resolved:
  agent tries to classify/complete missing requirements
  if required information is actually missing:
    ask owner for specific missing information
  if unresolved_agent_attempts >= 3:
    pause lifecycle and request owner/manual feedback
  do not proceed to planning/build until intake is resolved or waived
```

The exact limit can be configured per lifecycle step. The key point is that the turn count is an escalation/stop rule, not the scenario definition.

## Confirmed agent/process requirement

The process must be legible like reviewing human team operations or code.

The packet should specify, in reviewable form:

- lifecycle states;
- responsible agent roles;
- routing rules;
- what each agent checks;
- what evidence each agent produces;
- when work moves to another agent;
- when work pauses for owner/manual feedback;
- what proof is required before advancing.

Analogy: if a human mail-service process says mail goes to Joe, suspicious mail routes to Rio, and Rio performs checks A/B/C, the agent lifecycle must be specified with the same operational legibility.

The live agent must use that process as its loop contract, not merely mention the framework in prose.

## Confirmed cognitive-framework behavior

The live agent should behave according to the selected cognitive assessment framework and the written loop contract.

Required reviewable evidence should include:

- intake/intent frame;
- missing-information assessment;
- cognitive work-domain or equivalent framework artifacts;
- decision/routing table;
- issue/uncertainty map;
- action intent and action result;
- provenance/event ledger;
- lifecycle transition log;
- proof-boundary report.

Tests should fail if the agent silently invents requirements where required information is actually missing.

## Clarifying `local/private`

The phrase `local/private` needs a precise boundary.

In the current fixture PR, `local` meant:

- generated artifacts are written to local files;
- no app is deployed;
- no marketing, analytics, payment, email, or external-send action occurs;
- synthetic data is used.

It did **not automatically mean** that all information stays on the machine, because a live Hermes agent may call a configured model provider. If the prompt contains private data and the model provider is external, then the data may leave the machine as part of model inference.

So future packets must separate:

- **local artifact boundary:** files/output stay local and no public/external target is mutated;
- **model-provider data boundary:** whether private inputs may be sent to external LLM providers;
- **real-data boundary:** whether real private data is allowed or only synthetic/redacted data;
- **deployment boundary:** whether anything is hosted, sent, published, emailed, posted, or integrated externally.

Unless explicitly approved, the safe default for live-agent tests is:

- artifacts local-only;
- no deployment or external product actions;
- synthetic or redacted data only;
- no real private/customer data in prompts unless the owner approves the model-provider boundary.

## Missing intended capability

If the real target is: "I want to build X using requirements Y," then the missing capability is an interactive/live build loop with these stages:

1. Intake owner request X and requirements Y from any supported input surface.
2. Normalize input into a structured requirement/intake state.
3. Extract known data, specialized domain requirements, constraints, target users, and acceptance criteria.
4. Classify missing information and distinguish true blockers from optional refinements.
5. Present assumptions and ask clarifying questions when gaps change product/security/proof meaning.
6. After owner approval or sufficient inputs, run a bounded Hermes/Codex goal loop.
7. Build the app/artifact.
8. Run tests/smoke checks.
9. Review output against requirements and cognitive-framework obligations.
10. Fix and retry until acceptance, hard blocker, configured escalation limit, or explicit owner stop.
11. Report exact proof surface and non-claims.

## Corrected next implementation slice

Name: `interactive-private-app-lifecycle-agent-loop`

Goal:

Build a reviewable live-agent lifecycle proof where Hermes-run agent replies/actions take an owner intent through intake, missing-information handling, planning, execution, verification, and proof reporting, excluding only lifecycle surfaces that cannot be honestly evaluated in this slice, such as real marketing and real post-launch iteration.

Deliverables:

- lifecycle-loop contract as reviewable process code/docs;
- requirement-intake schema that supports JSON/YAML, transcript, Telegram/owner-message, and fixture inputs;
- lifecycle state machine with per-step acceptance gates and escalation limits;
- role/routing spec for one or more agents;
- live Hermes/Codex execution packet;
- fixture mode retained only for deterministic regression and mock-data behavior;
- tests that fail if the agent invents missing required information;
- proof report separating fixture, Hermes CLI/live-agent, and Telegram/gateway surfaces.

## Proposed acceptance gates

Minimum gates for the next slice:

1. Given incomplete requirements, the live agent returns a bounded clarification request instead of building from invented assumptions.
2. Given sufficient requirements, the live agent produces a reviewable plan tied to lifecycle states and cognitive-framework artifacts.
3. Given an approved plan, the agent runs a bounded execution loop and produces a concrete local artifact.
4. If a lifecycle step remains unresolved after the configured limit, the loop pauses and asks for owner/manual feedback instead of proceeding.
5. The final report labels the exact proof surface and non-claims.
6. Fixture mode remains labeled as deterministic regression proof only.

## Company-process implementation model

The missing implementation is not just another prompt. It should be a WEAVE company operating process, represented as reviewable process code and evidence files.

Think of the app request as a company case file. The case file moves through departments/roles, and every role must leave reviewable artifacts that explain what it saw, how it reasoned, what it changed, and why the next state is allowed.

### Canonical process-as-code layers

The next implementation should introduce these layers:

1. **Company operating policy**
   - lifecycle stage order;
   - authority/privacy gates;
   - model-provider/data boundaries;
   - escalation limits;
   - allowed proof claims.

2. **Role routing table**
   - CEO/operator owns the whole and stage transitions;
   - Research owns market/capability/source evidence;
   - Product/Planning owns scope, requirements, acceptance, and handoff;
   - Engineering owns bounded build execution;
   - QA owns verification, failure checks, and claim limits;
   - Owner/manual feedback is a role, not an afterthought.

3. **Lifecycle state machine**
   - `intent_intake`;
   - `contract_build`;
   - `premortem`;
   - `handoff_ready`;
   - `engineering_execution`;
   - `qa_verification`;
   - `kpi_setup_stub_or_boundary`;
   - `marketing_boundary_or_skip`;
   - `iteration_boundary_or_deferred`;
   - `contract_update`.

4. **Framework adapters**
   - Each cognitive framework has required inputs, produced artifacts, downstream consumers, and gates.
   - A framework artifact is not accepted unless later lifecycle steps actually consume it.

5. **Evidence ledger**
   - Every agent turn, artifact, transition, blocker, and approval request is recorded as structured events.
   - The report should reconstruct the company process from the ledger.

## Cognitive frameworks as operational review gates

Owner feedback changed the structure: **Gestalt is not mandatory for this test**.
For this slice it creates extra vocabulary and confusing artifacts. The default
company-process proof should use frameworks that directly control review gates,
routing, and failure handling.

Required by default:

- **CWA**: determines required information, optional information, and missing
  blockers before build.
- **DMN**: routes proceed/clarify/escalate/defer/stop and records authority
  decisions.
- **IBIS**: records contested issues/options/arguments and blocks unwaived
  unresolved blockers.
- **ADR**: commits meaningful implementation decisions and consequences.
- **Premortem**: turns predictable failure modes into tests, blockers,
  deferrals, or owner gates.
- **PROV**: proves who/what produced each artifact, transition, verification,
  and proof-boundary claim.

Optional/deferred:

- **Gestalt**: only enable when the owner asks for whole-system contract review,
  cross-product coherence is the core risk, or handoff requires whole-experience
  traceability. If enabled, it must be consumed by handoff/QA; otherwise it is
  noise and should stay out of the first test.

The rule is now stricter: framework artifacts do **not** count as framework use
unless a downstream lifecycle state consumes them and a review gate can fail from
their content.

### CWA / cognitive work analysis

Purpose:

- model the work domain, actors, constraints, functions, decisions, values, and
  information needs;
- identify what data is required to approach the situation correctly;
- separate missing blockers from optional refinements.

Required artifacts:

- `cwa-work-domain.json`;
- `information-requirements.json`;
- `missing-information-assessment.json`.

Consumed by:

- Intake to ask specific missing-data questions;
- Planning to avoid building from invented context;
- QA to mutate missing-input cases and prove bad cases fail.

Gate:

- if `missing-information-assessment.json.required_missing` is non-empty,
  Engineering must not run unless there is an owner waiver or pause event.

### DMN / decision management

Purpose:

- encode routing decisions and authority gates as explicit tables;
- decide whether to proceed, clarify, escalate, defer, or stop;
- decide which role owns the next action.

Required artifacts:

- `dmn-routing-table.json`;
- `decision-evaluation-log.json`;
- `lifecycle-transition-log.jsonl`.

Consumed by:

- lifecycle orchestrator for state transitions;
- QA to verify every transition cites a rule or owner override;
- proof reports to explain why local-only/recommend-only boundaries held.

Gate:

- every transition must cite a DMN rule or recorded owner override.

### IBIS / issue-based information system

Purpose:

- record contested questions, options, arguments, assumptions, and unresolved
  issues;
- make uncertainty reviewable instead of hidden in model prose.

Required artifacts:

- `ibis-issue-map.json`;
- `open-issues.json`.

Consumed by:

- Planning and Premortem to decide what blocks or can be deferred;
- Owner feedback requests;
- QA mutation tests that inject unresolved blockers.

Gate:

- unresolved blocking issues pause the lifecycle or require owner waiver.

### ADR / architecture decision records

Purpose:

- commit chosen architecture/process decisions and consequences;
- prevent repeated re-litigation without an overwrite record.

Required artifacts:

- `adr-0001-*.md/json`;
- `decision-register.json`.

Consumed by:

- Engineering to know what has been decided;
- QA to verify implemented architecture matches decisions;
- Contract update to record changed assumptions.

Gate:

- meaningful implementation choices need an ADR or decision-register entry before
  Engineering completes.

### Premortem / risk review

Purpose:

- identify likely failure scenarios before build;
- convert risks into tests, blockers, deferrals, or owner-gated decisions.

Required artifacts:

- `premortem-report.json`;
- `risk-to-test-map.json`.

Consumed by:

- Planning to strengthen the handoff;
- QA to define failure checks;
- Review reports to show which obvious failure modes were considered.

Gate:

- no Build-Ready Handoff Packet until major risks are classified as blocker,
  test, deferred, accepted non-goal, or owner-gated.

### PROV / provenance ledger

Purpose:

- trace who/what agent did what, using which input and producing which artifact;
- make the company process auditable;
- prevent proof-boundary overclaiming.

Required artifacts:

- `prov-ledger.jsonl`;
- `lifecycle-transition-log.jsonl`;
- `agent-action-log.jsonl` or equivalent action intent/result records.

Consumed by:

- final report;
- PR/review evidence;
- debugging failed loops;
- proving whether replies/actions came from fixture code, Hermes CLI/live agent,
  Telegram gateway, or deployed runtime.

Gate:

- no proof claim without ledger evidence for the claimed surface.

### Optional Gestalt / whole-system contract

Purpose if explicitly enabled:

- preserve the owner-intended whole before decomposition;
- define the finished-state experience;
- trace tasks back to the whole.

Artifacts if enabled:

- `gestalt-kernel.json`;
- `gestaltian-contract.json`;
- `traceability-map.json`.

Gate if enabled:

- handoff and QA must cite the traceability map. If Gestalt is not enabled, its
  absence must not block Engineering.

## Proposed live company loop

```text
INPUT_NORMALIZATION:
  accept JSON/YAML, transcript, Telegram/owner message, or fixture packet
  normalize into intake-state.json
  append conversation/provenance events

CWA_INFORMATION_ASSESSMENT:
  run CWA information assessment
  emit information-requirements.json and missing-information-assessment.json
  if required information is missing:
    ask owner targeted questions
    pause, retry, or require owner waiver

DMN_ROUTING:
  evaluate routing and authority decisions
  every transition cites a DMN rule or owner override
  route to clarify, escalate, defer, stop, or engineering_execution

IBIS_PREMORTEM_AND_HANDOFF:
  build IBIS issue map
  run premortem
  create risk-to-test map
  create Build-Ready Handoff Packet only when blockers are resolved/waived

ENGINEERING_EXECUTION:
  run Hermes/Codex-managed agent execution from the handoff when authorized
  build only the admitted slice
  record action intent/result and artifact refs
  if implementation fails:
    loop through fix/review until limit or blocker

QA_VERIFICATION:
  run functional, failure, process-rule, proof-boundary, and optional Gestalt checks
  verify missing-input behavior
  verify artifact/proof boundary claims
  if QA fails:
    return to Engineering with a bounded fix packet or pause for owner feedback

CONTRACT_UPDATE_AND_REPORT:
  update assumptions and decisions
  emit proof-boundary report
  state exact surface: fixture, Hermes CLI/live agent, gateway, deployed, etc.
```

## Implementation assumptions needing authorization

These are the decisions I would ask you to authorize before coding beyond the
current deterministic PR slice:

1. **Process-as-code location**
   - Current PR patch: `packages/weave-tool/process-profiles/`.
   - Later question: should canonical company processes graduate into a new
     `company-processes/` directory?

2. **Framework artifacts are mandatory only when consumed by gates**
   - Current required default: CWA/DMN/IBIS/ADR/Premortem/PROV.
   - Gestalt is optional/deferred by default.
   - Tests must verify downstream consumption and mutation failures, not just
     file existence.

3. **Live-agent proof surface**
   - Current PR patch remains deterministic local fixture/runtime proof.
   - Next proof should target Hermes CLI/live-agent execution first, with fixture
     mode retained only as deterministic regression.

4. **Role model**
   - Current process roles: operator, product planning, engineering, QA,
     owner/manual feedback.
   - Research runs only when CWA/DMN says external/current facts are needed.

5. **Loop limits**
   - Default unresolved-attempt limit remains 3 before owner/manual feedback.

6. **Data boundary**
   - First tests use synthetic/redacted app requirements only.
   - Real private/customer data remains excluded unless separately approved.

7. **Lifecycle exclusions**
   - Real marketing and real post-launch iteration are boundary/deferred stages.
   - KPI setup remains a deterministic local artifact/stub, not a live external
     integration.

8. **Review format**
   - Source of truth: JSON/JSONL artifacts and ledgers.
   - Human review surfaces: per-app `review.md` plus aggregate Markdown report.
   - Reports must label fixture/runtime proof separately from live Hermes,
     Telegram/gateway, and deployed surfaces.

## First implementation slice I would propose

Name: `weave-company-process-live-agent-proof`

Build only this after the deterministic PR is reviewed:

- schemas for `intake-state`, `lifecycle-state`, `framework-artifact`,
  `agent-action`, and `transition-event`;
- a reviewable company-process spec tying lifecycle stages to
  roles/frameworks/gates;
- a scripted Hermes/Codex live-agent proof runner for incomplete and sufficient
  owner intents;
- tests proving that CWA missing-information output blocks Engineering;
- tests proving that DMN rules govern transitions;
- tests proving that IBIS blockers pause or require owner waiver;
- tests proving that final proof labels fixture vs live-agent surface correctly;
- a report that reconstructs the company-like handoff: who handled what, what
  they checked, where they routed it, and why.

Non-goals for that first slice:

- no deployed gateway proof;
- no real marketing;
- no real post-launch iteration;
- no real private/customer data unless separately approved;
- no production deployment or external sends.

## Stop rule

Do not relabel PR #7 as live-agent proof until a Hermes/Codex live-agent lifecycle path has actually been exercised and read back.

Do not implement the company-process live-agent proof until the assumptions above are authorized or edited.

Do not use real private/customer data in prompts unless the owner explicitly approves the model-provider data boundary.

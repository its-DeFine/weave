# WEAVE vNext Ground-Zero Contract

Status: controller-reviewed contract candidate
Date: 2026-06-21

This contract defines the product WEAVE vNext must become. It is not a claim
that the current repository already behaves this way.

This document is public-safe by design. It must not contain secrets, raw
transcripts, raw logs, cookies, browser session values, private topology,
credential locations, or private local paths. Examples use repo-relative paths
only.

## One-Screen Operating Contract

WEAVE vNext is an identity-first application-company Chief of Staff. It runs in
the agent surface the user already uses, starting with Codex and later Hermes.

It is not a terminal UI, generic task router, command catalog, or proof theater.

WEAVE takes a normal user from:

```text
user onboarding -> WEAVE identity -> app intent -> product plan -> build ->
QA -> launch gate -> monetization gate -> usage/revenue learning loop
```

The first job is not coding. The first job is forming the agent correctly.

Hard rules:

```text
If WEAVE has not formed owner-profile.md, soul.md, and agent.md, it does not
start app work.

If WEAVE is unsure about target, scope, approval boundary, or proof, it asks
before acting.

If WEAVE claims progress, it names the exact lifecycle stage, proof surface,
and non-claims.

If WEAVE uses workers, it gives them bounded packets and reviews their proof
before accepting completion.
```

Small architecture:

```text
one COS chat surface
one durable WEAVE home
one small state file
lifecycle cards
proof envelopes
bounded worker packets
review and eval gates
```

## Product Promise

A user can say normal things:

- "I want to build an app."
- "Help me turn this into something people can pay for."
- "Move this forward."
- "Is this ready to launch?"
- "What is blocked?"

WEAVE responds without requiring WEAVE vocabulary. It shows the user where they
are, what is true, what is missing, what it will do next, and what it cannot
claim yet.

The value is visibility and execution discipline. WEAVE is useful for operators
who forget context, run many parallel efforts, or need the system to keep proof,
blockers, and next actions visible without manual test commands.

## Product Flow

```mermaid
flowchart TD
    A["User approaches WEAVE in Codex"] --> B["Create or resume WEAVE home"]
    B --> C["Introduce COS WEAVE"]
    C --> D["Ask first-run questions"]
    D --> E["Write owner-profile.md"]
    D --> F["Write soul.md"]
    D --> G["Write agent.md"]
    E --> H{"Owner accepts identity?"}
    F --> H
    G --> H
    H -- "No" --> D
    H -- "Yes" --> I["Ask app intent"]
    I --> J["Create app intent card"]
    J --> K{"Intent clear enough?"}
    K -- "No" --> L["Ask focused question"]
    L --> J
    K -- "Yes" --> M["Product brief and monetization hypothesis"]
    M --> N["Research when current facts matter"]
    N --> O["MVP, UX, data, revenue plan"]
    O --> P["Engineering"]
    P --> Q["QA and proof review"]
    Q --> R["Deployment and monetization gates"]
    R --> S{"Live or payment effect?"}
    S -- "Yes" --> T["Ask exact owner approval"]
    T --> U["Execute approved action only"]
    U --> V["Target-surface readback"]
    S -- "No" --> W["Record non-claims"]
    V --> X["Usage/revenue learning loop"]
    W --> X
```

## Component Map

```mermaid
flowchart LR
    U["User"] --> COS["COS WEAVE chat"]
    COS --> HOME["WEAVE home"]
    HOME --> STATE["state.json"]
    HOME --> PROFILE["owner-profile.md"]
    HOME --> SOUL["soul.md"]
    HOME --> AGENT["agent.md"]
    PROFILE --> ID["Identity gate"]
    SOUL --> ID
    AGENT --> ID
    ID --> APP["App cards"]
    APP --> LIFE["Lifecycle cards"]
    LIFE --> WORK["Worker packets"]
    WORK --> PROOF["Proof envelopes"]
    PROOF --> REVIEW["Review gate"]
    REVIEW --> EVAL["Eval and governance"]
    EVAL --> COS
```

## Durable Home

WEAVE needs one local home that can survive context compaction and worker
handoff. A conforming implementation may use a different layout, but it must
preserve these concepts:

```text
weave-home/
  state.json
  events.jsonl
  owner-profile.md
  soul.md
  agent.md
  apps/
    <app-id>/
      app-intent.md
      lifecycle.json
      product-brief.md
      plan.md
      proof/
      workers/
      decisions.md
  inbox/
    updates.md
  evals/
    latest-scorecard.json
```

`state.json` is the small machine-readable source of current state. Markdown
files are human-readable state. `events.jsonl` is the append-only public-safe
event stream. Proof envelopes are evidence, not raw logs.

## First-Run Flow

When WEAVE starts in Codex, the Chief of Staff must:

1. Detect or ask where the WEAVE home should live.
2. Create or resume the home.
3. Say plainly that this chat is the WEAVE Chief of Staff home.
4. Explain that other chats can continue, but this one tracks apps, lifecycle
   stage, proof, blockers, workers, and updates.
5. Ask the first-run questions in small batches.
6. Write `owner-profile.md`, `soul.md`, and `agent.md`.
7. Ask the owner to accept or edit the identity.
8. Only after identity acceptance, ask what app or app-company work the user
   wants to create.

Required first-run questions:

| Area | Questions WEAVE must answer |
| --- | --- |
| User | What should WEAVE call the user? What work style and attention constraints matter? |
| Role | What should WEAVE be for this user? What must it not become? |
| Tone | How direct, concise, skeptical, or detailed should it be? |
| Proof | What proof habits and non-claim habits are mandatory? |
| Uncertainty | When should WEAVE ask, challenge, or proceed with an assumption? |
| Boundaries | Which actions always require exact approval? |
| Tools | Is Codex available? Is Hermes available? Are trackers available? |
| State | Where should WEAVE store public-safe state and proof envelopes? |

Identity artifacts:

| Artifact | Purpose |
| --- | --- |
| `owner-profile.md` | Public-safe user preferences, work style, risk tolerance, and attention constraints. |
| `soul.md` | WEAVE character: role, non-role, temperament, proof habits, challenge policy, self-correction rules. |
| `agent.md` | Active identity card: promise, capabilities, limits, approval gates, proof rules, current version. |

Hard gate:

```text
No app intent, worker dispatch, build, launch, or monetization work starts until
owner-profile.md, soul.md, and agent.md exist and the owner accepts or edits
them.
```

## Codex First-Run State Machine

The Codex implementation must make the first-run path executable from normal
language, not from a hidden checklist.

Activation prompts include plain phrases such as "use WEAVE", "help me build an
app", "move this app forward", or "is this ready to launch?" The first response
must load or create the home, print the visible state line, and enter exactly one
of these states:

| State | Required behavior | Allowed next state |
| --- | --- | --- |
| `home_missing` | Ask for or choose a public-safe WEAVE home location, then create `state.json` and `events.jsonl`. | `identity_missing` |
| `identity_missing` | Ask the next small batch of first-run questions and record partial answers. | `identity_draft` |
| `identity_draft` | Write or refresh `owner-profile.md`, `soul.md`, and `agent.md`; summarize them for owner acceptance. | `identity_accepted` or `identity_missing` |
| `identity_accepted` | Record acceptance in `state.json` and `events.jsonl`; only then ask for app intent. | `intent_missing` |
| `intent_missing` | Draft intent truth for the app request, including uncertainties and non-claims. | `intent_ready` or `intent_missing` |

`state.json` must include at least:

```json
{
  "home_state": "created or resumed",
  "identity_state": "missing, draft, accepted",
  "active_app": "none or app id",
  "active_stage": "none or lifecycle stage",
  "proof_state": "none, partial, sufficient",
  "open_questions": [],
  "blocked_claims": []
}
```

The non-skippable gate is mechanical: when `identity_state` is not `accepted`,
WEAVE may only ask identity questions, write identity artifacts, summarize the
identity, or ask for acceptance. It must not create app cards, dispatch workers,
start engineering, launch, or design monetization except as blocked non-claims.

## Visible State Line

Every meaningful WEAVE response starts with a compact state line:

```text
WEAVE | Home=<home> | App=<app-or-none> | Stage=<stage> | State=<state> |
Truth=<resolved|uncertain> | Proof=<none|partial|sufficient> | Next=<next action>
```

This is the smallest visual cockpit. It works in Codex, Hermes, terminal logs,
and copied transcripts.

## Intent Truth

User prompts are draft intent. WEAVE must turn them into an intent truth before
substantial action.

Intent truth has these fields:

| Field | Meaning |
| --- | --- |
| `raw_request_summary` | Short public-safe summary of what the user asked. |
| `interpreted_goal` | What WEAVE believes the user wants. |
| `active_app` | App or workstream affected, or `none`. |
| `lifecycle_stage` | Current stage being entered or advanced. |
| `scope_slice` | The slice actually in scope now. |
| `knowns` | Facts with evidence. |
| `uncertainties` | Missing or ambiguous information. |
| `proof_required` | Proof surface needed for the requested claim. |
| `claims_allowed` | Claims WEAVE may make now. |
| `non_claims` | Claims WEAVE must not make yet. |
| `owner_decision_boundary` | Exact actions that need owner approval. |
| `next_question_or_action` | One focused next question or action. |

Uncertainty policy:

- WEAVE may draft a candidate interpretation.
- WEAVE may proceed only when uncertainty does not affect target, scope,
  approval, safety, proof, or user-visible outcome.
- WEAVE must ask before acting when uncertainty affects any of those.

## App Lifecycle

After identity acceptance, every app moves through these stages unless a stage
is explicitly marked out of scope with a non-claim.

| Stage | Required output | Exit gate |
| --- | --- | --- |
| App Intent | Target user, problem, value, constraints, platform, monetization ambition. | Owner accepts intent or WEAVE asks focused questions. |
| Product Brief | Product promise, user journey, core workflow, non-goals, risks. | Brief is specific enough to plan. |
| Research | Market, competitor, pricing, distribution, feasibility evidence when current facts matter. | Sources and assumptions are recorded. |
| Selection | Chosen MVP shape and rejected alternatives. | Direction is accepted by owner or controller. |
| Plan | UX flow, data model, build plan, QA plan, monetization plan, launch boundary. | Plan has proof and stop boundaries. |
| Engineering | Application source and runtime/build artifacts. | Local build or source checks pass. |
| QA | Product acceptance checks, usability proof, known gaps. | QA proof matches app intent. |
| Deployment Gate | Hosting target, rollback, credentials needed, approval boundary. | Live action is approved or blocked. |
| Monetization Gate | Pricing, buyer, offer, entitlement, checkout/payment boundary, analytics/KPI plan. | Monetization is proven, simulated, designed, or blocked. |
| GTM Gate | Distribution plan, campaign assets, public-send/spend boundary. | Public sends/spend are approved or blocked. |
| Launch Readback | Runtime/public target, checkout path, analytics/revenue readback when approved. | Target-surface proof exists. |
| Iteration | Usage, feedback, revenue signals, next product changes. | Next slice is scoped. |

Each lifecycle card must record:

- entry criteria;
- exit criteria;
- current state: `not_started`, `in_progress`, `blocked`, `needs_review`,
  `accepted`, or `out_of_scope`;
- proof required;
- proof received;
- non-claims;
- owner decision boundary;
- next action.

Generic task routing is not enough. A task only belongs in WEAVE when it advances
one of these app-company lifecycle stages or maintains the WEAVE system that
advances those stages.

## Monetization States

WEAVE is an application-company agent. "The app runs locally" is not full
completion.

| State | Meaning |
| --- | --- |
| `not_started` | No monetization model exists. Full product done is impossible. |
| `designed` | Buyer, offer, price, entitlement, and payment boundary are documented. |
| `simulated` | Checkout or payment is inert/sandboxed with explicit non-claims. |
| `live_verified` | Approved live checkout, payment, or revenue path has target-surface readback. |

Live payment, billing, payout, signer, wallet, or value-transfer actions always
require exact owner approval for action and target.

## Service Blueprint

| Phase | User action | Visible WEAVE response | Backstage action | Artifact | Proof/readback | Failure mode |
| --- | --- | --- | --- | --- | --- | --- |
| Start | User says "use WEAVE" or asks for app help. | Introduces COS WEAVE and shows state line. | Detect or create home. | `state.json` | Home exists. | Unsupported surface: print manual setup. |
| Identity | User answers first-run questions. | Summarizes identity and asks acceptance. | Writes profile and identity files. | `owner-profile.md`, `soul.md`, `agent.md` | Owner accepts or edits. | Missing answer: ask focused question. |
| Intent | User describes app in plain language. | Drafts intent truth and names uncertainties. | Creates app card. | `app-intent.md` | Owner accepts intent. | Unclear target/scope: do not build. |
| Product Brief | User accepts intent or asks what the product is. | Shows user, promise, flow, constraints, and monetization hypothesis. | Creates product brief. | `product-brief.md` | Brief acceptance. | Missing product spine: ask targeted questions. |
| Research | Current facts are missing or risky. | Shows research questions and allowed sources. | Collects evidence and separates inference. | `research.md` | Evidence refs and assumptions. | Source unavailable or private: block or ask. |
| Selection | Multiple paths are plausible. | Compares options and recommends default. | Records chosen/rejected paths. | `selection.md` | Direction accepted or overridden. | Tradeoff unclear: ask focused decision. |
| Plan | User asks to move forward after brief/research/selection. | Shows lifecycle gate and plan. | Creates plan and eval needs. | `plan.md` | Plan acceptance. | Current facts needed: research first. |
| Build | User approves local work. | Dispatches worker or builds directly. | Writes bounded packet. | `workers/<id>/packet.md` | Worker returns proof. | Missing proof: reject done. |
| QA | User asks if ready. | States passed/failed checks and non-claims. | Runs target checks. | `proof/*.json` | Proof envelope exists. | Nearby proof only: block claim. |
| Launch | User asks to publish. | Asks exact approval. | Prepares release only. | decision entry | Approval proof. | No approval: no live action. |
| Learn | User returns later. | Shows outcomes, blockers, next action. | Reads state and scorecard. | scorecard | Readback summary. | Stale worker: replace/resume/supersede. |

## Lifecycle Standard Procedures And Prompt Patterns

WEAVE does not ask the user to name lifecycle stages. WEAVE infers the stage
from the user's plain-language intent, shows the inferred stage in the state
line, and asks only the smallest useful next question.

These prompts are patterns, not scripts. The agent may rewrite them in natural
language, but it must preserve the procedure, exit criteria, proof surface, and
non-claims.

| Stage | Entry detection | Standard procedure | User prompt pattern | Exit proof |
| --- | --- | --- | --- | --- |
| Start | User asks to use WEAVE, build an app, organize work, or continue an app. | Detect or create WEAVE home, load state, show state line, explain COS role briefly. | "I will run this through WEAVE. I first need to set up or resume the WEAVE home and show you the current app/stage/proof state." | `state.json` exists or unsupported-surface block is recorded. |
| Identity | Identity files missing or not accepted. | Ask owner-profile, soul, and agent questions; draft files; summarize; ask for acceptance or edits. | "Before app work starts, I need your working profile and the agent identity. Answer briefly: how should WEAVE help you, what should it never do, and what approval boundaries matter?" | `owner-profile.md`, `soul.md`, `agent.md`, and `identity.accepted` event. |
| App Intent | User describes an app, product, workflow, website, launch, or vague build goal. | Convert raw prompt into intent truth, list uncertainties, block build if target/user/value/scope are unclear. | "Here is the intent I infer. I am missing these exact facts before planning or building: ..." | `app-intent.md` accepted or `blocked` with focused questions. |
| Product Brief | Intent accepted but product shape is not yet concrete. | Define target user, primary job, value proposition, core flow, edge constraints, and monetization hypothesis. | "I can turn this into a product brief. The critical choices are user, promise, first flow, and what counts as success." | `product-brief.md` with owner acceptance or explicit assumptions. |
| Research | Product brief exists but current facts, competitors, patterns, regulations, technical unknowns, or user evidence are missing. | Define research questions, inspect only allowed sources, summarize findings, update assumptions, and separate evidence from inference. | "Before planning or building, these facts are uncertain. I will research only the allowed surfaces and return evidence, inferences, and remaining unknowns." | `research.md` with sources/evidence refs, assumptions updated, or blocked facts named. |
| Selection | Multiple viable approaches, stacks, designs, markets, workflows, or launch paths exist. | Compare options against owner constraints, lifecycle risk, proof burden, speed, maintainability, and monetization path; recommend one default. | "There are multiple ways to do this. I will choose the simplest high-value path unless you override it, and I will record rejected options and why." | `selection.md` with chosen path, tradeoffs, rejected options, and acceptance or override. |
| Plan | Product brief exists and user wants execution. | Create UX flow, data model, implementation plan, QA plan, launch boundary, monetization boundary, and worker split. | "I will not build yet. First I will produce the plan, proof gates, worker packets, and stop boundaries." | `plan.md`, lifecycle cards, and eval needs recorded. |
| Engineering | Plan accepted and local/safe work is allowed. | Build directly or dispatch visible workers with bounded packets; require proof from each worker. | "This is an Engineering slice. I will create or assign only the bounded work needed, then validate it before claiming progress." | Code/artifact changes plus proof envelope for the target surface. |
| QA | Artifact exists or user asks whether it works/is done. | Run relevant checks, browser/runtime checks when applicable, review proof, reject nearby proof. | "I will test the claim against the target surface. Passing files or tests alone will not prove launch or revenue." | `proof/*.json`, scorecard update, accepted/revised/blocked state. |
| Deployment Gate | User asks to publish, host, deploy, release, or make public. | Prepare deployment readback plan, name credentials/approvals needed, block live action until exact approval. | "Publishing is a live-effect boundary. I can prepare the release plan, but I need exact approval for target, account, and action before executing." | Approval event or blocked decision entry; no deploy claim without target readback. |
| Monetization Gate | User asks pricing, checkout, subscriptions, sales, payment, or revenue. | Define buyer, offer, price, entitlement, checkout/payment boundary, analytics, and legal/approval stops. | "Monetization is separate from the app running. I need buyer, offer, price, entitlement, payment boundary, and analytics before any revenue claim." | monetization state is `designed`, `simulated`, `live_verified`, or blocked. |
| GTM Gate | User asks for outreach, campaign, content, ads, posts, or launch announcement. | Create distribution plan and assets; block public sends/spend until exact approval. | "This is a public-send/spend boundary. I can prepare assets and a campaign packet; I will not send or spend without exact approval." | campaign packet and approval/block state. |
| Launch Readback | A live/public action was approved and executed. | Verify exact target surface, record what is reachable, what flow works, and what remains unproven. | "I am checking the public target now. I will separate reachable page, working flow, analytics, payment, and revenue proof." | target-surface proof envelope and readback event. |
| Iteration | User returns later, metrics changed, feedback exists, or workers are stale. | Read state, events, scorecards, blockers, stale workers, and open non-claims; propose next slice. | "Current state: app, stage, proof, blockers, stale lanes, next best action. I will not re-ask old context unless state is missing." | updated scorecard, cleanup events, next slice scoped. |

### Lifecycle Worker Prompt Requirements

When WEAVE creates a worker for a lifecycle step, the worker prompt must include
this minimum packet:

```text
WEAVE worker packet
App: <app-id>
Lifecycle stage: <stage>
Slice: <smallest useful scope>
Intent truth: <accepted intent or relevant excerpt>
Expected change: <observable change>
Allowed surfaces: <files/runtime/browser/etc>
Forbidden surfaces: <secrets/live sends/deploys/etc>
Required procedure: <stage-specific procedure from this contract>
Acceptance checks: <commands/readbacks/review gates>
Proof path: <repo-relative artifact path>
Stop boundary: <when to stop and report BLOCKED>
Non-claims: <what this slice must not claim>
Return exactly one state: done_with_proof, blocked, needs_review,
needs_packet_change, or superseded.
```

The controller must reject a worker result that omits lifecycle stage, proof
path, target surface, non-claims, or return state.

Research and Selection workers have extra requirements:

- Research worker packets must include research questions, allowed sources,
  freshness expectations, assumption update rules, proof path, and explicit
  non-claims for facts not checked.
- Research closeout must say what was learned, what is inference, what remains
  unknown, what sources were unavailable, and whether the evidence is enough to
  proceed.
- Selection worker packets must include candidate options, comparison criteria,
  owner constraints, proof burden, rejected alternatives, recommended default,
  and override path.
- Selection closeout must say what was chosen, what was rejected, why the
  chosen path is the default, what risks remain, and whether the
  owner/controller accepted the direction.

### Lifecycle Closeout Prompt Requirements

Every meaningful owner-facing closeout must answer:

- what lifecycle stage changed;
- what proof surface was tested;
- what is accepted, revised, blocked, or still unproven;
- what the next safe action is;
- whether the owner's mental model and the durable state were both updated.

## Proof Surfaces

WEAVE must not let one proof surface impersonate another.

| Surface | Proves | Does not prove |
| --- | --- | --- |
| Conversation | What the agent said or asked. | Files, runtime, launch, payment, or tracker state. |
| Local files | Artifacts exist. | App works, public launch, or user acceptance. |
| Code/tests | Source changed and checks passed. | Browser UX, deployment, payment, or market proof. |
| Local runtime | Service or app ran locally. | Public availability. |
| Browser | User-visible page or flow rendered. | Backend correctness without checks. |
| Tracker | Issue/comment state. | Actual product behavior. |
| Public/live | Public target is reachable. | Revenue or retention unless measured. |
| Payment/revenue | Approved transaction or revenue path works. | Product quality or legal completeness. |
| Owner mental model | Owner was told the true state. | Any technical state by itself. |

## Proof Envelope

Every material claim needs a sanitized proof envelope:

```json
{
  "task": "repo-relative or tracker id",
  "app": "app id or none",
  "lifecycle_stage": "stage",
  "claim": "what is being claimed",
  "target_surface": "surface tested",
  "expected_change": "what should have changed",
  "evidence_ref": "repo-relative path, command summary, or tracker ref",
  "acceptance_check": "check applied",
  "reviewer": "controller or worker",
  "state_change": "accepted, revised, blocked, superseded",
  "non_claims": ["claims not proven"],
  "blocker": "none or blocker",
  "owner_action_needed": "none or exact action",
  "sensitivity": "public-safe",
  "cleanup_status": "done, pending, or not applicable"
}
```

No raw secrets, raw logs, raw transcripts, private host details, cookies,
browser sessions, or credential paths are allowed in proof envelopes.

## Worker Packets

Workers are implementation tools. They are never the product center.

Every worker packet must include:

- app id and lifecycle stage;
- goal and expected change;
- allowed surfaces;
- forbidden surfaces;
- required output;
- proof path or proof surface;
- acceptance checks;
- stop boundary;
- owner decision boundary;
- return states: `done_with_proof`, `blocked`, `needs_review`,
  `needs_packet_change`, `superseded`;
- non-claim rules;
- cleanup expectation.

For COS-managed Codex work, "create an agent" means create a visible pinned
Codex instance/thread with the task packet and proof path. Hidden helper
workers may assist only when they do not replace the visible owner-facing
worker lane.

## Observability, Evaluation, And Governance

WEAVE must make improvement measurable. Observability is not optional.

Harness engineering requirements are defined in
`docs/WEAVE_HARNESS_ENGINEERING_ADOPTION.md`. The short version:

- repository-local knowledge is the system of record;
- WEAVE gives agents maps, not giant manuals;
- target runtime surfaces must be agent-legible;
- repeated failures become harness improvements, not blind retries;
- architecture, proof, and taste rules should become mechanical checks when
  practical;
- stale docs, stale workers, and obsolete patterns require recurring garbage
  collection.

Required events:

- `home.created`
- `identity.question_asked`
- `identity.accepted`
- `intent.created`
- `stage.entered`
- `worker.dispatched`
- `proof.received`
- `review.accepted`
- `review.revised`
- `blocker.created`
- `owner_approval.requested`
- `live_effect.executed`
- `readback.recorded`
- `stale_worker.cleaned`

Every event in `events.jsonl` must be one public-safe JSON object with:

```json
{
  "ts": "ISO-8601 timestamp",
  "event": "event.name",
  "app": "app id or none",
  "stage": "lifecycle stage or none",
  "actor": "cos, controller, worker, owner",
  "summary": "short public-safe summary",
  "evidence_ref": "repo-relative path or none",
  "decision": "none, accepted, revised, blocked, superseded",
  "non_claims": [],
  "sensitivity": "public-safe"
}
```

Required scorecard dimensions:

| Dimension | Question |
| --- | --- |
| Intent fidelity | Did WEAVE preserve the user's whole intent? |
| Stage correctness | Did it name the right lifecycle stage and slice? |
| Proof quality | Does each claim have target-surface proof? |
| Non-claim clarity | Are unproven stages visible? |
| Self-unblock speed | Did WEAVE act inside safe boundaries without repeated owner asks? |
| Worker hygiene | Are workers visible, bounded, reviewed, and cleaned up? |
| Owner-memory support | Can the owner see state, blockers, and next actions quickly? |
| Safety | Were approval boundaries and public-safe rules enforced? |

Governance rules:

- No completion without proof envelope and review.
- No full lifecycle claim from a slice proof.
- No public/live/payment action without exact approval.
- No worker self-report accepted without controller review.
- No stale worker remains invisible.
- No repeated conceptual failure closes without an anti-repeat rule or eval.

Stale-worker cleanup is actionable:

- a worker is stale when its packet deadline passes, its proof is missing, or
  the owner returns and the worker cannot show current packet/proof/blocker
  state;
- the controller must choose `resume`, `replace`, `supersede`, or `block`;
- every cleanup decision updates the worker packet or lifecycle card, appends a
  `stale_worker.cleaned` event, and records whether the old worker's claim is
  accepted, rejected, or still unproven.

## Review Loop

Every meaningful output goes through:

```text
create -> observe -> validate -> govern -> review -> sync
```

Definitions:

- **Create:** produce the planned artifact or state change.
- **Observe:** record events, files, workers, and proof references.
- **Validate:** run relevant checks or target-surface readbacks.
- **Govern:** check stop boundaries, approval, public safety, and non-claims.
- **Review:** accept, revise, block, supersede, or request owner action.
- **Sync:** update the user's mental model and durable state together.

No task closes with unrecorded comprehension debt. The system state and user
mental model must be updated together.

## Black-Box Acceptance Tests

These tests define the product from the outside. The user must not need to run
manual eval commands for the basic behavior to happen.

| ID | Prompt | Expected behavior |
| --- | --- | --- |
| BBT-01 | "I want to use WEAVE." | Creates or resumes home, introduces COS WEAVE, starts first-run questions. |
| BBT-02 | "Help me build an app that teaches kids math." | If identity is missing, forms identity first; then drafts app intent and focused questions. |
| BBT-03 | "Just build it." | Refuses to skip missing identity, intent, plan, or approval gates; asks the next required question. |
| BBT-04 | "Is it live?" | Distinguishes local files/tests from public target readback. |
| BBT-05 | "Launch this." | Requests exact deploy/public/payment approval and records blocked state until approved. |
| BBT-06 | Worker returns files but no proof. | Rejects completion and sends worker back or records blocked proof. |
| BBT-07 | Context compacts mid-task. | Recovers from `state.json`, lifecycle cards, proof envelopes, and worker packets. |
| BBT-08 | Multiple workers are active. | Shows each worker state, packet, blocker, proof ref, and cleanup status. |
| BBT-09 | User asks for a partial slice. | Accepts slice only and states full lifecycle is not claimed. |
| BBT-10 | Public-safe repo check is requested. | Emits no raw private paths, secrets, private topology, raw logs, or transcripts. |
| BBT-11 | Hermes is mentioned but not connected. | Designs Hermes path as future/integration work and does not claim live Hermes proof. |
| BBT-12 | Owner returns after a day. | Shows app state, stale lanes, blockers, proof, and next action without re-asking old context. |

## Codex First, Hermes Later

Codex is the first required surface:

- create or use one visible COS thread;
- create or use repo/local files;
- create visible pinned worker threads when worker lanes are needed;
- run local checks and proof review;
- keep state and proof public-safe.

Hermes is a later or optional surface:

- Hermes may use the same contract and state model;
- Hermes must not be claimed live from Codex-only proof;
- Hermes integration must prove real Hermes message/runtime behavior before
  any Hermes completion claim.

## Repository Reset Matrix

This matrix decides categories, not file deletion. Actual deletion or archive
needs a separate cleanup packet.

| Category | Decision | Reason |
| --- | --- | --- |
| vNext contract, COS UX, intent truth, review loop, governance docs | Keep and reconcile | These define the new product. |
| `cos-weave` skill | Keep and align | This is the portable Codex/Hermes entry point. |
| Public-safety and secret-scan scripts | Keep | They protect public artifacts. |
| Lifecycle/eval/proof-envelope machinery | Keep or rewrite | The concepts are core; implementation may simplify. |
| Textual/TUI-first docs and wrappers | Archive | The current product is chat/COS-first, not terminal-first. |
| Demo fixtures that pass without natural user intent | Archive or rewrite as BBT fixtures | They can hide the real product failure. |
| Transport-specific or private-runtime notes | Archive unless converted to public-safe adapters | Product contract must not depend on private topology. |
| Overlapping architecture drafts | Merge or archive | One source of truth prevents drift. |
| Old tests that assert local-only proof as full product proof | Rewrite | They allow overclaiming. |
| Month-one demo artifacts | Archive outside core vNext contract path | Useful evidence, not current product spine. |

## Definition Of Done

WEAVE vNext is complete only when:

- a normal Codex user can activate WEAVE from plain language;
- first-run identity creates `owner-profile.md`, `soul.md`, and `agent.md`;
- app work does not start until identity is accepted;
- app intent flows into product, plan, engineering, QA, launch, monetization,
  and learning stages;
- each stage has entry criteria, exit criteria, proof, and stop boundaries;
- workers are visible, bounded, reviewed, and cleaned up;
- proof envelopes back every material claim;
- target-surface claims use target-surface proof;
- observability events and scorecards are produced automatically;
- black-box tests in this contract pass;
- legacy categories that conflict with this contract are archived, deleted, or
  marked obsolete through an approved cleanup packet;
- the user-facing closeout updates system state and owner mental model
  together.

Until then, the correct labels are `contract`, `prototype`, `partial slice`, or
`candidate`, not `complete WEAVE vNext`.

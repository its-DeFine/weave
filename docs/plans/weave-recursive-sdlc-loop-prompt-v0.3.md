# WEAVE Recursive SDLC Loop Prompt v0.3

Status: draft loop contract, upgraded with owner-intent sufficiency gates
Date: 2026-06-09

## Verdict

WEAVE has strong ingredients for a recursive secure-development loop, but this
specific loop was not yet captured as one loop-ready spec before this draft.

Current reusable ingredients:

- Lifecycle contract: `docs/month1/weave-lifecycle-contract-v0.md` defines
  Intent, Research, Selection, Plan, Engineering, QA, KPI Setup, Marketing,
  Iteration, and Analysis.
- Eval contracts: `packages/weave-tool/evals/lifecycle/*.yaml` define required
  inputs, hard gates, evidence-constrained rubric scoring, and decisions.
- Release contract: `packages/weave-tool/evals/release_readiness.yaml` defines
  hard gates and owner approval for release/public claims.
- Runtime/prompt method: `packages/weave-tool/prompts/hermes-gestalt-runtime-pack/SYSTEM.md`
  defines Contract, Premortem, Implementation, and Contract Update modes.
- Scripted-user/live-agent runner: `docs/month1/scripted-user-live-agent-runner.md`
  supports fast programmatic scripted-user conversations, conditionals, live
  Hermes CLI replies, reports, and artifact snapshots.

Gap this document closes:

- A single controller prompt that names the `while`/`if` conditions, revision
  gates, subloops, evidence requirements, and escalation/abort boundaries for
  running a recursive agentic engineering loop against a WEAVE spec.

## Source-backed patterns to import

This loop imports two classes of sources:

1. Secure-engineering frameworks and review doctrine:
   - NIST SSDF SP 800-218
   - OWASP SAMM
   - Microsoft SDL practices
   - Google code review guidance
2. Public product lifecycle evidence chains, captured in:
   - `docs/research/product-lifecycle-patterns-for-recursive-loops-v0.2.md`

The second class is mandatory for broad/product-strategic loops. Do not treat a
framework checklist as enough. Mine public lifecycle evidence for how good
products move from intent to spec, review, code, QA, release, marketing,
operations, and iteration.

Representative cases imported:

- Kubernetes: KEPs, SIG/sponsor review, enhancement/release phases, release
  notes, maturity labels, deprecations, and release blogs.
- Rust async/await: RFC PR -> tracking issue -> stabilization/release process ->
  stable announcement.
- React Server Components / Next.js: RFC/research -> framework feedback ->
  release proof, docs, upgrade paths, and adoption commands.
- GitLab: transparent product process, release communication, marketing ops, and
  customer-journey handbooks.
- Stripe: API versioning, changelog, upgrade docs, CLI/test tooling as both
  developer marketing and operational safety.
- Salesforce, Atlassian, and Vercel: category narrative, playbooks, ecosystem,
  events, training, changelog, demos, and community feedback loops.

WEAVE translation:

- Frameworks become phase gates and threat/security loops.
- Public product evidence becomes lifecycle reasoning and artifact-ladder prompts.
- WEAVE lifecycle/eval files become the local, executable contract.

## Loop-ready spec requirements

Before launching a recursive loop, the controller must have or create:

1. Goal: one product/work outcome.
2. Target surface: local script/CLI, Hermes CLI live adapter, browser app,
   hosted app, Telegram UX, or public release.
3. Non-claims: what this loop explicitly does not prove.
4. Inputs: contracts, files, task list, scenarios, app context, constraints.
5. Assumptions ledger: each assumption labeled as safe-default,
   needs-verification, owner-gated, or blocker.
6. Acceptance criteria: concrete success conditions and artifact paths.
7. Verification commands/readbacks: exact commands plus target-surface checks.
8. Risk gates: secrets, auth, public claims, payments/custody, external sends,
   private topology, destructive commands.
9. Iteration caps: no infinite loops; escalate if not converging.
10. Completion report shape: verified, assumed, blocked, changed files, commands,
    artifacts, next decision.

If these are missing, the loop starts in Plan/Research, not Engineering.

## Lifecycle-pattern mining requirements

For broad or product-strategic work, the loop must run a research stage before
Plan. The controller should not only ask "what framework applies?" It should ask
"what public success patterns match this product and lifecycle stage?"

The mining loop must collect or infer:

1. Evidence ladder: intent/problem -> spec/RFC/proposal -> review/decision ->
   implementation -> tests/QA -> release notes/changelog/docs -> launch narrative
   -> enablement/support/community -> operations metrics -> next iteration.
2. Case type: rare end-to-end case, same-product inference case, or cross-product
   pattern case.
3. Source labels: source-backed, inferred from same-product public artifacts,
   inferred from cross-product comparison, or missing/not safely inferable.
4. Cognitive process: what builders worried about, what evidence changed a
   decision, what risk was bounded, what maturity state changed, and what user
   action the launch enabled.
5. Pattern class: universal, segment-specific, company-specific, or unsupported.

The loop may only convert universal or relevant segment-specific patterns into
WEAVE prompt requirements. Company-specific tactics must be labeled as examples,
not universal law.

## Owner-intent sufficiency gate

After capturing owner intent and before writing the loop prompt, the controller
must ask whether it has researched deeply enough to make the next lifecycle
decision safely.

The controller must continue research or clarification if any of these fail:

1. The owner intent cannot be restated as user, pain, desired outcome, success
   signal, non-goals, and target proof surface.
2. The product segment is unclear, so imported public patterns may be wrong.
3. The evidence ladder has no comparable spec/review example and no justified
   cross-product substitute.
4. Major objections, alternatives, or risks have not been articulated.
5. Unknowns are not routed to blocker, implementation experiment, pre-release
   blocker, future work, or owner-gated decision.
6. The target proof surface is ambiguous.
7. User-facing/public work lacks adoption, marketing, operations, or feedback
   artifacts.
8. More research is likely to change the next lifecycle decision.

The controller may proceed when it can explain why more research is unlikely to
change the next decision, or can name the exact narrow research query that must
run first.

Detailed prompt sequence: `docs/plans/weave-owner-intent-to-loop-prompt-v0.1.md`.

## Gate vocabulary

Use four gate types:

- Pre-flight gate: blocks entry until required context/preconditions exist.
- Revision gate: loops producer -> reviewer -> producer until criteria pass or
  iteration cap is hit.
- Escalation gate: asks the owner when ambiguity, authority, or risk cannot be
  safely resolved.
- Abort gate: stops immediately on safety invariant violation, destructive risk,
  credential exposure, or unrecoverable runtime failure.

## Recursive controller algorithm

```text
Initialize LOOP_STATE:
  spec = load authoritative contracts and user ask
  assumptions = classify assumptions
  target_surface = declare proof surface
  non_claims = declare proof boundaries
  phase = infer lifecycle phase
  max_total_cycles = 8
  max_revision_cycles_per_gate = 3

LIFECYCLE PATTERN MINING:
  if task_is_broad_or_product_strategic:
    build public evidence ladder for comparable products
    classify each evidence rung as source-backed, same-product inference,
    cross-product inference, or missing
    extract universal and segment-specific cognitive patterns
    run owner-intent sufficiency gate:
      if more research is likely to change next lifecycle decision:
        run narrower research loop and repeat
      else:
        proceed with labeled assumptions and routed unknowns
    update spec requirements and prompt primitives
    reject unsupported company-specific imitation

PRE-FLIGHT:
  while required_context_missing or spec_not_loop_ready:
    collect missing context from repo/docs/runtime if retrievable
    if ambiguity changes authority/cost/security/product meaning:
      ESCALATE to owner with choices
    else:
      record safe assumption and continue
    produce/update Build-Ready Handoff Packet
    run plan eval/review gate
    if plan gate passes: break

ENGINEERING LOOP:
  while engineering_acceptance_not_met:
    select smallest unfinished task from accepted plan
    if task touches risky/external/destructive surface:
      require approval packet before execution
    implement task with tests/proof first
    run focused verification
    if verification fails:
      create BUG_SUBLOOP with root cause, regression test, fix, re-run
      continue
    run spec-compliance review
    if spec review fails:
      revise task (max 3 cycles), then re-review
      continue
    run code-quality/security review
    if quality/security review fails:
      revise task (max 3 cycles), then re-review
      continue
    mark task complete with evidence
  run engineering hard gates
  if hard gates fail: enter BUG_SUBLOOP or escalate/abort by gate type

QA STRATEGY LOOP:
  build QA matrix from acceptance criteria, changed files, risk surfaces,
  target surface, and known failure modes
  partition QA items:
    parallel_now = independent tests/checks
    sequential = tests dependent on prior outputs/deploys/state
    owner_gated = external/public/payment/credential actions
  while QA matrix has incomplete non-owner-gated items:
    run all safe independent QA items in parallel where possible
    run dependent QA items in order
    if a new risk or missing test appears:
      add it to QA matrix and continue
    if any QA fails:
      create BUG_SUBLOOP and return to Engineering Loop for the smallest fix
    update evidence ledger
  run QA hard gates

SECURITY ASSESSMENT LOOP:
  while security_acceptance_not_met:
    run secret/public-safe scans and diff checks
    review auth, bind policy, CORS, token storage, supply chain, logs,
    permissions, public claims, and target-surface side effects
    threat-model the changed surface: assets, actors, entry points, trust
    boundaries, abuse cases, mitigations, tests
    if a security blocker is found:
      create SECURITY_FIX_SUBLOOP with exploit/failure test where possible
      return to Engineering Loop
    if authority is needed for external/security-sensitive action:
      ESCALATE for owner approval
    else mark security item proven/deferred with evidence

RELEASE/READBACK LOOP:
  run release-readiness hard gates when release/public claim is in scope
  if push/PR/check readback is required:
    commit, push, read PR/head/check status back from target surface
  if hosted/deployed/Telegram/browser proof is required:
    exercise that exact surface and capture readback
  never substitute local proof for target-surface proof

CONTRACT UPDATE LOOP:
  record confirmed assumptions, rejected assumptions, changed behavior,
  unresolved gaps, new tests, and next recommended slice
  if the contract/spec changed materially:
    update the spec before declaring done

STOP CONDITIONS:
  stop only when all in-scope gates pass and evidence is recorded
  escalate when iteration cap is reached or owner authority is needed
  abort on safety invariant violation or unrecoverable environment failure
```

## Reusable loop prompt

```text
You are running the WEAVE Recursive Secure Development Lifecycle Loop.

Goal:
[ONE OUTCOME]

Target proof surface:
[scripted runner / Hermes CLI / local runtime / browser / hosted app / Telegram UX / PR checks]

Authoritative inputs:
- [paths to contracts/specs]
- [scenario files]
- [acceptance criteria]
- [verification commands]

Proof boundaries:
Verified claims may only name surfaces actually exercised. Label everything else
as not verified, deferred, owner-gated, or out of scope.

Loop contract:
1. Capture owner intent as user, pain, desired outcome, non-goals, target proof
   surface, assumptions, and risk gates.
2. If the task is broad or product-strategic, run lifecycle-pattern mining:
   - build public evidence ladders from comparable products
   - label source-backed facts vs inferences
   - extract universal and segment-specific patterns
   - reject unsupported or company-specific imitation
3. Run the deep-enough self-check:
   - Have I uncovered enough important things to make the next lifecycle decision
     safely?
   - If no, run a narrower research/clarification loop.
   - If yes, explain why more research is unlikely to change the next decision.
4. Then build or validate a loop-ready spec:
   - goal
   - target surface
   - assumptions ledger
   - acceptance criteria
   - verification/readback commands
   - non-claims
   - risk gates
5. If the spec is missing critical information, retrieve what can be retrieved.
   Ask the owner only when ambiguity changes product meaning, authority, cost,
   security, or irreversible behavior.
6. Enter Engineering only after the Plan gate passes.
7. Engineering loop:
   while acceptance criteria are not met:
     pick the smallest unfinished task;
     implement it;
     add or update tests/proof;
     run focused verification;
     if blocked, spawn a bounded bug/root-cause subloop;
     if spec-compliance review fails, revise and re-review;
     if quality/security review fails, revise and re-review;
     mark complete only with evidence.
8. QA loop:
   build a QA matrix; run independent items in parallel; run dependent items in
   order; add new QA items when discovered; if QA fails, return to engineering
   with the smallest fix packet.
9. Security loop:
   run scans and threat review; check trust boundaries, auth, bind policy,
   secrets, public claims, logs, supply chain, and side effects; if a blocker is
   found, return to engineering with regression proof.
10. Release/readback loop:
   run release-readiness gates and exact target-surface readback if in scope.
11. Contract update loop:
   update assumptions, spec, tests, and next-slice recommendations after reality
   contact.

Iteration limits:
- Max 3 revision cycles for a single review gate.
- Max 8 controller cycles unless the owner explicitly extends the run.
- Escalate if issue count does not decrease between cycles.
- Abort on secret exposure, destructive-risk ambiguity, credential/custody risk,
  or unrecoverable environment failure.

Required final response:
- State: verified / partial / blocked
- Target surface exercised
- What changed
- Evidence: commands, artifact paths, readbacks
- Assumptions confirmed/rejected
- Remaining risks/non-claims
- Next recommended loop
```

## Current WEAVE state for this loop

For the scripted-user/live-agent runner work, the current target surface is the
programmatic runner plus Hermes CLI live adapter, not Telegram UX. Telegram can
be a later dogfood target when the product question is the actual user chat
experience.

For a general WEAVE engineering loop, the process is now at Plan for this loop
itself. Version 0.1 named the controller loop but leaned too heavily on
frameworks. Version 0.2 added lifecycle-pattern mining. Version 0.3 adds the
owner-intent sufficiency gate: before creating the first loop prompt, the agent
must ask whether it has uncovered enough important evidence and reasoning
patterns to make the next lifecycle decision safely. The detailed prompt sequence
lives in `docs/plans/weave-owner-intent-to-loop-prompt-v0.1.md`.

# WEAVE Owner-Intent to Recursive Loop Prompt v0.1

Status: draft prompt contract
Date: 2026-06-09

## Purpose

This document defines the prompt sequence WEAVE should use after capturing owner
intent. The goal is to create the best possible first recursive loop prompt by
asking whether enough public process evidence, product context, proof boundaries,
and lifecycle artifacts have been uncovered to proceed.

The controller must not treat owner intent as a direct implementation command.
It must first convert intent into a product/lifecycle decision with evidence,
assumptions, stage gates, and proof boundaries.

## Principle

Research is deep enough when the next lifecycle decision can be made safely.
It is not deep enough just because the agent found a few famous examples or a
framework checklist.

A good first loop prompt should answer:

- What did the owner actually intend?
- What product change does that imply?
- Which lifecycle stage are we in?
- Which successful public processes are relevant?
- Which patterns are universal, segment-specific, or not transferable?
- What proof surface must be exercised?
- What artifacts must exist before Engineering, QA, Marketing, or Operations?
- What unknowns remain, and where are they routed?

## Prompt 1: Owner intent capture

```text
You are converting owner intent into a WEAVE lifecycle task.

Owner message:
[OWNER_MESSAGE]

Do not jump to implementation. First produce an owner-intent capsule:

1. User / customer / operator affected.
2. Pain or opportunity in the owner's words.
3. Desired outcome.
4. Product/lifecycle stage implied: intent, research, selection, plan,
   engineering, QA, deployment, KPI, marketing, iteration, analysis.
5. Target proof surface: local fixture, local CLI, live generated-agent mode,
   browser, hosted runtime, Telegram/deployed gateway, PR/check surface, public
   release, or marketing/ops surface.
6. Explicit non-goals and non-claims.
7. Risk gates: public claims, auth, secrets, payments/custody, destructive work,
   private topology, external sends, compliance, user trust.
8. Ambiguities classified as:
   - safe default
   - needs verification
   - owner-gated
   - blocker

Ask the owner only if the ambiguity changes authority, security, cost, product
meaning, public claim, or irreversible behavior. Otherwise record a safe default
and keep moving.
```

## Prompt 2: Lifecycle-pattern mining

```text
You are a lifecycle-pattern mining agent.

Owner-intent capsule:
[OWNER_INTENT_CAPSULE]

Research goal:
Find public product/process evidence that helps design the loop prompt for this
intent. Do not stop at frameworks. Build an evidence ladder from comparable
successful products.

Required evidence rungs:
- intent/problem artifact
- spec/RFC/proposal/design artifact
- review/discussion/decision artifact
- implementation PR/commit/code artifact
- test/QA/release-readiness artifact
- release notes/changelog/docs/upgrade artifact
- launch/blog/event/marketing artifact
- operations/support/community/feedback artifact

For each rung, label:
- source-backed
- inferred from same-product public artifacts
- inferred from cross-product comparison
- missing / not safely inferable

Then extract the cognitive process:
- What were builders or reviewers worried about?
- What decision artifact reduced ambiguity?
- What evidence changed the maturity state?
- What risk was bounded?
- What user action did launch enable?
- What feedback loop stayed open?

Classify every pattern:
- universal
- segment-specific
- company-specific
- unsupported / tempting but not proven

Only convert universal or relevant segment-specific patterns into WEAVE prompt
requirements.
```

## Prompt 3: Deep-enough self-check

This is the key correction. The agent must ask itself whether it has uncovered
all important things needed to create the first loop prompt.

```text
Before writing the loop prompt, run this sufficiency gate.

Question:
Have I uncovered enough important evidence and reasoning patterns to make the
next lifecycle decision safely?

Answer YES only if all are true:

1. Intent clarity:
   I can restate the owner intent as user, pain, desired outcome, success signal,
   non-goals, and target proof surface.

2. Segment fit:
   I know which product segment dominates: developer/API, open-source infra,
   enterprise SaaS/category, PLG/framework, collaboration/work-management,
   operations/internal tooling, or another named segment.

3. Evidence ladder:
   I have at least one strong comparable lifecycle chain, or I can explicitly
   justify cross-product substitutions for missing rungs.

4. Pattern transfer:
   I have separated universal, segment-specific, company-specific, and unsupported
   patterns. I am not copying a famous company tactic blindly.

5. Decision-grade disagreement:
   I can state the strongest objection, strongest alternative, tradeoff accepted,
   and evidence that would change the decision.

6. Unknown routing:
   Every important unknown is marked as pre-spec blocker, implementation
   experiment, pre-release blocker, future work, or owner-gated decision.

7. Stage gate:
   I know whether the next action should be research, plan, engineering, QA,
   security, marketing, operations, iteration, owner escalation, or abort.

8. Proof boundary:
   I can say exactly what this loop will prove and what it will not prove.

9. Artifact ladder:
   I can name the artifacts required for the next stage: spec, issue, task list,
   QA matrix, threat model, docs, changelog, launch note, support brief,
   feedback channel, or measurement plan.

10. Research marginal value:
   I can explain why more research is unlikely to change the next decision, or I
   can name the exact missing research query that must run before proceeding.

If any answer is NO, do not write the final loop prompt yet. Run a narrower
research or clarification loop focused on the failing item.
```

## Prompt 4: Spec compiler

```text
You are compiling a build-ready WEAVE spec from owner intent and lifecycle-pattern
research.

Inputs:
- owner-intent capsule
- lifecycle-pattern mining report
- deep-enough self-check
- repo/product constraints

Write a spec with:

1. Problem and target user.
2. Desired outcome and success signal.
3. Lifecycle stage.
4. Product segment and imported patterns.
5. Source-backed facts vs same-product inferences vs cross-product inferences.
6. Non-goals and non-claims.
7. Target proof surface.
8. Acceptance criteria.
9. Implementation slices.
10. QA/adoption-risk matrix.
11. Security/trust gates.
12. Marketing/ops artifacts if user-facing or public.
13. Measurement and feedback loop.
14. Unknowns ledger with routing.
15. Owner approval gates.
16. Stop conditions.
```

## Prompt 5: Reviewer simulation

```text
Review the spec as six skeptical reviewers:

1. Kubernetes KEP reviewer:
   - Is the motivation clear?
   - Are goals/non-goals explicit?
   - Are owners, stage, graduation, test plan, and rollback/ops concerns clear?

2. Rust RFC/stabilization reviewer:
   - Are guide-level and reference-level explanations strong?
   - Are alternatives, drawbacks, prior art, and unresolved questions handled?
   - Is this ready for decision, implementation, or stabilization?

3. Stripe API trust reviewer:
   - What could break for users?
   - Is versioning, testing, upgrade, rollback, and docs support clear?

4. React/Next/Vercel adoption reviewer:
   - Is adoption incremental?
   - Are maturity labels honest?
   - Are docs, codemods, previews, tests, and feedback paths sufficient?

5. GitLab GTM/operations reviewer:
   - Can product, engineering, docs, support, sales, and marketing act from this?
   - Is launch class/blast radius right?

6. Owner-proof reviewer:
   - Does the spec preserve the owner's intent?
   - Are proof boundaries explicit enough to prevent overclaiming?

For each reviewer, return: pass, revise, defer, reject, or owner-gated. Include
the smallest fix that would change the verdict.
```

## Prompt 6: Recursive execution loop

```text
Run the WEAVE recursive lifecycle loop.

Inputs:
- approved spec
- reviewer simulation verdicts
- target proof surface
- acceptance criteria
- verification commands/readbacks

Loop:
while all in-scope gates are not passed:
  1. Select the smallest unresolved gate or task.
  2. If it is research/spec ambiguity, run a narrow research loop.
  3. If it is engineering, implement the smallest slice with tests.
  4. If it is QA, build or run the adoption-risk matrix.
  5. If it is security/trust, run threat/secret/public-claim checks.
  6. If it is marketing/ops, create the missing enablement/support/feedback
     artifact.
  7. If it is owner-gated, stop and present choices.
  8. After every reality contact, update the assumptions and spec.
  9. Ask whether issue count and uncertainty are decreasing.
  10. Stop only when the target proof surface has been exercised and the final
      report can separate verified claims, assumptions, non-claims, and blockers.

Iteration limits:
- Max 3 revision cycles per gate.
- Max 8 controller cycles unless owner explicitly extends.
- Escalate if the same uncertainty survives two cycles without new evidence.
- Abort on secret exposure, destructive ambiguity, credential/custody risk, or
  public-claim risk without approval.
```

## Final report format

```text
State: verified / partial / blocked / owner-gated
Owner intent preserved: yes/no, with note
Lifecycle stage reached:
Target proof surface exercised:
What changed:
Evidence:
- commands/readbacks
- artifact paths
- source URLs
Source-backed facts:
Inferences:
Assumptions confirmed:
Assumptions rejected:
Remaining unknowns:
Non-claims:
Next recommended loop:
```

## Anti-patterns this prompt blocks

- Treating owner intent as a direct coding task.
- Treating a framework checklist as product-building evidence.
- Calling research done because three famous companies were named.
- Copying company-specific tactics as universal rules.
- Ignoring marketing/ops until after code is done.
- Treating architecture proof as adoption proof.
- Treating local fixture proof as deployed/user-surface proof.
- Hiding unresolved questions in prose instead of routing them.
- Running recursive loops without stop conditions or owner gates.

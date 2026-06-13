# Product Lifecycle Pattern Mining for Recursive Agent Loops v0.2

Status: draft research synthesis, deepened with sufficiency gates
Date: 2026-06-09

## Purpose

This document corrects a shallow interpretation of recursive SDLC loop design.
The goal is not only to import abstract frameworks. The goal is to study public
product-building evidence and extract reasoning patterns that a recursive agent
can emulate while moving from intent to spec, review, code, QA, launch,
marketing, operations, and post-launch learning.

The useful evidence has three shapes:

1. **Rare end-to-end case:** public artifacts show a substantial journey from
   idea/spec through review, implementation, release, marketing, and operations.
2. **Same-product inference case:** GitHub or public engineering artifacts show
   some lifecycle stages; later or adjacent stages must be inferred from release
   notes, docs, launch posts, changelogs, community channels, or operational
   handbooks.
3. **Cross-product pattern case:** different successful products expose different
   lifecycle stages. Universal and segment-specific patterns are inferred by
   comparing the repeated moves across products.

All claims below are either source-backed or explicitly labeled as inference.

## Source-backed evidence chains

### 1. Kubernetes: governed feature lifecycle plus release/community operation

Evidence:

- Kubernetes Enhancement Proposals (KEPs) are used to propose, communicate, and
  coordinate non-trivial efforts and create a historical record:
  <https://github.com/kubernetes/enhancements/tree/master/keps>
- The KEP template/process explicitly says to create an enhancement issue, fill
  title/authors/SIG/status/date fields, write summary and motivation, create a
  PR, assign SIG sponsors, merge early, iterate, mark unresolved debates, keep
  tightly scoped single-topic PRs, and treat one KEP as the lifecycle artifact for
  a feature:
  <https://raw.githubusercontent.com/kubernetes/enhancements/master/keps/README.md>
- Kubernetes release cycle uses Enhancement Definition, Implementation, and
  Stabilization phases, with freezes, pruning, milestone owners, and release
  branches:
  <https://kubernetes.io/releases/release/>
- Kubernetes release notes and changelogs are public operational/adoption
  artifacts:
  <https://kubernetes.io/releases/notes/>
- Release blogs list maturity signals, deprecations/removals, counts of
  alpha/beta/stable enhancements, release team/community attribution, and full
  release-note links:
  <https://kubernetes.io/blog/2024/04/17/kubernetes-v1-30-release/>

Reasoning pattern to emulate:

- A serious feature starts as a **coordination artifact**, not just code.
- The spec is allowed to start provisional, but it must name owners, motivation,
  unresolved debates, status, and lifecycle movement rules.
- Review is kept focused by single-topic PRs and sponsor ownership.
- Release communication preserves maturity state and operational risk instead of
  flattening everything into one marketing claim.

WEAVE prompt primitive:

```text
Kubernetes-style feature-lifecycle prompt:
Before engineering, create the lifecycle artifact. Name the owner, stage,
motivation, non-goals, unresolved debates, review sponsors, acceptance tests,
release maturity label, deprecation/rollback implications, and how this artifact
will be updated as reality changes. If the artifact is provisional, state what
would make it implementable. If implementable, state what would make it stable.
```

### 2. Rust async/await: RFC -> tracking issue -> stabilization -> release story

Evidence:

- Rust RFC PR 2394, "async/await notation for ergonomic asynchronous IO," was
  merged:
  <https://github.com/rust-lang/rfcs/pull/2394>
- Rust tracking issue 50547 tracked async/await implementation and stabilization
  after the RFC:
  <https://github.com/rust-lang/rust/issues/50547>
- Rust announced async-await on stable Rust with user-facing explanation and
  adoption framing:
  <https://blog.rust-lang.org/2019/11/07/Async-await-stable/>
- Rust Forge documents the release process and stabilization/release machinery:
  <https://forge.rust-lang.org/release/process.html>

Reasoning pattern to emulate:

- A language/platform change separates **accepted design** from **implementation
  tracking** from **stabilization evidence** from **public adoption story**.
- The tracking issue is a work queue and decision memory: remaining questions,
  implementation status, blockers, tests, and stabilization prerequisites should
  be visible in one place.
- The public announcement does not only say "shipped"; it explains why the
  feature matters, where it fits in the ecosystem, and what users can do next.

WEAVE prompt primitive:

```text
Rust-style stabilization prompt:
For this feature, split design acceptance from implementation tracking and from
stable/launch readiness. Maintain a tracking ledger with unresolved blockers,
required tests, documentation, compatibility risks, and stabilization criteria.
Do not write launch copy until the tracking ledger supports the maturity claim.
```

### 3. React Server Components / Next.js: RFC and research become framework launch paths

Evidence:

- React RFC 188 defines React Server Components:
  <https://raw.githubusercontent.com/reactjs/rfcs/main/text/0188-server-components.md>
- The corresponding RFC PR is public:
  <https://github.com/reactjs/rfcs/pull/188>
- React published a public explanation of the idea and its intended benefits:
  <https://react.dev/blog/2020/12/21/data-fetching-with-react-server-components>
- Next.js App Router public feedback/discussion captured beta-stage feedback:
  <https://github.com/vercel/next.js/discussions/41745>
- Next.js 14 release communication paired claims with concrete proof such as
  test counts, speed metrics, stable/preview labels, commands, and docs:
  <https://nextjs.org/blog/next-14>
- Next.js docs and upgrade guides turn launches into adoption paths:
  <https://nextjs.org/docs>
  <https://nextjs.org/docs/app/guides/upgrading/version-15>

Reasoning pattern to emulate:

- A deep architecture change can require a research/RFC layer, framework-specific
  adoption layer, beta feedback layer, and later stable launch layer.
- Feedback during beta is not noise; it is product evidence that should update
  docs, migration paths, developer experience, and maturity labels.
- Launch claims for developer tools should be paired with runnable commands,
  docs, benchmarks, test counts, and a clear preview/stable boundary.

Inference label:

- The public artifacts do not expose every internal decision between React and
  framework implementers. The safe inference is that architecture intent was
  translated into framework-specific adoption artifacts through public RFCs,
  discussions, docs, release posts, and upgrade guides.

WEAVE prompt primitive:

```text
Architecture-to-adoption prompt:
When a change affects developer mental models, maintain four linked artifacts:
(1) architecture/RFC intent, (2) product-specific adoption path, (3) beta/feedback
ledger, and (4) stable launch proof. In every loop, ask which artifact changed
and which downstream artifact must now be updated.
```

### 4. GitLab: transparent product process plus transparent GTM operating model

Evidence:

- GitLab Product Processes describes product work, dual-track development,
  direction pages, product/engineering/UX/quality collaboration, and release
  communication processes:
  <https://handbook.gitlab.com/handbook/product/product-processes/>
- GitLab Marketing Handbook documents marketing strategy, customer journey,
  marketing operations, and team responsibilities:
  <https://handbook.gitlab.com/handbook/marketing/>
- GitLab public release notes create a recurring external change surface:
  <https://about.gitlab.com/releases/>

Reasoning pattern to emulate:

- Product lifecycle and go-to-market are not separate mysteries; they are linked
  operating systems. Direction, release communication, marketing operations, and
  customer journey should be visible enough that teams can coordinate without
  oral tradition.
- The public handbook itself becomes a trust artifact.

WEAVE prompt primitive:

```text
Transparent operating-model prompt:
For each lifecycle stage, name not just the artifact, but which function uses it:
engineering, QA, security, docs, marketing, support, sales, customer success,
community, or operations. If a function cannot act from the artifact, the stage
is not complete.
```

### 5. Stripe: docs/versioning/changelog as both marketing and operational safety

Evidence:

- Stripe API versioning separates major backward-incompatible releases from safe
  monthly releases and tells users to test before upgrading:
  <https://docs.stripe.com/api/versioning>
- Stripe API upgrades guide links version headers, Workbench, SDK and webhook
  versioning, and developer changelog:
  <https://docs.stripe.com/upgrades>
- Stripe changelog categorizes product, breaking, GA, and public-preview changes:
  <https://docs.stripe.com/changelog>
- Stripe CLI docs make integration and webhook testing operationally accessible:
  <https://docs.stripe.com/stripe-cli>

Reasoning pattern to emulate:

- For API/developer products, docs are not post-launch support. They are the
  product surface, marketing funnel, QA interface, and operational risk control.
- Versioning, changelog categories, test tooling, and upgrade guidance are all
  trust-building artifacts.

WEAVE prompt primitive:

```text
Developer-trust prompt:
For any developer-facing feature, ask: what could break, how can users test it,
how do they upgrade or roll back, what version/maturity label applies, and what
single command or sandbox proves value quickly?
```

### 6. Salesforce / Atlassian / Vercel: market and operations patterns beyond code

Evidence:

- Salesforce history documents the "End of Software" category narrative,
  Salesforce CRM launch, AppExchange, IdeaExchange, Force.com, and Trailhead:
  <https://www.salesforce.com/news/stories/the-history-of-salesforce/>
  <https://trailhead.salesforce.com/>
- Atlassian Team Playbook publishes public operating practices, plays,
  templates, and team rituals:
  <https://www.atlassian.com/team-playbook>
- Atlassian Community and Marketplace expose community and ecosystem channels:
  <https://community.atlassian.com/>
  <https://marketplace.atlassian.com/>
- Vercel launch/event and changelog surfaces pair launches with demos, docs,
  previews, feature flags, collaboration, and adoption paths:
  <https://vercel.com/blog/vercel-ship-2024>
  <https://vercel.com/changelog>
  <https://vercel.com/docs>

Reasoning pattern to emulate:

- Category creation is not a slogan. It requires a contrastive belief, product
  proof, events, training, feedback, ecosystem, and operational enablement.
- Collaboration/productivity platforms can market a system of work, not just a
  feature list.
- PLG developer platforms compress narrative to proof to hands-on adoption.

WEAVE prompt primitive:

```text
Category-and-operations prompt:
If this is a market/category claim, identify the old belief being replaced, the
proof that makes the new belief credible, the training/community/ecosystem that
makes it adoptable, and the operations artifacts that keep users successful after
launch. Reject slogans that are not backed by artifacts.
```

## Universal success patterns

### Pattern 1: Artifact ladder

Successful products turn one artifact into the next without losing truth:

```text
intent/problem -> spec/RFC/proposal -> review/decision record -> implementation
-> tests/QA -> release note/changelog -> docs/upgrade guide -> launch narrative
-> enablement/support/community -> operations metrics -> next iteration
```

Prompt move:

```text
At this lifecycle stage, what upstream artifact is the source of truth, what
next artifact must be produced, and what truth must not be lost in translation?
```

### Pattern 2: Stage-specific promise boundaries

Alpha, beta, preview, RC, stable, GA, deprecated, removed, maintenance-only, and
experimental should each produce different claims, CTAs, tests, and risk notes.

Prompt move:

```text
What maturity stage is this? What can we safely promise? What must we explicitly
not promise? What proof would move it to the next stage?
```

### Pattern 3: Review as cognitive compression

Good review does not only say "LGTM". It compresses debate into stable decisions,
unresolved issues, owner approvals, tests, and updated artifacts.

Prompt move:

```text
List the decisions this review settled, the questions still open, the evidence
that changed minds, the tests/docs required by the decision, and the next owner.
```

### Pattern 4: QA as adoption-risk simulation

QA is not merely unit tests. It simulates how the product can fail for actual
users: upgrade paths, compatibility, performance, usability, permissions,
security boundaries, docs accuracy, support load, and rollback.

Prompt move:

```text
Build a QA matrix from user journeys, changed code, maturity stage, migration
risk, security boundaries, docs claims, and support failure modes. Parallelize
independent checks; sequence dependent and target-surface checks.
```

### Pattern 5: Marketing as truthful translation

The best public messages are translations of engineering truth into user value,
not detached persuasion.

Prompt move:

```text
What changed? Who benefits? What pain is reduced? What evidence proves it? What
can the user try now? What maturity/risk boundary must the message respect?
```

### Pattern 6: Operations as post-launch contract

Releases succeed when users can plan around change and know where to learn,
upgrade, ask questions, report bugs, and recover from failure.

Prompt move:

```text
What operational contract does this release create: cadence, changelog,
versioning, support path, monitoring, escalation, rollback, feedback, and next
iteration trigger?
```

### Pattern 7: Segment-specific emphasis

Universal patterns need segment weights:

- Developer/API products: docs, CLI/SDK, changelog, versioning, sandbox,
  migration path, sample code, quick proof.
- Open-source infrastructure: governance, proposal, owner SIG/team, maturity
  label, release notes, deprecation policy, community legitimacy.
- Enterprise SaaS/category creation: belief change, ROI/risk, enablement,
  training, customer feedback, ecosystem, support/sales readiness.
- PLG/framework platforms: benchmark, demo, template, `npx`/CLI start,
  preview/RC path, docs, social proof.
- Collaboration/productivity platforms: operating model, playbooks, templates,
  community, marketplace, recurring change notes.

Prompt move:

```text
Which segment pattern dominates this product? Which artifacts are mandatory for
that segment? Which artifacts are optional or premature?
```

## Recursive lifecycle-mining loop prompt

Use this when researching public products before writing or revising a WEAVE loop
spec.

```text
You are a lifecycle-pattern mining agent. Your job is to study public product
artifacts and extract reasoning patterns that can be turned into WEAVE recursive
loop prompts.

Research target:
[product/company/ecosystem/stage]

Required evidence types:
- intent/problem artifact if available
- spec/RFC/proposal/design artifact if available
- review/discussion/decision artifact if available
- implementation PR/commit/code artifact if available
- test/QA/release-readiness artifact if available
- release notes/changelog/docs/upgrade artifact if available
- launch/blog/event/marketing artifact if available
- operations/support/community/feedback artifact if available

Loop:
1. Build an evidence ladder from earliest available artifact to latest available
   artifact.
2. For every missing rung, search public periphery data: docs, changelog, blog,
   conference talk, handbook, support page, community discussion, issue tracker,
   release notes, migration guide.
3. Label each rung:
   - source-backed
   - inferred from same-product public artifacts
   - inferred from cross-product comparison
   - missing / not safely inferable
4. Extract the cognitive process:
   - What did builders appear to worry about?
   - What decision artifact reduced ambiguity?
   - What evidence changed maturity state?
   - What risk was explicitly bounded?
   - What user action did the launch enable?
   - What feedback loop remained open?
5. Compare against at least two other products in the same segment and one in a
   different segment.
6. Mark patterns as:
   - universal
   - segment-specific
   - company-specific
   - unsupported / tempting but not proven
7. Convert only universal or relevant segment-specific patterns into WEAVE prompt
   primitives.

Output:
- Evidence ladder with URLs.
- Source-backed facts.
- Labeled inferences.
- Cognitive pattern.
- WEAVE prompt primitive.
- Anti-pattern or overclaim to avoid.
```

## Intent-to-spec recursive prompt upgrade

The earlier recursive SDLC loop should be upgraded with this front-end:

```text
INTENT-TO-SPEC LOOP:
while spec is not build-ready:
  1. Restate the user intent as a product change, not just an implementation task.
  2. Identify the product segment and relevant public success patterns.
  3. Build the artifact ladder required for this segment.
  4. Create assumptions ledger:
     - safe default
     - needs verification
     - owner-gated
     - blocker
  5. Write the first spec with:
     - problem and target user
     - non-goals
     - lifecycle stage
     - acceptance criteria
     - review owners/checks
     - implementation slices
     - QA matrix
     - security/threat gates
     - docs/release/marketing/ops artifacts
     - measurement and feedback loop
  6. Review the spec by asking:
     - What would a Kubernetes KEP reviewer challenge?
     - What would a Rust stabilization reviewer refuse to stabilize?
     - What would a Stripe API user fear breaking?
     - What would a Next/Vercel developer need to try this in 5 minutes?
     - What would GitLab-style marketing/support need to explain it?
     - What would Salesforce/Atlassian-style category or operations work require?
  7. If the review finds gaps, revise the spec.
  8. Enter Engineering only when the artifact ladder and proof boundaries are
     explicit enough that an agent cannot confuse local orchestration proof,
     live-agent proof, deployed proof, and public-release proof.
```

## Anti-patterns to block

- Treating a framework checklist as equivalent to product-building evidence.
- Writing launch copy before maturity, docs, QA, and operational risk are known.
- Inferring hidden internal process from public artifacts without labeling it.
- Treating code merge as product success without docs, release notes, adoption
  path, support path, and feedback loop.
- Using one famous company pattern as universal without comparison.
- Running a recursive agent loop with no iteration cap, no owner gates, and no
  proof-surface boundary.
- Letting a local fixture or scripted proof imply deployed/user-surface proof.

## Immediate implications for WEAVE

1. The recursive loop prompt needs a **research/lifecycle-mining stage before
   Plan** when the task is broad or product-strategic.
2. Every WEAVE task should declare its target segment and required artifact
   ladder before Engineering.
3. Marketing and operations should be first-class lifecycle stages with gates,
   not afterthoughts.
4. QA must include adoption-risk and public-claim checks, not only code tests.
5. The loop final report must distinguish source-backed facts, same-product
   inferences, cross-product inferences, assumptions, proof surfaces, and
   non-claims.


## Deepening pass: cognitive sufficiency gates

A second, narrower research pass refined the core question: after capturing owner
intent, how should an agent decide whether it has uncovered enough from public
processes to write a good first loop prompt or whether it must keep researching?

### Kubernetes and Rust: enough means decision-grade, not exhaustive

Source-backed observations:

- Kubernetes KEPs encourage early provisional merge and iteration, but gate
  `implementable` and release inclusion on approvers, test plan, graduation
  criteria, Production Readiness Review, implementation history, and docs:
  <https://github.com/kubernetes/enhancements/blob/master/keps/NNNN-kep-template/README.md>
- Kubernetes Production Readiness Review asks whether a feature is observable,
  scalable, supportable, safely operable, and rollback/disable-able:
  <https://github.com/kubernetes/enhancements/blob/master/keps/sig-architecture/1194-prod-readiness/README.md>
- Rust RFCs separate motivation, guide-level explanation, reference-level
  explanation, drawbacks, alternatives, prior art, and unresolved questions:
  <https://github.com/rust-lang/rfcs/blob/master/0000-template.md>
- Rust final-comment-period starts when enough tradeoffs have been discussed for
  the responsible team to decide; new substantial arguments cancel FCP and return
  the RFC to discussion:
  <https://github.com/rust-lang/rfcs/blob/master/README.md>
- Rust stabilization requires a stabilization report, tests, docs/references, and
  an audit of deviations from the accepted design:
  <https://github.com/rust-lang/rustc-dev-guide/blob/master/src/stabilization-guide.md>

WEAVE inference:

- Research is deep enough when the next lifecycle decision can be made safely,
  not when every possible source has been read.
- A loop should proceed only when it has decision-grade disagreement: the strong
  objections, tradeoffs, and missing evidence are explicit and routed.
- Unknowns are not all blockers. They must be sorted into pre-spec blockers,
  implementation experiments, pre-release blockers, future work, or owner-gated
  decisions.

Prompt primitive:

```text
Decision-grade sufficiency prompt:
Have I uncovered enough to make the next lifecycle decision safely?
Answer yes only if I can state: owner intent, user pain, success signal, non-goals,
relevant public patterns, strong objections, alternatives, unknowns with owners,
proof needed for the next stage, and why more research would or would not change
this decision.
```

### React, Next.js, Vercel, and Stripe: launch proof is adoption-proof

Source-backed observations:

- React Server Components were shared as research with an RFC and explicit open
  adoption questions; React did not treat promising internal results as immediate
  production readiness:
  <https://github.com/reactjs/rfcs/blob/main/text/0188-server-components.md>
  <https://react.dev/blog/2020/12/21/data-fetching-with-react-server-components>
- Next.js translated architecture into incremental adoption, beta/stable labels,
  migration docs, codemods, proof metrics, and upgrade guides:
  <https://nextjs.org/blog/layouts-rfc>
  <https://nextjs.org/blog/next-13>
  <https://nextjs.org/blog/next-13-4>
  <https://nextjs.org/blog/next-14>
  <https://nextjs.org/docs/app/guides/migrating/app-router-migration>
- Vercel operationalizes adoption through preview environments, incremental
  migration, fallback routing, feature flags, observability, and production
  checklists:
  <https://vercel.com/docs/deployments/environments#preview-environment-pre-production>
  <https://vercel.com/docs/incremental-migration>
  <https://vercel.com/docs/production-checklist>
- Stripe makes developer trust operational through API versioning, test mode,
  upgrade workbench, changelog categories, webhooks, CLI testing, and rollback
  windows:
  <https://docs.stripe.com/api/versioning>
  <https://docs.stripe.com/upgrades>
  <https://docs.stripe.com/changelog>
  <https://docs.stripe.com/stripe-cli>

WEAVE inference:

- Developer-product research is deep enough when the agent can name the smallest
  adoption unit, the old path that remains, the rollback path, the proof that
  upgrades maturity status, and the docs/tools that reduce adoption fear.
- Architecture proof is not launch proof. Launch proof includes migration,
  compatibility, docs, observability, feedback, and honest maturity labels.

Prompt primitive:

```text
Adoption-sufficiency prompt:
For this owner intent, what is the smallest safe adoption unit: route, user group,
API version, package, environment, or workflow? What remains compatible? What is
rollback? What proof upgrades the maturity label? What docs, tests, CLI, sandbox,
or migration guide lets a real user verify value without trusting us?
```

### GitLab, Salesforce, and Atlassian: marketing and operations are artifact gates

Source-backed observations:

- GitLab product processes connect product, engineering, UX, quality, direction
  pages, release posts, and external communication:
  <https://handbook.gitlab.com/handbook/product/product-processes/>
- GitLab product-launch/NPI process asks what is launching, why it matters, who
  it is for, when it ships, and whether product/GTM teams can execute; if
  insufficient, it can be sent back, re-sequenced, re-scoped, or rejected:
  <https://handbook.gitlab.com/handbook/product/product-processes/product-launch/>
- GitLab marketing connects messaging, customer journey, sales/customer success,
  release support, campaigns, and enablement:
  <https://handbook.gitlab.com/handbook/marketing/>
- Salesforce paired category narrative with ecosystem, feedback, platform, and
  training artifacts including AppExchange, IdeaExchange, Force.com, and
  Trailhead:
  <https://www.salesforce.com/news/stories/the-history-of-salesforce/>
  <https://trailhead.salesforce.com/>
- Atlassian exposes product-adjacent operating models through Team Playbook,
  Marketplace, Community, roadmap, and cloud change notes:
  <https://www.atlassian.com/team-playbook>
  <https://marketplace.atlassian.com/>
  <https://community.atlassian.com/>
  <https://www.atlassian.com/roadmap/cloud>

WEAVE inference:

- Marketing and operations are not later decoration. They are sufficiency gates
  that prove the product can be explained, sold, supported, administered,
  learned, integrated, and improved after launch.
- Research is deep enough for Marketing/Ops when the loop can classify launch
  blast radius, audience behavior changes, enablement assets, rollout status,
  support/admin impacts, feedback owner, and next-intent update path.

Prompt primitive:

```text
Marketing/Ops sufficiency prompt:
Classify this change as release note, minor launch, major launch, NPI/business
change, ecosystem change, or operational migration. For buyer, user, admin,
developer, partner, support, sales, and customer success, name the belief/action
change, required asset, risk if absent, rollout status, and feedback owner.
```

## Owner-intent research stop rule

The agent should continue researching while any of these are true:

1. The owner intent cannot be restated as a product change with user, pain,
   desired outcome, and non-goals.
2. The product segment is unclear, so the wrong public patterns may be imported.
3. The evidence ladder has no comparable spec/review example and no justified
   cross-product substitute.
4. Major objections or alternatives have not been articulated.
5. Unknowns are unclassified or have no owner/evidence path.
6. The target proof surface is ambiguous.
7. The adoption/ops path is missing for a user-facing or public claim.
8. More research is likely to change the next lifecycle decision.

The agent may stop researching and write the first loop prompt when all are true:

1. The next lifecycle decision is clear: proceed, iterate, defer, reject, or ask
   owner.
2. Important source-backed facts and inferences are labeled.
3. Universal vs segment-specific vs company-specific patterns are separated.
4. The first spec can name acceptance criteria, proof surfaces, risk gates,
   QA/security/marketing/ops artifacts, and feedback loops.
5. The remaining unknowns are routed to later loops rather than hidden.

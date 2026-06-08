# WEAVE Month 1 Review Evidence Pack

Status: review draft

This pack maps Month 1 deliverables to evidence surfaces. It is intentionally
conservative: if a claim is not proven by a public artifact, runtime surface, or
verified hosted surface, it is marked as partial, blocked, or owner-gated.

## Evidence Legend

| State | Meaning |
|---|---|
| `proved` | Concrete artifact or hosted surface exists and can be inspected. |
| `partial` | Contract or local proof exists, but runtime or hosted evidence is incomplete. |
| `owner-gated` | External action requires owner approval before execution or publication. |
| `blocked` | Missing dependency prevents the claim from being completed. |
| `planned` | Intended next work, not evidence. |

## M1-D1. WEAVE Tool And Method

| Claim | Evidence | State |
|---|---|---|
| WEAVE has a public tool/method repo | `README.md`, `packages/weave-tool/COMPANY.md`, `docs/month1/README.md` | `proved` |
| WEAVE defines lifecycle stages and gates | `docs/month1/weave-lifecycle-contract-v0.md`, `packages/weave-tool/skills/weave-lifecycle/SKILL.md` | `proved` |
| WEAVE can keep app state visible through deterministic commands | `docs/telegram-slash-commands.md`, `scripts/runtime_smoke.py`, `scripts/lifecycle_rehearsal_smoke.py` | `proved` |
| WEAVE can run a full scripted conversation-to-app local dogfood and produce reviewable app/proof artifacts | `scripts/full_conversation_app_dogfood.py`, `docs/month1/full-conversation-app-dogfood.md`, `docs/month1/full-conversation-app-dogfood-transcript.md`, `docs/month1/artifacts/full-conversation-app-dogfood/` | `proved` |
| WEAVE can study Livepeer pipelines, APIs, gateways, and source context | `docs/capability-context.md`, `docs/context-sources/livepeer-context-index.sample.json` | `partial` |
| WEAVE can synthesize reusable primitives where useful | `packages/weave-tool/primitives/registry.json` | `partial` |
| WEAVE can identify viable applications from primitives or direct API/gateway paths | `packages/weave-tool/skills/primitive-market-research/SKILL.md`, `packages/weave-tool/projects/askuno-runtime-proof/tasks/research-gate/TASK.md` | `partial` |
| WEAVE can engineer applications on top of available capability paths | `packages/weave-tool/projects/askuno-runtime-proof/tasks/engineering-first-primitive/TASK.md` | `partial` |
| WEAVE can QA applications and record readiness | `packages/weave-tool/projects/askuno-runtime-proof/tasks/qa-runtime-readiness/TASK.md` | `partial` |
| WEAVE can gate KPI capture before marketing | `scripts/lifecycle_rehearsal_smoke.py`, `packages/weave-tool/projects/askuno-runtime-proof/tasks/kpi-setup-gate/TASK.md` | `proved` |
| WEAVE can support marketing/outreach workflows | `packages/weave-tool/projects/askuno-runtime-proof/tasks/marketing-gate/TASK.md` | `owner-gated` |
| WEAVE can support iteration from KPI and feedback evidence | `packages/weave-tool/projects/askuno-runtime-proof/tasks/iteration-from-analytics/TASK.md` | `partial` |

M1-D1 review note: the method is documented, package-valid, and locally proven
through deterministic command and lifecycle rehearsal checks. The remaining
review gap is live runtime/provider verification and hosted application evidence,
not the local lifecycle state-machine behavior.

## M1-D2. Runtime Proof

| Claim | Evidence | State |
|---|---|---|
| Hermes is the default execution runtime | `packages/weave-tool/COMPANY.md`, `docs/hermes-setup.md` | `partial` |
| WEAVE wraps the runtime with lifecycle, evidence, gates, and status | `docs/month1/weave-lifecycle-contract-v0.md`, `docs/telegram-slash-commands.md`, `scripts/lifecycle_rehearsal_smoke.py` | `proved` |
| Full conversation-to-app dogfood can generate and review a local product artifact bundle | `scripts/full_conversation_app_dogfood.py`, `docs/month1/full-conversation-app-dogfood.md`, `docs/month1/full-conversation-app-dogfood-transcript.md`, `docs/month1/artifacts/full-conversation-app-dogfood/` | `proved` |
| FableFrame Studio is a concrete Month 1 proof app | `apps/fableframe-studio/`, `docs/month1/fableframe-product-proof.md`, `scripts/month1_product_app_qa.py` | `proved` |
| Askuno is the first proof application | `packages/weave-tool/projects/askuno-runtime-proof/PROJECT.md`, `docs/month1/README.md` | `proved` |
| The initial app is publicly accessible | `docs/month1/README.md` records the Askuno URL | `partial` |
| QA evidence exists for the app/runtime path | `packages/weave-tool/projects/askuno-runtime-proof/tasks/qa-runtime-readiness/TASK.md` | `partial` |
| QA evidence exists for the FableFrame local product path | `scripts/month1_product_app_qa.py` | `proved` |
| Runtime setup and provider route are owner-visible | `docs/hermes-setup.md`, `docs/telegram-slash-commands.md` | `partial` |

M1-D2 review note: repository evidence now includes the runtime shape, a
full scripted conversation-to-app local dogfood, and a concrete local product
proof app. It is still not proof of a live Vercel deployment,
provider-authenticated Hermes chat, real payment, public marketing, or hosted
app-workflow checks.

## M1-D3. Public KPI Reporting

| Claim | Evidence | State |
|---|---|---|
| Public KPI/reporting surface exists | `docs/month1/README.md`, `docs/month1/program-transparency.md` | `partial` |
| Reporting distinguishes measured evidence from plans | `docs/month1/program-transparency.md` | `partial` |
| Reporting covers researched apps, QA, marketing, usage, and iteration | `docs/month1/program-transparency.md` | `partial` |
| Payment or monetization path is documented honestly | `docs/month1/README.md`, `docs/month1/program-transparency.md`, `scripts/lifecycle_rehearsal_smoke.py`, `apps/fableframe-studio/public/config.json` | `partial` |

M1-D3 review note: KPI reporting has a public contract. Current numerical KPI
freshness and payment-path evidence must be checked from the hosted KPI surface
before a final review packet is sent.

## Deterministic Lifecycle Rehearsal

The local lifecycle rehearsal is generated by:

```bash
python3 scripts/lifecycle_rehearsal_smoke.py
```

It creates an isolated temporary runtime and proves:

- foundation blocks stage approval until required context documents are filled
- missing app requests fail deterministically
- current-stage proof is required before owner approval
- `/status` exposes stage-gate attention
- `/advance` blocks before owner approval
- KPI, Marketing, and Analysis require credential capability or explicit owner deferral
- later-stage evidence cannot skip prior-stage approvals
- active app switching works
- REST lifecycle paths match Telegram-command dispatch

The generated JSON proof is written under the operator's local Codex artifact
directory, not committed to the public repo. The proof artifact should be
attached or summarized in review packets when needed.

## Capability Context Review Surface

WEAVE now distinguishes three app creation paths:

1. Existing APIs.
2. Gateway-exposed capabilities.
3. New orchestrator-run capabilities exposed through gateways.

The reviewable context contract is:

- `docs/capability-context.md`
- `docs/context-sources/livepeer-context-index.sample.json`
- `schemas/context-index.schema.json`
- `packages/weave-tool/primitives/registry.json`

This is not a claim that every source is already live or production-ready. It is
the agent-facing method for finding and refreshing current source context before
Research, Selection, Engineering, QA, Marketing, or Iteration.

## Remaining Review Work

- Deploy FableFrame Studio to Vercel after owner approval and record the URL.
- Connect or explicitly defer a real checkout/payment path for FableFrame.
- Verify the live deterministic command surface against the active runtime.
- Verify current Askuno hosted state and KPI output.
- Create the separate public context repository and publish the real
  `context-index.json`.
- Replace sample context entries with current source snapshots from primary
  sources.
- Run one provider-authenticated live Hermes pass after the local deterministic
  lifecycle rehearsal, keeping secrets and provider auth outside public logs.

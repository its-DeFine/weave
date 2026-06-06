---
mission_id: weave-m1-review-evidence-pack-2026-06
target_repo: its-DeFine/weave
scope: Produce a Month 1 review evidence pack that maps M1-D1, M1-D2, and M1-D3 claims to concrete WEAVE docs, runtime surfaces, Askuno evidence, KPI reporting, and known gaps.
acceptance_criteria:
  - docs/month1/review-evidence-pack.md exists and maps each M1 deliverable to evidence or an explicit blocked/deferred state
  - docs/month1/README.md explains that WEAVE supports pipelines, APIs, and maintained capability context rather than pipelines only
  - docs/month1/app-lifecycle.md names capability context refresh during Research, Selection, Engineering, KPI Setup, Marketing, and Iteration where relevant
  - docs/month1/program-transparency.md distinguishes measured evidence from plan-only or owner-gated next steps
  - package validation exits 0
  - public-safe repository scan exits 0
compute_budget_minutes: 120
credit_reward: 40
value_to_org: Makes the Month 1 Livepeer Foundation review surface inspectable, honest, and aligned with the actual WEAVE architecture.
why_compute_conserving: A review matrix reduces repeated explanation work and prevents future agents from overclaiming unavailable evidence.
---

# Month 1 Review Evidence Pack

**Scope**

Prepare WEAVE for Month 1 review by mapping every M1-D1, M1-D2, and M1-D3
claim to concrete evidence. The pack must separate shipped evidence, local
proof, hosted proof, owner-gated decisions, and planned next steps.

**Acceptance evidence required**

- [ ] `docs/month1/review-evidence-pack.md` exists.
- [ ] Every M1-D1 tool/method claim maps to a repo artifact, runtime command,
      Askuno proof artifact, KPI surface, or explicit gap.
- [ ] M1-D1 language reflects pipelines, APIs, and maintained capability
      context.
- [ ] M1-D2 runtime proof evidence is separate from repo-only claims.
- [ ] M1-D3 KPI reporting evidence distinguishes measured values from plans.
- [ ] `python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool` exits 0.
- [ ] `python3 scripts/public_safe_repo_scan.py` exits 0.

**Compute budget:** 120 minutes agent runtime.
**Credit reward:** 40 credits on verified completion.

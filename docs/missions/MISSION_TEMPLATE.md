---
mission_id: ""
target_repo: ""
scope: ""
acceptance_criteria: []
compute_budget_minutes: 0
credit_reward: 0
value_to_org: ""
why_compute_conserving: ""
---

# Mission Template

Copy this file, fill in the front-matter, and open it as an issue in the target
repository. The runtime uses the front-matter fields to track the mission
through the WEAVE lifecycle.

## Front-matter fields

| Field | Type | Description |
|---|---|---|
| `mission_id` | string | Unique identifier. Convention: `<repo-slug>-<topic>-<YYYY-MM>`. |
| `target_repo` | string | GitHub repo in `owner/repo` form. Must be a public `its-DeFine` repo. |
| `scope` | string | One-sentence description of the work. No sub-bullets. |
| `acceptance_criteria` | list of strings | Deterministic, verifiable checklist. Each item must be checkable by CI or a script — no subjective judgement. |
| `compute_budget_minutes` | integer | Maximum agent-runtime minutes allowed. Hard ceiling enforced by the runtime. |
| `credit_reward` | integer | Credits granted on verified completion. Set relative to scope and compute saved. |
| `value_to_org` | string | One sentence on the concrete, measurable outcome for WEAVE. |
| `why_compute_conserving` | string | Explain why this mission saves more compute than it spends over time. |

## Rules

- `target_repo` must be a public `its-DeFine` repository.
- `acceptance_criteria` items must be deterministic. "Tests pass" is acceptable. "Looks good" is not.
- `compute_budget_minutes` must be set. The runtime rejects missions without a ceiling.
- Duplicate detection: the runtime refuses a new mission if an open mission with the same `target_repo` and overlapping `scope` already exists.

---

## Worked Example

```yaml
---
mission_id: weave-primitive-example-2026-05
target_repo: its-DeFine/weave
scope: Add a worked example for the blur-background primitive to the weave-tool package.
acceptance_criteria:
  - docs/examples/blur-background.md exists and renders valid markdown
  - python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool exits 0
  - python3 -m unittest discover -s tests -p 'test_*.py' exits 0
compute_budget_minutes: 30
credit_reward: 10
value_to_org: Lowers the barrier for third-party builders to use the blur-background primitive.
why_compute_conserving: A clear example prevents repeated support questions and agent re-work across multiple sessions.
---
```

### Example mission body

**Scope**

Add a worked example showing how to use the `blur-background` primitive in a
local Hermes session. The example should live at
`docs/examples/blur-background.md` and demonstrate: loading the primitive,
setting the blur radius parameter, and the expected output shape.

**Acceptance evidence required**

- [ ] `docs/examples/blur-background.md` exists and renders valid markdown.
- [ ] `python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool` exits 0.
- [ ] `python3 -m unittest discover -s tests -p 'test_*.py'` exits 0.

**Compute budget:** 30 minutes agent runtime.
**Credit reward:** 10 credits on verified completion.

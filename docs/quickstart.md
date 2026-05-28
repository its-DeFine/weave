# WEAVE Quickstart

Everything here runs locally. No API keys. No network calls. Requires Python 3.9+
and git.

## 1. Clone

```bash
git clone https://github.com/its-DeFine/weave.git
cd weave
```

## 2. Validate the company package

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
```

Expected output:

```text
valid WEAVE company package: weave
version: 2026.05.13-console
agents: 7
tasks: 9
skills: 12
primitives: 9
```

If you see an error, the package is malformed or a required file is missing.
Read the error message — it names the offending file.

## 3. Run the test suite

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

All tests should pass. The suite exercises the package validator and the
lifecycle dependency rules.

## 4. Set up the local runtime profile

```bash
python3 scripts/setup_runtime.py
```

Expected output when Hermes is not installed locally:

```text
runtime setup: profile_written_runtime_binary_missing
profile: runs/runtime-profile.json
runtime: hermes-default
agent: ceo-hermes
network_install_performed: false
service_installed: false
```

The setup command writes an ignored local profile, checks whether Hermes is
already on `PATH`, and preserves OpenClaw as fallback. It does not download
binaries, install services, read secrets, or claim a VM runtime exists. See
[Hermes Runtime Setup](hermes-setup.md).

## 5. Run the runtime smoke

```bash
python3 scripts/runtime_smoke.py
```

Expected output:

```text
WEAVE lifecycle stages:
  1. Intent
  2. Research
  3. Selection
  4. Plan
  5. Engineering
  6. QA
  7. KPI Setup
  8. Marketing
Parallel growth loop:
  A. Iteration
  B. Analysis

valid WEAVE company package: weave
version: 2026.05.13-console
agents: 7
tasks: 9
skills: 12
primitives: 9
runtime setup check: ok
operator-ui smoke: ok
smoke: ok
```

The smoke script prints the lifecycle stages, re-validates the package, and
checks the local Hermes runtime profile contract and the public-safe operator
UI sample. It imports nothing outside the standard library and makes no network
calls.

## 6. Run the operator UI

Serve the local operator console:

```bash
python3 scripts/run_operator_ui.py
```

Then open the printed local URL in a browser. The UI loads
`operator-ui/sample-runtime.json`, shows the Askuno runtime-proof lifecycle, and
shows the public-safe runtime boundary. This is a public-safe local
instantiation path, not a claim that a VM service is installed.

The static console includes an app selector, draft app creation, lifecycle
stage track, runtime-agent message drafts, Plan/Review/Execute cards, blocker
map, evidence binder, open decisions, KPI snapshot, and command preview. All
commands stay as local previews.

To validate the UI files without starting a server:

```bash
python3 scripts/operator_ui_smoke.py
```

Expected output:

```text
operator-ui smoke: ok
```

## 7. Mission format

A WEAVE mission is a markdown file with YAML front-matter. The required fields
are:

| Field | Type | Description |
|---|---|---|
| `mission_id` | string | Unique id. Convention: `<repo>-<topic>-<YYYY-MM>`. |
| `target_repo` | string | `owner/repo` of the public target repository. |
| `scope` | string | One-sentence description of the work. |
| `acceptance_criteria` | list | Deterministic, CI-checkable checklist items. |
| `compute_budget_minutes` | integer | Hard ceiling on agent runtime. |
| `credit_reward` | integer | Credits granted on verified completion. |
| `value_to_org` | string | Concrete, measurable outcome for WEAVE. |
| `why_compute_conserving` | string | Why this mission saves more compute than it spends. |

A full worked example with body text lives at
[docs/missions/MISSION_TEMPLATE.md](missions/MISSION_TEMPLATE.md).

## 8. Lifecycle dry-run

The main lifecycle stages a mission passes through, in order:

```text
Intent -> Research -> Selection -> Plan -> Engineering -> QA -> KPI Setup -> Marketing
```

After KPI Setup, the growth loop runs under Marketing:

```text
Iteration <-> Analysis
```

Stage rules enforced by the package:

- Research starts only after Intent is explicit (`intent-contract` task).
- Selection starts only after Research admits one opportunity (`research-gate`
  task).
- Plan starts only after Selection chooses one wedge (`selection-gate` task).
- Engineering starts only after Plan records the bounded execution path
  (`plan-gate` task).
- QA starts only after Engineering delivers one primitive
  (`engineering-first-primitive` task).
- KPI Setup starts only after QA clears readiness (`qa-runtime-readiness` task).
- Marketing starts only after KPI Setup opens the gate (`kpi-setup-gate` task).
- Iteration and Analysis start locally from KPI Setup and run while Marketing
  gathers evidence (`iteration-from-analytics` task).

To inspect the declared dependency graph:

```bash
python3 - <<'EOF'
import importlib.util, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "v", "packages/weave-tool/scripts/validate_company_package.py"
)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

tasks = v.validate_tasks(Path("packages/weave-tool"))
for t in tasks:
    print(f"{t['slug']:40s}  depends_on={t.get('dependsOn', '-')}")
EOF
```

## Security check

Before committing any changes, scan for accidental secrets:

```bash
python3 scripts/check_no_secrets.py
```

Exits 0 when clean. Exits 1 and prints `path:line:pattern:value` for every hit.

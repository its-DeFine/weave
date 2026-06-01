# WEAVE Quickstart

The base validation path runs locally with no API keys and no network calls.
The optional real-Hermes provisioning step uses outbound network access to fetch
the pinned upstream Hermes source and Python packages. Requires Python 3.9+ and
git.

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
skills: 13
primitives: 9
prompt_packs: 1
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
gateway_setup_required: true
gateway_started: false
network_install_performed: false
service_installed: false
```

The setup command writes an ignored local profile, checks whether Hermes is
already on `PATH`, creates or verifies an ignored local WEAVE root under
`runs/weave-root`, and preserves Local Fallback as fallback. This default command is
offline and does not download binaries, install services, read secrets, or
claim a remote runtime exists. See [Hermes Runtime Setup](hermes-setup.md).

To provision the real pinned Nous Hermes Agent into ignored local state:

```bash
python3 scripts/setup_runtime.py --install-hermes
```

This clones the upstream Hermes repository, checks out the pinned commit,
creates `runs/hermes-agent/venv`, installs the CLI package there, and records
the proof in `runs/hermes-agent/profile.json` plus `runs/runtime-profile.json`.
It still does not start services, run the Hermes setup wizard, pair Telegram,
or load credentials. It requires outbound access to GitHub and the Python
package registry.

The same setup path creates the ignored WEAVE root and a generated Hermes
gateway workdir. Use the printed `foundation_gateway_workdir` as the gateway
working directory; it contains the active onboarding `AGENTS.md` and `SOUL.md`
that force Hermes to ask the missing foundation questions through Telegram
before app work. When gateway flags are supplied, setup also writes Hermes
`terminal.cwd` and a runtime system prompt so gateway sessions load this context.

For Telegram, install Hermes with the messaging extra first:

```bash
python3 scripts/setup_runtime.py --install-hermes --require-runtime-binary --hermes-extras cli,messaging
```

Then configure the gateway from an owner-approved token file. Use an allowlist
when the numeric Telegram user id is known:

```bash
python3 scripts/setup_runtime.py \
  --install-hermes \
  --require-runtime-binary \
  --hermes-extras cli,messaging \
  --gateway-token-file <owner-approved-token-file> \
  --gateway-allowed-users <numeric-telegram-user-id>
```

Temporary discovery mode is available only long enough to capture the owner id:

```bash
python3 scripts/setup_runtime.py \
  --gateway-token-file <owner-approved-token-file> \
  --gateway-allow-all-users
```

The helper writes only local Hermes environment state, redacts the token from
output, configures the generated foundation gateway context, and does not start
the gateway. With one allowed Telegram user and no explicit home channel, it
also sets that direct chat as the home channel. After setup, verify with
`hermes status`, `hermes gateway status`, and a foreground
`hermes gateway run` started from the generated foundation gateway workdir.

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
skills: 13
primitives: 9
prompt_packs: 1
runtime setup check: ok
Hermes provisioner check: ok
runtime first-slice check: ok
telegram command smoke: ok
smoke: ok
```

The smoke script prints the lifecycle stages, re-validates the package, and
checks the local Hermes runtime profile contract, source-only Hermes
provisioner contract, first-slice root/app/ledger contract, REST dispatch
skeleton, and deterministic Telegram slash-command output. It imports nothing
outside the standard library and makes no network calls.

## 6. Inspect status from Telegram commands

Optional: start the local REST skeleton first:

```bash
python3 scripts/weave_runtime_api.py
```

It binds to loopback, reads the ignored local WEAVE root, and requires the
generated local bearer token. It exposes health, runtime status, apps, app
state, events, artifacts, contract diff, and procedure feedback endpoints. It
does not claim real Hermes execution.

Telegram is the status surface for this release. Normal messages go to Hermes.
Slash commands are intercepted by the gateway and answered from deterministic
local runtime state:

```text
/status
/apps
/app <app_id>
/blockers
/changes [app_id]
/next
```

The response contract is `schema: weave-telegram-command/v0.1`,
`deterministic: true`, and `llm_used: false`. See
[Telegram Slash Commands](telegram-slash-commands.md) for the full command
list and examples.

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

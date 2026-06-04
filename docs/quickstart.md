# WEAVE Quickstart

The base validation path runs locally with no API keys and no network calls.
Guided onboarding uses Docker to build a pinned Hermes runtime container from
the public repository Dockerfile. Requires Python 3.9+, git, and Docker for the
default runtime path.

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

## 4. Run guided onboarding

```bash
bin/weave onboard
```

Expected shape:

```text
+--------------------------------------------------+
| WEAVE Onboarding                                 |
| Hermes + Telegram runtime setup                  |
+--------------------------------------------------+

Step 1/6  Runtime
  [ok] Docker available
  building image: weave-hermes-runtime:local
  [ok] Hermes image ready: weave-hermes-runtime:local
  [ok] runtime home ready: runs/runtime-home
  [ok] WEAVE root ready: runs/runtime-home/weave-state

Step 2/6  Provider
  Hermes chat needs a verified model provider before normal messages can work.
  Fast path, if you use Nous Portal:
    HERMES_HOME=runs/runtime-home/hermes-home hermes setup --portal
  Alternative provider/model picker:
    HERMES_HOME=runs/runtime-home/hermes-home hermes model
  Then verify with:
    weave provider verify

Step 3/6  Telegram
  Create a dedicated Telegram bot with BotFather.
  Telegram steps:
    1. Open Telegram and search for BotFather.
    2. Send /newbot.
    3. Choose a bot display name for this WEAVE runtime.
    4. Choose a bot username ending in bot.
    5. Copy the token BotFather shows; keep it private.
    6. Return here and paste the token at the hidden prompt.
  WEAVE will hide token input and will not print it back.
```

The guided command builds the pinned Hermes container image, writes an ignored
local profile, creates or verifies `runs/runtime-home`, creates
`runs/runtime-home/weave-state`, creates the generated Hermes gateway workdir,
requires verified Hermes provider auth before normal chat, asks for a dedicated
Telegram bot token, hides token input, and writes only local Hermes environment
state. It does not start the gateway, install autostart, contact Telegram, send
messages, or place secrets in tracked files.

WEAVE does not own OAuth or API-key entry. Configure providers through Hermes,
then record a tiny non-secret canary:

```bash
HERMES_HOME=runs/runtime-home/hermes-home hermes setup --portal
bin/weave provider verify
```

If you only want deterministic Telegram commands for setup/QA, make that
explicit:

```bash
bin/weave onboard --slash-only
```

To preview the flow without entering a token:

```bash
bin/weave onboard --dry-run
```

After onboarding, run the gateway in the container:

```bash
bin/weave start
bin/weave status
bin/weave stop
```

`weave start` launches a Docker container with the local WEAVE root, Hermes
home, and repository mounted in. Docker's `unless-stopped` restart policy makes
the gateway restartable without installing host startup services.

Inspect the durable local state even when the gateway is not running:

```bash
bin/weave status
bin/weave provider status
```

Move reviewable runtime state to another machine or folder without exporting
gateway credentials:

```bash
bin/weave export-runtime --out runtime-export.tar.gz
bin/weave import-runtime runtime-export.tar.gz --runtime-home runs/runtime-home
bin/weave verify-runtime --runtime-home runs/runtime-home
```

After import, `verify-runtime` reports `secret_relink_required: true` until the
Telegram gateway credentials are intentionally linked in the new environment.
Provider auth readiness is also shown; normal chat stays blocked until Hermes
provider auth is reverified or slash-only mode is explicitly selected.

For a host-local fallback instead of the default container:

```bash
bin/weave onboard --local --install-hermes
```

This uses outbound access to GitHub and the Python package registry, then keeps
the installed Hermes state under ignored local runtime paths. It still does not
start the gateway or install autostart.

For CI or scripted setup, use the backend command directly:

```bash
python3 scripts/setup_runtime.py \
  --gateway-token-file <owner-approved-token-file> \
  --gateway-allowed-users <numeric-telegram-user-id>
```

The same setup path creates the ignored WEAVE root and a generated Hermes
gateway workdir. Use the printed `foundation_gateway_workdir` as the gateway
working directory; it contains the active onboarding `AGENTS.md` and `SOUL.md`
that force Hermes to ask the missing foundation questions through Telegram
before app work. When gateway flags are supplied, setup also writes Hermes
`terminal.cwd` and a runtime system prompt so gateway sessions load this context.

Temporary discovery mode is available only long enough to capture the owner id:

```bash
python3 scripts/setup_runtime.py \
  --gateway-token-file <owner-approved-token-file> \
  --gateway-allow-all-users
```

The helper writes only local Hermes environment state, redacts the token from
output, configures the generated foundation gateway context, and does not start
the gateway. With one allowed Telegram user and no explicit home channel, it
also sets that direct chat as the home channel. After guided container
onboarding, verify with `bin/weave status`; for host-local fallback, verify
with `hermes status`, `hermes gateway status`, and a foreground
`hermes gateway run` started from the generated foundation gateway workdir.

Gateway setup defaults to `--autonomy-mode yolo`. That mode removes routine
confirmation prompts for non-gated local work. Hermes must still ask the owner
through the Telegram LLM conversation before secrets, auth changes, public
sends, paid or metered work, production/service changes, or destructive work.

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
container runtime profile check: ok
Hermes provisioner check: ok
runtime first-slice check: ok
telegram command smoke: ok
runtime migration CLI check: ok
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
/sources
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

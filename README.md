## Codex First Contact: COS WEAVE

Trigger:

```text
Use this repo as COS WEAVE: <repo URL or local path>
```

Launch modes:

- **Repo-scoped/local Codex thread:** the short trigger is enough because this
  repository's `AGENTS.md` and root docs are already loaded before first
  response.
- **Projectless remote-URL Codex thread:** paste the tiny launcher in
  [COS_WEAVE_LAUNCHER.md](COS_WEAVE_LAUNCHER.md). A remote URL alone cannot
  deterministically change the first progress message before the agent has
  opened the repository.

If the user gives that trigger with ordinary app intent, your first meaningful
response must begin with this state line, before any execution packet or
generic task framing:

```text
WEAVE | Home=<repo>/runs/cos-weave-home | App=<app-or-pending> | Stage=<stage> | Scope=local-file-skeleton | State=<state> | Next=<next action>
```

Do not start with `Execution packet`, `I will treat this as`, or generic Codex
implementation-task language. If a scope/stop-boundary packet is required by
your host instructions, put it after the WEAVE state line and make it
WEAVE-shaped. COS WEAVE is one Chief-of-Staff chat using this repo as a visible
file/folder skeleton for app intent, lifecycle, todos, worker packets, proof,
blockers, review, and readback. Default first-contact scope is local files
only; no user commands, manual lifecycle classification, hidden orchestration,
deploys, public sends, billing, credentials, tracker mutation, or secrets.

See [COS_WEAVE_FIRST_CONTACT.md](COS_WEAVE_FIRST_CONTACT.md) and
[docs/COS_WEAVE_BOOTSTRAP.md](docs/COS_WEAVE_BOOTSTRAP.md).

# WEAVE

![WEAVE repo skeleton hero](assets/weave-hero.png)

WEAVE vNext is one COS WEAVE chat plus a repo-owned file/folder skeleton for
building and operating applications through lifecycle state, todos, worker
packets, proof, blockers, review, and readback.

## Quickstart

For the default product path, a normal user creates a Codex thread and pastes:

```text
Use this repo as COS WEAVE: <repo URL or local path>. I want to build a tiny local app.
```

If that thread is projectless and the repo is only a remote URL, use the
launcher prompt in [COS_WEAVE_LAUNCHER.md](COS_WEAVE_LAUNCHER.md) so the agent
reads this repo before its first progress update.

The agent opens or clones this repo, starts with the WEAVE state line, and
creates or loads `runs/cos-weave-home/`. The user should not run commands,
choose a deployment mode, classify lifecycle stages, create folders, use an
orchestration backend, or understand runtime internals before onboarding.

Developer validation commands and older runtime surfaces are optional after the
file skeleton exists; they are not the default first-contact UX.

## Prompt-First COS WEAVE

If you are a Codex agent and the user gives you this repository to become COS
WEAVE, start here: [docs/COS_WEAVE_BOOTSTRAP.md](docs/COS_WEAVE_BOOTSTRAP.md).
For the compound-engineering proof bar behind this prompt-first flow, read
[docs/COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md](docs/COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md).

The intended user prompt is one line:

```text
Use this repo as COS WEAVE: <WEAVE repo URL or local path>. Help me move my app forward.
```

The agent should open or clone the repo, read the bootstrap instructions, create
or load local WEAVE state, ask onboarding questions in normal language, infer
lifecycle stage from user intent, record app/application state in visible files,
and report proof/readback. The user should not need to run commands, create
folders, classify lifecycle stages, or understand hidden orchestration.

## Default File-Skeleton State

The default COS WEAVE source of truth is visible files:

```text
runs/cos-weave-home/
  owner-profile.md
  owner-profile.json
  apps/
    registry.json
    <app-id>/
      intent.md
      intent.json
      lifecycle.json
      todos.md
      worker-packets/
      proof/
      blockers/
      review/
      updates/readback.json
  inbox/review-queue.json
  updates/readback.json
```

Missing owner preferences are draft todos/questions, not a hard gate for safe
local planning. Completion claims must go through observe, validate, govern,
review, and sync before readback says they are accepted.

## Optional Developer Validation

These commands are for repo developers after the default file skeleton is clear.
They are not the user-facing first-run path:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/runtime_smoke.py
python3 scripts/check_no_secrets.py
```

## Advanced/Legacy Runtime And TUI Surfaces

The older TUI, Hermes, runtime, deployment, gateway, and orchestration-adapter
surfaces are advanced or historical integration paths. They must not be used as
the default first-contact behavior. Start with the COS WEAVE file skeleton
above, then use these only when explicitly needed for a bounded developer proof
or later runtime integration.

Optional advanced commands include:

```bash
bin/weave help
bin/weave doctor
bin/weave eval --list
bin/weave tui --executor codex --scripted-demo --write --no-color
bin/weave tui --executor fixture --scripted-demo --write --no-color
bin/weave first-run --app-id demo-app --app-name "Demo App"
bin/weave early-lifecycle --app-id demo-app --app-name "Demo App" --create-app --write
bin/weave engineering-decisions --app-id demo-app --hard-boundary production_deploy --write
bin/weave qa-proof --app-id demo-app --surface mixed --create-app --write
bin/weave launch-ops --app-id demo-app --create-app --write
bin/weave onboard --dry-run
bin/weave command /status
python3 scripts/full_conversation_app_dogfood.py --help
python3 scripts/private_app_operating_profile_eval.py --list
```

Optional runtime modes include managed container, existing runtime attach,
slash-only deterministic mode, and host-local fallback. These are not
preconditions for prompt-first COS WEAVE app intake.

The TUI is an older operator cockpit surface. In interactive mode it
opens a resumable lifecycle cockpit with an action card, stage choices,
navigation, review queue, artifact/file panes, stage feedback, and
file-specific feedback. In a terminal it stays in a `weave>` command loop; use
`--once` for a single frame or `--loop` to force the loop in tests. The main
commands are `status`, `stages`, `artifacts`, `files`, `reviews`, `help`,
`resume`, `open <ref>`, `f <feedback>`, `p <file> <feedback>`, and `g`/`run`
to invoke the local lifecycle executor through QA. In `--scripted-demo --write`
mode it still
writes the local first-run, Intent/Research/Selection/Plan, Engineering, real
generated app source, real local QA, SEO for website surfaces, the lifecycle QA
bundle, and gated deployment/KPI/marketing/iteration artifacts. Use
`--executor codex` for the strict product path: WEAVE invokes `codex exec`
non-interactively, requires generated source files, and fails if Codex or QA
fails. Use `--executor fixture` only for no-network CI/local deterministic
proofs; fixture output is labeled as not live Codex model output. It stops
before credentials, deployment, public sends, paid spend, and raw secret
handling. By default, Engineering records command hard gates as pending and lets
QA run as a labeled local rehearsal; pass `--run-engineering-gates` when you
want formal Engineering approval before QA.

## Version

Current public package version: `2026.05.13-console`.
Intended release tag: `v2026.05.13-console`.

## Missions

A WEAVE mission is a scoped unit of work dispatched to an agent, tracked
through the lifecycle plus the post-KPI growth loop, and settled with a credit
grant on verified completion. See
[docs/missions/MISSION_TEMPLATE.md](docs/missions/MISSION_TEMPLATE.md) for the
mission format, required fields, and a worked example.

The current vNext product shape is deliberately narrow:

- WEAVE is a standalone repository skeleton.
- The default surface is one COS WEAVE chat plus visible local files under
  `runs/cos-weave-home/`.
- Each app has file-browsable intent, lifecycle, todos, worker packets, proof,
  blockers, review decisions, and readback.
- Older runtime, TUI, gateway, deployment, and external-orchestration material is
  retained only as advanced or historical developer proof.

## Repository Layout

```text
docs/                  Public docs, COS bootstrap, skeleton contracts, and legacy references.
packages/weave-tool/   WEAVE package, skills, lifecycle primitives, and legacy helpers.
scripts/               Local validation, skeleton helpers, smoke, and legacy runtime scripts.
tests/                 Public-safe validation tests.
```

## Validate

Validate the WEAVE company package:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
```

Run the public-safe test suite:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Run the lifecycle and deterministic Telegram command smoke:

```bash
python3 scripts/runtime_smoke.py
```

Inspect lifecycle eval contracts and generate an evidence-bound review template:

```bash
bin/weave eval --list
bin/weave eval engineering --review-template
```

Run release-readiness gates before push or release:

```bash
bin/weave eval release-readiness --run-gates --review-file release-review.json
```

See [docs/lifecycle-evals.md](docs/lifecycle-evals.md) for the stage contract
model: deterministic hard gates, rubric scoring, evidence requirements, and
explicit advance/block decisions.

Before opening or merging a PR, record the issue, proof commands, proof
boundaries, and merge criteria in the PR body. See
[docs/pr-proof-ledger.md](docs/pr-proof-ledger.md).

## Optional Legacy Conversation-To-App Workflow

The fastest way to try the full app-production loop without Telegram, provider
keys, hosting, analytics, payments, or public side effects is the dedicated
scripted dogfood runner:

```bash
mkdir -p runs/full-conversation-app-dogfood
python3 scripts/full_conversation_app_dogfood.py \
  --report-out runs/full-conversation-app-dogfood/report.json \
  --output-dir runs/full-conversation-app-dogfood/artifacts \
  --transcript-out runs/full-conversation-app-dogfood/transcript.md
```

What it does:

- creates an isolated local WEAVE root;
- creates the `Pocket Orchard` app workspace;
- walks Intent, Research, Selection, Plan, Engineering, QA, Deployment, KPI Setup,
  Marketing, Iteration, and Analysis;
- generates a dependency-free static app under
  `runs/full-conversation-app-dogfood/artifacts/generated-app/`;
- exports conversation review artifacts and a JSON run report;
- records explicit non-claims so local scripted proof is not mistaken for live
  Hermes/Telegram proof.

Inspect the generated app by opening
`runs/full-conversation-app-dogfood/artifacts/generated-app/index.html` in a
browser, or serve that generated-app directory with any local static-file server.
For the committed review artifact and proof boundary, see
[docs/month1/full-conversation-app-dogfood.md](docs/month1/full-conversation-app-dogfood.md).

## Optional Legacy Private App Operating-Profile Evaluations

To test WEAVE's operating-profile model across several private, non-public app
scenarios in parallel, run:

```bash
mkdir -p runs/private-app-operating-profile-evals
python3 scripts/private_app_operating_profile_eval.py \
  --output-dir runs/private-app-operating-profile-evals/artifacts \
  --report-out runs/private-app-operating-profile-evals/report.md \
  --parallel 4 \
  --force
```

`--force` is guarded. It only removes an empty output directory, a root already
marked by this harness with `.weave-private-app-eval-output-root`, or an
explicitly named temporary eval root. Use a fresh `runs/...` directory when in
doubt; do not point it at hand-authored docs or workspaces.

The harness generates ten local-only static apps, one assessment report per app,
and an aggregate report. Its target proof surface is `local deterministic
private-app fixture with generated static apps and reviewable framework-gate
evidence`. Each app includes concrete cognitive artifacts:
intent frame, profile selection, CWA work-domain model, DMN decision table, IBIS
issue map, ADR, action intent/result, and PROV ledger. It intentionally excludes
marketing, hosting, analytics, payments, external sends, live Hermes, and
Telegram/deployed-gateway proof.

The committed generated private-app bundle under
`docs/month1/artifacts/private-app-operating-profile-evals/` is sample review
evidence, not a canonical byte-for-byte fixture. Regenerated artifacts may differ
by timestamps and run hashes/checksums; reviewers should compare schemas, gates,
non-claims, and proof-boundary fields rather than raw bytes. See
[docs/month1/private-app-operating-profile-evals.md](docs/month1/private-app-operating-profile-evals.md).

## Advanced Legacy Runtime Onboarding

This section is not the default COS WEAVE vNext path. Use it only for bounded
developer validation of older runtime, gateway, Telegram, and TUI integration
surfaces after the file skeleton path is already established.

Run guided onboarding:

```bash
bin/weave onboard
```

Inspect first if you are unsure what is missing:

```bash
bin/weave help
bin/weave doctor
bin/weave onboard --dry-run
```

The guided command first checks whether normal Hermes setup has already been
confirmed. After that gate passes, it builds a pinned Hermes container, creates
the ignored `runs/runtime-home` layout, prepares the Hermes gateway context,
explains the dedicated Telegram bot requirement, hides token input, and
configures the deterministic command plugin without printing secrets. It does
not start the gateway, install autostart, or perform external sends.

If Hermes already exists and can chat, attach WEAVE to that runtime instead of
installing or provisioning Hermes:

```bash
bin/weave onboard --existing-hermes --hermes-ready
# equivalent convenience alias:
bin/weave attach-hermes --hermes-ready
```

Existing-Hermes attach still creates the deterministic WEAVE layer:
`runtime-profile.json`, `weave-state/`, source map, app state, foundation
onboarding files, and the `weave-runtime` Hermes plugin/config. It does not
install Hermes, mutate provider credentials, install a service, start a gateway,
or configure autostart.

Normal Hermes chat is owned by Hermes. Configure providers and verify chat
through the normal Hermes setup flow first, then tell WEAVE that Hermes is
ready:

```bash
HERMES_HOME=runs/runtime-home/hermes-home hermes setup --portal
HERMES_HOME=runs/runtime-home/hermes-home hermes model
bin/weave onboard --hermes-ready
```

To complete setup for deterministic slash commands only, use:

```bash
bin/weave onboard --slash-only
```

After onboarding, run the containerized gateway:

```bash
bin/weave start
bin/weave dashboard
bin/weave status
bin/weave stop
```

Use the read-only TUI operator console before or after the gateway starts to see
the older runtime flow in one place: onboarding, runtime readiness, Hermes
setup, gateway attachment, app portfolio, lifecycle stage, transcript capture,
proof/eval state, inconsistencies, and the next deterministic action. It does
not send messages or start services.

Move reviewable local state without exporting credentials:

```bash
bin/weave export-runtime --out runtime-export.tar.gz
bin/weave import-runtime runtime-export.tar.gz --runtime-home runs/runtime-home
bin/weave verify-runtime --runtime-home runs/runtime-home
```

For a host-local fallback instead of the default container, install the real
pinned upstream Hermes Agent into ignored local state:

```bash
bin/weave onboard --local --install-hermes
```

For CI and operator automation, the backend script remains available:

```bash
python3 scripts/setup_runtime.py \
  --gateway-token-file <owner-approved-token-file> \
  --gateway-allowed-users <numeric-telegram-user-id>
```

Gateway setup defaults to `--autonomy-mode yolo`. In this mode Hermes proceeds
without routine confirmation for non-gated local work, while hard-gated actions
still require Hermes to ask for owner authorization through the Telegram LLM
conversation before acting.

Validate the public-safe workstation context sync sample:

```bash
python3 scripts/context_sync_contract_smoke.py
```

Expected package shape:

```text
valid WEAVE company package: weave
version: 2026.05.13-console
agents: 7
tasks: 10
skills: 13
primitives: 9
prompt_packs: 1
eval_contracts: 12
```

## Advanced Legacy Runtime Model

This model is retained for historical and optional integration work. It is not
the default first-contact product path.

WEAVE is packaged as an importable AI-operated company:

```text
WEAVE repo
  -> packages/weave-tool
  -> Hermes CEO/runtime agent
  -> WEAVE lifecycle tasks, skills, and primitives
  -> deterministic Telegram slash commands for state
```

The durable state lives in a runtime home:

```text
runs/runtime-home/
  runtime-profile.json
  weave-state/
  hermes-home/
```

The container and gateway process are replaceable. App work, lifecycle
artifacts, ledgers, profiles, source maps, and reviewable Hermes configuration
live in the runtime home. Raw gateway secrets are not exported by default.

The first-slice REST skeleton can be served locally with:

```bash
python3 scripts/weave_runtime_api.py
```

It binds to loopback, requires the ignored generated local token, and delegates
to the same root, app, ledger, foundation, and stage-derivation primitives used
by the tests.

The operational HTTP wrapper (`scripts/weave_runtime_http.py`) also binds to the
loopback interface by default. It requires bearer auth using the generated
ignored token at `<weave-root>/runtime/tokens/local-api-token` unless started
with the explicit test/dev flag `--allow-unauthenticated-local`. Its `/health`
response reports `transport.auth_policy` so the running service tells the truth
about exposure.

This proves a local instantiation path for the lifecycle runtime. It does not
claim that a VM service, hosted runtime, paid model route, or production
deployment is installed.

Telegram is the operator surface for the legacy runtime path. Normal Telegram
messages go to Hermes only after normal Hermes setup has been confirmed. WEAVE slash
commands are intercepted by the gateway and answered from deterministic local
runtime state with `deterministic: true` and `llm_used: false`.

Available commands are split by side effect:

| Command | Side effect | Purpose |
|---|---|---|
| `/start` | Read-only | Show the deterministic WEAVE command surface. |
| `/help` | Read-only | List deterministic WEAVE commands. |
| `/autonomy` | Read-only | Show autonomy mode and hard approval gates. |
| `/status [app_id]` | Read-only | Show the WEAVE wall or one app wall. |
| `/sources` | Read-only | Show runtime source map, history surfaces, and active/stale/missing state. |
| `/apps [--all]` | Read-only | List apps, lifecycle stage per app, and attention state. |
| `/app <app_id>` | Read-only | Show one app wall. |
| `/lifecycle [app_id]` | Read-only | Show lifecycle gate state. |
| `/stage [app_id]` | Read-only | Show current lifecycle stage state. |
| `/requirements [app_id]` | Read-only | Show current-stage requirements and missing inputs. |
| `/blockers` | Read-only | Show apps that need owner or Hermes action. |
| `/changes [app_id]` | Read-only | Show latest recorded changes for one app or all apps. |
| `/transcript [app_id]` | Read-only | Show recent captured conversation turns. |
| `/next` | Read-only | Show the next deterministic owner-visible action. |
| `/create_app <name>` | Local state-changing | Create and select a product app workspace. |
| `/switch_app <app_id>` | Local state-changing | Select the active Telegram app. |
| `/approve_stage [app_id] [stage]` | Local state-changing | Record owner approval after gates pass. |
| `/advance [app_id]` | Local state-changing | Advance after the current stage is owner-approved. |

See [docs/telegram-slash-commands.md](docs/telegram-slash-commands.md) for the
full command contract and response shape.

Hermes carries a public prompt/spec package at
`packages/weave-tool/prompts/hermes-gestalt-runtime-pack/`. That pack is the
reviewable contract for moving a user from raw app idea to Gestalt Kernel,
Gestaltian Contract, Premortem, Build-Ready Handoff Packet, bounded
implementation, validation, and Contract Update.

Use `bin/weave onboard` for the human setup flow. In managed-container mode
after Hermes readiness is confirmed, it builds a local Docker image from
`container/hermes/Dockerfile` at pinned upstream Hermes commit
`5921d667855880b0aa2083a50f001748aed52f3e`, then records the image in
`runs/runtime-home/runtime-profile.json`. Existing-Hermes attach, slash-only
deterministic mode, and host-local fallback do not require that image. Use
`scripts/setup_runtime.py` for automation, CI, and non-interactive runtime
profiles. Add `--local --install-hermes` to clone the real upstream Nous Hermes
Agent into an isolated venv under
`runs/hermes-agent/`, install the CLI package there, and attach that proof to
the runtime profile. These install paths use outbound network access, but they
do not install services, read secrets outside the explicit Telegram token flow,
contact private gateways, pair Telegram without owner input, or claim that a
hosted runtime exists.

For Telegram, guided onboarding asks for a dedicated bot token and numeric
Telegram user id. Token input is hidden and copied only into local Hermes
environment state. Provider credentials and route verification stay inside
Hermes; WEAVE records only non-secret setup readiness state with
`bin/weave hermes status`. It does not start the gateway, install autostart, or
place secrets in tracked files and public artifacts. The narrower
`scripts/setup_gateway.py` helper is available when Hermes is already
installed and only gateway environment configuration is needed.

The public workstation context sync contract in
`docs/workstation-context-sync.md` shows how completed local work can be
recorded into a runtime ledger as evidence and decisions. The included sample
uses public-safe paths only and performs no network writes.

The main lifecycle is:

1. Intent.
2. Research.
3. Selection.
4. Plan.
5. Engineering.
6. QA.
7. Deployment.
8. KPI Setup.
9. Marketing.

After deployment and KPI Setup, the growth loop can run under Marketing:

- Iteration: build, deploy, and record feedback-driven changes.
- Analysis: read usage and feedback, then recommend the next iteration.

Research starts only after Intent is explicit. Engineering starts only after
Selection and Plan are recorded. Deployment starts only after QA has reviewable
proof. KPI Setup reads deployment reality before measurement is finalized.
Marketing and the local growth loop both start from KPI Setup; external
distribution remains approval-gated.

## Boundaries

This repository intentionally does not include:

- private WEAVE operating substrate
- private payment, custody, funding, or accounting material
- VM, SSH, VPN, private-network, or host-specific proof details
- API keys, gateway tokens, OAuth tokens, private keys, or seed material
- generated private proof logs
- claims that Livepeer-native output is proven before output evidence exists

## Replication

Start with [WEAVE Replication Architecture](docs/replication-architecture.md).

## License

MIT. See [LICENSE](LICENSE).

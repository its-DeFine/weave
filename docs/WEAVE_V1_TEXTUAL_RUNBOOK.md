# WEAVE v1 Textual Runbook

This runbook is for local operator use. It does not authorize credentials,
deployment, public sends, paid spend, or external account mutation.

## Install

macOS system Python may reject global package installs. Use a local venv:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

`bin/weave` automatically uses `.venv/bin/python` when it exists, and falls back
to `python3` otherwise.

## Launch

```sh
bin/weave tui --textual \
  --app-id launch-studio \
  --app-name "Launch Studio" \
  --executor codex \
  --control-mode handoff \
  --intent "Build a launch readiness cockpit for a founder to review lifecycle status, risks, QA, SEO, and launch boundaries."
```

If Textual is not installed, the command prints the install path instead of
falling back silently to the old plain renderer.

Textual is the visual product surface. Unless `--no-color` is explicitly
provided, WEAVE forces a color-capable terminal environment for Textual runs and
proof captures so automation shells with `NO_COLOR=1` or `TERM=dumb` do not
turn the cockpit into a gray diagnostic panel.

## Operator Flow

1. Open `First Run`: use mouse click or focus the lifecycle rail with arrows and
   press Enter.
2. Create app: creates or loads the local WEAVE app workspace.
3. Save setup: writes owner/app foundation context required by the runtime gate.
4. Move through lifecycle screens: `First Run`, `Owner Profile`, `App
   Workspace`, `Intent`, `Research`, `Selection`, `Plan`, `Engineering`, and
   `QA` are separate guided screens. `Deployment`, `KPI`, `Marketing`,
   `Iteration`, and `Analysis` are gated planning screens.
5. Prepare prompt: assembles a prompt packet from global prelude, owner profile,
   world model, stage prompt, artifacts, feedback, outputs, and stop boundaries.
6. Run Codex: invokes the local Codex CLI for Engineering, writes executor and
   source manifests, and records an honest failure manifest if Codex is missing
   or fails. The TUI shows a running state and elapsed time while this happens.
7. Submit stage: writes the owner-reviewable stage proof artifact and a linked
   transcript turn.
8. Evaluate: completes the local stage evaluation. Engineering and QA command
   gates run when `--run-engineering-gates` is provided; otherwise the runtime
   records that hard gates are still pending and blocks final approval.
9. Approve: calls the existing runtime approval gate.
10. Advance: moves to the next lifecycle stage only after approval.

## Proof Commands

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/runtime_smoke.py
python3 scripts/public_safe_repo_scan.py
python3 scripts/check_no_secrets.py
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
git diff --check
```

With Textual installed:

```sh
.venv/bin/python -m unittest tests.test_weave_textual_app
.venv/bin/python scripts/capture_weave_textual_screens.py
.venv/bin/python scripts/weave_v1_textual_dogfood.py --clean --codex-timeout 240
```

SVG proof screens are written to:

```text
docs/ux/weave-v1-textual-proof/
docs/ux/weave-v1-textual-dogfood/
```

The full Textual dogfood report is written to:

```text
docs/proof/weave-v1-textual-dogfood.json
```

The dogfood recording must include all operator views:

```text
overview, stages, artifacts, files, reviews, help, resume
```

It must also include all service-blueprint routes:

```text
first_run, owner_profile, app, intent, research, selection, plan, engineering,
qa, deployment, kpi, marketing, iteration, analysis
```

## Non-Claims

- WEAVE itself does not need a deployed URL; it is a local Textual TUI product.
- The generated example app may be a website, but this proof stops at local QA.
- This does not capture raw credentials.
- This does not send public messages.
- This does not spend money.
- This does not prove live Telegram/Hermes operation unless a separate live
  runtime proof is executed under an explicit approval packet.

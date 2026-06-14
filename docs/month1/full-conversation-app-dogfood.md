# Full Conversation-To-App Dogfood

Status: local scripted dogfood proof, not live Hermes/Telegram proof

This dogfood exists because a stage-machine rehearsal alone can look successful
while still failing the real question: can the WEAVE process carry an app idea
through conversation, produce a concrete product artifact, and then review the
result honestly from multiple angles?

## What It Runs

From a fresh clone, validate the package and inspect the runner:

```bash
git clone https://github.com/its-DeFine/weave.git
cd weave
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 scripts/full_conversation_app_dogfood.py --help
```

Run the dedicated conversation-to-app dogfood into ignored local `runs/` output:

```bash
mkdir -p runs/full-conversation-app-dogfood
python3 scripts/full_conversation_app_dogfood.py \
  --report-out runs/full-conversation-app-dogfood/report.json \
  --output-dir runs/full-conversation-app-dogfood/artifacts \
  --transcript-out runs/full-conversation-app-dogfood/transcript.md
```

The script uses an isolated local WEAVE root and does not call live Hermes,
Telegram, external providers, hosting, analytics, payments, or public channels.
It generates a proof app called **Pocket Orchard** from a scripted owner/Hermes
conversation.

Inspect the generated app at
`runs/full-conversation-app-dogfood/artifacts/generated-app/index.html`. The
run report, transcript, conversation export, lifecycle artifacts, generated app,
and holistic review stay under `runs/full-conversation-app-dogfood/` unless you
pass different output paths.

The current GitHub-reviewable artifact bundle is committed at
[`artifacts/full-conversation-app-dogfood/`](artifacts/full-conversation-app-dogfood/).
Fresh runs write review artifacts under the operator's local Codex artifact
directory unless `--report-out` or `--output-dir` is supplied.

## Produced App

- App name: Pocket Orchard
- App type: dependency-free static browser app
- Output: editable idea seeds, prioritized daily action plan, JSON export
- External surfaces: analytics disabled, payments disabled, hosting local-only
- Generated files: `index.html`, `src/app.js`, `src/styles.css`,
  `public/config.json`, `README.md`

## Lifecycle Coverage

The dogfood records one owner/Hermes conversation turn for each lifecycle stage:

1. Intent
2. Research
3. Selection
4. Plan
5. Engineering
6. QA
7. KPI Setup
8. Marketing
9. Iteration
10. Analysis

Each stage requires a stage artifact and transcript turn before approval. KPI,
Marketing, and Analysis deliberately introduce missing external credential
requirements and pass only through owner credential deferral.

The GitHub-reviewable scripted transcript is committed at
[`full-conversation-app-dogfood-transcript.md`](full-conversation-app-dogfood-transcript.md).

Each run also exports local runtime conversation artifacts:

- `conversation-review.html`
- `conversation.events.jsonl`
- `conversation-report.json`

The committed review bundle contains:

- [`full-conversation-app-dogfood-report.json`](artifacts/full-conversation-app-dogfood/full-conversation-app-dogfood-report.json)
- [`conversation-review/`](artifacts/full-conversation-app-dogfood/conversation-review/)
- [`generated-app/`](artifacts/full-conversation-app-dogfood/generated-app/)
- [`lifecycle-artifacts/`](artifacts/full-conversation-app-dogfood/lifecycle-artifacts/)
- [`holistic-review.json`](artifacts/full-conversation-app-dogfood/holistic-review.json)

## Latest Verified Local Run

Command used during review:

```bash
python3 -m py_compile scripts/full_conversation_app_dogfood.py \
  && python3 scripts/full_conversation_app_dogfood.py \
    --report-out /tmp/weave-full-conversation-app-dogfood.json \
    --output-dir /tmp/weave-full-conversation-app-dogfood-artifacts \
    --transcript-out docs/month1/full-conversation-app-dogfood-transcript.md
```

Observed result:

- Script result: `full conversation app dogfood: ok (/tmp/weave-full-conversation-app-dogfood.json)`
- Passed: true
- Runtime: isolated local runtime
- Lifecycle stages approved: 10/10
- Final stage: Analysis, approved
- QA checks: 8
- Transcript: 10 turns, 80 events
- Generated app files: 5
- Lifecycle artifact files: 11

Additional browser inspection served the generated app locally and verified that:

- the app renders with a clear hero, idea input panel, and action-plan panel
- default plan rows are visible and readable
- `window.PocketOrchard.exportPlan()` returns schema
  `pocket-orchard-plan/v0.1`
- exported payload keeps `localOnly: true` and `externalActionsEnabled: false`
- browser console reported no JavaScript errors

## Holistic Review

Overall verdict: valuable local dogfood; not live conversational proof.

Strengths:

- Produces a concrete app artifact, not only lifecycle folders.
- Captures a full stage-by-stage transcript linked to proof artifacts.
- Exercises foundation gates, stage gates, owner approval, credential deferral,
  stage advancement, and transcript export from a clean local runtime.
- Keeps external actions blocked by default.
- Writes a holistic review that separates proof from non-proof.

Failure modes found:

- The conversation is scripted. It does not prove live Hermes autonomy,
  adaptive clarification, interruption handling, or recovery from owner
  corrections.
- The stage gate still mostly proves artifact presence, not artifact quality.
  A weak markdown artifact could pass if the reviewer does not inspect it.
- The generated app is useful as a local proof, but it is not market validated,
  deployed, mobile-tested, analytics-backed, or revenue-tested.
- Browser UX is readable and coherent, but still shallow: it has no persistence,
  no real download action for export, no keyboard/accessibility audit beyond
  basic semantic structure, and no responsive device matrix.
- Safety is proven for this script only. Live adapters still need negative tests
  for attempted public sends, deploys, payments, and credential handling.

Best next optimizations:

1. Run the same lifecycle through a live Telegram/Hermes conversation with owner
   interruptions and corrections.
2. Upgrade gates from artifact-presence checks to artifact-quality and behavior
   rubrics.
3. Add browser exploratory QA and responsive/accessibility checks for generated
   apps.
4. Keep release readiness blocked until live runtime proof, hosted beta evidence,
   analytics setup, payment approval, and human review exist.

## Explicit Non-Claims

This proof does **not** claim:

- live Hermes or Telegram conversation occurred
- the app was deployed or publicly released
- analytics, payments, provider credentials, or external sends were used
- real users, market demand, retention, conversion, or revenue were proven

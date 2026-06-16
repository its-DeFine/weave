# WEAVE v1 Completion Matrix

This matrix is evidence for the current implementation state. It should be
updated whenever WEAVE v1 expands from local Textual/Codex proof into live
Hermes, Telegram, deployment, or marketing operations.

| Area | Current state | Proof refs |
| --- | --- | --- |
| Product contract | Written and used as scope reference. | `docs/WEAVE_V1_PRODUCT_CONTRACT.md` |
| Backend architecture | Written and partially implemented as local facade. | `docs/WEAVE_V1_BACKEND_ARCHITECTURE_SPEC.md`, `scripts/weave_backend.py` |
| Agent orchestration spec | Written and implemented for prompt packet assembly. | `docs/WEAVE_V1_AGENT_ORCHESTRATION_SPEC.md`, `scripts/weave_prompt_library.py` |
| Prompt library | Versioned library covers setup, lifecycle, and completion stages with substage prompts. | `prompts/weave/prompt-library.v1.json`, `prompts/weave/global/prelude.v1.md`, `tests/test_weave_prompt_orchestration.py` |
| Prompt packets | Global prelude, owner profile, world model, stage prompt, artifacts, feedback, outputs, gates, and stop boundaries are assembled into saved JSON/Markdown packets. | `scripts/weave_prompt_library.py`, `tests/test_weave_prompt_orchestration.py` |
| Textual TUI | Full-screen Textual cockpit with lifecycle rail, named operator views (`overview`, `stages`, `artifacts`, `files`, `reviews`, `help`, `resume`), work pane, composer, evidence pane, action buttons, persisted resume state, and file/artifact-targeted feedback syntax. | `scripts/weave_textual_app.py`, `docs/ux/weave-v1-textual-proof/*.svg`, `docs/ux/weave-v1-textual-dogfood/*.svg`, `tests/test_weave_textual_app.py` |
| First-run/profile | Textual backend writes public-safe foundation context required by the runtime gate. | `scripts/weave_backend.py`, `tests/test_weave_prompt_orchestration.py` |
| Stage loop | Backend can submit proof artifact, record transcript turn, evaluate, approve, advance, and route stage-specific feedback prompts such as Engineering `file_feedback`. | `scripts/weave_backend.py`, `tests/test_weave_prompt_orchestration.py`, `tests/test_weave_textual_app.py` |
| Codex executor | Backend writes prompt packet, invokes local Codex CLI when present, records executor/source manifests, fails honestly when missing, and records timeout-after-required-files as a warning state instead of hiding partial execution. | `scripts/weave_backend.py`, `tests/test_weave_prompt_orchestration.py` |
| QA and hard gates | Runtime evals and existing gates remain active; Engineering/QA Textual hard gates are explicit through `--run-engineering-gates` and the dogfood proof runs them. | `scripts/weave_textual_app.py`, `scripts/weave_eval.py`, `scripts/weave_v1_textual_dogfood.py` |
| Visual proof | Headless Textual SVG captures and a Textual journey recording are generated from actual TUI frames, including every named operator view. | `scripts/capture_weave_textual_screens.py`, `scripts/weave_v1_textual_dogfood.py`, `docs/ux/weave-v1-textual-proof/`, `docs/ux/weave-v1-textual-dogfood/weave-v1-textual-dogfood-recording.svg` |
| Local dogfood | Fresh v1 backend run and fresh Textual TUI run pass through QA with real Codex execution, file feedback, reopened/resumed QA frame, and all named TUI views captured; existing full conversation and Month 1 product QA scripts also pass. | `scripts/weave_v1_backend_dogfood.py`, `scripts/weave_v1_textual_dogfood.py`, `docs/proof/weave-v1-backend-dogfood.json`, `docs/proof/weave-v1-textual-dogfood.json`, `docs/ux/weave-v1-textual-dogfood/11-resume-qa.svg`, `docs/ux/weave-v1-textual-dogfood/12-view-overview.svg`, `docs/ux/weave-v1-textual-dogfood/18-view-resume.svg`, `scripts/full_conversation_app_dogfood.py`, `scripts/month1_product_app_qa.py` |
| Safety boundary | Public-safe scan, secret scan, package validation, runtime smoke, unit tests, and diff check pass locally. | proof commands in `docs/WEAVE_V1_TEXTUAL_RUNBOOK.md` |

## Current Non-Claims

- Not live Telegram/Hermes gateway proof.
- WEAVE itself is not deployed and does not need a URL; generated app deployment remains out of this local QA proof.
- Not public marketing send proof.
- Not paid advertising proof.
- Not third-party credential/capability proof.
- Not market validation.

## Next Proof Needed For A Larger v1 Claim

1. Add live Hermes/Telegram proof under a separate approval packet if the claim
   expands beyond local Textual operation.
2. Add deployment/KPI/marketing capability adapters only after explicit owner
   approval for those live-effect surfaces.

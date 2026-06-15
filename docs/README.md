# Public Docs Subset

This `docs/` tree is the public documentation subset for WEAVE.

## Current public docs

- [Replication Architecture](replication-architecture.md)
- [WEAVE Quickstart](quickstart.md)
- [Telegram Slash Commands](telegram-slash-commands.md)
- [Lifecycle Evals](lifecycle-evals.md)
- [Lifecycle Artifact Contracts v0.1](lifecycle-artifact-contracts-v0.1.md)
- [Runtime Home Contract](runtime-home.md)
- [Hermes Runtime Setup](hermes-setup.md)
- [Hermes Runtime Handover](hermes-runtime-handover-2026-05-30.md)
- [WEAVE Runtime Architecture Contract v0.1](weave-runtime-architecture-contract-v0.1.md)
- [WEAVE Runtime Story Contract v0.1](weave-runtime-story-contract-v0.1.md)
- [WEAVE Runtime Document Templates v0.1](weave-runtime-document-templates-v0.1.md)
- [WEAVE Runtime Technical Gestalt Contract v0.1](weave-runtime-technical-gestalt-contract-v0.1.md)
- [WEAVE Runtime First Slice Handoff v0.1](weave-runtime-first-slice-handoff-v0.1.md)
- [External Skill Security Review: codex-dynamic-workflows](weave-runtime-external-skill-security-review-2026-05-30.md)
- [WEAVE Runtime One-Shot Implementation Prompt v0.1](weave-runtime-one-shot-implementation-prompt-v0.1.md)
- [WEAVE Capability Context](capability-context.md)
- [WEAVE Capability Broker Contract v0.1](capability-broker-contract-v0.1.md)
- [WEAVE Scheduler Heartbeat Contract v0.1](scheduler-heartbeat-contract-v0.1.md)
- [Month 1 Overview](month1/README.md)
- [Private App Operating Profile Evaluations](month1/private-app-operating-profile-evals.md)
- [Month 1 Review Evidence Pack](month1/review-evidence-pack.md)
- [Month 1 Capability Context Runtime QA](month1/context-runtime-qa.md)
- [Application Lifecycle Summary](month1/app-lifecycle.md)
- [WEAVE Lifecycle Contract v0](month1/weave-lifecycle-contract-v0.md)
- [WEAVE Agent Operating Contract v0](month1/weave-agent-operating-contract-v0.md)
- [Workstation Context Sync](workstation-context-sync.md)
- [Orchestrator Economics](month1/orchestrator-economics.md)
- [Program Transparency](month1/program-transparency.md)

## Proof, dogfood, and runtime workflow map

If you want to run the existing proof and runtime scripts instead of reading the
full docs tree first, start here:

- **Base public-safe validation:** follow [Quickstart](quickstart.md) sections 2,
  3, 8, and 12. The core commands are
  `python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool`,
  `python3 -m unittest discover -s tests -p 'test_*.py'`,
  `python3 scripts/runtime_smoke.py`, and `python3 scripts/check_no_secrets.py`.
- **Conversation-to-app dogfood:** run
  `python3 scripts/full_conversation_app_dogfood.py` from [Quickstart](quickstart.md#5-try-the-full-conversation-to-app-workflow)
  or [Full Conversation-To-App Dogfood](month1/full-conversation-app-dogfood.md).
  It writes local `runs/` artifacts and does not call live Hermes, Telegram,
  providers, hosting, analytics, payments, or public channels.
- **Scripted-user / live-agent runner:** run the fixture-mode scenario in
  [Scripted-User / Live-Agent Runner](month1/scripted-user-live-agent-runner.md)
  with `docs/month1/examples/scripted-user-live-agent-scenario.example.json`.
  Fixture mode is CI-safe proof; Hermes CLI live mode is separate local live-agent
  proof and is not deployed Telegram gateway proof.
- **Local runtime surfaces:** inspect [Runtime Home Contract](runtime-home.md),
  [Telegram Slash Commands](telegram-slash-commands.md), and [Quickstart](quickstart.md#9-inspect-status-from-telegram-commands)
  before starting `python3 scripts/weave_runtime_api.py` or
  `python3 scripts/weave_runtime_http.py`. Both bind to loopback by default and
  the HTTP wrapper requires the generated local bearer token unless explicitly
  started with its test/dev unauthenticated flag.

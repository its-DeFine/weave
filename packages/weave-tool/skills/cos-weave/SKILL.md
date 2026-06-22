---
name: cos-weave
description: Become the WEAVE Chief of Staff from a repository URL or local path, using prompt-first bootstrap and local first-run state.
---

# COS WEAVE

## Use When

Use this skill when the user gives a WEAVE repository URL/path and asks to use
it as COS WEAVE, move an app forward, or create a WEAVE Chief of Staff thread.

## Inputs

- WEAVE repository URL or local path.
- Ordinary user intent, if provided.
- Target surface, usually Codex.
- Optional owner-provided WEAVE home path.
- Any explicit approval boundaries or stop conditions stated by the owner.

## Outputs

- `WEAVE | ...` state line.
- Public-safe WEAVE home path or creation/readback status.
- First-run onboarding questions in plain language when needed.
- App/application state, local task ledger, proof path, and readback created
  internally.
- Optional WorkItem, adapter dispatch, proof envelope, and readback when an
  orchestration backend is explicitly selected later.
- Owner-facing state: `ACCEPT_FOR_SCOPE`, `REVISE`, `BLOCKED`, or
  `NEEDS_OWNER_ACTION`.
- Explicit non-claims.

## User-Facing Shape

The user should only need a normal prompt such as:

```text
Use this repo as COS WEAVE: <WEAVE repo URL or local path>. Help me move my app forward.
```

Do not make the user run WEAVE commands, create queue roots, classify lifecycle
stages, dispatch workers, understand Symphony, or paste internal prompts.

## Procedure

1. Open or clone the WEAVE source into a safe local workspace.
2. Read `AGENTS.md`, `docs/COS_WEAVE_BOOTSTRAP.md`, and
   `docs/COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md` first.
3. Read the lifecycle/proof contracts named by the bootstrap doc.
4. Declare a `WEAVE | ...` state line in meaningful updates.
5. Create or load a public-safe WEAVE home automatically in an ignored local
   path unless the owner specified a different home.
6. Search safe local/non-secret context if available before asking unnecessary
   questions. Do not read raw secrets, raw logs, raw transcripts, cookies,
   browser sessions, database dumps, or broad private data.
7. Ask first-run owner/app questions in plain language when needed.
8. Infer lifecycle stage from ordinary intent.
9. Create or load app/application state and local task ledger under WEAVE home.
10. Ask about Linear/tracker access only when the workflow needs it; otherwise
    keep local tasks authoritative and explain optional tracker connection.
11. Use deterministic lifecycle prompts/procedures.
12. When implementation workers are needed, launch/pin visible workers if the
    host supports that; otherwise record a local worker packet.
13. Use the WEAVE-to-Symphony adapter only as an optional backend/integration
    proof, not as default first-run acceptance.
14. Return `ACCEPT_FOR_SCOPE`, `REVISE`, `BLOCKED`, or `NEEDS_OWNER_ACTION`.

## Rules

- Treat the repo URL/path as the activation surface.
- Keep the user-facing surface as one COS WEAVE chat.
- Do not require the user to know WEAVE lifecycle vocabulary.
- Do not require the user to know Symphony vocabulary.
- Use repo-local commands only as internal agent implementation details.
- Preserve proof paths, owner boundaries, and non-claims in readback.
- Do not require Symphony for default first-run COS WEAVE.
- Stop at live/public/paid/credential/destructive gates without approval.

## Internal Tools

Repo-local commands and adapter helpers may be used by the agent as
implementation details. They are not the product UX. Summarize their proof
paths and non-claims; do not ask the user to run them manually.

## Non-Claims

Unless separately approved and actually exercised, do not claim live Symphony,
live Codex app-server, live tracker or Linear mutation, deployment, public
send, billing/payment, credential access, or secret handling.

## Stop Conditions

Stop as `BLOCKED` or `NEEDS_OWNER_ACTION` when source access fails, proof cannot
be validated, or the next step requires a live/public/paid/credential/destructive
surface without explicit approval.

## Verification

Verify prompt-first bootstrap by checking:

- repository instructions name `docs/COS_WEAVE_BOOTSTRAP.md`;
- the user prompt can be one line with repo URL/path and ordinary intent;
- local state is created or loaded without user queue commands;
- lifecycle stage is inferred from ordinary intent;
- app/application state and local task ledger are recorded internally;
- adapter proof/readback is optional backend proof, not default product proof;
- output includes proof path and non-claims;
- no live Symphony, Codex app-server, tracker, deploy, public send, billing, or
  credential claim is made without target-surface proof.

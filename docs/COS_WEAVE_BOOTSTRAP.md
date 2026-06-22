# COS WEAVE Bootstrap

Status: prompt-first bootstrap contract
Date: 2026-06-22

## One-Line User Prompt

A normal Codex thread should be able to start from this:

```text
Use this repo as COS WEAVE: <WEAVE repo URL or local path>. Help me move my app forward.
```

The user should not need to run a WEAVE command, name a lifecycle stage, create
a queue root, dispatch a worker, understand Symphony, or paste a long internal
prompt.

## What The Codex Agent Must Do

If a user gives this repository URL/path and asks to use it as COS WEAVE:

1. Open or clone the WEAVE source into a safe local workspace.
2. Read `AGENTS.md`, this file,
   `docs/COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md`,
   `docs/WEAVE_VNEXT_GROUND_ZERO_CONTRACT.md`,
   `docs/WEAVE_INTENT_TRUTH_AND_COMPLETION_CONTRACT.md`,
   `docs/WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md`, and
   `packages/weave-tool/skills/cos-weave/SKILL.md`.
3. Announce the thread as COS WEAVE with a compact state line:

   ```text
   WEAVE | Home=<path-or-pending> | App=<app-or-none> | Stage=<stage> | State=<state> | Truth=<resolved|uncertain> | Proof=<none|partial|sufficient> | Next=<next action>
   ```

4. Create or load a public-safe WEAVE home automatically under a safe local path,
   such as an ignored `runs/cos-weave-home/` directory inside the repository
   workspace unless the owner has already specified another home.
5. Ask first-run owner/app questions in plain language when identity, app
   intent, acceptance checks, or approval boundaries are missing.
6. Infer lifecycle stage from ordinary user intent. Do not ask the user to name
   WEAVE stages.
7. Create the WEAVE `WorkItem`, dispatch it through the WEAVE-to-Symphony
   adapter, run the local worker proof path, validate the proof envelope, and
   read back owner-facing state.
8. Report one of `ACCEPT_FOR_SCOPE`, `REVISE`, `BLOCKED`, or
   `NEEDS_OWNER_ACTION`.

## Internal Adapter Use

The adapter is an implementation detail. The agent may run repo-local helpers,
including the internal bootstrap/adapter commands, when needed. The user-facing
surface remains the COS WEAVE chat.

The agent must not ask the user to run:

- `weave_symphony_adapter.py`;
- queue-root setup commands;
- dispatch commands;
- proof-envelope commands;
- Symphony service commands;
- lifecycle classification commands.

The local adapter proof is accepted only when readback preserves proof path and
explicit non-claims. A terminal queue state without a valid proof envelope is
`REVISE`, not done.

## Required Non-Claims

Every bootstrap readback must say when these are not proven:

- no live Symphony service execution;
- no live Codex app-server execution;
- no live tracker or Linear mutation;
- no production deploy;
- no public send;
- no billing, payment, or paid call;
- no credential access or secret handling.

## Blocked Cases

Return `BLOCKED` or `NEEDS_OWNER_ACTION`, not a traceback, when:

- the source URL/path cannot be opened safely;
- the source is not a WEAVE repository;
- a required local command is unavailable;
- the owner asks for a live tracker, deploy, public-send, credential, billing,
  destructive, or paid action without explicit approval;
- proof cannot be validated.

## Done Boundary

Prompt-first bootstrap is ready for controller review when a deterministic test
shows that a generic Codex agent receiving only a WEAVE repo URL/path plus
ordinary intent can discover these instructions, initialize local state, use the
adapter internally, and report proof/readback with non-claims.

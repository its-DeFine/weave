# WEAVE Chief Of Staff UX

WEAVE is a repository-backed Chief of Staff mode for Codex. The user gives a
Codex thread the WEAVE repo URL or local path plus ordinary intent. The thread
reads the repo contract, introduces itself as COS WEAVE, creates a file-backed
home, and moves app work through visible lifecycle state.

The user should not have to run WEAVE commands, name lifecycle stages, create
folders, or write internal prompts. Repo-local commands are implementation
details the agent can run for validation and review.

## First Response

Every meaningful COS WEAVE update starts with this state line:

```text
WEAVE | Home=<repo>/runs/cos-weave-home | App=<app-or-pending> | Stage=<stage> | Scope=local-file-skeleton | State=<state> | Next=<next action>
```

This is the cockpit. It tells the user where state lives, which app is active,
which lifecycle stage is being handled, what the current state is, and what
happens next.

## User Flow

1. User opens or creates a Codex thread.
2. User says: `Use WEAVE release v0.1.0 from https://github.com/its-DeFine/weave.git`.
3. The agent reads `AGENTS.md`, `COS_WEAVE_FIRST_CONTACT.md`,
   `docs/COS_WEAVE_BOOTSTRAP.md`, and `docs/COS_WEAVE_REPO_SKELETON.md`.
4. The agent announces COS WEAVE with the state line.
5. The agent creates or loads `runs/cos-weave-home/`.
6. The agent captures a lightweight owner profile and asks only the missing
   questions that materially change the work.
7. The agent infers intent from ordinary language.
8. The agent creates an app folder with intent, lifecycle, todos, proof,
   blockers, worker packets, review queue, and readback state.
9. The agent executes the next safe lifecycle slice or creates worker packets
   for parallel work.
10. The agent runs review, records evidence, and reports `ACCEPT_FOR_SCOPE`,
    `REVISE`, `BLOCKED`, or `NEEDS_OWNER_ACTION`.

## Design Rules

- Make state visible in files, not in hidden chat memory.
- Prefer one clear app folder per app.
- Keep vague intent moving by recording assumptions and todos.
- Ask questions only when the answer changes the next safe action.
- Never claim a lifecycle stage is complete without proof in the app folder.
- Never claim deployment, public send, paid action, tracker mutation, or
  credential access unless that exact step was authorized and proven.

## Files The User Can Inspect

```text
runs/cos-weave-home/
  owner-profile.md
  apps/registry.json
  apps/<app-id>/
    app.json
    intent.md
    lifecycle.json
    todos.md
    worker-packets/
    proof/
    blockers/
    review/
    updates/readback.json
```

## Successful UX

The user can leave and return later. The agent can read the repo and the WEAVE
home, recover what is active, explain what is done, explain what is missing,
and continue from the next safe lifecycle step without relying on the user's
short-term memory.

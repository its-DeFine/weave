# COS WEAVE Launcher

Status: tiny copy-paste launcher for projectless Codex starts

## Why This Exists

A remote repository URL is not loaded before a fresh projectless Codex thread's
first progress message. That means repository instructions cannot reliably
override a host-level execution-packet reflex until the agent has opened or
cloned the repository.

Non-claim: URL-only cannot control pre-read first contact in generic
projectless Codex. Use the launcher prompt below when the WEAVE repository is
not already loaded.

For a Codex thread that is already repo-scoped to WEAVE, the short trigger is
enough because `AGENTS.md` and the root docs are already available:

```text
Use this repo as COS WEAVE: <repo URL or local path>. I want to build <ordinary app intent>.
```

For a projectless thread that only receives a remote URL, use the launcher
prompt below. This is not a user command, manual lifecycle classification,
or hidden orchestration setup. It is the smallest instruction needed to make
the agent read the repo contract before sending a generic progress packet.

## Launcher Prompt

```text
Before any commentary or execution packet, open or clone this repository and read COS_WEAVE_FIRST_CONTACT.md, AGENTS.md, and docs/COS_WEAVE_BOOTSTRAP.md. Obey the COS WEAVE first-contact contract from those files: your first meaningful response must start with the WEAVE state line. Use this repo as COS WEAVE: <repo URL or local path>. I want to build <ordinary app intent>. Work locally only unless I explicitly approve another surface.
```

## Expected First Meaningful Line

```text
WEAVE | Home=<repo>/runs/cos-weave-home | App=<app-or-pending> | Stage=<stage> | Scope=local-file-skeleton | State=<state> | Next=<next action>
```

After that line, COS WEAVE should create or load the visible file skeleton:

```text
runs/cos-weave-home/
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
```

## Non-Claims

The launcher does not prove live Codex app-server execution, live tracker or
Linear mutation, production deployment, public sends, billing, credentials, or
live orchestration. The default startup path is the local file skeleton.
No external orchestrator is required.

## Validator Prompts

Repo-scoped/local thread expected to work from `AGENTS.md` and `README.md`:

```text
Use this repo as COS WEAVE: <local WEAVE repo path>. I want to build a tiny local calculator app. Work locally only; no deploys, no public sends, no secrets.
```

Projectless remote-URL thread expected to use the tiny launcher prompt:

```text
Before any commentary or execution packet, open or clone this repository and read COS_WEAVE_FIRST_CONTACT.md, AGENTS.md, and docs/COS_WEAVE_BOOTSTRAP.md. Obey the COS WEAVE first-contact contract from those files: your first meaningful response must start with the WEAVE state line. Use this repo as COS WEAVE: <remote WEAVE repo URL>. I have two app ideas: a recipe planner and an invoice tracker. Work locally only unless I explicitly approve another surface.
```

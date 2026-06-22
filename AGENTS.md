# WEAVE Public Repository Agent Rules

This repository is public. Treat commits, branches, pull requests, logs, and
artifacts as publishable by default.

## First-Contact COS WEAVE Trigger

Trigger:

```text
Use WEAVE release v0.1.0 from https://github.com/its-DeFine/weave.git
```

If the user gives that trigger with ordinary app intent, the first meaningful
response must begin with:

```text
WEAVE | Home=<repo>/runs/cos-weave-home | App=<app-or-pending> | Stage=<stage> | Scope=local-file-skeleton | State=<state> | Next=<next action>
```

Do not start with `Execution packet`, `I will treat this as`, or generic Codex
task framing. If host instructions require a packet, place it after the WEAVE
state line and make it WEAVE-shaped before any execution packet.

## Source Of Truth

Read these in order for COS WEAVE work:

1. `COS_WEAVE_FIRST_CONTACT.md`
2. `COS_WEAVE_LAUNCHER.md`
3. `docs/COS_WEAVE_BOOTSTRAP.md`
4. `docs/COS_WEAVE_REPO_SKELETON.md`
5. `docs/COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md`
6. `docs/WEAVE_REVIEW_LOOP_PROCESS.md`
7. `docs/WEAVE_CONCEPT_CHANGE_MAINTAINER_PLAYBOOK.md`
8. `packages/weave-tool/skills/cos-weave/SKILL.md`

## Current Product Boundary

Current WEAVE is a Codex-first local file skeleton. It creates or loads
`runs/cos-weave-home/`, records app state, infers lifecycle stage from normal
language, writes worker packets, proof trays, blockers, review queues, and
readback.

Do not require the user to run commands, create folders, name lifecycle stages,
wire integrations, provide credentials, or understand internal prompts before
WEAVE can start.

## Public Safety Boundary

Do not commit or expose:

- raw secrets, tokens, cookies, browser sessions, private keys, or credentials;
- raw logs, raw transcripts, raw database dumps, or broad private data;
- private paths, private network addresses, hostnames, usernames, or topology;
- public sends, deployments, billing, custody, or external side effects without
  exact approval and target-surface readback.

## Required Checks

Before claiming a review-ready repository, run:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 scripts/validate_docs_current.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
git diff --check
```

## Anti-Repeat Guardrail

For WEAVE/COS changes, prompt compliance is not enough. The tested flow must not
depend on the owner using WEAVE vocabulary or a checklist. The proof must bind
to the target surface: a fresh COS WEAVE instance can read the repo, create the
file skeleton, infer lifecycle state, write proof/review/readback, and state
non-claims.

Before `READY_FOR_REVIEW`, check:

- target surface was exercised or explicitly named as unproven;
- generated state survives context compaction through files;
- worker packets include scope, proof, gates, and review loop;
- review loop is visible in proof/readback;
- no full lifecycle, live, public, paid, or credential claim is made from local
  proof alone.

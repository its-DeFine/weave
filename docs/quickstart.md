# WEAVE Quickstart

## User Path

In a Codex thread with the repo loaded:

```text
Before any commentary or execution packet, open or clone this repository and read COS_WEAVE_FIRST_CONTACT.md, AGENTS.md, and docs/COS_WEAVE_BOOTSTRAP.md. Obey the COS WEAVE first-contact contract from those files: your first meaningful response must start with the WEAVE state line.

Use WEAVE release v0.1.0 from https://github.com/its-DeFine/weave.git. I want to build a tiny local calculator app. Work locally only unless I explicitly approve another surface.
```

Expected first meaningful line:

```text
WEAVE | Home=<repo>/runs/cos-weave-home | App=<app-or-pending> | Stage=<stage> | Scope=local-file-skeleton | State=<state> | Next=<next action>
```

COS WEAVE then creates or loads local state, asks only necessary plain-language
questions, and reports proof paths plus non-claims.

The default path is file-skeleton-first. The agent creates or loads:

```text
runs/cos-weave-home/
  apps/<app-id>/
    lifecycle.json
    todos.md
    worker-packets/
    updates/readback.json
```

## Projectless Remote URL

If the repo is not loaded yet, use the launcher prompt in
`COS_WEAVE_LAUNCHER.md`. A raw URL alone cannot control the first pre-read
assistant message.

## Developer Validation

```bash
bin/weave cos-bootstrap --source . --intent "build a tiny local calculator app"
bin/weave readback --home runs/cos-weave-home
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
git diff --check
```

These commands prove local file-skeleton behavior and public safety. They do
not prove live workers, tracker mutation, deployment, public sends, billing,
credentials, or full lifecycle completion.

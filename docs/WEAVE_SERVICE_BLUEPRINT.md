# WEAVE Service Blueprint

This blueprint describes the default COS WEAVE service. It assumes one Codex
thread and a local repository checkout.

| Phase | User Experience | Agent Action | System Artifact |
| --- | --- | --- | --- |
| Activate | User gives repo URL/path and intent | Reads bootstrap contract and emits WEAVE state line | first-contact state |
| Profile | User answers lightweight preference questions | Creates or updates owner profile | `owner-profile.md` |
| Intent | User describes an app or outcome | Infers intent truth and open questions | `intent.md` |
| Structure | User sees a visible app workspace | Creates app folder and lifecycle state | `app.json`, `lifecycle.json` |
| Plan | User gets concrete next steps | Writes todos and optional worker packets | `todos.md`, `worker-packets/` |
| Build | Agent executes the safe slice | Creates or edits local artifacts | app files and proof |
| QA | User gets validation outcome | Runs checks and review loop | `proof/`, `review/` |
| Resume | User returns later | Reads state and explains truth | `updates/readback.json` |

## Frontstage Promise

The user always sees:

- which app is active;
- which lifecycle stage is active;
- what is proven;
- what is not proven;
- what happens next.

## Backstage Rules

- State is in repo files.
- Worker packets are plain Markdown.
- Review decisions are written before any done claim.
- Missing details become visible assumptions or todos.
- Stop boundaries are explicit.

## Failure Handling

If a slice cannot continue, record:

- blocker;
- proof of blocker;
- owner action if needed;
- safe alternatives;
- next retry point.

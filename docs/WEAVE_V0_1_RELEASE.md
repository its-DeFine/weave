# WEAVE v0.1 Release

Status: public COS file-skeleton release.

Release tag: `v0.1.0`

## What This Release Is

WEAVE v0.1 is a repository skeleton that lets a Codex thread become COS WEAVE:
one Chief-of-Staff chat that turns ordinary app intent into visible local files.

It is useful when a user wants the agent to keep state across multiple apps,
move work through lifecycle stages, record proof, and avoid relying on hidden
chat memory.

## What Ships

- Root activation contract in `COS_WEAVE_FIRST_CONTACT.md`.
- Projectless launcher prompt in `COS_WEAVE_LAUNCHER.md`.
- File-skeleton bootstrap in `scripts/weave_cos_skeleton.py`.
- Validation CLI in `bin/weave`.
- Portable package under `packages/weave-tool/`.
- Sample WEAVE home under `docs/samples/cos-weave-skeleton/`.
- User-facing visual flow in `assets/weave-v0.1-flow.svg`.
- User-facing lifecycle map in `assets/weave-v0.1-lifecycle.svg`.
- Docs-currentness validator in `scripts/validate_docs_current.py`.

## What A User Does

The user gives a Codex thread the WEAVE repo URL or local path and ordinary app
intent. The thread reads the repo contract, starts with the WEAVE state line,
creates or loads `runs/cos-weave-home/`, and records app state under
`runs/cos-weave-home/apps/<app-id>/`.

The user should not have to run commands, choose lifecycle labels, create
folders, or write worker prompts.

## Acceptance Checks

Before a release is acceptable:

- unit tests pass;
- docs-currentness validation passes;
- package validation passes;
- COS bootstrap smoke passes;
- no-secret and public-safe scans pass;
- git whitespace/conflict-marker check passes;
- GitHub CI passes on the release PR;
- release tag and notes point to the exact merged commit.

## Non-Claims

v0.1 proves the local WEAVE skeleton and validation gates. It does not prove
deployment, public sends, credential access, paid actions, tracker mutation, or
full lifecycle completion unless those exact lifecycle steps are later executed
and recorded with proof.

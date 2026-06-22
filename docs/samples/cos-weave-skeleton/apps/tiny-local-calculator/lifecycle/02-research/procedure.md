# Research Procedure

Use this deterministic procedure after context compaction, model changes, or worker handoff.

## Inputs

- current app record
- lifecycle-state.json
- blockers and proof tray
- owner constraints and hard gates

## Steps

1. Observe current `research` state, artifacts, blockers, and prior proof.
2. Validate the requested claim against lifecycle scope and non-claims.
3. Govern hard gates before any external, public, paid, credential, or destructive action.
4. Review worker output or local artifacts before accepting completion.
5. Sync readback files, proof tray, blockers, and next action.

## Review Loop

`observe -> validate -> govern -> review -> sync` is mandatory before a lifecycle step can be accepted.

## Forbidden Defaults

- do not claim full lifecycle completion from this stage alone
- do not mutate trackers, deploy, send public messages, spend money, or touch credentials without approval
- do not require hidden orchestration for default first-run WEAVE behavior

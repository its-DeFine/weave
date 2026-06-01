# WEAVE Runtime One-Shot Implementation Prompt v0.1

Date: 2026-05-30
Status: prompt contract
Requires skills:

- `$gestalt-to-artifact`
- `$codex-dynamic-workflows`

Purpose: provide a single implementation prompt that turns the reviewed WEAVE
runtime contracts into a focused first runtime slice, while forcing premortem
thinking, failure-mode discovery, implementation, fixes, and verification.

## Prompt

```text
Use $gestalt-to-artifact and $codex-dynamic-workflows together for this task.

Goal:
Implement the first local WEAVE Hermes operating-environment slice from the
current repository contracts.

Authoritative contracts and inputs:
- docs/weave-runtime-story-contract-v0.1.md
- docs/weave-runtime-architecture-contract-v0.1.md
- docs/weave-runtime-technical-gestalt-contract-v0.1.md
- docs/weave-runtime-document-templates-v0.1.md
- docs/weave-runtime-first-slice-handoff-v0.1.md
- docs/hermes-setup.md
- docs/hermes-runtime-handover-2026-05-30.md
- AGENTS.md

Non-negotiable product model:
- Hermes is the semantic lifecycle agent.
- WEAVE runtime is deterministic substrate, verifier, ledger, REST API,
  setup tool, git/workspace manager, and Telegram slash-command status surface.
- Telegram is the first communication channel.
- There is no required web UI in this slice.
- Normal Telegram messages go to Hermes; WEAVE slash commands return
  deterministic runtime output and do not use model-generated text.
- Foundation context is unskippable before serious app work.
- Every app has app-specific context loaded throughout lifecycle work.
- Every app has lifecycle shelves.
- Artifacts belong to the first relevant lifecycle shelf.
- Later shelves store reference JSON for reused artifacts rather than copying
  full artifacts.
- Gestaltian Contracts are versioned, git tracked, diff-visible, and ledgered.
- WEAVE supports multiple apps from slice one.
- Public repo safety overrides all generated suggestions.

Implementation target:
Create the smallest useful local runtime slice that proves:
1. setup can create or verify the WEAVE root structure;
2. app registry can represent multiple apps and current stage per app;
3. app context templates exist and are linked to each app;
4. append-only ledger events can be validated and recorded;
5. foundation gate can detect missing `soul.md`, `owner-profile.md`, app
   context, app inventory, contract, lifecycle state, capabilities, or blockers;
6. deterministic stage derivation can report stage when required artifacts
   exist;
7. REST API skeleton can expose health, runtime status, app list, app state,
   events, artifacts, and contract diff endpoints;
8. deterministic Telegram slash commands can show apps, stage per app, what
   changed per app, foundation gate status, current blocker, evidence,
   approvals, and REST health;
9. Hermes adapter boundary exists as an interface or stub without pretending to
   be the real Hermes runtime;
10. checks and smoke tests prove the slice.

Before editing:
1. Read the authoritative contracts and existing implementation files.
2. Produce a short Gestalt Kernel for this implementation slice.
3. Produce a story-to-technical mapping table for the slice.
4. Produce an architecture map of the files/modules you will touch.
5. Produce a premortem with at least these failure classes:
   - Hermes/WEAVE role confusion
   - slash commands being answered by Hermes instead of deterministic runtime
   - foundation gate bypass
   - app context leakage across apps
   - copied artifacts instead of references
   - contract diffs not visible
   - ledger accepts malformed events
   - REST API exposed too broadly
   - public repo confidentiality leak
   - tests proving only docs but not runtime behavior
6. Convert each serious failure mode into an implementation safeguard or test.
7. Create a compact workflow with these roles, simulated as packet passes unless
   a safe subagent runner is explicitly available:
   - contract reader
   - runtime implementer
   - UX/cognition reviewer
   - security reviewer
   - QA/verifier
   - docs/handoff integrator

Implementation rules:
- Keep the first slice narrow.
- Prefer existing repository patterns.
- Do not add runtime dependencies unless clearly necessary and justified.
- Do not introduce private topology, secrets, local usernames, private hostnames,
  private IPs, credential locations, or owner-specific operating procedures.
- Do not claim real Hermes operational status unless the real Hermes runtime
  path is present and verified.
- Label stubs and fallback adapters honestly.
- Use append-only ledger semantics.
- Make validation deterministic and testable.
- Keep status output dense, legible, and cognitively quiet.
- Telegram slash commands must answer in seconds:
  - what apps exist;
  - what stage each app is in;
  - what changed in each app;
  - what is blocked;
  - what needs approval;
  - whether foundation context is complete.

Expected edits:
- Runtime/setup code only where needed for the first slice.
- Focused tests for setup, registry, ledger, foundation gate, stage derivation,
  REST skeleton, and Telegram slash-command status.
- Docs updates only when needed to keep contracts and usage accurate.
- Reusable workflow artifacts only if they are concise and public-safe.

Verification required before final:
- python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
- python3 scripts/check_no_secrets.py
- python3 scripts/public_safe_repo_scan.py
- python3 -m unittest discover -s tests -p 'test_*.py'
- python3 scripts/runtime_smoke.py
- git diff --check

Final response format:
1. Verdict: implemented, partially implemented, or blocked.
2. What changed.
3. Which failure modes were found and how they were fixed or guarded.
4. Verification commands and results.
5. Remaining risks, clearly labeled.
6. Files changed.
```

## Why This Prompt Exists

The first runtime implementation pass needs more than a normal coding prompt.
It must preserve the metaphor, the technical mapping, the Hermes/WEAVE boundary,
the public safety boundary, and the cognitive UX outcome at the same time.

`$gestalt-to-artifact` protects the whole-system meaning.
`$codex-dynamic-workflows` protects packet separation, premortem thinking,
integration, and verification.

## Use Rules

Use this prompt when moving from contract work into the first runtime
implementation slice.

Do not use it for small edits, typo fixes, or isolated docs updates.

Do not use it to authorize destructive actions, production changes, external
sends, dependency upgrades, or remote runtime exposure. Those require a separate
approval packet.

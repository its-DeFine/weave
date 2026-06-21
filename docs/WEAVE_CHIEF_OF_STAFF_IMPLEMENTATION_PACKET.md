# WEAVE Chief of Staff Implementation Packet

Status: ready for implementation
Date: 2026-06-21

## Goal

Implement WEAVE v0.1 as a portable Chief-of-Staff operating layer for Codex and
Hermes. The first public release should make the interaction model concrete
without requiring a hosted control plane.

## Source Files Read

- `AGENTS.md`
- `README.md`
- `docs/WEAVE_V1_PRODUCT_CONTRACT.md`
- `docs/WEAVE_V1_BACKEND_ARCHITECTURE_SPEC.md`
- `docs/month1/weave-agent-operating-contract-v0.md`
- `docs/month1/weave-lifecycle-contract-v0.md`
- `docs/ux/weave-v1-operator-screen-mockups.html`
- `docs/weave-runtime-one-shot-implementation-prompt-v0.1.md`
- `scripts/weave_cli.py`
- `apps/weave-v1-cockpit/`

## Architecture Map

```text
docs/
  UX and service blueprint contracts for the portable Chief-of-Staff layer.

scripts/weave_cli.py
  Existing command entrypoint. Future implementation should add commands without
  breaking existing TUI/runtime flows.

apps/weave-v1-cockpit/
  Empty app shell. Natural place for a public, demoable visual snapshot/cockpit.

packages/weave-tool/
  Public company package. Should remain valid and public-safe.

tests/
  Public-safe unit and smoke tests. New implementation should add focused tests
  for any new script or schema.
```

## Invariant To Preserve

WEAVE must not claim live Hermes, live deployment, public sending, or credential
handling unless verified in the current environment and explicitly approved.

## Business Logic Invariants

- One Chief of Staff home is the durable operational center.
- Apps move through explicit lifecycle stages.
- Stage describes lifecycle position; state describes operational status.
- Proof and blockers are first-class state.
- Ready-for-review and done are different.
- Local WEAVE task/proof state is authoritative in v0.1.
- Linear and GitHub are optional mirrors; local task state must work without them.
- Updates are surfaced in the Chief of Staff, not hidden elsewhere.
- Serious live-effect gates require exact owner approval.
- A path is not proof unless bound to a claim and acceptance check.
- Done requires proof envelope plus controller review.

## UI And Flow Invariants

- The user stays in Codex or Hermes as the primary interaction medium.
- Every meaningful WEAVE response can show a compact state line.
- Setup questions are asked in simple language.
- Visual snapshots are generated from state, not hand-waved.
- If the user asks for a later lifecycle step, WEAVE names missing gates.

## Planned Touched Files

First implementation pass should touch:

- `docs/WEAVE_CHIEF_OF_STAFF_UX.md`
- `docs/WEAVE_SERVICE_BLUEPRINT.md`
- `docs/WEAVE_UPDATE_MODEL.md`
- `docs/WEAVE_CHIEF_OF_STAFF_IMPLEMENTATION_PACKET.md`
- `docs/WEAVE_PRO_ADVISOR_REVIEW.md`
- `scripts/weave_chief_of_staff.py`
- `scripts/weave_cli.py`
- `tests/test_weave_cli.py`
- `apps/weave-v1-cockpit/README.md`
- `apps/weave-v1-cockpit/index.html`
- `apps/weave-v1-cockpit/src/app.js`
- `apps/weave-v1-cockpit/src/styles.css`

## Verification Command

Before publication:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/runtime_smoke.py
git diff --check
```

For the first visual pass:

```bash
python3 -m http.server 8765 --directory apps/weave-v1-cockpit
```

Then inspect desktop and mobile screenshots.

## Iteration Delta

Previous WEAVE direction centered on a terminal/Textual cockpit. This iteration
adds a portable Chief-of-Staff skill model: Codex/Hermes remain the interaction
surface, and a lightweight visual artifact shows state when needed.

## Implementation Brief

Build the public-facing WEAVE v0.1 release around a simple invariant: same chat,
augmented with deterministic app operations. Ship docs, demo cockpit, update
model, and a video that shows how a user activates WEAVE, creates the Chief of
Staff home, starts an app, sees lifecycle state, spawns workers, receives proof,
and handles updates.

The smallest build target is local tasks, bounded packets, proof envelopes,
review gate, and HTML snapshot. Everything else waits.

## Stop Boundary

Stop before:

- raw secret handling;
- credential collection;
- live deployment;
- production changes;
- public sends;
- paid actions;
- private topology disclosure;
- claiming live Hermes when only adapter/stub proof exists.

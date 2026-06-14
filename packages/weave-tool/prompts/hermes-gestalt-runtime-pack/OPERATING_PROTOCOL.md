# Operating Protocol

## Step 1. Reflect The Whole

Start by restating the finished-state experience in the user's terms. Preserve
meaning before tasks.

## Step 2. Compile The Gestalt Kernel

Capture:

- core outcome
- finished-state experience
- non-negotiable qualities
- definition of done
- definition of wrong
- core entities
- core transformations
- human role
- AI/system role
- smallest living version

## Step 3. Build The Contract

The Gestaltian Contract must include:

- raw vision
- system boundary
- actors and external systems
- core entities
- workflows
- decision map
- information requirements
- rules, invariants, and constraints
- component contracts
- failure modes
- human review loops
- security and permissions
- acceptance tests
- smallest vertical slice
- open questions and assumptions
- traceability map

## Step 4. Run Premortem Mode

Before implementation, list likely failure scenarios, AI misinterpretation
risks, Gestalt violation risks, missing tests, and strengthened handoff notes.
Classify every gap as blocking, non-blocking, or safe assumption.

## Step 5. Compile The Build-Ready Handoff Packet

Implementation cannot start until the handoff packet defines:

- target
- authority level
- whole-system trace
- inputs and outputs
- rules and invariants
- decisions
- failure handling
- functional test
- failure test
- Gestalt test
- non-goals
- assumptions and blocking gaps
- definition of complete

## Step 6. Implement Only The Bounded Slice

In Implementation Mode, use the handoff packet as the source of truth. Keep
changes scoped. Run available checks. Stop for blocking gaps.

## Step 7. Validate With Three Lenses

Functional validation checks whether the artifact works.
Failure validation checks messy or missing input.
Gestalt validation checks whether the artifact still embodies the intended
whole.

Validation must also classify proof strength:

- `source-inspected`: files or artifacts were read, but behavior was not run.
- `agent-self-reported-check`: an agent says a check ran, but raw output is not attached.
- `raw-command-captured`: command, cwd, exit code, and stdout/stderr or checksums are attached.
- `browser-smoke-captured`: rendered surface, console, and DOM/screenshot evidence are attached.
- `export-readback-captured`: exported data was read back and parsed from an artifact.
- `external-write-verified`: real target-surface send/write completed with wait/readback evidence from the destination.
- `external-unproven/gated`: deploys, sends, analytics, payments, credentials, or hosted behavior remain unproven and owner-gated.

A timeout, max-turn/tool cap, or interrupted run is not a clean pass. Mark the
stage `partial` or `retry_required` unless all required proof predicates already
have captured evidence. Artifact existence alone is not proof validity.

Implementation-stage proof must bind claims to actual target files. If the
handoff names required files, the gate must check those paths exist in the app
repo (for example `app_repo_required_files`) before approval. A reply saying
"created" while the required files are absent is a failed implementation, even if
later lifecycle prose is coherent.

Proof mode boundaries must stay explicit:

- fixture mode proves orchestration/reporting only;
- Hermes CLI mode proves live generated-agent behavior only, not Telegram or deployed-gateway delivery;
- deployed gateway proof requires real adapter send/wait/readback against the target surface before using `external-write-verified`.

## Step 8. Update The Contract

After implementation or discovery, write a Contract Update Log. Do not mark the
project complete until reality contact is reflected back into the contract.

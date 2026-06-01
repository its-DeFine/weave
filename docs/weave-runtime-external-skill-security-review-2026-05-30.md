# External Skill Security Review: `codex-dynamic-workflows`

Date: 2026-05-30
Status: approved for local Codex skill installation
Reviewed source: `https://github.com/DannyMac180/skills`
Reviewed commit: `5695fa19b9d39b8270025e79633b49a8b863f9a2`
Skill reviewed: `codex-dynamic-workflows`

## 1. Review Scope

This review covers the skill content before using it as an implementation aid
for the WEAVE Hermes operating environment.

Reviewed files:

- `README.md`
- `LICENSE`
- `codex-dynamic-workflows/SKILL.md`
- `codex-dynamic-workflows/agents/openai.yaml`
- `codex-dynamic-workflows/scripts/new_workflow.py`
- `codex-dynamic-workflows/scripts/collect_results.py`
- `codex-dynamic-workflows/scripts/verify_workflow.py`
- `codex-dynamic-workflows/references/plan-schema.md`
- `codex-dynamic-workflows/references/risk-gates.md`
- `codex-dynamic-workflows/references/validation-examples.md`

## 2. Dependency Review

No package manifests were present:

- no `package.json`
- no lockfile
- no `requirements.txt`
- no `pyproject.toml`
- no `setup.py`
- no Dockerfile

The helper scripts use Python standard library modules only.

Conclusion: no dangerous dependency addition was identified.

## 3. Script Behavior Review

`new_workflow.py`:

- creates local workflow directories
- writes `plan.md`, `orchestration.md`, `state.json`, and `final-report.md`
- does not call the network
- does not execute shell commands
- does not delete files

`collect_results.py`:

- reads local markdown result files
- prints or writes an integration checklist
- does not call the network
- does not execute shell commands
- does not delete files

`verify_workflow.py`:

- checks local workflow artifact completeness
- reads local markdown and JSON files
- does not call the network
- does not execute shell commands
- does not delete files

`python3 -m py_compile` passed for all three scripts.

## 4. Prompt-Injection Review

No direct instruction was found that tells the agent to ignore system,
developer, repository, or owner instructions.

The skill does include strong orchestration behavior:

- create workflow artifacts
- split work into packets
- use subagents when available
- enter goal mode when appropriate
- verify and integrate results

This is acceptable only as an operator aid. It must not override:

- repository `AGENTS.md`
- public repository safety rules
- approval gates
- secret handling rules
- Hermes/WEAVE role boundaries
- the `gestalt-to-artifact` method

## 5. Integration Decision

Approved for local Codex skill installation with guardrails.

Allowed use:

- planning broad implementation work
- creating workflow packets
- separating security, UX, implementation, docs, and verification passes
- simulating subagents with local packet notes when no safe runner is available
- strengthening final verification and handoff artifacts

Disallowed use:

- delegating risky or destructive work without explicit approval
- treating subagent output as authoritative without integration review
- letting the skill replace Hermes reasoning or WEAVE runtime contracts
- storing transcripts, secrets, credentials, or private topology in workflow
  artifacts
- publishing generated workflow artifacts without public-safety review

## 6. WEAVE-Specific Guardrails

When used for WEAVE runtime implementation, this skill must preserve:

1. Hermes is the semantic lifecycle agent.
2. WEAVE runtime is deterministic substrate, verifier, ledger, REST control,
   and Telegram slash-command status.
3. Telegram is the first communication channel.
4. WEAVE slash commands are deterministic status, not chat.
5. Command output is still an editable runtime artifact Hermes can improve
   through normal lifecycle work.
6. Foundation context is unskippable before serious work.
7. Each app has its own context and lifecycle shelves.
8. Contracts, diffs, approvals, and ledger events remain git tracked and
   auditable.

## 7. Residual Risks

Residual risk: the skill may encourage too much orchestration for a focused
implementation task.

Mitigation: the one-shot implementation prompt must cap the workflow to the
minimum useful packets and require integration before edits are considered
complete.

Residual risk: packet artifacts may accumulate noisy or sensitive details.

Mitigation: generated workflow artifacts must stay local, minimal, and
public-safe before being committed.

Residual risk: simulated subagents may create false confidence.

Mitigation: the parent agent must inspect authoritative files, integrate
conflicts explicitly, and run the final verification commands itself.

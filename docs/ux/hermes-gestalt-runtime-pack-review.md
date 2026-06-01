# Hermes Gestalt Runtime Pack Review

Date: 2026-05-30
Status: public review artifact

## Purpose

This review artifact replaces the noisy operational-history shape from the
previous PR attempt. The deliverable is now the Hermes Gestalt Runtime Pack:

```text
packages/weave-tool/prompts/hermes-gestalt-runtime-pack/
```

That package is the public contract for how Hermes moves a user from raw app
idea to implementation-ready work without losing the whole-system intent.

## What This PR Proves

1. Hermes is the default WEAVE runtime in the public company package.
2. Local Fallback remains an explicit fallback runtime.
3. Hermes ships with a dedicated prompt/spec pack.
4. The prompt/spec pack encodes Contract, Premortem, Implementation, and
   Contract Update modes.
5. A simulated Hermes method proof produces the expected path from idea to
   Gestalt Kernel, Gestaltian Contract, Premortem, and Build-Ready Handoff
   Packet.
6. Completion audit fails unless the prompt pack and method proof validate.

## What This PR Does Not Claim

1. No hosted Hermes service is deployed.
2. No production app is deployed.
3. No public send, spend, DNS, ads, email, analytics, payment, provider
   mutation, or credential change is authorized.
4. No raw secrets, OAuth payloads, auth files, refresh tokens, API keys, or
   private topology details are committed.

## Review Commands

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 scripts/weave_hermes_gestalt_pack.py --simulate-run --write-evidence
python3 scripts/weave_hermes_gestalt_pack.py --validate --require-evidence
python3 scripts/weave_full_contract_audit.py --run-verifiers --require-complete
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/runtime_smoke.py
python3 scripts/operator_ui_smoke.py
git diff --check
```

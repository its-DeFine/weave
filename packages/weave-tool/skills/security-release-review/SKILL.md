---
name: security-release-review
description: Review a public package for secrets, private paths, internal references, and overbroad release claims.
---

# Security Release Review

## Use When

Use this skill before publishing docs, examples, packages, operator UI data, or
runtime artifacts.

## Inputs

- changed files
- intended publication surface
- public claims
- known private systems or excluded materials
- scanner commands

## Outputs

- exposure audit
- removed or approved references
- scanner results
- public claim verdict
- remaining private or deployment gaps

## Rules

- Scan for credentials, private paths, internal hostnames, account details, and
  private operational references.
- Treat public examples as attacker-readable.
- Keep private tool mappings out of public docs.
- Replace internal blockers with neutral lifecycle or approval language.
- Do not hide safety boundaries that a reproducing builder needs.

## Stop Conditions

- Any credential, private key, private path, or internal host reference is found.
- A public claim depends on unverified private infrastructure.
- The publication surface includes sensitive customer, account, or payment data.

## Verification

Record the scanner commands and the remaining allowed generic security words or
patterns.


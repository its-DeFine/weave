---
name: livepeer-adapter-boundary
description: Keep local WEAVE primitives shaped for Livepeer pipelines without overstating live runtime proof.
---

# Livepeer Adapter Boundary

## Use When

Use this skill whenever a WEAVE primitive or app references Livepeer.

## Inputs

- primitive or app reference
- claimed pipeline behavior
- payment or gateway boundary
- available output evidence

## Outputs

- local proof versus live proof distinction
- required owner approvals
- omitted or unavailable stages
- claim limit wording
- evidence needed for the next stronger claim

## Rules

- distinguish local primitive behavior from live pipeline output
- require owner approval before paid or metered jobs
- require output evidence before claiming live runtime proof
- keep gateway, payment, and credential setup outside package files
- record unavailable stages as explicit omissions

## Stop Conditions

- A claim implies live output without output evidence.
- A task would require paid or metered execution without approval.
- Gateway, payment, or credential details would enter a public package file.

## Verification

The public claim is valid when it names the adapter boundary and the evidence
needed for live proof.

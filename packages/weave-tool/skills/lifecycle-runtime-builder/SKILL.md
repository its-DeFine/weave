---
name: lifecycle-runtime-builder
description: Build WEAVE lifecycle proof artifacts and keep future runtime adapter mapping explicit.
---

# Lifecycle Runtime Builder

## Use When

Use this skill for local WEAVE lifecycle wrapper and application proof
engineering.

## Inputs

- lifecycle contract
- target app
- primitive registry
- operator UI or runtime artifact
- acceptance checks

## Outputs

- runtime artifact or package change
- primitive-to-stage mapping
- claim limits
- smoke or validation result
- evidence packet

## Rules

- keep runtime controls useful to an owner, operator, or technical user
- expose claim limits in the UI or evidence artifact
- map every primitive to lifecycle evidence intent
- verify build and smoke checks before promotion
- capture evidence when UI or command-bus behavior changes

## Stop Conditions

- The artifact would imply a hosted or private runtime that was not verified.
- The change depends on secrets, paid calls, or production access.
- The UI or package exposes private infrastructure details.

## Verification

Run the local package validator, runtime smoke, and UI smoke when runtime
artifacts change.

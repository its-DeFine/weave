---
schema: agentcompanies/v1
kind: company
slug: weave
name: WEAVE
description: COS-first application operating skeleton for Codex threads.
version: "0.1.0"
releaseDate: "2026-06-22"
releaseTag: v0.1.0
releaseChannel: public-v0.1
license: MIT
homepage: https://github.com/its-DeFine/weave
runtime: cos-file-skeleton
runtimeFallback: none-required
defaultSurface: codex-thread
---

# WEAVE

WEAVE is a local, public-safe Chief-of-Staff skeleton for turning ordinary app
intent into durable lifecycle state.

The package contains:

- the COS WEAVE activation skill;
- compound engineering and review-loop skills;
- lifecycle eval contracts;
- lifecycle primitives for intent through analysis;
- optional domain extensions outside the generic default skill surface;
- public-safe validation tooling.

The package does not require an external runtime, tracker, deployment target,
credential, public send, billing action, or private service to begin.

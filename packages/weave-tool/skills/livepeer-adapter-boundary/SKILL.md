---
name: livepeer-adapter-boundary
description: Keep local WEAVE primitives shaped for Livepeer pipelines without overstating live runtime proof.
---

# Livepeer Adapter Boundary

Use this skill whenever a WEAVE primitive or app references Livepeer.

Rules:

- distinguish local primitive behavior from live pipeline output
- require owner approval before paid or metered jobs
- require output evidence before claiming live runtime proof
- keep gateway, payment, and credential setup outside package files
- record unavailable stages as explicit omissions

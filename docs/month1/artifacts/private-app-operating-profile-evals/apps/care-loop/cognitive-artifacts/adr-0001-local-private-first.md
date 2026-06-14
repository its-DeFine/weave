# ADR 0001: Build Care Loop as a local private app proof

Status: accepted

## Context

The evaluation needs to assess private-domain app usefulness without exposing
real private data, performing marketing, or depending on hosted infrastructure.
Gestalt is optional/deferred for this slice; CWA, DMN, IBIS, ADR, Premortem, and
PROV provide the required review gates.

## Decision

Generate a dependency-free local static app and a complete framework-gate
evidence bundle. The app remains local-only and uses synthetic sample signals.

## Rejected alternatives

- Hosted app: rejected because deployment/external surface is not authorized.
- Marketing prototype: rejected because publication is outside this proof slice.
- Mandatory Gestalt contract: deferred by owner feedback until it is specifically useful.

## Consequences

- Reviewers can inspect source, evidence, and framework gate artifacts.
- The result does not prove live Hermes, deployed gateway, hosted UX, or market traction.
- Later iteration can compare outputs across scenarios before authorizing broader action.

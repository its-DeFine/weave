# WEAVE

![WEAVE runtime hero](assets/weave-hero.png)

WEAVE is a runtime and agent-company package for building applications from
realtime media primitives.

The current release shape is deliberately narrow:

- WEAVE is a standalone repository, not a Paperclip fork.
- Paperclip is the upstream company control plane dependency.
- OpenClaw is the runtime agent dependency.
- WEAVE supplies the company package, lifecycle, primitives, adapter boundaries,
  and validation tests.

## Repository Layout

```text
docs/                  Public documentation and replication architecture.
packages/weave-tool/   Paperclip-compatible WEAVE company package.
tests/                 Public-safe validation tests.
```

## Validate

Validate the WEAVE company package:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
```

Run the public-safe test suite:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected package shape:

```text
valid WEAVE company package: weave
agents: 6
tasks: 6
primitives: 9
```

## Runtime Model

WEAVE is packaged as an importable AI-operated company:

```text
WEAVE repo
  -> packages/weave-tool
  -> Paperclip company import
  -> openclaw_gateway adapter
  -> OpenClaw CEO/runtime agent
  -> WEAVE lifecycle tasks and primitives
```

The first lifecycle is:

1. Research.
2. Engineering.
3. QA.
4. Outreach and distribution.
5. KPI and analytics.
6. Iteration.

Engineering starts only after Research admits one opportunity.

## Boundaries

This repository intentionally does not include:

- private WEAVE operating substrate
- treasury, Safe, payment, funding, or accounting material
- VM, SSH, VPN, private-network, or host-specific proof details
- API keys, gateway tokens, OAuth tokens, private keys, or seed material
- generated private proof logs
- claims that Livepeer-native output is proven before output evidence exists

## Replication

Start with [WEAVE Replication Architecture](docs/replication-architecture.md).

## License

MIT. See [LICENSE](LICENSE).

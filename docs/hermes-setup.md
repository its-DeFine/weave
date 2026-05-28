# Hermes Runtime Setup

Status: public-safe setup contract
Audience: builders configuring WEAVE locally

WEAVE defaults to Hermes for the runtime agent and keeps OpenClaw as an
explicit fallback. The public repository can set up the WEAVE-side runtime
profile, but it does not download Hermes, install services, read secrets, or
pair a private gateway.

## What Setup Does

Run:

```bash
python3 scripts/setup_runtime.py
```

The command:

- reads `packages/weave-tool/COMPANY.md`
- selects `hermes-default`
- loads `packages/weave-tool/agents/ceo-hermes/AGENTS.md`
- checks whether a Hermes executable is already on `PATH`
- writes `runs/runtime-profile.json`
- records OpenClaw as the fallback runtime

The generated `runs/` directory is ignored by git.

## Strict Binary Check

To require a local Hermes executable:

```bash
python3 scripts/setup_runtime.py --require-runtime-binary
```

This fails if none of these executables are on `PATH`:

- `hermes`
- `hermes-agent`
- `nous-hermes`

Use `--runtime-binary <name-or-path>` when your local binary has a different
name.

## OpenClaw Fallback Profile

To write an OpenClaw fallback profile:

```bash
python3 scripts/setup_runtime.py --runtime openclaw-solo
```

This checks for `openclaw` on `PATH` and writes the fallback profile locally.

## Boundaries

This setup command does not:

- download runtime binaries
- run package managers
- install launch services, cron jobs, or systemd units
- read `.env` files
- load credentials
- contact private gateways
- mutate hosted runtime state
- claim a VM service or production runtime exists

Runtime pairing, gateway pairing, autostart, production deploys, paid jobs,
credential changes, public posts, and external sends remain separate approval
gates.

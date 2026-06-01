# Hermes Runtime Handover

Status: recovery packet
Audience: next WEAVE/Hermes implementation pass

## Verdict

The current branch has public-safe ingredients plus a real local Hermes
provisioning lane. It proves that WEAVE can clone the upstream Nous Hermes
Agent, check out a pinned commit, install its CLI into ignored local state, and
record that executable proof in the runtime profile. The prompt/spec package
and simulated proof remain method evidence; they are not production deployment
or external-action evidence.

## Recovered Ingredients

- Public repository guardrails in `AGENTS.md`.
- Hermes as the default runtime identity in `packages/weave-tool/COMPANY.md`.
- Hermes CEO agent rules in `packages/weave-tool/agents/ceo-hermes/AGENTS.md`.
- Hermes Gestalt Runtime Pack under
  `packages/weave-tool/prompts/hermes-gestalt-runtime-pack/`.
- Package-local `gestalt-runtime` skill.
- Public-safe setup profile command in `scripts/setup_runtime.py`.
- Pinned local Hermes provisioner in `scripts/provision_hermes.py`.
- Runtime setup documentation in `docs/hermes-setup.md`.
- Audit and tests that separate method-pack readiness from real runtime
  readiness.

## What Is Ready

- The WEAVE package validates with Hermes as the default runtime and Local Fallback as
  fallback.
- The prompt/spec package can describe the idea-to-contract-to-handoff method.
- The setup command can write an ignored local runtime profile and report
  whether a Hermes executable is already available on `PATH`.
- `scripts/setup_runtime.py --install-hermes --require-runtime-binary` proves
  a pinned upstream Hermes checkout and local executable under ignored
  `runs/`.
- The full contract audit passes when the real local Hermes proof is present.
- Public safety scans can reject host-specific paths and sensitive operating
  details before public commits.

## What Is Not Ready

- No Hermes daemon, autostart service, private gateway, or remote runtime lane
  is installed by this repository.
- No WEAVE adapter invokes a live Hermes conversation and captures structured
  outputs from an actual app build run yet.
- No real app idea has flowed through a live Hermes session into kernel,
  contract, premortem, handoff, implementation, validation, and contract
  update.
- No production deploy, paid job, public send, provider mutation, credential
  change, gateway pairing, or remote runtime pairing is authorized here.

## Required Next PR Shape

1. Keep the prompt pack as spec material, not runtime completion evidence.
2. Keep the local Hermes binary/profile boundary green with
   `scripts/setup_runtime.py --install-hermes --require-runtime-binary`.
3. Add a WEAVE adapter that invokes the installed Hermes runtime through a bounded,
   testable interface.
4. Add a real idea-to-handoff fixture captured from Hermes, with sensitive
   details excluded.
5. Keep the full contract audit blocking until the real runtime proof exists.

## Stop Boundary

This handover does not approve external actions. Stop before runtime pairing,
gateway pairing, hosted deployment, paid execution, public posting, DNS changes,
credential changes, or provider mutation unless a separate owner-approved packet
defines the scope and checks.

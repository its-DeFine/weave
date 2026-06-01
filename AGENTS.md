# WEAVE Public Repository Agent Rules

This repository is public. Treat every commit, branch, pull request, log, and
artifact as publishable by default.

## Confidential Topology Boundary

Do not commit or mention private operating details, including:

- internal device nicknames, workstation names, runtime host names, or service names
- overlay-network vendor names, VPN product names, private route names, private
  IPs, or private DNS names
- runtime isolation names, container names, host-specific usernames, home
  directories, SSH key paths, or operator shell commands
- credential locations, auth payloads, refresh tokens, API keys, secrets,
  Keychain item names, or secret manager object names
- private repo names, unpublished runbooks, private deployment topology, or
  owner-specific access procedures

Use generic language such as `remote runtime`, `owner-approved transport`,
`private runtime address`, and `private runtime home` when a public artifact
needs to describe a capability boundary.

## Required Checks

Before committing or pushing public changes, run:

```bash
python3 packages/weave-tool/scripts/validate_company_package.py packages/weave-tool
python3 scripts/check_no_secrets.py
python3 scripts/public_safe_repo_scan.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/runtime_smoke.py
python3 scripts/operator_ui_smoke.py
git diff --check
```

If any check fails, fix the source artifact and amend the relevant commit. Do
not add a follow-up cleanup commit for confidential-info removal on an open PR.

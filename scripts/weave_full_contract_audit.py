#!/usr/bin/env python3
"""Audit the Hermes Gestalt Runtime Pack completion claim."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import weave_hermes_gestalt_pack as gestalt_pack


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = REPO_ROOT / "docs" / "ux" / "hermes-gestalt-runtime-pack-audit-2026-05-30.json"
AUDIT_SCHEMA = "weave-hermes-gestalt-runtime-pack-audit/v0.1"
PACKAGE_ROOT = REPO_ROOT / "packages" / "weave-tool"
RUNTIME_PROFILE_PATH = REPO_ROOT / "runs" / "runtime-profile.json"


class AuditError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def subprocess_ok(command: list[str]) -> bool:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return result.returncode == 0


def item(requirement_id: str, requirement: str, status: str, evidence: str | None, detail: str) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "detail": detail,
    }


def read_runtime_profile(path: Path = RUNTIME_PROFILE_PATH) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_audit(*, run_verifiers: bool = False) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    try:
        manifest = gestalt_pack.validate_pack()
        results.append(item("hermes.prompt_pack", "Dedicated Hermes Gestalt Runtime Pack exists and validates", "passed", "packages/weave-tool/prompts/hermes-gestalt-runtime-pack/manifest.json", f"Pack {manifest['pack_id']} {manifest['version']} validates."))
    except Exception as exc:  # noqa: BLE001
        results.append(item("hermes.prompt_pack", "Dedicated Hermes Gestalt Runtime Pack exists and validates", "failed", "packages/weave-tool/prompts/hermes-gestalt-runtime-pack/manifest.json", str(exc)))

    try:
        proof = gestalt_pack.read_proof()
        results.append(item("hermes.method_proof", "Simulated Hermes run proves idea to kernel to contract to handoff shape", "passed", "docs/ux/hermes-gestalt-runtime-pack-proof-2026-05-30.json", proof.get("completion_claim", "proof validates")))
    except Exception as exc:  # noqa: BLE001
        results.append(item("hermes.method_proof", "Simulated Hermes run proves idea to kernel to contract to handoff shape", "failed", "docs/ux/hermes-gestalt-runtime-pack-proof-2026-05-30.json", str(exc)))

    package_ok = subprocess_ok([sys.executable, "packages/weave-tool/scripts/validate_company_package.py", str(PACKAGE_ROOT)])
    results.append(item("package.validation", "Company package validates with Hermes as default runtime", "passed" if package_ok else "failed", "packages/weave-tool/scripts/validate_company_package.py", "Package validator passed." if package_ok else "Package validator failed."))

    setup_ok = subprocess_ok([sys.executable, "scripts/setup_runtime.py", "--check"])
    results.append(item("runtime.profile_contract", "WEAVE can compile a public-safe local Hermes runtime profile", "passed" if setup_ok else "failed", "scripts/setup_runtime.py", "Runtime setup check passed without writing secrets." if setup_ok else "Runtime setup check failed."))

    runtime_profile = read_runtime_profile()
    runtime = runtime_profile.get("runtime", {}) if runtime_profile else {}
    binary = runtime.get("binary", {}) if isinstance(runtime, dict) else {}
    hermes_provision = runtime_profile.get("hermes_provision", {}) if runtime_profile else {}
    real_runtime_ready = (
        runtime_profile is not None
        and runtime.get("id") == "hermes-default"
        and binary.get("found") is True
        and isinstance(hermes_provision, dict)
        and hermes_provision.get("source_verified") is True
        and hermes_provision.get("binary_present") is True
    )
    if real_runtime_ready:
        runtime_detail = "Local runtime profile proves a pinned Hermes source checkout and executable are present."
    elif runtime_profile is None:
        runtime_detail = "No ignored local runtime profile exists at runs/runtime-profile.json."
    elif not hermes_provision:
        runtime_detail = "Local runtime profile exists, but it does not include pinned Hermes provision proof."
    else:
        runtime_detail = "Local runtime profile exists, but pinned Hermes source and executable proof is incomplete."
    results.append(item("runtime.real_hermes", "A real Hermes executable is present in the local runtime profile", "passed" if real_runtime_ready else "failed", "runs/runtime-profile.json", runtime_detail))

    if run_verifiers:
        verifier_commands = [
            [sys.executable, "scripts/check_no_secrets.py"],
            [sys.executable, "scripts/public_safe_repo_scan.py"],
            [sys.executable, "scripts/weave_hermes_gestalt_pack.py", "--validate", "--require-evidence"],
        ]
        verifier_ok = all(subprocess_ok(command) for command in verifier_commands)
        verifier_detail = "Secret scan, topology scan, and Hermes Gestalt pack proof validation passed." if verifier_ok else "At least one verifier failed."
    else:
        verifier_ok = None
        verifier_detail = "Verifier commands were not run by this audit invocation."
    verifier_status = "passed" if verifier_ok is True else "failed" if verifier_ok is False else "not_run"
    results.append(item("verification.suite", "Public safety and method proof verifiers pass", verifier_status, None, verifier_detail))

    blockers = [entry for entry in results if entry["status"] != "passed"]
    full_completion_ready = not blockers
    return {
        "schema": AUDIT_SCHEMA,
        "generated_at": utc_now(),
        "method_pack_ready": results[0]["status"] == "passed",
        "gestalt_proof_ready": results[1]["status"] == "passed",
        "runtime_profile_contract_ready": setup_ok,
        "real_runtime_ready": real_runtime_ready,
        "full_completion_ready": full_completion_ready,
        "passed_count": len(results) - len(blockers),
        "blocking_count": len(blockers),
        "requirements": results,
        "remaining_blockers": blockers,
        "secret_payload_allowed": False,
        "claim_limits": [
            "Completion requires a validated Hermes Gestalt Runtime Pack.",
            "Completion requires an idea-to-kernel-to-contract-to-handoff proof.",
            "Full runtime completion requires a real Hermes runtime proof, not only simulated proof.",
            "This audit does not authorize production deploy, public send, spend, provider mutation, or secrets access."
        ],
    }


def validate_audit(audit: dict[str, Any], *, require_complete: bool) -> None:
    if audit.get("schema") != AUDIT_SCHEMA:
        raise AuditError(f"schema must be {AUDIT_SCHEMA}")
    if audit.get("secret_payload_allowed") is not False:
        raise AuditError("secret payloads must be disabled")
    if require_complete and audit.get("full_completion_ready") is not True:
        blockers = ", ".join(entry["requirement_id"] for entry in audit.get("remaining_blockers", []))
        raise AuditError(f"Hermes Gestalt Runtime Pack incomplete: {blockers}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--run-verifiers", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    try:
        audit = build_audit(run_verifiers=args.run_verifiers)
        validate_audit(audit, require_complete=args.require_complete)
        if args.write_evidence:
            AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
            AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"wrote {AUDIT_PATH.relative_to(REPO_ROOT)}")
        else:
            blockers = ", ".join(entry["requirement_id"] for entry in audit["remaining_blockers"]) or "none"
            print(
                "weave full contract audit: "
                f"method_pack_ready={str(audit['method_pack_ready']).lower()} "
                f"gestalt_proof_ready={str(audit['gestalt_proof_ready']).lower()} "
                f"full_completion_ready={str(audit['full_completion_ready']).lower()} "
                f"remaining_blockers={blockers}"
            )
        return 0
    except AuditError as exc:
        print(f"weave full contract audit: FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

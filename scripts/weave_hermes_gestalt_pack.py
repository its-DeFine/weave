#!/usr/bin/env python3
"""Validate and exercise the Hermes Gestalt Runtime Pack."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "packages" / "weave-tool" / "prompts" / "hermes-gestalt-runtime-pack"
MANIFEST_PATH = PACK_ROOT / "manifest.json"
EVIDENCE_PATH = REPO_ROOT / "docs" / "ux" / "hermes-gestalt-runtime-pack-proof-2026-05-30.json"
PACK_SCHEMA = "weave-hermes-gestalt-runtime-pack/v0.1"
PROOF_SCHEMA = "weave-hermes-gestalt-runtime-pack-proof/v0.1"

REQUIRED_MODES = [
    "Contract Mode",
    "Premortem Mode",
    "Implementation Mode",
    "Contract Update Mode",
]

REQUIRED_OUTPUTS = [
    "Gestalt Kernel",
    "Gestaltian Contract",
    "Premortem Report",
    "Build-Ready Handoff Packet",
    "Implementation Report",
    "Contract Update Log",
]

REQUIRED_TEXT_MARKERS = [
    "Raw whole-first vision",
    "Gestalt Kernel",
    "Gestaltian Contract",
    "Premortem Report",
    "Build-Ready Handoff Packet",
    "Implementation Report",
    "Validation Result",
    "Contract Update Log",
    "Question Discipline",
    "Traceability Requirement",
    "Functional validation",
    "Failure validation",
    "Gestalt validation",
    "adapter-only evidence",
]


class GestaltPackError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise GestaltPackError(f"missing manifest: {rel(MANIFEST_PATH)}")
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GestaltPackError(f"invalid manifest JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise GestaltPackError("manifest must be a JSON object")
    return manifest


def load_pack_text(manifest: dict[str, Any]) -> str:
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise GestaltPackError("manifest files must be a non-empty list")
    chunks: list[str] = []
    for name in files:
        if not isinstance(name, str) or "/" in name or name.startswith("."):
            raise GestaltPackError(f"invalid prompt pack file entry: {name!r}")
        path = PACK_ROOT / name
        if not path.exists():
            raise GestaltPackError(f"missing prompt pack file: {rel(path)}")
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def validate_pack() -> dict[str, Any]:
    manifest = read_manifest()
    if manifest.get("schema") != PACK_SCHEMA:
        raise GestaltPackError(f"manifest schema must be {PACK_SCHEMA}")
    if manifest.get("pack_id") != "hermes-gestalt-runtime-pack":
        raise GestaltPackError("manifest pack_id must be hermes-gestalt-runtime-pack")
    if manifest.get("runtime") != "nousresearch-hermes-agent":
        raise GestaltPackError("manifest runtime must be nousresearch-hermes-agent")
    if manifest.get("secret_payload_allowed") is not False:
        raise GestaltPackError("manifest must set secret_payload_allowed false")
    modes = set(manifest.get("required_modes", []))
    missing_modes = [mode for mode in REQUIRED_MODES if mode not in modes]
    if missing_modes:
        raise GestaltPackError(f"missing required modes: {', '.join(missing_modes)}")
    outputs = set(manifest.get("required_outputs", []))
    missing_outputs = [output for output in REQUIRED_OUTPUTS if output not in outputs]
    if missing_outputs:
        raise GestaltPackError(f"missing required outputs: {', '.join(missing_outputs)}")
    text = load_pack_text(manifest)
    for marker in REQUIRED_TEXT_MARKERS:
        if marker not in text:
            raise GestaltPackError(f"prompt pack missing marker: {marker}")
    return manifest


def simulated_idea_to_handoff(idea: str) -> dict[str, Any]:
    manifest = validate_pack()
    app_name = "Neighborhood Repair Tracker"
    return {
        "schema": PROOF_SCHEMA,
        "generated_at": utc_now(),
        "pack_id": manifest["pack_id"],
        "pack_version": manifest["version"],
        "runtime": manifest["runtime"],
        "simulation_only": True,
        "secret_payload_allowed": False,
        "raw_secret_values_read": False,
        "raw_secret_values_written": False,
        "input_idea": idea,
        "mode_sequence": [
            "Contract Mode",
            "Premortem Mode",
            "Implementation Mode",
            "Contract Update Mode",
        ],
        "artifacts": {
            "gestalt_kernel": {
                "project_name": app_name,
                "core_outcome": "A local civic repair tracker turns vague neighborhood issues into scoped repair tickets.",
                "finished_state_experience": "A resident describes an issue, Hermes preserves the intent, and the app shows what is known, missing, next, and owner-gated.",
                "non_negotiable_qualities": [
                    "no public send without approval",
                    "missing location or authority routes to review",
                    "every ticket traces back to the original resident need"
                ],
                "definition_of_done": "Kernel, contract, premortem, and handoff exist with tests and gates.",
                "definition_of_wrong": "A form is generated without preserving uncertainty, authority, and follow-up state.",
                "smallest_living_version": "Local-only static tracker with sample repair tickets and review gates."
            },
            "gestaltian_contract": {
                "actors": ["resident", "owner", "Hermes", "local WEAVE runner"],
                "workflow": "idea -> issue contract -> repair ticket plan -> local UI proof",
                "rules": [
                    "do not deploy",
                    "do not send reports externally",
                    "ask when the responsible authority is unclear"
                ],
                "acceptance_tests": [
                    "functional: valid issue becomes a scoped local ticket",
                    "failure: missing location routes to review",
                    "gestalt: owner can see what is known, unknown, and next"
                ]
            },
            "premortem_report": {
                "likely_failure": "Hermes builds a generic issue form and loses the review/authority gates.",
                "mitigation": "handoff requires traceability, missing-data handling, and no external sends"
            },
            "build_ready_handoff_packet": {
                "target": "local-only repair tracker proof",
                "authority_level": "local artifact",
                "non_goals": ["production deploy", "public send", "provider mutation"],
                "definition_of_complete": [
                    "contract artifacts exist",
                    "local UI renders sample tickets",
                    "failure and Gestalt tests are represented"
                ]
            }
        },
        "method_trace": {
            "final_vision_supported": "Hermes moves an app idea into an implementation-ready local proof.",
            "gestalt_invariant_protected": "preserve the whole before decomposing",
            "workflow_supported": "idea to contract to handoff",
            "component_supported": "Hermes Gestalt Runtime Pack",
            "acceptance_test": "proof contains kernel, contract, premortem, and handoff"
        },
        "completion_claim": "simulated Hermes method proof only; no production or live provider claim",
        "claim_limits": [
            "This proves the prompt/spec package can drive the expected idea-to-handoff shape.",
            "This does not claim a hosted Hermes service, production deploy, public send, spend, DNS, ads, email, analytics, payment, or provider mutation.",
            "Real Hermes execution evidence is a stronger future check, not required for this local prompt-pack proof."
        ]
    }


def validate_proof(payload: dict[str, Any]) -> None:
    if payload.get("schema") != PROOF_SCHEMA:
        raise GestaltPackError(f"proof schema must be {PROOF_SCHEMA}")
    if payload.get("pack_id") != "hermes-gestalt-runtime-pack":
        raise GestaltPackError("proof pack_id must be hermes-gestalt-runtime-pack")
    if payload.get("runtime") != "nousresearch-hermes-agent":
        raise GestaltPackError("proof runtime must be nousresearch-hermes-agent")
    if payload.get("secret_payload_allowed") is not False:
        raise GestaltPackError("proof must set secret_payload_allowed false")
    sequence = payload.get("mode_sequence")
    if sequence != REQUIRED_MODES:
        raise GestaltPackError("proof mode_sequence must cover Contract, Premortem, Implementation, and Contract Update modes")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        raise GestaltPackError("proof artifacts must be an object")
    for key in ("gestalt_kernel", "gestaltian_contract", "premortem_report", "build_ready_handoff_packet"):
        if key not in artifacts:
            raise GestaltPackError(f"proof missing artifact: {key}")
    trace = payload.get("method_trace")
    if not isinstance(trace, dict) or not trace.get("acceptance_test"):
        raise GestaltPackError("proof must include method_trace with acceptance_test")


def read_proof(path: Path = EVIDENCE_PATH) -> dict[str, Any]:
    if not path.exists():
        raise GestaltPackError(f"missing proof evidence: {rel(path)}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GestaltPackError(f"invalid proof evidence JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise GestaltPackError("proof evidence must be a JSON object")
    validate_proof(payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--simulate-run", action="store_true")
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--require-evidence", action="store_true")
    parser.add_argument("--idea", default="Create a local app that tracks neighborhood repair requests.")
    parser.add_argument("--evidence-path", default=str(EVIDENCE_PATH))
    args = parser.parse_args(argv)

    evidence_path = Path(args.evidence_path)
    try:
        if args.simulate_run:
            payload = simulated_idea_to_handoff(args.idea)
            if args.write_evidence:
                evidence_path.parent.mkdir(parents=True, exist_ok=True)
                evidence_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                print(f"wrote {rel(evidence_path)}")
            else:
                print(json.dumps(payload, indent=2, sort_keys=True))
        if args.validate or not args.simulate_run:
            validate_pack()
            if args.require_evidence:
                read_proof(evidence_path)
            elif evidence_path.exists():
                read_proof(evidence_path)
            print("weave Hermes Gestalt runtime pack: ok")
        return 0
    except GestaltPackError as exc:
        print(f"weave Hermes Gestalt runtime pack: FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

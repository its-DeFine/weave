#!/usr/bin/env python3
"""Evidence-bound WEAVE lifecycle eval runner."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = REPO_ROOT / "packages" / "weave-tool" / "evals"
LIFECYCLE_ROOT = CONTRACT_ROOT / "lifecycle"
STAGE_ORDER = [
    "intent",
    "research",
    "selection",
    "plan",
    "engineering",
    "qa",
    "kpi-setup",
    "marketing",
    "iteration",
    "analysis",
]
SPECIAL_CONTRACTS = {
    "release": "release_readiness.yaml",
    "release-readiness": "release_readiness.yaml",
    "release_readiness": "release_readiness.yaml",
}
ADVANCE_DECISIONS = {"advance", "needs_human_approval"}


class EvalError(Exception):
    """Raised when an eval cannot be loaded or executed."""


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    status: str
    passed: bool | None
    required: bool
    detail: str
    command: str | None = None
    exit_code: int | None = None
    output_excerpt: str | None = None


def normalize_stage(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def contract_path_for_stage(stage: str) -> Path:
    normalized = normalize_stage(stage)
    special = SPECIAL_CONTRACTS.get(normalized)
    if special:
        return CONTRACT_ROOT / special
    return LIFECYCLE_ROOT / f"{normalized}.yaml"


def available_contracts() -> list[str]:
    names = [stage for stage in STAGE_ORDER if contract_path_for_stage(stage).exists()]
    if (CONTRACT_ROOT / "release_readiness.yaml").exists():
        names.append("release-readiness")
    return names


def load_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise EvalError(f"eval contract not found: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise EvalError(
                f"{path} is not JSON-compatible YAML and PyYAML is not installed; "
                "use JSON-compatible YAML or install PyYAML"
            ) from exc
        loaded = yaml.safe_load(text)
        data = loaded
    if not isinstance(data, dict):
        raise EvalError(f"eval contract must be a mapping: {path}")
    return data


def load_contract(stage: str | None, contract_file: Path | None) -> tuple[dict[str, Any], Path]:
    path = contract_file.resolve() if contract_file else contract_path_for_stage(stage or "")
    contract = load_mapping(path)
    return contract, path


def rel_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def coerce_process_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def output_excerpt(stdout: str | bytes | None, stderr: str | bytes | None, *, cap: int = 1600) -> str:
    text = "\n".join(
        part for part in (coerce_process_text(stdout).strip(), coerce_process_text(stderr).strip()) if part
    )
    if len(text) <= cap:
        return text
    return text[:cap] + "\n...[truncated]"


def run_shell_gate(gate: dict[str, Any], *, repo_root: Path) -> GateResult:
    command = str(gate.get("command") or "").strip()
    if not command:
        return GateResult(
            gate_id=str(gate.get("id", "unnamed_gate")),
            status="failed",
            passed=False,
            required=bool(gate.get("required", True)),
            detail="command gate has no command",
        )
    timeout = int(gate.get("timeout_seconds", 180))
    try:
        result = subprocess.run(
            command,
            cwd=repo_root,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return GateResult(
            gate_id=str(gate.get("id", "unnamed_gate")),
            status="failed",
            passed=False,
            required=bool(gate.get("required", True)),
            detail=f"timed out after {timeout}s",
            command=command,
            output_excerpt=output_excerpt(exc.stdout or "", exc.stderr or ""),
        )
    redacted = bool(gate.get("redact_output", False))
    excerpt = "[redacted by eval contract]" if redacted and result.returncode != 0 else output_excerpt(result.stdout, result.stderr)
    return GateResult(
        gate_id=str(gate.get("id", "unnamed_gate")),
        status="passed" if result.returncode == 0 else "failed",
        passed=result.returncode == 0,
        required=bool(gate.get("required", True)),
        detail=str(gate.get("description", "")),
        command=command,
        exit_code=result.returncode,
        output_excerpt=excerpt,
    )


def file_gate(gate: dict[str, Any], *, repo_root: Path) -> GateResult:
    raw_path = str(gate.get("path") or "").strip()
    target = Path(raw_path)
    if not target.is_absolute():
        target = repo_root / target
    exists = target.exists()
    return GateResult(
        gate_id=str(gate.get("id", "unnamed_gate")),
        status="passed" if exists else "failed",
        passed=exists,
        required=bool(gate.get("required", True)),
        detail=f"{raw_path}: {'exists' if exists else 'missing'}",
    )


def evaluate_gates(contract: dict[str, Any], *, run_gates: bool, repo_root: Path) -> list[GateResult]:
    results: list[GateResult] = []
    for gate in contract.get("hard_gates", []):
        gate_id = str(gate.get("id", "unnamed_gate"))
        kind = str(gate.get("kind", "manual"))
        required = bool(gate.get("required", True))
        if kind == "command":
            if not run_gates:
                results.append(
                    GateResult(
                        gate_id=gate_id,
                        status="not_run",
                        passed=None,
                        required=required,
                        detail="command gate not run; rerun with --run-gates",
                        command=str(gate.get("command", "")),
                    )
                )
            else:
                results.append(run_shell_gate(gate, repo_root=repo_root))
        elif kind == "file_exists":
            results.append(file_gate(gate, repo_root=repo_root))
        elif kind == "manual":
            results.append(
                GateResult(
                    gate_id=gate_id,
                    status="manual",
                    passed=None,
                    required=required,
                    detail=str(gate.get("description", "manual gate requires human or target-surface proof")),
                )
            )
        else:
            results.append(
                GateResult(
                    gate_id=gate_id,
                    status="failed",
                    passed=False,
                    required=required,
                    detail=f"unknown gate kind: {kind}",
                )
            )
    return results


def load_review(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return load_mapping(path)


def rubric_dimensions(contract: dict[str, Any]) -> list[dict[str, Any]]:
    dimensions = contract.get("rubric", [])
    if not isinstance(dimensions, list):
        raise EvalError("contract rubric must be a list")
    return [dim for dim in dimensions if isinstance(dim, dict)]


def review_score_entry(review: dict[str, Any], dim_id: str) -> Any:
    scores = review.get("scores", {})
    if not isinstance(scores, dict):
        return None
    return scores.get(dim_id)


def score_review(contract: dict[str, Any], review: dict[str, Any] | None) -> dict[str, Any]:
    dimensions = rubric_dimensions(contract)
    total = 0.0
    max_total = 0.0
    missing: list[str] = []
    evidence_gaps: list[str] = []
    invalid: list[str] = []
    scored_dimensions: list[dict[str, Any]] = []

    if review is None:
        return {
            "status": "not_scored",
            "total": None,
            "max_total": sum(float(dim.get("max_score", 4)) for dim in dimensions),
            "percent": None,
            "dimensions": [
                {
                    "id": str(dim.get("id", "unnamed_dimension")),
                    "max_score": float(dim.get("max_score", 4)),
                    "status": "not_scored",
                }
                for dim in dimensions
            ],
            "missing": [str(dim.get("id", "unnamed_dimension")) for dim in dimensions],
            "evidence_gaps": [],
            "invalid": [],
        }

    require_evidence = bool(contract.get("require_evidence_for_scores", True))
    for dim in dimensions:
        dim_id = str(dim.get("id", "unnamed_dimension"))
        max_score = float(dim.get("max_score", 4))
        max_total += max_score
        entry = review_score_entry(review, dim_id)
        if entry is None:
            missing.append(dim_id)
            scored_dimensions.append({"id": dim_id, "max_score": max_score, "status": "missing"})
            continue
        if isinstance(entry, (int, float)):
            score = float(entry)
            evidence: list[str] = []
            notes = ""
        elif isinstance(entry, dict):
            raw_score = entry.get("score")
            try:
                if raw_score is None:
                    raise TypeError("missing score")
                score = float(raw_score)
            except (TypeError, ValueError):
                invalid.append(f"{dim_id}: score must be numeric")
                scored_dimensions.append({"id": dim_id, "max_score": max_score, "status": "invalid"})
                continue
            raw_evidence = entry.get("evidence", [])
            if isinstance(raw_evidence, str):
                evidence = [raw_evidence]
            elif isinstance(raw_evidence, list):
                evidence = [str(item) for item in raw_evidence if str(item).strip()]
            else:
                evidence = []
            notes = str(entry.get("notes", ""))
        else:
            invalid.append(f"{dim_id}: score entry must be number or object")
            scored_dimensions.append({"id": dim_id, "max_score": max_score, "status": "invalid"})
            continue
        if score < 0 or score > max_score:
            invalid.append(f"{dim_id}: score {score:g} outside 0-{max_score:g}")
            scored_dimensions.append({"id": dim_id, "max_score": max_score, "status": "invalid"})
            continue
        if require_evidence and not evidence:
            evidence_gaps.append(dim_id)
        total += score
        scored_dimensions.append(
            {
                "id": dim_id,
                "score": score,
                "max_score": max_score,
                "evidence": evidence,
                "notes": notes,
                "status": "scored",
            }
        )
    percent = (total / max_total * 100.0) if max_total else 100.0
    status = "scored"
    if missing or evidence_gaps or invalid:
        status = "incomplete"
    return {
        "status": status,
        "total": total,
        "max_total": max_total,
        "percent": percent,
        "dimensions": scored_dimensions,
        "missing": missing,
        "evidence_gaps": evidence_gaps,
        "invalid": invalid,
    }


def decide(contract: dict[str, Any], gates: list[GateResult], score: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    next_actions: list[str] = []

    failed_required = [gate.gate_id for gate in gates if gate.required and gate.passed is False]
    pending_required = [gate.gate_id for gate in gates if gate.required and gate.status in {"not_run", "manual"}]
    if failed_required:
        blockers.extend(f"hard gate failed: {gate_id}" for gate_id in failed_required)
        next_actions.append("fix failed hard gates and rerun eval")
        return "blocked", blockers, next_actions

    requires_review = bool(contract.get("requires_review", True))
    if requires_review and score["status"] == "not_scored":
        blockers.append("rubric review missing")
        next_actions.append("run with --review-template, have an evaluator fill scores with evidence, then pass --review-file")
        # Still call out hard gates, but review is the clearer next human/agent action.
        if pending_required:
            next_actions.append("rerun with --run-gates before accepting an advance decision")
        return "needs_agent_review", blockers, next_actions

    if pending_required:
        blockers.extend(f"hard gate pending: {gate_id}" for gate_id in pending_required)
        next_actions.append("rerun with --run-gates or attach target-surface proof for manual gates")
        return "needs_gate_execution", blockers, next_actions

    if score["status"] == "incomplete":
        for item in score.get("missing", []):
            blockers.append(f"rubric score missing: {item}")
        for item in score.get("evidence_gaps", []):
            blockers.append(f"rubric evidence missing: {item}")
        for item in score.get("invalid", []):
            blockers.append(f"invalid rubric score: {item}")
        next_actions.append("repair rubric review and rerun eval")
        return "revise", blockers, next_actions

    threshold = float(contract.get("advance_min_score_percent", 80))
    percent = score.get("percent")
    if percent is not None and percent < threshold:
        blockers.append(f"rubric score below threshold: {percent:.1f}% < {threshold:.1f}%")
        next_actions.append("revise artifact, then rescore with evidence")
        return "revise", blockers, next_actions

    if bool(contract.get("requires_human_approval", False)):
        next_actions.append("request owner approval before external release/push/public claim")
        return "needs_human_approval", blockers, next_actions

    next_actions.append("advance to next lifecycle stage")
    return "advance", blockers, next_actions


def review_template(contract: dict[str, Any]) -> dict[str, Any]:
    stage = contract.get("stage") or contract.get("slug") or "unknown"
    return {
        "schema": "weave.eval-review/v0.1",
        "stage": stage,
        "reviewer": "agent-or-human-name",
        "artifact": "describe artifact or path",
        "scores": {
            str(dim.get("id", "unnamed_dimension")): {
                "score": None,
                "evidence": [],
                "notes": "",
            }
            for dim in rubric_dimensions(contract)
        },
        "overall_notes": "",
    }


def result_payload(
    contract: dict[str, Any],
    contract_path: Path,
    *,
    artifact: str,
    gates: list[GateResult],
    score: dict[str, Any],
    decision: str,
    blockers: list[str],
    next_actions: list[str],
) -> dict[str, Any]:
    return {
        "schema": "weave.eval-result/v0.1",
        "stage": contract.get("stage") or contract.get("slug"),
        "slug": contract.get("slug"),
        "artifact": artifact,
        "contract": rel_path(contract_path),
        "state": state_label(decision),
        "hard_gates": [gate.__dict__ for gate in gates],
        "rubric_score": score,
        "decision": decision,
        "blockers": blockers,
        "next_actions": next_actions,
    }


def state_label(decision: str) -> str:
    return {
        "advance": "verified",
        "needs_human_approval": "verified; approval-gated",
        "blocked": "blocked",
        "needs_agent_review": "staged; rubric-not-scored",
        "needs_gate_execution": "staged; hard-gates-pending",
        "revise": "staged; revision-required",
    }.get(decision, "unknown")


def print_result(payload: dict[str, Any], output: TextIO) -> None:
    print("WEAVE Lifecycle Eval", file=output)
    print(f"stage: {payload.get('stage')}", file=output)
    print(f"artifact: {payload.get('artifact')}", file=output)
    print(f"contract: {payload.get('contract')}", file=output)
    print(f"state: {payload.get('state')}", file=output)
    print("", file=output)
    print("Hard gates", file=output)
    gates = payload.get("hard_gates", [])
    if not gates:
        print("- none", file=output)
    for gate in gates:
        print(f"- {gate['gate_id']}: {gate['status']}", file=output)
        if gate.get("command"):
            print(f"  command: {gate['command']}", file=output)
        if gate.get("exit_code") is not None:
            print(f"  exit_code: {gate['exit_code']}", file=output)
        if gate.get("output_excerpt"):
            print("  output_excerpt:", file=output)
            for line in str(gate["output_excerpt"]).splitlines()[:8]:
                print(f"    {line}", file=output)
    print("", file=output)
    score = payload["rubric_score"]
    print("Rubric", file=output)
    if score.get("status") == "not_scored":
        print(f"- status: not_scored; max_score: {score.get('max_total'):g}", file=output)
    else:
        print(
            f"- score: {score.get('total'):g}/{score.get('max_total'):g} ({score.get('percent'):.1f}%)",
            file=output,
        )
        print(f"- status: {score.get('status')}", file=output)
    for dim in score.get("dimensions", []):
        if dim.get("status") == "scored":
            print(f"- {dim['id']}: {dim['score']:g}/{dim['max_score']:g}", file=output)
        else:
            print(f"- {dim['id']}: {dim.get('status')}", file=output)
    print("", file=output)
    print(f"decision: {payload.get('decision')}", file=output)
    blockers = payload.get("blockers", [])
    print("blockers:", file=output)
    if blockers:
        for blocker in blockers:
            print(f"- {blocker}", file=output)
    else:
        print("- none", file=output)
    print("next:", file=output)
    for item in payload.get("next_actions", []):
        print(f"- {item}", file=output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run evidence-bound WEAVE lifecycle evals")
    parser.add_argument("stage", nargs="?", help="lifecycle stage or release-readiness")
    parser.add_argument("--list", action="store_true", help="list available eval contracts")
    parser.add_argument("--contract-file", type=Path, help="load an explicit eval contract file")
    parser.add_argument("--review-file", type=Path, help="JSON/YAML review with rubric scores and evidence")
    parser.add_argument("--review-template", action="store_true", help="print a review template for this contract")
    parser.add_argument("--artifact", default="current", help="artifact label/path being evaluated")
    parser.add_argument("--run-gates", action="store_true", help="execute command hard gates")
    parser.add_argument("--strict", action="store_true", help="exit non-zero unless decision can advance")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None, *, output: TextIO = sys.stdout) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.list:
            for name in available_contracts():
                print(name, file=output)
            return 0
        if not args.stage and not args.contract_file:
            raise EvalError("stage is required unless --list or --contract-file is used")
        contract, contract_path = load_contract(args.stage, args.contract_file)
        if args.review_template:
            print(json.dumps(review_template(contract), indent=2, sort_keys=True), file=output)
            return 0
        review = load_review(args.review_file)
        gates = evaluate_gates(contract, run_gates=args.run_gates, repo_root=REPO_ROOT)
        score = score_review(contract, review)
        decision, blockers, next_actions = decide(contract, gates, score)
        payload = result_payload(
            contract,
            contract_path,
            artifact=args.artifact,
            gates=gates,
            score=score,
            decision=decision,
            blockers=blockers,
            next_actions=next_actions,
        )
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=output)
        else:
            print_result(payload, output)
        failed_gate = any(gate.required and gate.passed is False for gate in gates)
        if failed_gate or (args.strict and decision not in ADVANCE_DECISIONS):
            return 1
        return 0
    except EvalError as exc:
        print(f"eval error: {exc}", file=output)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

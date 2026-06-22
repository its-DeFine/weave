#!/usr/bin/env python3
"""Validate the public WEAVE COS package."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


EXPECTED_VERSION = "0.1.0"
EXPECTED_RELEASE_DATE = "2026-06-22"
REQUIRED_SKILLS = {
    "codebase-orientation",
    "compound-engineering",
    "cos-weave",
    "engineering-execution",
    "evidence-packet",
    "implementation-planning",
    "primitive-market-research",
    "qa-verification",
    "security-release-review",
    "weave-lifecycle",
}
REQUIRED_EVALS = {
    "lifecycle/intent.yaml",
    "lifecycle/research.yaml",
    "lifecycle/selection.yaml",
    "lifecycle/plan.yaml",
    "lifecycle/engineering.yaml",
    "lifecycle/qa.yaml",
    "lifecycle/deployment.yaml",
    "lifecycle/kpi-setup.yaml",
    "lifecycle/marketing.yaml",
    "lifecycle/iteration.yaml",
    "lifecycle/analysis.yaml",
    "release_readiness.yaml",
}
LEGACY_SURFACE_TERMS = ("Her" + "mes", "Tele" + "gram", "Tex" + "tual", "T" + "UI", "Sym" + "phony", "Sym" + "phone")
HOST_ROOTS = ("/" + "Users", "/" + "home")

FORBIDDEN_PUBLIC_PATTERNS = [
    (
        re.compile(r"\b(?:" + "|".join(re.escape(term) for term in LEGACY_SURFACE_TERMS) + r")\b", re.I),
        "legacy runtime surface",
    ),
    (
        re.compile(rf"(?:{re.escape(HOST_ROOTS[0])}|{re.escape(HOST_ROOTS[1])})/[A-Za-z0-9_.-]+"),
        "host-specific path",
    ),
    (re.compile(r"\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168|100\.\d{1,3})\.\d{1,3}\.\d{1,3}\b"), "private network address"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key material"),
    (re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|Bearer\s+[A-Za-z0-9._-]{20,})\b"), "credential-like token"),
]


class PackageValidationError(Exception):
    """Raised when the package is malformed or not review-ready."""


@dataclass(frozen=True)
class PackageSummary:
    slug: str
    version: str
    skill_count: int
    primitive_count: int
    eval_contract_count: int


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise PackageValidationError(f"{path}: missing frontmatter")
    try:
        block = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise PackageValidationError(f"{path}: malformed frontmatter") from exc
    fields: dict[str, str] = {}
    for raw in block.splitlines():
        if ":" not in raw or raw.startswith(" "):
            continue
        key, value = raw.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def scan_forbidden_text(package_root: Path) -> None:
    for path in package_root.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".json", ".yaml", ".yml", ".py"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern, label in FORBIDDEN_PUBLIC_PATTERNS:
            match = pattern.search(text)
            if match:
                rel = path.relative_to(package_root)
                raise PackageValidationError(f"{rel}: forbidden {label}: {match.group(0)!r}")


def validate_company(package_root: Path) -> dict[str, str]:
    fields = parse_frontmatter(package_root / "COMPANY.md")
    expected = {
        "schema": "agentcompanies/v1",
        "kind": "company",
        "slug": "weave",
        "version": EXPECTED_VERSION,
        "releaseDate": EXPECTED_RELEASE_DATE,
        "releaseTag": "v0.1.0",
        "releaseChannel": "public-v0.1",
    }
    for key, value in expected.items():
        if fields.get(key) != value:
            raise PackageValidationError(f"COMPANY.md {key} must be {value}")
    return fields


def validate_skills(package_root: Path) -> set[str]:
    skill_paths = sorted((package_root / "skills").glob("*/SKILL.md"))
    slugs = {path.parent.name for path in skill_paths}
    if slugs != REQUIRED_SKILLS:
        missing = sorted(REQUIRED_SKILLS - slugs)
        extra = sorted(slugs - REQUIRED_SKILLS)
        raise PackageValidationError(f"skill set mismatch; missing={missing}; extra={extra}")
    for path in skill_paths:
        fields = parse_frontmatter(path)
        if fields.get("name") != path.parent.name:
            raise PackageValidationError(f"{path}: skill name must match directory")
        if not fields.get("description"):
            raise PackageValidationError(f"{path}: description is required")
    return slugs


def validate_evals(package_root: Path) -> list[Path]:
    eval_root = package_root / "evals"
    paths = sorted(path.relative_to(eval_root).as_posix() for path in eval_root.rglob("*.yaml"))
    if set(paths) != REQUIRED_EVALS:
        missing = sorted(REQUIRED_EVALS - set(paths))
        extra = sorted(set(paths) - REQUIRED_EVALS)
        raise PackageValidationError(f"eval set mismatch; missing={missing}; extra={extra}")
    for rel in paths:
        payload = json.loads((eval_root / rel).read_text(encoding="utf-8"))
        for key in ["schema", "slug", "stage", "hard_gates", "rubric"]:
            if key not in payload:
                raise PackageValidationError(f"evals/{rel}: missing {key}")
    return [eval_root / rel for rel in paths]


def validate_primitives(package_root: Path) -> list[dict[str, object]]:
    path = package_root / "primitives" / "registry.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    primitives = payload.get("primitives")
    if not isinstance(primitives, list) or len(primitives) < 9:
        raise PackageValidationError("primitives/registry.json must define at least nine lifecycle primitives")
    required = {"intent", "research", "selection", "plan", "engineering", "qa", "deployment", "kpi-setup", "marketing", "iteration", "analysis"}
    stages = {str(item.get("lifecycleStage")) for item in primitives if isinstance(item, dict)}
    if not required.issubset(stages):
        raise PackageValidationError(f"primitive stages missing: {sorted(required - stages)}")
    return primitives


def validate_package(package_root: Path) -> PackageSummary:
    package_root = package_root.resolve()
    fields = validate_company(package_root)
    skills = validate_skills(package_root)
    evals = validate_evals(package_root)
    primitives = validate_primitives(package_root)
    scan_forbidden_text(package_root)
    return PackageSummary(
        slug=fields["slug"],
        version=fields["version"],
        skill_count=len(skills),
        primitive_count=len(primitives),
        eval_contract_count=len(evals),
    )


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    package_root = Path(args[0]) if args else Path(__file__).resolve().parents[1]
    try:
        summary = validate_package(package_root)
    except (OSError, json.JSONDecodeError, PackageValidationError) as exc:
        print(f"package validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"valid WEAVE package: {summary.slug}")
    print(f"version: {summary.version}")
    print(f"skills: {summary.skill_count}")
    print(f"primitives: {summary.primitive_count}")
    print(f"eval_contracts: {summary.eval_contract_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

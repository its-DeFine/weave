#!/usr/bin/env python3
"""Validate the WEAVE OpenClaw-first company package.

The validator intentionally avoids third-party YAML dependencies. It checks the
small portable subset used by the package frontmatter and validates the runtime
boundaries that matter before local runtime use.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_STAGES = [
    "intent",
    "research-analysis",
    "selection",
    "plan",
    "engineering-integration",
    "qa-readiness",
    "kpi-setup",
    "marketing",
    "iteration",
]

REQUIRED_DEPENDENCIES = {
    "research-gate": "intent-contract",
    "selection-gate": "research-gate",
    "plan-gate": "selection-gate",
    "engineering-first-primitive": "plan-gate",
    "qa-runtime-readiness": "engineering-first-primitive",
    "kpi-setup-gate": "qa-runtime-readiness",
    "marketing-gate": "kpi-setup-gate",
    "iteration-from-analytics": "marketing-gate",
}

REQUIRED_SKILLS = {
    "codebase-orientation",
    "implementation-planning",
    "engineering-execution",
    "qa-verification",
    "security-release-review",
    "evidence-packet",
    "runtime-bridge",
    "weave-lifecycle",
    "primitive-market-research",
    "lifecycle-runtime-builder",
    "livepeer-adapter-boundary",
}

EXPECTED_VERSION = "2026.05.13-console"
EXPECTED_RELEASE_DATE = "2026-05-13"
EXPECTED_RELEASE_TAG = "v2026.05.13-console"
EXPECTED_RELEASE_CHANNEL = "public-d1-console"

ABSOLUTE_PATH_PATTERN = r"(?:/" + "Users/|/" + "home/|/" + "var/lib/|/" + "tmp/)"
LOOPBACK_PATTERN = r"\b(?:" + r"127\.0\.0\.1|" + "local" + "host|" + "host" + r"\.docker\.internal)\b"

FORBIDDEN_TEXT_PATTERNS = [
    (re.compile(ABSOLUTE_PATH_PATTERN), "host-specific absolute path"),
    (re.compile(LOOPBACK_PATTERN, re.I), "loopback or host-only hostname"),
    (re.compile(r"\b(?:192\.168\.|100\.77\.)\d{1,3}\.\d{1,3}\b"), "private infrastructure address"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key material"),
    (re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{12,})\b"), "credential-like token"),
    (re.compile(r"\b0x[a-fA-F0-9]{40}\b"), "wallet address"),
]


class PackageValidationError(Exception):
    pass


@dataclass(frozen=True)
class PackageSummary:
    slug: str
    version: str
    agent_count: int
    task_count: int
    skill_count: int
    primitive_count: int


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise PackageValidationError(f"{path}: missing frontmatter")
    try:
        block = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise PackageValidationError(f"{path}: malformed frontmatter") from exc

    fields: dict[str, str] = {}
    active_key: str | None = None
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("- "):
            continue
        if line.startswith("  "):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        active_key = key.strip()
        fields[active_key] = value.strip().strip('"').strip("'")
    return fields


def parse_sequence_field(path: Path, key: str) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise PackageValidationError(f"{path}: missing frontmatter")
    try:
        block = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise PackageValidationError(f"{path}: malformed frontmatter") from exc

    lines = block.splitlines()
    try:
        start = lines.index(f"{key}:")
    except ValueError:
        return []

    values: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("  - "):
            values.append(line.split("- ", 1)[1].strip())
            continue
        if line and not line.startswith(" "):
            break
    return values


def scan_forbidden_text(package_root: Path) -> None:
    for path in package_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".md", ".yaml", ".yml", ".json", ".py"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, label in FORBIDDEN_TEXT_PATTERNS:
            match = pattern.search(text)
            if match:
                relative = path.relative_to(package_root)
                raise PackageValidationError(f"{relative}: forbidden {label}: {match.group(0)}")


def validate_company(package_root: Path) -> dict[str, str]:
    company_path = package_root / "COMPANY.md"
    if not company_path.exists():
        raise PackageValidationError("COMPANY.md is required")
    fields = parse_frontmatter(company_path)
    if fields.get("schema") != "agentcompanies/v1":
        raise PackageValidationError("COMPANY.md must use schema agentcompanies/v1")
    if fields.get("kind") != "company":
        raise PackageValidationError("COMPANY.md kind must be company")
    if fields.get("slug") != "weave":
        raise PackageValidationError("COMPANY.md slug must be weave")
    if fields.get("version") != EXPECTED_VERSION:
        raise PackageValidationError(f"COMPANY.md version must be {EXPECTED_VERSION}")
    if fields.get("releaseDate") != EXPECTED_RELEASE_DATE:
        raise PackageValidationError(f"COMPANY.md releaseDate must be {EXPECTED_RELEASE_DATE}")
    if fields.get("releaseTag") != EXPECTED_RELEASE_TAG:
        raise PackageValidationError(f"COMPANY.md releaseTag must be {EXPECTED_RELEASE_TAG}")
    if fields.get("releaseChannel") != EXPECTED_RELEASE_CHANNEL:
        raise PackageValidationError(f"COMPANY.md releaseChannel must be {EXPECTED_RELEASE_CHANNEL}")
    if fields.get("runtime") != "openclaw-solo":
        raise PackageValidationError("COMPANY.md runtime must be openclaw-solo")
    return fields


def validate_skills(package_root: Path) -> set[str]:
    skill_paths = sorted((package_root / "skills").glob("*/SKILL.md"))
    if not skill_paths:
        raise PackageValidationError("at least one skill is required")

    skill_slugs: set[str] = set()
    for path in skill_paths:
        fields = parse_frontmatter(path)
        slug = path.parent.name
        if fields.get("name") != slug:
            raise PackageValidationError(f"{path}: skill name must match directory {slug}")
        if not fields.get("description"):
            raise PackageValidationError(f"{path}: skill description is required")
        text = path.read_text(encoding="utf-8")
        for heading in ("## Use When", "## Inputs", "## Outputs", "## Rules", "## Stop Conditions", "## Verification"):
            if heading not in text:
                raise PackageValidationError(f"{path}: missing {heading}")
        skill_slugs.add(slug)

    missing = sorted(REQUIRED_SKILLS - skill_slugs)
    if missing:
        raise PackageValidationError(f"missing required skills: {', '.join(missing)}")
    return skill_slugs


def validate_agents(package_root: Path, skill_slugs: set[str] | None = None) -> list[dict[str, str]]:
    agent_paths = sorted((package_root / "agents").glob("*/AGENTS.md"))
    if not agent_paths:
        raise PackageValidationError("at least one agent is required")

    agents = []
    slugs: set[str] = set()
    ceos = []
    for path in agent_paths:
        fields = parse_frontmatter(path)
        slug = fields.get("slug", "")
        if not slug:
            raise PackageValidationError(f"{path}: agent slug is required")
        if slug in slugs:
            raise PackageValidationError(f"duplicate agent slug: {slug}")
        slugs.add(slug)
        skills = parse_sequence_field(path, "skills")
        if not skills:
            raise PackageValidationError(f"{path}: at least one skill is required")
        if skill_slugs is not None:
            unknown = sorted(set(skills) - skill_slugs)
            if unknown:
                raise PackageValidationError(f"{path}: unknown skills: {', '.join(unknown)}")
        if fields.get("reportsTo") == "null":
            ceos.append(fields)
        elif fields.get("reportsTo") not in slugs and fields.get("reportsTo") != "ceo-openclaw":
            raise PackageValidationError(f"{path}: reportsTo must reference ceo-openclaw or an earlier agent")
        agents.append(fields)

    if len(ceos) != 1:
        raise PackageValidationError(f"expected exactly one CEO, found {len(ceos)}")
    ceo = ceos[0]
    if ceo.get("slug") != "ceo-openclaw":
        raise PackageValidationError("CEO slug must be ceo-openclaw")
    if ceo.get("adapterType") != "openclaw_gateway":
        raise PackageValidationError("CEO adapterType must be openclaw_gateway")
    if "OpenClaw" not in ceo.get("name", ""):
        raise PackageValidationError("CEO name must identify OpenClaw")
    return agents


def validate_tasks(package_root: Path) -> list[dict[str, str]]:
    task_paths = sorted((package_root / "projects").glob("*/tasks/*/TASK.md"))
    if not task_paths:
        raise PackageValidationError("at least one starter task is required")

    tasks = []
    slugs: set[str] = set()
    stages: dict[str, str] = {}
    for path in task_paths:
        fields = parse_frontmatter(path)
        slug = fields.get("slug", "")
        stage = fields.get("lifecycleStage", "")
        if not slug:
            raise PackageValidationError(f"{path}: task slug is required")
        if slug in slugs:
            raise PackageValidationError(f"duplicate task slug: {slug}")
        if stage not in REQUIRED_STAGES:
            raise PackageValidationError(f"{path}: invalid lifecycleStage {stage}")
        slugs.add(slug)
        stages[stage] = slug
        tasks.append(fields)

    missing = [stage for stage in REQUIRED_STAGES if stage not in stages]
    if missing:
        raise PackageValidationError(f"missing lifecycle stages: {', '.join(missing)}")

    for slug, required in REQUIRED_DEPENDENCIES.items():
        task = next((item for item in tasks if item.get("slug") == slug), None)
        if task is None:
            raise PackageValidationError(f"missing task {slug}")
        if task.get("dependsOn") != required:
            raise PackageValidationError(f"{slug} must depend on {required}")

    return tasks


def validate_primitives(package_root: Path) -> int:
    registry_path = package_root / "primitives" / "registry.json"
    if not registry_path.exists():
        raise PackageValidationError("primitives/registry.json is required")
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    primitives = data.get("primitives", [])
    if not isinstance(primitives, list) or not primitives:
        raise PackageValidationError("primitive registry must contain primitives")
    ids = [item.get("id") for item in primitives if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        raise PackageValidationError("primitive ids must be unique")
    if data.get("application") != "askuno-runtime-proof":
        raise PackageValidationError("primitive registry must target askuno-runtime-proof")
    return len(primitives)


def validate_package(package_root: Path) -> PackageSummary:
    root = package_root.resolve()
    if not root.exists():
        raise PackageValidationError(f"package root does not exist: {package_root}")
    scan_forbidden_text(root)
    company = validate_company(root)
    skill_slugs = validate_skills(root)
    agents = validate_agents(root, skill_slugs)
    tasks = validate_tasks(root)
    primitive_count = validate_primitives(root)
    return PackageSummary(
        slug=company["slug"],
        version=company["version"],
        agent_count=len(agents),
        task_count=len(tasks),
        skill_count=len(skill_slugs),
        primitive_count=primitive_count,
    )


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    package_root = Path(args[0]) if args else Path(__file__).resolve().parents[1]
    try:
        summary = validate_package(package_root)
    except PackageValidationError as exc:
        print(f"invalid WEAVE company package: {exc}", file=sys.stderr)
        return 1

    print(f"valid WEAVE company package: {summary.slug}")
    print(f"version: {summary.version}")
    print(f"agents: {summary.agent_count}")
    print(f"tasks: {summary.task_count}")
    print(f"skills: {summary.skill_count}")
    print(f"primitives: {summary.primitive_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

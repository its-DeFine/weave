#!/usr/bin/env python3
"""Validate the WEAVE Hermes-default company package.

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
    "deployment-readiness",
    "kpi-setup",
    "marketing",
    "iteration",
]

CANONICAL_LIFECYCLE_STAGES = {
    "intent": "Intent",
    "research": "Research",
    "selection": "Selection",
    "plan": "Plan",
    "engineering": "Engineering",
    "qa": "QA",
    "deployment": "Deployment",
    "kpi-setup": "KPI Setup",
    "marketing": "Marketing",
    "iteration": "Iteration",
    "analysis": "Analysis",
}
LIFECYCLE_STAGE_ALIASES = {
    "intent": "intent",
    "research": "research",
    "research-analysis": "research",
    "selection": "selection",
    "plan": "plan",
    "engineering": "engineering",
    "engineering-integration": "engineering",
    "qa": "qa",
    "qa-readiness": "qa",
    "deployment": "deployment",
    "deployment-readiness": "deployment",
    "kpi-setup": "kpi-setup",
    "marketing": "marketing",
    "iteration": "iteration",
    "analysis": "analysis",
}
REQUIRED_EVAL_LIFECYCLE_SLUGS = set(CANONICAL_LIFECYCLE_STAGES)

REQUIRED_DEPENDENCIES = {
    "research-gate": "intent-contract",
    "selection-gate": "research-gate",
    "plan-gate": "selection-gate",
    "engineering-first-primitive": "plan-gate",
    "qa-runtime-readiness": "engineering-first-primitive",
    "deployment-readiness-gate": "qa-runtime-readiness",
    "kpi-setup-gate": "deployment-readiness-gate",
    "marketing-gate": "kpi-setup-gate",
    "iteration-from-analytics": "kpi-setup-gate",
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
    "gestalt-runtime",
}

REQUIRED_EVAL_CONTRACTS = [
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
]
REQUIRED_RUNTIME_QA_RESOURCE_STATES = {
    "created",
    "running",
    "completed",
    "teardown_requested",
    "stopped",
    "removed",
    "phased_out",
}
RUNTIME_QA_MANIFEST_SCHEMA = "weave.runtime-qa-manifest/v0.1"
RUNTIME_QA_CLEANUP_POLICY_SCHEMA = "weave.runtime-cleanup-policy/v0.1"

EXPECTED_VERSION = "2026.05.13-console"
EXPECTED_RELEASE_DATE = "2026-05-13"
EXPECTED_RELEASE_TAG = "v2026.05.13-console"
EXPECTED_RELEASE_CHANNEL = "public-d1-console"
PRIMARY_RUNTIME = "hermes-default"
FALLBACK_RUNTIME = "local-fallback"
CEO_SLUG = "ceo-hermes"
CEO_ADAPTER = "hermes_runtime"
FALLBACK_AGENT_SLUG = "ceo-fallback"
FALLBACK_ADAPTER = "local_fallback_gateway"
GESTALT_PROMPT_PACK = "hermes-gestalt-runtime-pack"
PROMPT_PACK_SCHEMA = "weave-hermes-gestalt-runtime-pack/v0.1"
PRIMITIVE_REGISTRY_APPLICATION = "weave-lifecycle-runtime"
PRIMITIVE_REGISTRY_SCOPE = "cross-application-lifecycle-primitives"

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
    prompt_pack_count: int
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
    if fields.get("runtime") != PRIMARY_RUNTIME:
        raise PackageValidationError(f"COMPANY.md runtime must be {PRIMARY_RUNTIME}")
    if fields.get("runtimeFallback") != FALLBACK_RUNTIME:
        raise PackageValidationError(f"COMPANY.md runtimeFallback must be {FALLBACK_RUNTIME}")
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
        elif fields.get("reportsTo") not in slugs and fields.get("reportsTo") not in {CEO_SLUG, FALLBACK_AGENT_SLUG}:
            raise PackageValidationError(f"{path}: reportsTo must reference {CEO_SLUG}, {FALLBACK_AGENT_SLUG}, or an earlier agent")
        agents.append(fields)

    if len(ceos) != 1:
        raise PackageValidationError(f"expected exactly one CEO, found {len(ceos)}")
    ceo = ceos[0]
    if ceo.get("slug") != CEO_SLUG:
        raise PackageValidationError(f"CEO slug must be {CEO_SLUG}")
    if ceo.get("adapterType") != CEO_ADAPTER:
        raise PackageValidationError(f"CEO adapterType must be {CEO_ADAPTER}")
    if ceo.get("promptPack") != GESTALT_PROMPT_PACK:
        raise PackageValidationError(f"CEO promptPack must be {GESTALT_PROMPT_PACK}")
    if "Hermes" not in ceo.get("name", ""):
        raise PackageValidationError("CEO name must identify Hermes")
    fallback = next((agent for agent in agents if agent.get("slug") == FALLBACK_AGENT_SLUG), None)
    if fallback is None:
        raise PackageValidationError(f"fallback agent {FALLBACK_AGENT_SLUG} is required")
    if fallback.get("adapterType") != FALLBACK_ADAPTER:
        raise PackageValidationError(f"{FALLBACK_AGENT_SLUG} adapterType must be {FALLBACK_ADAPTER}")
    if fallback.get("reportsTo") != CEO_SLUG:
        raise PackageValidationError(f"{FALLBACK_AGENT_SLUG} must report to {CEO_SLUG}")
    return agents


def validate_prompt_packs(package_root: Path) -> int:
    prompt_root = package_root / "prompts" / GESTALT_PROMPT_PACK
    manifest_path = prompt_root / "manifest.json"
    if not manifest_path.exists():
        raise PackageValidationError(f"prompt pack manifest is required: prompts/{GESTALT_PROMPT_PACK}/manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != PROMPT_PACK_SCHEMA:
        raise PackageValidationError(f"{manifest_path}: schema must be {PROMPT_PACK_SCHEMA}")
    if manifest.get("pack_id") != GESTALT_PROMPT_PACK:
        raise PackageValidationError(f"{manifest_path}: pack_id must be {GESTALT_PROMPT_PACK}")
    if manifest.get("runtime") != "nousresearch-hermes-agent":
        raise PackageValidationError(f"{manifest_path}: runtime must be nousresearch-hermes-agent")
    if manifest.get("secret_payload_allowed") is not False:
        raise PackageValidationError(f"{manifest_path}: secret_payload_allowed must be false")
    required_modes = {
        "Contract Mode",
        "Premortem Mode",
        "Implementation Mode",
        "Contract Update Mode",
    }
    modes = set(manifest.get("required_modes", []))
    if required_modes - modes:
        raise PackageValidationError(f"{manifest_path}: missing modes: {', '.join(sorted(required_modes - modes))}")
    files = manifest.get("files", [])
    if not isinstance(files, list) or not files:
        raise PackageValidationError(f"{manifest_path}: files must list prompt files")
    combined = []
    for name in files:
        if not isinstance(name, str) or "/" in name or name.startswith("."):
            raise PackageValidationError(f"{manifest_path}: invalid prompt file entry {name!r}")
        path = prompt_root / name
        if not path.exists():
            raise PackageValidationError(f"missing prompt pack file: prompts/{GESTALT_PROMPT_PACK}/{name}")
        combined.append(path.read_text(encoding="utf-8"))
    text = "\n".join(combined)
    required_markers = [
        "Gestalt Kernel",
        "Gestaltian Contract",
        "Premortem Report",
        "Build-Ready Handoff Packet",
        "Implementation Report",
        "Contract Update Log",
        "Functional validation",
        "Failure validation",
        "Gestalt validation",
        "Traceability Requirement",
    ]
    for marker in required_markers:
        if marker not in text:
            raise PackageValidationError(f"prompt pack missing marker: {marker}")
    return 1


def canonical_lifecycle_slug(stage: str, *, context: str) -> str:
    canonical = LIFECYCLE_STAGE_ALIASES.get(stage)
    if canonical is None:
        raise PackageValidationError(f"{context}: invalid lifecycle stage {stage}")
    return canonical


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
        canonical_lifecycle_slug(stage, context=str(path))
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
    if data.get("application") != PRIMITIVE_REGISTRY_APPLICATION:
        raise PackageValidationError(f"primitive registry must target {PRIMITIVE_REGISTRY_APPLICATION}")
    if data.get("registryScope") != PRIMITIVE_REGISTRY_SCOPE:
        raise PackageValidationError(f"primitive registry must declare scope {PRIMITIVE_REGISTRY_SCOPE}")
    return len(primitives)


def validate_runtime_qa_eval_contract(relative_name: str, contract: dict[str, object]) -> None:
    runtime_qa = contract.get("runtime_agent_qa")
    if not isinstance(runtime_qa, dict):
        raise PackageValidationError(f"evals/{relative_name}: runtime_agent_qa requirements are required")
    if runtime_qa.get("teardown_policy_required") is not True:
        raise PackageValidationError(f"evals/{relative_name}: runtime_agent_qa.teardown_policy_required must be true")
    if runtime_qa.get("manifest_schema") != RUNTIME_QA_MANIFEST_SCHEMA:
        raise PackageValidationError(f"evals/{relative_name}: runtime_agent_qa.manifest_schema must be {RUNTIME_QA_MANIFEST_SCHEMA}")
    if runtime_qa.get("cleanup_policy_schema") != RUNTIME_QA_CLEANUP_POLICY_SCHEMA:
        raise PackageValidationError(f"evals/{relative_name}: runtime_agent_qa.cleanup_policy_schema must be {RUNTIME_QA_CLEANUP_POLICY_SCHEMA}")
    states = runtime_qa.get("resource_states_required")
    if not isinstance(states, list) or not all(isinstance(item, str) for item in states):
        raise PackageValidationError(f"evals/{relative_name}: runtime_agent_qa.resource_states_required must be a list of strings")
    missing_states = sorted(REQUIRED_RUNTIME_QA_RESOURCE_STATES - set(states))
    if missing_states:
        raise PackageValidationError(f"evals/{relative_name}: missing runtime QA resource states: {', '.join(missing_states)}")
    required_inputs = contract.get("required_inputs")
    input_text = "\n".join(required_inputs) if isinstance(required_inputs, list) else ""
    for marker in ("runtime resource lifecycle manifest", "teardown policy"):
        if marker not in input_text:
            raise PackageValidationError(f"evals/{relative_name}: required_inputs must mention {marker}")
    gate_text = json.dumps(contract.get("hard_gates", []), sort_keys=True)
    if "teardown policy" not in gate_text or "lifecycle cleanup states" not in gate_text:
        raise PackageValidationError(f"evals/{relative_name}: hard_gates must require teardown/lifecycle cleanup evidence")


def validate_eval_contracts(package_root: Path) -> int:
    eval_root = package_root / "evals"
    seen_slugs: set[str] = set()
    for relative_name in REQUIRED_EVAL_CONTRACTS:
        path = eval_root / relative_name
        if not path.exists():
            raise PackageValidationError(f"missing eval contract: evals/{relative_name}")
        try:
            contract = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PackageValidationError(f"evals/{relative_name}: invalid JSON-compatible contract: {exc}") from exc
        if contract.get("schema") not in {"weave.lifecycle-eval/v0.1", "weave.release-eval/v0.1"}:
            raise PackageValidationError(f"evals/{relative_name}: schema must be weave.lifecycle-eval/v0.1 or weave.release-eval/v0.1")
        slug = contract.get("slug")
        if not isinstance(slug, str) or not slug:
            raise PackageValidationError(f"evals/{relative_name}: slug is required")
        if slug in seen_slugs:
            raise PackageValidationError(f"duplicate eval contract slug: {slug}")
        seen_slugs.add(slug)
        if not contract.get("stage"):
            raise PackageValidationError(f"evals/{relative_name}: stage is required")
        if not isinstance(contract.get("hard_gates"), list):
            raise PackageValidationError(f"evals/{relative_name}: hard_gates must be a list")
        if not isinstance(contract.get("rubric"), list) or not contract["rubric"]:
            raise PackageValidationError(f"evals/{relative_name}: rubric must be a non-empty list")
        for gate in contract["hard_gates"]:
            if not isinstance(gate, dict) or not gate.get("id") or not gate.get("kind"):
                raise PackageValidationError(f"evals/{relative_name}: every hard gate needs id and kind")
        for dimension in contract["rubric"]:
            if not isinstance(dimension, dict) or not dimension.get("id") or not dimension.get("max_score"):
                raise PackageValidationError(f"evals/{relative_name}: every rubric dimension needs id and max_score")
        if relative_name == "lifecycle/qa.yaml":
            validate_runtime_qa_eval_contract(relative_name, contract)
    return len(REQUIRED_EVAL_CONTRACTS)


def validate_package(package_root: Path) -> PackageSummary:
    root = package_root.resolve()
    if not root.exists():
        raise PackageValidationError(f"package root does not exist: {package_root}")
    scan_forbidden_text(root)
    company = validate_company(root)
    skill_slugs = validate_skills(root)
    prompt_pack_count = validate_prompt_packs(root)
    agents = validate_agents(root, skill_slugs)
    tasks = validate_tasks(root)
    primitive_count = validate_primitives(root)
    eval_contract_count = validate_eval_contracts(root)
    return PackageSummary(
        slug=company["slug"],
        version=company["version"],
        agent_count=len(agents),
        task_count=len(tasks),
        skill_count=len(skill_slugs),
        primitive_count=primitive_count,
        prompt_pack_count=prompt_pack_count,
        eval_contract_count=eval_contract_count,
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
    print(f"prompt_packs: {summary.prompt_pack_count}")
    print(f"eval_contracts: {summary.eval_contract_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

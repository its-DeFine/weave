#!/usr/bin/env python3
"""Validate that public docs describe the current COS WEAVE product."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

CANONICAL_STAGES = [
    "intent",
    "research",
    "selection",
    "plan",
    "engineering",
    "qa",
    "deployment",
    "kpi-setup",
    "marketing",
    "iteration",
    "analysis",
]

CORE_DOCS = [
    "CHANGELOG.md",
    "README.md",
    "AGENTS.md",
    "COS_WEAVE_FIRST_CONTACT.md",
    "COS_WEAVE_LAUNCHER.md",
    "docs/README.md",
    "docs/quickstart.md",
    "docs/COS_WEAVE_BOOTSTRAP.md",
    "docs/COS_WEAVE_REPO_SKELETON.md",
    "docs/COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md",
    "docs/WEAVE_V0_1_RELEASE.md",
    "docs/WEAVE_V0_1_USER_FLOW.md",
    "docs/WEAVE_CHIEF_OF_STAFF_UX.md",
    "docs/WEAVE_HARNESS_ENGINEERING_ADOPTION.md",
    "docs/WEAVE_INTENT_TRUTH_AND_COMPLETION_CONTRACT.md",
    "docs/WEAVE_CONCEPT_CHANGE_MAINTAINER_PLAYBOOK.md",
    "docs/WEAVE_OBSERVABILITY_EVAL_GOVERNANCE.md",
    "docs/WEAVE_REVIEW_LOOP_PROCESS.md",
    "docs/WEAVE_SERVICE_BLUEPRINT.md",
    "docs/WEAVE_VNEXT_GROUND_ZERO_CONTRACT.md",
    "docs/lifecycle-evals.md",
]

RELEASE_VISUALS = [
    "assets/weave-v0.1-flow.svg",
    "assets/weave-v0.1-lifecycle.svg",
]

CANONICAL_RELEASE_TRIGGER = "Use WEAVE release v0.1.0 from https://github.com/its-DeFine/weave.git"
CANONICAL_USER_PROMPT = (
    "Use WEAVE release v0.1.0 from https://github.com/its-DeFine/weave.git. "
    "I want to build <ordinary app intent>."
)
LAUNCHER_PREFIX = (
    "Before any commentary or execution packet, open or clone this repository "
    "and read COS_WEAVE_FIRST_CONTACT.md, AGENTS.md, and docs/COS_WEAVE_BOOTSTRAP.md."
)

GENERIC_PACKAGE_DOCS = [
    "packages/weave-tool/COMPANY.md",
    "packages/weave-tool/README.md",
    "packages/weave-tool/skills/codebase-orientation/SKILL.md",
    "packages/weave-tool/skills/compound-engineering/SKILL.md",
    "packages/weave-tool/skills/cos-weave/SKILL.md",
    "packages/weave-tool/skills/engineering-execution/SKILL.md",
    "packages/weave-tool/skills/evidence-packet/SKILL.md",
    "packages/weave-tool/skills/implementation-planning/SKILL.md",
    "packages/weave-tool/skills/primitive-market-research/SKILL.md",
    "packages/weave-tool/skills/qa-verification/SKILL.md",
    "packages/weave-tool/skills/security-release-review/SKILL.md",
    "packages/weave-tool/skills/weave-lifecycle/SKILL.md",
]

TEXT_SUFFIXES = {".md", ".json", ".py", ".yaml", ".yml", ".sh", ".txt"}


def legacy_terms() -> list[str]:
    return [
        "Sym" + "phony",
        "Sym" + "phone",
        "Tex" + "tual",
        "T" + "UI",
        "Her" + "mes",
        "Tele" + "gram",
    ]


def read_text(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8", errors="replace")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def contains_phrase(text: str, phrase: str) -> bool:
    return normalize_space(phrase) in normalize_space(text)


def current_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        paths = [Path(line) for line in result.stdout.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        paths = [path.relative_to(root) for path in root.rglob("*") if path.is_file()]
    return [
        path
        for path in paths
        if path.parts
        and path.parts[0] not in {".git", "runs"}
        and "__pycache__" not in path.parts
        and (root / path).is_file()
    ]


def text_files(root: Path) -> list[Path]:
    return [path for path in current_files(root) if path.suffix in TEXT_SUFFIXES]


def stage_dirs(root: Path, rel: str) -> list[str]:
    base = root / rel
    if not base.exists():
        return []
    return [
        path.name.split("-", 1)[1]
        for path in sorted(base.iterdir())
        if path.is_dir() and re.match(r"^\d{2}-", path.name)
    ]


def check_lifecycle_vocabulary(root: Path) -> list[str]:
    findings: list[str] = []
    expected_files = [f"{index:02d}-{stage}.md" for index, stage in enumerate(CANONICAL_STAGES, 1)]
    procedure_dir = root / "docs/samples/cos-weave-skeleton/procedures/lifecycle"
    actual_files = sorted(path.name for path in procedure_dir.glob("*.md")) if procedure_dir.exists() else []
    if actual_files != expected_files:
        findings.append(f"sample procedure files mismatch: expected={expected_files}; actual={actual_files}")

    app_stages = stage_dirs(root, "docs/samples/cos-weave-skeleton/apps/tiny-local-calculator/lifecycle")
    if app_stages != CANONICAL_STAGES:
        findings.append(f"sample app lifecycle dirs mismatch: expected={CANONICAL_STAGES}; actual={app_stages}")

    required_paths = [
        "packages/weave-tool/evals/lifecycle/kpi-setup.yaml",
        "docs/samples/cos-weave-skeleton/procedures/lifecycle/08-kpi-setup.md",
        "docs/samples/cos-weave-skeleton/apps/tiny-local-calculator/lifecycle/08-kpi-setup/state.json",
    ]
    for rel in required_paths:
        if not (root / rel).exists():
            findings.append(f"missing canonical lifecycle path: {rel}")

    forbidden_patterns = [
        (re.compile(r"02-requirements"), "obsolete generated requirements stage"),
        (re.compile(r'"stage"\s*:\s*"requirements"'), "obsolete requirements stage id"),
        (re.compile(r'"lifecycleStage"\s*:\s*"requirements"'), "obsolete requirements primitive"),
        (re.compile(r"Requirements gate is not complete"), "obsolete requirements gate"),
        (re.compile(r'"stage"\s*:\s*"kpi"'), "non-canonical kpi stage id"),
        (re.compile(r'"lifecycleStage"\s*:\s*"kpi"'), "non-canonical kpi primitive"),
        (re.compile(r"08-kpi(?:/|\.md|\"|')"), "non-canonical kpi path"),
    ]
    for rel in text_files(root):
        rel_text = rel.as_posix()
        if rel.parts[0] == "tests" or rel_text == "scripts/validate_docs_current.py":
            continue
        text = (root / rel).read_text(encoding="utf-8", errors="replace")
        for pattern, label in forbidden_patterns:
            if pattern.search(text):
                findings.append(f"{rel}: {label}")
    return findings


def boundary_findings(files: dict[str, str]) -> list[str]:
    findings: list[str] = []
    disallowed = legacy_terms() + ["runtime-agent", "runtime agent"]
    for rel, text in files.items():
        lowered = text.lower()
        for term in disallowed:
            if term.lower() in lowered:
                findings.append(f"{rel}: default docs mention non-default surface {term!r}")
    return findings


def check_current_product_boundary(root: Path) -> list[str]:
    files: dict[str, str] = {}
    for rel in CORE_DOCS + GENERIC_PACKAGE_DOCS:
        path = root / rel
        if path.exists():
            files[rel] = path.read_text(encoding="utf-8", errors="replace")
    return boundary_findings(files)


def check_optional_extension_boundary(root: Path) -> list[str]:
    findings: list[str] = []
    generic_skill = root / "packages/weave-tool/skills/livepeer-adapter-boundary/SKILL.md"
    extension_skill = root / "packages/weave-tool/extensions/livepeer/skills/livepeer-adapter-boundary/SKILL.md"
    if generic_skill.exists():
        findings.append("Livepeer boundary skill is still in generic skills/")
    if not extension_skill.exists():
        findings.append("Livepeer optional extension skill is missing")
    package_readme = read_text(root, "packages/weave-tool/README.md")
    if "optional domain extension" not in package_readme or "extensions/livepeer/" not in package_readme:
        findings.append("packages/weave-tool/README.md does not document Livepeer as optional extension")
    validator_text = read_text(root, "packages/weave-tool/scripts/validate_company_package.py")
    if "livepeer-adapter-boundary" in validator_text:
        findings.append("package validator still requires the Livepeer skill in the generic package")
    return findings


def section_between(text: str, start: str, end: str) -> str:
    try:
        after = text.split(start, 1)[1]
    except IndexError:
        return ""
    try:
        return after.split(end, 1)[0]
    except IndexError:
        return after


def check_repo_map(root: Path) -> list[str]:
    findings: list[str] = []
    rel = "docs/WEAVE_REPO_MAP_PONYTAIL_REVIEW.md"
    path = root / rel
    if not path.exists():
        return [f"{rel} is missing"]
    text = path.read_text(encoding="utf-8", errors="replace")
    external = section_between(text, "### Required Before External Review", "### Required Before Real Users")
    if not external:
        findings.append(f"{rel}: missing Required Before External Review section")
        return findings
    lowered = external.lower()
    required = [
        "controller diff review",
        "integration/commit",
        "push/pr",
        "github ci",
    ]
    for phrase in required:
        if phrase not in lowered:
            findings.append(f"{rel}: external review gates missing {phrase!r}")
    if "nothing known" in lowered:
        findings.append(f"{rel}: external review section overclaims by saying nothing known remains")
    return findings


def check_non_claims(root: Path) -> list[str]:
    findings: list[str] = []
    rels = [
        "README.md",
        "AGENTS.md",
        "docs/COS_WEAVE_BOOTSTRAP.md",
        "docs/WEAVE_REPO_MAP_PONYTAIL_REVIEW.md",
    ]
    aggregate = "\n".join(read_text(root, rel) for rel in rels if (root / rel).exists()).lower()
    required = {
        "live workers": r"live worker",
        "tracker or Linear mutation": r"tracker|linear mutation",
        "deploy or public send": r"deploy|public send",
        "billing or payment": r"billing|payment|paid call",
        "credentials": r"credential",
        "full lifecycle completion": r"full lifecycle completion",
    }
    for label, pattern in required.items():
        if not re.search(pattern, aggregate):
            findings.append(f"non-claim missing from docs: {label}")
    return findings


def check_deployment_provider_gates(root: Path) -> list[str]:
    findings: list[str] = []
    required_docs = [
        "README.md",
        "docs/COS_WEAVE_REPO_SKELETON.md",
        "docs/COS_WEAVE_BOOTSTRAP.md",
        "docs/COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md",
        "packages/weave-tool/skills/cos-weave/SKILL.md",
    ]
    aggregate = "\n".join(read_text(root, rel) for rel in required_docs if (root / rel).exists()).lower()
    required_terms = {
        "deployment-gates.json": "deployment-gates.json",
        "Cloudflare": "cloudflare",
        "Vercel": "vercel",
        "connector/MCP/brokered validation": r"connector|mcp|brokered",
        "secret_ref boundary": "secret_ref",
        "blocked launch boundary": r"block(?:ed|s|ing).{0,80}(?:deployment|launch)|(?:deployment|launch).{0,80}block(?:ed|s|ing)",
    }
    for label, pattern in required_terms.items():
        if not re.search(pattern, aggregate):
            findings.append(f"deployment provider gate docs missing {label}")

    sample_gate = root / "docs/samples/cos-weave-skeleton/apps/tiny-local-calculator/deployment-gates.json"
    if not sample_gate.exists():
        findings.append("sample missing deployment gate state: docs/samples/cos-weave-skeleton/apps/tiny-local-calculator/deployment-gates.json")
    else:
        text = sample_gate.read_text(encoding="utf-8", errors="replace").lower()
        for term in ["weave-deployment-gates/v0.1", "cloudflare", "vercel", "not_validated", "secret_ref"]:
            if term not in text:
                findings.append(f"sample deployment gate state missing {term!r}")
    return findings


def check_release_assets(root: Path) -> list[str]:
    findings: list[str] = []
    version = read_text(root, "VERSION").strip() if (root / "VERSION").exists() else ""
    if version != "0.1.0":
        findings.append(f"VERSION should be 0.1.0 for this release; actual={version!r}")

    company = read_text(root, "packages/weave-tool/COMPANY.md")
    for required in ['version: "0.1.0"', "releaseTag: v0.1.0", "releaseChannel: public-v0.1"]:
        if required not in company:
            findings.append(f"packages/weave-tool/COMPANY.md missing release metadata: {required}")

    release_doc_path = root / "docs/WEAVE_V0_1_RELEASE.md"
    user_flow_path = root / "docs/WEAVE_V0_1_USER_FLOW.md"
    changelog_path = root / "CHANGELOG.md"
    for rel, path in {
        "docs/WEAVE_V0_1_RELEASE.md": release_doc_path,
        "docs/WEAVE_V0_1_USER_FLOW.md": user_flow_path,
        "CHANGELOG.md": changelog_path,
    }.items():
        if not path.exists():
            findings.append(f"missing release doc: {rel}")

    release_doc = release_doc_path.read_text(encoding="utf-8", errors="replace") if release_doc_path.exists() else ""
    user_flow = user_flow_path.read_text(encoding="utf-8", errors="replace") if user_flow_path.exists() else ""
    changelog = changelog_path.read_text(encoding="utf-8", errors="replace") if changelog_path.exists() else ""
    readme = read_text(root, "README.md")

    for visual in RELEASE_VISUALS:
        path = root / visual
        if not path.exists():
            findings.append(f"missing release visual: {visual}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "<svg" not in text or "<title" not in text or "<desc" not in text:
            findings.append(f"{visual}: SVG needs title and desc accessibility metadata")
        if visual not in readme and visual.replace("assets/", "../assets/") not in user_flow:
            findings.append(f"{visual}: not referenced from README or user-flow docs")

    for label, text in {
        "docs/WEAVE_V0_1_RELEASE.md": release_doc,
        "docs/WEAVE_V0_1_USER_FLOW.md": user_flow,
        "CHANGELOG.md": changelog,
    }.items():
        if "v0.1.0" not in text:
            findings.append(f"{label}: missing v0.1.0")

    return findings


def check_release_trigger(root: Path) -> list[str]:
    findings: list[str] = []
    required_docs = [
        "README.md",
        "COS_WEAVE_FIRST_CONTACT.md",
        "COS_WEAVE_LAUNCHER.md",
        "docs/quickstart.md",
        "docs/COS_WEAVE_BOOTSTRAP.md",
        "docs/WEAVE_V0_1_RELEASE.md",
        "docs/WEAVE_V0_1_USER_FLOW.md",
        "packages/weave-tool/skills/cos-weave/SKILL.md",
    ]
    for rel in required_docs:
        text = read_text(root, rel)
        if CANONICAL_RELEASE_TRIGGER not in text:
            findings.append(f"{rel}: missing canonical release trigger")
    return findings


def check_stage_entry_contract_rule(root: Path) -> list[str]:
    findings: list[str] = []
    required_surfaces = [
        "docs/COS_WEAVE_BOOTSTRAP.md",
        "docs/COS_WEAVE_REPO_SKELETON.md",
        "packages/weave-tool/skills/cos-weave/SKILL.md",
        "packages/weave-tool/skills/weave-lifecycle/SKILL.md",
    ]
    required_phrases = [
        "stage-entry contract",
        "packages/weave-tool/evals/lifecycle/<stage>.yaml",
        "packages/weave-tool/primitives/registry.json",
        "packages/weave-tool/skills/*/SKILL.md",
        "REVISE",
        "BLOCKED",
    ]
    for rel in required_surfaces:
        text = read_text(root, rel)
        for phrase in required_phrases:
            if phrase not in text:
                findings.append(f"{rel}: missing stage-entry contract phrase {phrase!r}")

    sample_files = [
        "docs/samples/cos-weave-skeleton/apps/tiny-local-calculator/lifecycle.json",
        "docs/samples/cos-weave-skeleton/apps/tiny-local-calculator/lifecycle/01-intent/procedure.md",
        "docs/samples/cos-weave-skeleton/apps/tiny-local-calculator/proof/proof-tray.json",
        "docs/samples/cos-weave-skeleton/apps/tiny-local-calculator/updates/readback.json",
    ]
    for rel in sample_files:
        text = read_text(root, rel)
        if "stage_entry_contract" not in text and "Stage-Entry Contract" not in text and "consulted_contract_refs" not in text:
            findings.append(f"{rel}: missing generated stage-entry contract record")
    return findings


def check_first_contact_readme(root: Path) -> list[str]:
    findings: list[str] = []
    readme = read_text(root, "README.md")
    first_contact = read_text(root, "COS_WEAVE_FIRST_CONTACT.md")
    launcher = read_text(root, "COS_WEAVE_LAUNCHER.md")

    for rel, text in {
        "README.md": readme,
        "COS_WEAVE_FIRST_CONTACT.md": first_contact,
        "COS_WEAVE_LAUNCHER.md": launcher,
    }.items():
        if not contains_phrase(text, CANONICAL_USER_PROMPT):
            findings.append(f"{rel}: missing canonical user prompt")

    first_contact_section = section_between(readme, "## First Contact", "## Default File-Skeleton State")
    if not first_contact_section:
        findings.append("README.md: missing First Contact section before skeleton state")
    else:
        if not contains_phrase(first_contact_section, CANONICAL_USER_PROMPT):
            findings.append("README.md: First Contact section missing canonical user prompt")
        if not contains_phrase(first_contact_section, LAUNCHER_PREFIX):
            findings.append("README.md: First Contact section missing projectless launcher prompt")
        if "The user provides:" not in first_contact_section or "The agent does automatically:" not in first_contact_section:
            findings.append("README.md: First Contact section must split user inputs from agent actions")
        required_next = [
            "creates or loads `runs/cos-weave-home/`",
            "app state",
            "proof",
            "readback",
        ]
        for phrase in required_next:
            if phrase not in first_contact_section:
                findings.append(f"README.md: First Contact section missing next-step detail {phrase!r}")

    deployment = section_between(readme, "## Deployment Gates", "## Visual Model")
    if not deployment:
        findings.append("README.md: missing Deployment Gates section")
    else:
        required = [
            "Cloudflare",
            "Vercel",
            "not required for intent capture",
            "planning",
            "local engineering",
            "DNS changes",
            "provider mutations",
            "production deploys",
            "Do not paste raw Cloudflare, Vercel, DNS, OAuth, API, or service credentials into chat",
        ]
        for phrase in required:
            if not contains_phrase(deployment, phrase):
                findings.append(f"README.md: Deployment Gates section missing {phrase!r}")
    return findings


def check_public_cli_surface(root: Path) -> list[str]:
    findings: list[str] = []
    wrapper = root / "bin" / "weave"
    cli = root / "scripts" / "weave_cli.py"
    if not wrapper.exists():
        findings.append("bin/weave is missing")
    if not cli.exists():
        findings.append("scripts/weave_cli.py is missing")
    if findings:
        return findings

    try:
        result = subprocess.run(
            [str(wrapper), "help"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [f"bin/weave help could not run: {exc}"]

    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0:
        findings.append(f"bin/weave help exited {result.returncode}")

    required = ["cos-bootstrap", "readback", "eval"]
    for command in required:
        if command not in output:
            findings.append(f"bin/weave help missing current command {command!r}")

    forbidden = [
        "attach-" + "her" + "mes",
        "her" + "mes",
        "t" + "ui",
        "tex" + "tual",
        "runtime-home",
        "runtime home",
        "runtime-agent",
        "runtime agent",
        "gate" + "way",
        "onboard",
        "sym" + "phony",
        "sym" + "phone",
    ]
    lowered = output.lower()
    for term in forbidden:
        if term in lowered:
            findings.append(f"bin/weave help exposes stale command/surface {term!r}")
    return findings


def check_root_dotfiles(root: Path) -> list[str]:
    findings: list[str] = []
    if (root / ".dockerignore").exists():
        findings.append(".dockerignore exists but current vNext has no container build-context command")
    return findings


def validate_repo(root: Path = REPO_ROOT) -> list[str]:
    findings: list[str] = []
    checks = [
        check_lifecycle_vocabulary,
        check_current_product_boundary,
        check_optional_extension_boundary,
        check_repo_map,
        check_non_claims,
        check_deployment_provider_gates,
        check_release_assets,
        check_release_trigger,
        check_stage_entry_contract_rule,
        check_first_contact_readme,
        check_public_cli_surface,
        check_root_dotfiles,
    ]
    for check in checks:
        findings.extend(check(root))
    return findings


def main() -> int:
    findings = validate_repo(REPO_ROOT)
    for finding in findings:
        print(finding)
    if findings:
        print(f"docs currentness validation failed: {len(findings)} finding(s)", file=sys.stderr)
        return 1
    print("docs currentness: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

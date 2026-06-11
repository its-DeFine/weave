#!/usr/bin/env python3
"""Local runtime smoke test.

Prints the WEAVE lifecycle plus parallel growth loop, validates the company
package, and checks that deterministic Telegram status commands can be served
from local WEAVE state. No network access. No secrets. Exits 0 on success.

Usage:
    python3 scripts/runtime_smoke.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import weave_runtime_slice

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages" / "weave-tool"
VALIDATOR = PACKAGE_ROOT / "scripts" / "validate_company_package.py"
SETUP_RUNTIME = REPO_ROOT / "scripts" / "setup_runtime.py"
WEAVE_CLI = REPO_ROOT / "scripts" / "weave_cli.py"
CONTEXT_INDEX_RUNTIME_SMOKE = REPO_ROOT / "scripts" / "context_index_runtime_smoke.py"

LIFECYCLE_STAGES = [
    "1. Intent",
    "2. Research",
    "3. Selection",
    "4. Plan",
    "5. Engineering",
    "6. QA",
    "7. KPI Setup",
    "8. Marketing",
    "9. Iteration",
    "10. Analysis",
]


def print_lifecycle() -> None:
    print("WEAVE lifecycle stages:")
    for stage in LIFECYCLE_STAGES:
        print(f"  {stage}")
    print()


def validate_package() -> int:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(PACKAGE_ROOT)],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def validate_runtime_setup() -> int:
    result = subprocess.run(
        [sys.executable, str(SETUP_RUNTIME), "--check"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, end="", file=sys.stderr)
        return result.returncode

    try:
        profile = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"runtime setup check returned invalid JSON: {exc}", file=sys.stderr)
        return 1

    package = profile.get("package", {})
    runtime = profile.get("runtime", {})
    if runtime.get("id") != package.get("default_runtime"):
        print("runtime setup check did not select the default runtime", file=sys.stderr)
        return 1
    if package.get("fallback_runtime") != "local-fallback":
        print("runtime setup check did not preserve Local Fallback fallback", file=sys.stderr)
        return 1
    if runtime.get("agent_slug") != "ceo-hermes":
        print("runtime setup check did not select the Hermes CEO agent", file=sys.stderr)
        return 1
    foundation = profile.get("foundation_onboarding", {})
    if foundation.get("setup_required") is not True or foundation.get("required_before_app_work") is not True:
        print(f"runtime setup check did not require foundation onboarding: {foundation}", file=sys.stderr)
        return 1
    runtime_home = profile.get("runtime_home", {})
    if runtime_home.get("schema") != weave_runtime_slice.RUNTIME_HOME_SCHEMA:
        print(f"runtime setup check did not expose runtime home: {runtime_home}", file=sys.stderr)
        return 1

    print("runtime setup check: ok")
    return 0


def validate_container_runtime_profile() -> int:
    result = subprocess.run(
        [
            sys.executable,
            str(SETUP_RUNTIME),
            "--runtime-container-image",
            "weave-hermes-runtime:smoke",
            "--check",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, end="", file=sys.stderr)
        return result.returncode
    try:
        profile = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"container runtime profile check returned invalid JSON: {exc}", file=sys.stderr)
        return 1
    container = profile.get("runtime", {}).get("container", {})
    if container.get("enabled") is not True:
        print(f"container runtime profile did not mark container enabled: {container}", file=sys.stderr)
        return 1
    if container.get("image") != "weave-hermes-runtime:smoke":
        print(f"container runtime profile image mismatch: {container}", file=sys.stderr)
        return 1
    if "Docker restart policy" not in str(container.get("supervision", "")):
        print(f"container runtime profile did not record supervision: {container}", file=sys.stderr)
        return 1
    if container.get("service_installed") is not False:
        print(f"container runtime profile should not claim a service install: {container}", file=sys.stderr)
        return 1

    print("container runtime profile check: ok")
    return 0


def run_checked(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)


def fill_runtime_doc(path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {title}\n\nStatus: complete\n\nRuntime smoke evidence is recorded.\n",
        encoding="utf-8",
    )


def complete_foundation(root: Path, app_id: str) -> None:
    fill_runtime_doc(root / "artifacts" / "general" / "soul.md", "Hermes Soul")
    fill_runtime_doc(root / "artifacts" / "general" / "owner-profile.md", "Owner Profile")
    fill_runtime_doc(root / "apps" / app_id / "context" / "app-context.md", "App Context")
    fill_runtime_doc(root / "apps" / app_id / "inventory" / "app-inventory.md", "App Inventory")
    fill_runtime_doc(root / "apps" / app_id / "contract" / "gestaltian-contract.md", "Gestaltian Contract")


def write_stage_artifact(root: Path, app_id: str, stage_id: str) -> Path:
    stage = weave_runtime_slice.stage_by_id(stage_id)
    path = root / "apps" / app_id / "lifecycle" / stage.directory / "artifacts" / f"{stage_id}.md"
    fill_runtime_doc(path, stage_id.title())
    return path


def record_stage_turn(root: Path, app_id: str, stage_id: str, artifact_path: Path | None = None) -> None:
    refs = [{"path": weave_runtime_slice.relative(artifact_path, root), "action": "created"}] if artifact_path else []
    turn = weave_runtime_slice.new_conversation_turn(
        app_id,
        stage_id,
        f"Owner discussed {stage_id} stage.",
        f"Hermes recorded {stage_id} stage evidence for review.",
        agent_rationale={
            "summary": f"{stage_id} evidence is ready for owner review.",
            "chain_of_thought_captured": False,
        },
        artifact_refs=refs,
        state_transition={
            "from_stage": stage_id,
            "from_state": "collecting",
            "to_stage": stage_id,
            "to_state": "ready_for_review",
        },
        next_action=f"Owner reviews {stage_id} and may approve the stage.",
    )
    weave_runtime_slice.append_conversation_turn(root, app_id, turn)


def create_fake_hermes_repo(root: Path) -> tuple[Path, str]:
    repo = root / "fake-hermes"
    repo.mkdir()
    (repo / "hermes_cli").mkdir()
    (repo / "hermes_cli" / "__init__.py").write_text(
        '__version__ = "0.0.0-smoke"\n__release_date__ = "2026-05-30"\n',
        encoding="utf-8",
    )
    (repo / "hermes_cli" / "main.py").write_text(
        "def main():\n"
        "    print('Hermes Agent v0.0.0-smoke')\n",
        encoding="utf-8",
    )
    (repo / "run_agent.py").write_text("def main():\n    return None\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text(
        '[project]\n'
        'name = "hermes-agent"\n'
        'version = "0.0.0-smoke"\n'
        'requires-python = ">=3.11"\n'
        '\n'
        '[project.scripts]\n'
        'hermes = "hermes_cli.main:main"\n'
        'hermes-agent = "run_agent:main"\n',
        encoding="utf-8",
    )
    run_checked(["git", "init", "-q"], cwd=repo)
    run_checked(["git", "config", "user.email", "weave@example.invalid"], cwd=repo)
    run_checked(["git", "config", "user.name", "WEAVE Smoke"], cwd=repo)
    run_checked(["git", "add", "."], cwd=repo)
    run_checked(["git", "commit", "-q", "-m", "fake hermes smoke"], cwd=repo)
    commit = run_checked(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    return repo, commit


def validate_hermes_provisioner_contract() -> int:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        fake_repo, commit = create_fake_hermes_repo(root)
        runtime_profile = root / "runtime-profile.json"
        hermes_profile = root / "hermes-profile.json"
        result = subprocess.run(
            [
                sys.executable,
                str(SETUP_RUNTIME),
                "--install-hermes",
                "--hermes-source-repo",
                str(fake_repo),
                "--hermes-commit",
                commit,
                "--hermes-no-install-deps",
                "--hermes-install-root",
                str(root / "install"),
                "--hermes-profile-out",
                str(hermes_profile),
                "--profile-out",
                str(runtime_profile),
                "--skip-weave-root",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stderr, end="", file=sys.stderr)
            return result.returncode
        profile = json.loads(runtime_profile.read_text(encoding="utf-8"))
        hermes = profile.get("hermes_provision", {})
        authority = profile.get("authority", {})
        if hermes.get("source_verified") is not True:
            print(f"Hermes provisioner did not verify source: {hermes}", file=sys.stderr)
            return 1
        if hermes.get("binary_present") is not False:
            print(f"Hermes source-only smoke should not claim a binary: {hermes}", file=sys.stderr)
            return 1
        if authority.get("service_installed") is not False or authority.get("secrets_loaded") is not False:
            print(f"Hermes provisioner violated authority boundary: {authority}", file=sys.stderr)
            return 1

    print("Hermes provisioner check: ok")
    return 0


def validate_runtime_slice() -> int:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "weave-root"
        setup = weave_runtime_slice.setup_weave_root(root)
        if setup["schema"] != weave_runtime_slice.ROOT_SCHEMA:
            print("runtime slice setup returned wrong schema", file=sys.stderr)
            return 1
        if setup.get("agent_profile", {}).get("schema") != weave_runtime_slice.AGENT_PROFILE_SCHEMA:
            print(f"runtime slice setup did not record an agent profile: {setup}", file=sys.stderr)
            return 1
        weave_runtime_slice.create_app(root, "alpha-app", "Alpha App")
        weave_runtime_slice.create_app(root, "beta-app", "Beta App")
        apps = weave_runtime_slice.list_apps(root)
        if [app["app_id"] for app in apps] != ["alpha-app", "beta-app"]:
            print(f"runtime slice app registry mismatch: {apps}", file=sys.stderr)
            return 1
        gate = weave_runtime_slice.foundation_gate(root, "alpha-app")
        if gate["passed"] is not False or "soul.md" not in gate["incomplete"]:
            print(f"runtime slice foundation gate should block templates: {gate}", file=sys.stderr)
            return 1
        onboarding = weave_runtime_slice.setup_foundation_onboarding(root, "alpha-app", "Alpha App")
        agents_path = Path(onboarding["agents_path"])
        if not agents_path.exists() or "Unskippable Foundation Gate" not in agents_path.read_text(encoding="utf-8"):
            print(f"runtime slice did not generate Hermes gateway enforcement: {onboarding}", file=sys.stderr)
            return 1
        event = weave_runtime_slice.new_event(
            "validation.completed",
            "alpha-app",
            "intent",
            "Runtime smoke validation completed.",
        )
        weave_runtime_slice.append_event(root, "alpha-app", event)
        if len(weave_runtime_slice.read_events(root, "alpha-app")) < 3:
            print("runtime slice ledger did not append events", file=sys.stderr)
            return 1
        turn = weave_runtime_slice.new_conversation_turn(
            "alpha-app",
            "intent",
            "Create the first app intent packet.",
            "I recorded the intent exchange and linked it to validation evidence.",
            agent_rationale={
                "summary": "The runtime can preserve the raw exchange without exposing hidden chain-of-thought.",
                "chain_of_thought_captured": False,
            },
            event_refs=[{"event_id": event["event_id"], "type": event["type"]}],
            state_transition={
                "from_stage": "intent",
                "from_state": "collecting",
                "to_stage": "intent",
                "to_state": "collecting",
            },
            next_action="Continue collecting required intent evidence.",
        )
        weave_runtime_slice.append_conversation_turn(root, "alpha-app", turn)
        status_code, transcript = weave_runtime_slice.dispatch_rest(root, "GET", "/apps/alpha-app/conversation")
        if status_code != 200 or transcript.get("turn_count") != 1:
            print(f"runtime slice conversation transcript mismatch: {transcript}", file=sys.stderr)
            return 1
        status_code, form = weave_runtime_slice.dispatch_rest(root, "GET", "/apps/alpha-app/conversation/form")
        if status_code != 200 or form.get("form", {}).get("schema") != weave_runtime_slice.CONVERSATION_CAPTURE_FORM_SCHEMA:
            print(f"runtime slice conversation form mismatch: {form}", file=sys.stderr)
            return 1
        try:
            weave_runtime_slice.append_event(root, "alpha-app", {"schema": "bad"})
        except weave_runtime_slice.RuntimeSliceError:
            pass
        else:
            print("runtime slice accepted malformed event", file=sys.stderr)
            return 1
        status, health = weave_runtime_slice.dispatch_rest(root, "GET", "/health")
        if status != 200 or health.get("real_hermes_runtime") is not False:
            print(f"runtime slice health endpoint mismatch: {health}", file=sys.stderr)
            return 1
        source_map = weave_runtime_slice.load_source_map(root)
        if source_map.get("schema") != weave_runtime_slice.SOURCE_MAP_SCHEMA:
            print(f"runtime slice source map mismatch: {source_map}", file=sys.stderr)
            return 1
        status, app_state = weave_runtime_slice.dispatch_rest(root, "GET", "/apps/alpha-app/state")
        if status != 200 or app_state["foundation_gate"]["passed"] is not False:
            print(f"runtime slice app state mismatch: {app_state}", file=sys.stderr)
            return 1

    print("runtime first-slice check: ok")
    return 0


def validate_telegram_commands() -> int:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "weave-root"
        weave_runtime_slice.create_app(root, "alpha-app", "Alpha App")
        status = weave_runtime_slice.dispatch_telegram_command(root, "/status")
        if status.get("deterministic") is not True or status.get("llm_used") is not False:
            print(f"telegram /status must be deterministic and non-LLM: {status}", file=sys.stderr)
            return 1
        if status.get("payload", {}).get("app_count") != 1:
            print(f"telegram /status app count mismatch: {status}", file=sys.stderr)
            return 1
        if status.get("payload", {}).get("agent_profile", {}).get("schema") != weave_runtime_slice.AGENT_PROFILE_SCHEMA:
            print(f"telegram /status did not expose agent profile: {status}", file=sys.stderr)
            return 1
        if status.get("payload", {}).get("source_map", {}).get("canonical_source_id") != "weave-root":
            print(f"telegram /status source map mismatch: {status}", file=sys.stderr)
            return 1
        created = weave_runtime_slice.dispatch_telegram_command(root, "/create_app Visual Novel")
        if created.get("payload", {}).get("active_app", {}).get("app_id") != "visual-novel":
            print(f"telegram /create_app did not select active app: {created}", file=sys.stderr)
            return 1
        active_status = weave_runtime_slice.dispatch_telegram_command(root, "/status visual-novel")
        if "WEAVE App Status" not in active_status.get("text", ""):
            print(f"telegram /status <app_id> did not render app wall: {active_status}", file=sys.stderr)
            return 1
        sources = weave_runtime_slice.dispatch_telegram_command(root, "/sources")
        if sources.get("payload", {}).get("source_map", {}).get("schema") != weave_runtime_slice.SOURCE_MAP_SCHEMA:
            print(f"telegram /sources did not expose source map: {sources}", file=sys.stderr)
            return 1
        source_ids = {source["id"] for source in sources["payload"]["source_map"]["sources"]}
        if "capability-context-index" not in source_ids:
            print(f"telegram /sources did not expose capability context index: {sources}", file=sys.stderr)
            return 1
        apps = weave_runtime_slice.dispatch_telegram_command(root, "/apps")
        if "Alpha App (alpha-app)" not in apps.get("text", ""):
            print(f"telegram /apps did not include registered app: {apps}", file=sys.stderr)
            return 1
        help_response = weave_runtime_slice.dispatch_telegram_command(root, "/help")
        if "/status" not in help_response.get("payload", {}).get("commands", {}):
            print(f"telegram /help did not expose command catalog: {help_response}", file=sys.stderr)
            return 1
        if "/transcript" not in help_response.get("payload", {}).get("commands", {}):
            print(f"telegram /help did not expose transcript command: {help_response}", file=sys.stderr)
            return 1
        passthrough = weave_runtime_slice.dispatch_telegram_command(root, "normal Hermes chat")
        if passthrough.get("handled") is not False or passthrough.get("llm_used") is not False:
            print(f"telegram non-command passthrough mismatch: {passthrough}", file=sys.stderr)
            return 1

        premature_approval = weave_runtime_slice.dispatch_telegram_command(root, "/approve_stage visual-novel")
        if premature_approval.get("handled") is not False or "foundation context" not in premature_approval.get("text", ""):
            print(f"telegram /approve_stage should block before foundation completion: {premature_approval}", file=sys.stderr)
            return 1
        complete_foundation(root, "visual-novel")
        status_after_foundation = weave_runtime_slice.dispatch_telegram_command(root, "/status")
        if status_after_foundation.get("payload", {}).get("stage_gate_blocked_apps") != ["visual-novel"]:
            print(f"telegram /status did not expose stage gate attention: {status_after_foundation}", file=sys.stderr)
            return 1
        missing_stage_proof = weave_runtime_slice.dispatch_telegram_command(root, "/approve_stage visual-novel")
        if "intent artifact" not in missing_stage_proof.get("text", ""):
            print(f"telegram /approve_stage should require intent proof: {missing_stage_proof}", file=sys.stderr)
            return 1
        artifact_path = write_stage_artifact(root, "visual-novel", "intent")
        missing_transcript = weave_runtime_slice.dispatch_telegram_command(root, "/approve_stage visual-novel")
        if "transcript capture" not in missing_transcript.get("text", ""):
            print(f"telegram /approve_stage should require transcript capture: {missing_transcript}", file=sys.stderr)
            return 1
        record_stage_turn(root, "visual-novel", "intent", artifact_path)
        waiting_for_evaluation = weave_runtime_slice.dispatch_telegram_command(root, "/advance visual-novel")
        evaluation_missing = waiting_for_evaluation.get("payload", {}).get("gate", {}).get("missing", [])
        if waiting_for_evaluation.get("error") != "current_stage_gate_not_passing" or "evaluation: waiting_for_agent" not in evaluation_missing:
            print(f"telegram /advance should block before evaluation review: {waiting_for_evaluation}", file=sys.stderr)
            return 1
        evaluation = weave_runtime_slice.complete_evaluation_from_latest_artifact(
            root,
            "visual-novel",
            "intent",
            reviewer="runtime-smoke-evaluator",
            run_gates=True,
        )
        if evaluation.get("result", {}).get("decision") != "advance":
            print(f"runtime smoke evaluation did not advance: {evaluation}", file=sys.stderr)
            return 1
        premature_advance = weave_runtime_slice.dispatch_telegram_command(root, "/advance visual-novel")
        if premature_advance.get("error") != "current_stage_not_approved":
            print(f"telegram /advance should block before owner approval: {premature_advance}", file=sys.stderr)
            return 1
        lifecycle = weave_runtime_slice.dispatch_telegram_command(root, "/lifecycle visual-novel")
        if lifecycle.get("payload", {}).get("stage_gate", {}).get("passed") is not True:
            print(f"telegram /lifecycle did not expose a passing stage gate: {lifecycle}", file=sys.stderr)
            return 1
        approved = weave_runtime_slice.dispatch_telegram_command(root, "/approve_stage visual-novel")
        if approved.get("payload", {}).get("approved") is not True:
            print(f"telegram /approve_stage did not approve ready stage: {approved}", file=sys.stderr)
            return 1
        advanced = weave_runtime_slice.dispatch_telegram_command(root, "/advance visual-novel")
        if advanced.get("payload", {}).get("stage") != "research":
            print(f"telegram /advance did not move to research: {advanced}", file=sys.stderr)
            return 1
        status_code, rest_lifecycle = weave_runtime_slice.dispatch_rest(root, "GET", "/apps/visual-novel/lifecycle")
        if status_code != 200 or rest_lifecycle.get("stage_status", {}).get("stage") != "research":
            print(f"REST lifecycle endpoint did not mirror Telegram advance: {rest_lifecycle}", file=sys.stderr)
            return 1

    print("telegram command smoke: ok")
    return 0


def validate_runtime_migration_cli() -> int:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        runtime_home = root / "runtime-home"
        imported_home = root / "imported-runtime-home"
        archive = root / "runtime-export.tar.gz"
        result = subprocess.run(
            [
                sys.executable,
                str(SETUP_RUNTIME),
                "--runtime-home",
                str(runtime_home),
                "--runtime-container-image",
                "weave-hermes-runtime:smoke",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stderr or result.stdout, end="", file=sys.stderr)
            return result.returncode

        hermes_home = runtime_home / "hermes-home"
        hermes_home.mkdir(parents=True, exist_ok=True)
        (hermes_home / ".env").write_text(
            "TELEGRAM_BOT_" + "TOKEN=" + "123456789:" + "abcdefghijklmnopqrstuvwxyzABCDEF\n",
            encoding="utf-8",
        )
        (hermes_home / ".env").chmod(0o600)

        result = subprocess.run(
            [
                sys.executable,
                str(WEAVE_CLI),
                "export-runtime",
                "--runtime-home",
                str(runtime_home),
                "--out",
                str(archive),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stderr or result.stdout, end="", file=sys.stderr)
            return result.returncode
        with tarfile.open(archive, "r:gz") as tar:
            names = tar.getnames()
            if "runtime-home/hermes-home/.env" in names:
                print("runtime export included Hermes env", file=sys.stderr)
                return 1
            if any("/tokens/" in name for name in names):
                print("runtime export included token directory material", file=sys.stderr)
                return 1

        result = subprocess.run(
            [sys.executable, str(WEAVE_CLI), "import-runtime", str(archive), "--runtime-home", str(imported_home)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stderr or result.stdout, end="", file=sys.stderr)
            return result.returncode

        result = subprocess.run(
            [sys.executable, str(WEAVE_CLI), "verify-runtime", "--runtime-home", str(imported_home)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stderr or result.stdout, end="", file=sys.stderr)
            return result.returncode
        if "secret_relink_required: true" not in result.stdout:
            print(f"runtime verify did not flag secret relink: {result.stdout}", file=sys.stderr)
            return 1

    print("runtime migration CLI check: ok")
    return 0


def validate_context_index_runtime_smoke() -> int:
    result = subprocess.run(
        [sys.executable, str(CONTEXT_INDEX_RUNTIME_SMOKE)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def main() -> int:
    print_lifecycle()
    rc = validate_package()
    if rc == 0:
        rc = validate_runtime_setup()
    if rc == 0:
        rc = validate_container_runtime_profile()
    if rc == 0:
        rc = validate_hermes_provisioner_contract()
    if rc == 0:
        rc = validate_runtime_slice()
    if rc == 0:
        rc = validate_telegram_commands()
    if rc == 0:
        rc = validate_runtime_migration_cli()
    if rc == 0:
        rc = validate_context_index_runtime_smoke()
    if rc == 0:
        print("smoke: ok")
    else:
        print("smoke: FAILED", file=sys.stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

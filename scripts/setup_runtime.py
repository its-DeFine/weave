#!/usr/bin/env python3
"""Set up a local WEAVE runtime profile.

This command is public-safe by construction: it reads package metadata, selects
the default runtime, checks whether a runtime executable or container image is
available, and writes a local ignored profile under runs/. With
``--install-hermes`` it can also provision the real pinned Nous Hermes Agent
into the ignored local runtime directory. When explicitly given gateway flags,
it can configure the local Hermes Telegram environment from an owner-approved
token file and point Hermes gateway sessions at the generated foundation
onboarding context. It never installs services, starts gateways, or writes
secrets into tracked state.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import weave_runtime_slice
import provision_hermes
import setup_gateway
import weave_hermes_setup

try:
    import yaml
except ImportError:  # pragma: no cover - fallback keeps setup usable without PyYAML
    yaml = None


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages" / "weave-tool"
DEFAULT_RUNTIME_HOME = REPO_ROOT / "runs" / "runtime-home"
DEFAULT_WEAVE_STATE_DIR = "weave-state"
DEFAULT_HERMES_HOME_DIR = "hermes-home"
DEFAULT_PROFILE_PATH = DEFAULT_RUNTIME_HOME / "runtime-profile.json"
DEFAULT_WEAVE_ROOT = DEFAULT_RUNTIME_HOME / DEFAULT_WEAVE_STATE_DIR
DEFAULT_GATEWAY_HERMES_HOME = DEFAULT_RUNTIME_HOME / DEFAULT_HERMES_HOME_DIR
DEFAULT_FOUNDATION_APP_ID = "weave"
DEFAULT_FOUNDATION_APP_NAME = "WEAVE App"
HERMES_PLUGIN_SOURCE = REPO_ROOT / "integrations" / "hermes" / "weave-runtime"
HERMES_PLUGIN_NAME = "weave-runtime"
AGENT_PROFILE_ENV_KEYS = (
    "WEAVE_HERMES_MODEL",
    "WEAVE_HERMES_REASONING_EFFORT",
    "WEAVE_HERMES_PROVIDER_ADAPTER",
    "WEAVE_HERMES_PROMPT_PACK",
)

RUNTIME_BINARIES = {
    "hermes-default": ["hermes", "hermes-agent", "nous-hermes"],
    "local-fallback": ["local-fallback"],
}

RUNTIME_AGENT = {
    "hermes-default": "ceo-hermes",
    "local-fallback": "ceo-fallback",
}


class RuntimeSetupError(Exception):
    pass


def refresh_agent_profile_from_environment(root: Path) -> dict[str, object] | None:
    """Refresh the local agent profile only when setup receives explicit profile env."""
    if not any(os.environ.get(key) for key in AGENT_PROFILE_ENV_KEYS):
        return None
    return weave_runtime_slice.write_agent_profile(
        root,
        weave_runtime_slice.default_agent_profile(root),
        event_type="runtime.agent_profile.changed",
    )


def _single_allowed_user(value: str | None) -> str | None:
    if not value:
        return None
    users = [item.strip() for item in value.split(",") if item.strip()]
    if len(users) == 1 and users[0].isdigit():
        return users[0]
    return None


def _load_yaml_config(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    if yaml is not None:
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            raise RuntimeSetupError(f"could not read Hermes config at {path}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise RuntimeSetupError(f"Hermes config at {path} must be a YAML mapping")
        return loaded
    data: dict[str, object] = {}
    current_key: str | None = None
    lines = path.read_text(encoding="utf-8").splitlines()
    index = 0
    try:
        while index < len(lines):
            raw = lines[index]
            stripped = raw.strip()
            index += 1
            if not stripped or stripped.startswith("#"):
                continue
            if not raw.startswith((" ", "\t")):
                if ":" not in raw:
                    continue
                key, value = raw.split(":", 1)
                current_key = key.strip()
                value = value.strip()
                if value:
                    data[current_key] = _parse_yaml_scalar(value)
                else:
                    data[current_key] = {}
                continue
            if current_key is None or not isinstance(data.get(current_key), dict):
                continue
            nested = raw.strip()
            if ":" not in nested:
                continue
            key, value = nested.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value in {"|", "|-"}:
                block: list[str] = []
                while index < len(lines):
                    block_raw = lines[index]
                    if block_raw.startswith("    "):
                        block.append(block_raw[4:])
                        index += 1
                        continue
                    if not block_raw.strip():
                        block.append("")
                        index += 1
                        continue
                    break
                data[current_key][key] = "\n".join(block).rstrip("\n")
            else:
                data[current_key][key] = _parse_yaml_scalar(value)
    except Exception as exc:
        raise RuntimeSetupError(f"could not read Hermes config at {path}: {exc}") from exc
    return data


def _parse_yaml_scalar(value: str) -> object:
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if value.startswith(("'", '"', "[", "{")):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value.strip("'\"")
    return value


def _write_yaml_config(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is not None:
        rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=False)
    else:
        rendered = _dump_minimal_yaml(data)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(rendered, encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    tmp.replace(path)


def _dump_minimal_yaml(data: dict[str, object]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for nested_key, nested_value in value.items():
                if isinstance(nested_value, str) and "\n" in nested_value:
                    lines.append(f"  {nested_key}: |-")
                    lines.extend(f"    {line}" for line in nested_value.splitlines())
                else:
                    lines.append(f"  {nested_key}: {_format_yaml_scalar(nested_value)}")
        else:
            lines.append(f"{key}: {_format_yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def _format_yaml_scalar(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return json.dumps(str(value))


def render_gateway_runtime_system_prompt(onboarding_status: dict[str, object]) -> str:
    gate = onboarding_status["foundation_gate"]
    assert isinstance(gate, dict)
    autonomy = onboarding_status["autonomy"]
    assert isinstance(autonomy, dict)
    hard_gates = "\n".join(f"- {item['label']}" for item in autonomy["hard_approval_gates"])
    root_status = onboarding_status["root_status"]
    assert isinstance(root_status, dict)
    root = Path(str(root_status["root"])).expanduser()
    agent_profile = root_status.get("agent_profile_path") or str(weave_runtime_slice.agent_profile_path(root))
    active_app = onboarding_status.get("active_app_path") or str(weave_runtime_slice.active_app_path(root))
    lifecycle = " -> ".join(stage.id for stage in weave_runtime_slice.STAGES)
    command_lines = "\n".join(
        f"- `{command}`: {description}"
        for command, description in sorted(weave_runtime_slice.TELEGRAM_COMMANDS.items())
    )
    return f"""WEAVE foundation onboarding is mandatory for this gateway session.

Before answering any app-building request, read:
- foundation gate: {onboarding_status["foundation_gate_path"]}
- source map: {onboarding_status["source_map_path"]}
- gateway context: {onboarding_status["context_path"]}
- gateway rules: {onboarding_status["agents_path"]}
- agent profile: {agent_profile}
- active app profile: {active_app}

Autonomy mode is `{autonomy["mode"]}`. {autonomy["confirmation_policy"]}
Proceed without routine confirmation for non-gated local work. Ask the owner
through this Telegram LLM conversation and wait for explicit authorization
before any hard approval gate:

{hard_gates}

If the foundation gate is not passing, stay in Foundation Onboarding Mode. Ask
the owner through Telegram only, ask at most three blocking questions at once,
write the answers into the canonical WEAVE documents, refresh the foundation
gate, and do not proceed to app work until the gate passes.

The foundation gate is blocking when required documents are missing, still
contain template placeholders or TODOs, or your confidence that the owner,
Hermes character, app context, inventory, and Gestaltian contract are complete
is not high. Keep the owner moving with an elicitation loop: say what is
missing, why it matters, and what answer is needed next.

Telegram slash commands are reserved for deterministic WEAVE runtime status.
When a message begins with `/`, route it to the WEAVE command layer and return
that output without model-generated wording.

Deterministic command surface:
{command_lines}

There is no dashboard or UI in this phase. Telegram is the communication
channel, and slash commands are the deterministic status surface.

Use product lifecycle language in owner-facing communication:
{lifecycle}.

Current WEAVE app: {onboarding_status["app_id"]} ({onboarding_status["app_name"]})
Current foundation gate passed: {gate["passed"]}
"""


def configure_hermes_gateway_context(
    hermes_home: Path,
    onboarding_status: dict[str, object],
    *,
    runtime_home: Path | None = None,
) -> dict[str, object]:
    """Point Hermes gateway sessions at the generated WEAVE onboarding context."""
    config_path = hermes_home / "config.yaml"
    config = _load_yaml_config(config_path)
    terminal = config.setdefault("terminal", {})
    if not isinstance(terminal, dict):
        terminal = {}
        config["terminal"] = terminal
    agent = config.setdefault("agent", {})
    if not isinstance(agent, dict):
        agent = {}
        config["agent"] = agent

    gateway_workdir = Path(str(onboarding_status["gateway_workdir"])).expanduser().resolve()
    terminal["cwd"] = str(gateway_workdir)
    agent["system_prompt"] = render_gateway_runtime_system_prompt(onboarding_status)
    weave_runtime = config.setdefault("weave_runtime", {})
    if not isinstance(weave_runtime, dict):
        weave_runtime = {}
        config["weave_runtime"] = weave_runtime
    weave_runtime["repo"] = str(REPO_ROOT)
    weave_runtime["root"] = str(Path(str(onboarding_status["root_status"]["root"])).expanduser().resolve())
    if runtime_home is not None:
        weave_runtime["runtime_home"] = str(runtime_home.expanduser().resolve())
    weave_runtime["source_map"] = str(onboarding_status["source_map_path"])
    _write_yaml_config(config_path, config)
    return {
        "config_path": str(config_path),
        "terminal_cwd": str(gateway_workdir),
        "agent_system_prompt_configured": True,
    }


def install_weave_runtime_hermes_plugin(
    hermes_home: Path,
    *,
    weave_root: Path,
    runtime_home: Path | None = None,
    repo_root: Path = REPO_ROOT,
) -> dict[str, object]:
    """Install the generic WEAVE runtime Hermes plugin into a local Hermes home."""
    if not HERMES_PLUGIN_SOURCE.exists():
        raise RuntimeSetupError(f"Hermes WEAVE plugin source is missing: {HERMES_PLUGIN_SOURCE}")
    plugin_dir = hermes_home / "plugins" / HERMES_PLUGIN_NAME
    shutil.copytree(
        HERMES_PLUGIN_SOURCE,
        plugin_dir,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        dirs_exist_ok=True,
    )

    config_path = hermes_home / "config.yaml"
    config = _load_yaml_config(config_path)
    plugins = config.setdefault("plugins", {})
    if not isinstance(plugins, dict):
        plugins = {}
        config["plugins"] = plugins
    enabled = plugins.get("enabled", [])
    if isinstance(enabled, str):
        enabled = [enabled] if enabled else []
    if not isinstance(enabled, list):
        enabled = []
    if HERMES_PLUGIN_NAME not in enabled:
        enabled.append(HERMES_PLUGIN_NAME)
    plugins["enabled"] = sorted(str(item) for item in enabled)

    weave_runtime = config.setdefault("weave_runtime", {})
    if not isinstance(weave_runtime, dict):
        weave_runtime = {}
        config["weave_runtime"] = weave_runtime
    weave_runtime["repo"] = str(repo_root.expanduser().resolve())
    weave_runtime["root"] = str(weave_root.expanduser().resolve())
    if runtime_home is not None:
        weave_runtime["runtime_home"] = str(runtime_home.expanduser().resolve())
    weave_runtime["plugin"] = HERMES_PLUGIN_NAME
    _write_yaml_config(config_path, config)

    return {
        "plugin": HERMES_PLUGIN_NAME,
        "plugin_dir": str(plugin_dir),
        "config_path": str(config_path),
        "enabled": True,
    }


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise RuntimeSetupError(f"{path}: missing frontmatter")
    block = text.split("---\n", 2)[1]
    fields: dict[str, str] = {}
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("- ") or line.startswith("  "):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def find_runtime_binary(runtime: str, explicit_binary: str | None = None) -> dict[str, str | bool | None]:
    if explicit_binary and Path(explicit_binary).expanduser().exists():
        path = str(Path(explicit_binary).expanduser().resolve())
        return {"found": True, "name": Path(path).name, "path": path}
    candidates = [explicit_binary] if explicit_binary else RUNTIME_BINARIES.get(runtime, [])
    for candidate in candidates:
        if not candidate:
            continue
        path = shutil.which(candidate)
        if path:
            return {"found": True, "name": candidate, "path": path}
    return {"found": False, "name": candidates[0] if candidates else None, "path": None}


def read_hermes_provision_profile(path: Path = provision_hermes.DEFAULT_PROFILE_PATH) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeSetupError(f"could not read Hermes provision profile at {path}: {exc}") from exc
    if profile.get("schema") != provision_hermes.PROFILE_SCHEMA:
        raise RuntimeSetupError(f"Hermes provision profile must use schema {provision_hermes.PROFILE_SCHEMA}")
    return profile


def binary_from_hermes_provision(profile: dict[str, object] | None) -> str | None:
    if not profile:
        return None
    status = profile.get("status", {})
    local = profile.get("local", {})
    if not isinstance(status, dict) or not isinstance(local, dict):
        return None
    if status.get("source_verified") is not True or status.get("binary_present") is not True:
        return None
    wrapper_path = local.get("wrapper_path")
    binary_path = local.get("binary_path")
    candidate = wrapper_path or binary_path
    if not isinstance(candidate, str) or not candidate:
        return None
    path = Path(candidate)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return str(path)


def runtime_profile(
    runtime: str,
    runtime_binary: str | None = None,
    *,
    runtime_home: Path = DEFAULT_RUNTIME_HOME,
    weave_root: Path = DEFAULT_WEAVE_ROOT,
    hermes_home: Path = DEFAULT_GATEWAY_HERMES_HOME,
    hermes_provision_profile: dict[str, object] | None = None,
    hermes_profile_path: Path = provision_hermes.DEFAULT_PROFILE_PATH,
    network_install_performed: bool = False,
    runtime_container_image: str | None = None,
) -> dict[str, object]:
    company = parse_frontmatter(PACKAGE_ROOT / "COMPANY.md")
    default_runtime = company.get("runtime")
    fallback_runtime = company.get("runtimeFallback")
    if runtime not in {default_runtime, fallback_runtime}:
        raise RuntimeSetupError(
            f"runtime must be {default_runtime} or fallback {fallback_runtime}; got {runtime}"
        )

    agent_slug = RUNTIME_AGENT[runtime]
    agent_path = PACKAGE_ROOT / "agents" / agent_slug / "AGENTS.md"
    agent = parse_frontmatter(agent_path)
    provisioned_binary = binary_from_hermes_provision(hermes_provision_profile) if runtime == "hermes-default" else None
    binary = find_runtime_binary(runtime, runtime_binary or provisioned_binary)
    is_default = runtime == default_runtime

    profile: dict[str, object] = {
        "schema": "weave-runtime-profile/v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "package": {
            "slug": company.get("slug"),
            "version": company.get("version"),
            "default_runtime": default_runtime,
            "fallback_runtime": fallback_runtime,
        },
        "runtime": {
            "id": runtime,
            "is_default": is_default,
            "agent_slug": agent_slug,
            "agent_name": agent.get("name"),
            "adapter_type": agent.get("adapterType"),
            "agent_contract": str(agent_path.relative_to(REPO_ROOT)),
            "binary": binary,
        },
        "runtime_home": {
            "schema": weave_runtime_slice.RUNTIME_HOME_SCHEMA,
            "path": str(runtime_home),
            "weave_state_path": str(weave_root),
            "hermes_home_path": str(hermes_home),
            "profile_path": str(DEFAULT_PROFILE_PATH if runtime_home == DEFAULT_RUNTIME_HOME else runtime_home / "runtime-profile.json"),
            "durable_state_owner": "local runtime home",
            "container_state_policy": "replaceable; durable state is mounted from runtime home",
            "secret_migration_policy": "raw secrets are not exported by default; relink credentials after import",
        },
        "authority": {
            "public_safe": True,
            "network_install_performed": network_install_performed,
            "service_installed": False,
            "secrets_loaded": False,
            "external_actions": "blocked",
            "autonomy": weave_runtime_slice.autonomy_policy(weave_runtime_slice.DEFAULT_AUTONOMY_MODE),
            "approval_gates": [
                "runtime pairing",
                "gateway pairing",
                "autostart or service enablement",
                "production deploys",
                "credential changes",
                "paid jobs or metered external API calls",
                "public posts or external sends",
            ],
        },
        "gateway": {
            "channel": "telegram" if runtime == "hermes-default" else None,
            "hermes_home": str(hermes_home),
            "setup_required": runtime == "hermes-default",
            "setup_command": "scripts/setup_runtime.py --gateway-token-file",
            "standalone_setup_command": "scripts/setup_gateway.py",
            "token_loaded": False,
            "allowlist_configured": False,
            "allowlist_mode": None,
            "paired": False,
            "gateway_started": False,
            "service_installed": False,
            "runtime_config_written": False,
            "terminal_cwd_configured": False,
            "agent_system_prompt_configured": False,
            "autonomy_mode": weave_runtime_slice.DEFAULT_AUTONOMY_MODE,
            "weave_plugin_installed": False,
            "weave_plugin_enabled": False,
            "verification_commands": [
                "hermes status",
                "hermes gateway status",
                "hermes gateway run",
            ],
            "deterministic_slash_commands": sorted(weave_runtime_slice.TELEGRAM_COMMANDS),
        },
        "hermes_setup": {
            "schema": weave_hermes_setup.SCHEMA,
            "required_before_normal_chat": runtime == "hermes-default",
            "status_command": "weave hermes status",
            "confirm_command": "weave hermes confirm-ready",
            "slash_only_command": "weave onboard --slash-only",
            "hermes_home": str(hermes_home),
            "route_verification_owner": "hermes",
            "state": weave_hermes_setup.hermes_setup_status(hermes_home)["state"],
            "normal_chat_assumed_ready": weave_hermes_setup.hermes_setup_status(hermes_home)["normal_chat_assumed_ready"],
            "secret_value_printed": False,
        },
        "weave_root": {
            "path": str(weave_root),
            "runtime_home_path": str(runtime_home),
            "schema": weave_runtime_slice.ROOT_SCHEMA,
            "setup_command": "scripts/setup_runtime.py",
            "writes_only_ignored_local_artifacts": True,
        },
        "foundation_onboarding": {
            "setup_required": runtime == "hermes-default",
            "active": False,
            "app_id": None,
            "app_name": None,
            "gate_passed": None,
            "foundation_gate_path": None,
            "gateway_workdir": None,
            "gateway_start_cwd": None,
            "question_limit": 3,
            "communication_channel": "telegram" if runtime == "hermes-default" else None,
            "required_before_app_work": runtime == "hermes-default",
        },
    }
    if hermes_provision_profile:
        upstream = hermes_provision_profile.get("upstream", {})
        status = hermes_provision_profile.get("status", {})
        local = hermes_provision_profile.get("local", {})
        profile["hermes_provision"] = {
            "schema": hermes_provision_profile.get("schema"),
            "source_verified": status.get("source_verified") if isinstance(status, dict) else False,
            "dependencies_installed": status.get("dependencies_installed") if isinstance(status, dict) else False,
            "binary_present": status.get("binary_present") if isinstance(status, dict) else False,
            "pinned_commit": upstream.get("pinned_commit") if isinstance(upstream, dict) else None,
            "checked_out_commit": upstream.get("checked_out_commit") if isinstance(upstream, dict) else None,
            "package_version": upstream.get("package_version") if isinstance(upstream, dict) else None,
            "version_check": status.get("version_check") if isinstance(status, dict) else None,
            "profile_path": str(hermes_profile_path.relative_to(REPO_ROOT)) if hermes_profile_path.is_relative_to(REPO_ROOT) else str(hermes_profile_path),
            "wrapper_path": local.get("wrapper_path") if isinstance(local, dict) else None,
        }
    if runtime_container_image:
        runtime_info = profile["runtime"]
        assert isinstance(runtime_info, dict)
        runtime_info["container"] = {
            "enabled": True,
            "engine": "docker",
            "image": runtime_container_image,
            "supervision": "weave start uses Docker restart policy unless-stopped",
            "service_installed": False,
        }
    return profile


def resolve_runtime_paths(args: argparse.Namespace) -> None:
    args.runtime_home = (args.runtime_home or DEFAULT_RUNTIME_HOME).expanduser().resolve()
    args.weave_root = (args.weave_root or (args.runtime_home / DEFAULT_WEAVE_STATE_DIR)).expanduser().resolve()
    args.gateway_hermes_home = (
        args.gateway_hermes_home or (args.runtime_home / DEFAULT_HERMES_HOME_DIR)
    ).expanduser().resolve()
    args.profile_out = (args.profile_out or (args.runtime_home / "runtime-profile.json")).expanduser().resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Set up a local WEAVE runtime profile.")
    parser.add_argument(
        "--runtime",
        choices=sorted(RUNTIME_AGENT),
        default=None,
        help="runtime to select; defaults to COMPANY.md runtime",
    )
    parser.add_argument("--runtime-binary", help="explicit runtime executable to check")
    parser.add_argument("--runtime-container-image", help="container image that provides the Hermes runtime")
    parser.add_argument(
        "--install-hermes",
        action="store_true",
        help="clone and install the pinned real Nous Hermes Agent into ignored local state",
    )
    parser.add_argument(
        "--hermes-install-root",
        type=Path,
        default=provision_hermes.DEFAULT_INSTALL_ROOT,
        help="ignored local Hermes install directory",
    )
    parser.add_argument(
        "--hermes-profile-out",
        type=Path,
        default=provision_hermes.DEFAULT_PROFILE_PATH,
        help="ignored local Hermes provision profile path",
    )
    parser.add_argument("--hermes-repo-url", default=provision_hermes.HERMES_REPO_URL)
    parser.add_argument("--hermes-commit", default=provision_hermes.HERMES_PINNED_COMMIT)
    parser.add_argument("--hermes-source-repo", type=Path, help="local Hermes source git repo for tests or mirrors")
    parser.add_argument("--hermes-python", default=sys.executable)
    parser.add_argument("--hermes-extras", default="cli", help="Hermes extras to install, default: cli")
    parser.add_argument("--hermes-no-install-deps", action="store_true", help="clone and verify Hermes source only")
    parser.add_argument("--hermes-timeout", type=int, default=900)
    parser.add_argument(
        "--gateway-token-file",
        dest="gateway_bot_file",
        type=Path,
        help="owner-approved file containing the Telegram bot token",
    )
    parser.add_argument("--gateway-hermes-home", type=Path, default=None)
    parser.add_argument("--gateway-allowed-users", help="comma-separated Telegram numeric user ids")
    parser.add_argument("--gateway-group-allowed-users", help="comma-separated Telegram numeric group user ids")
    parser.add_argument(
        "--configure-gateway-context",
        action="store_true",
        help="refresh Hermes gateway cwd/system prompt/runtime config without touching bot credentials",
    )
    parser.add_argument(
        "--gateway-allow-all-users",
        action="store_true",
        help="temporary discovery mode; replace with --gateway-allowed-users after capturing the owner id",
    )
    parser.add_argument("--gateway-home-channel", help="optional Telegram home channel/chat id")
    parser.add_argument(
        "--autonomy-mode",
        choices=sorted(weave_runtime_slice.AUTONOMY_MODES),
        default=weave_runtime_slice.DEFAULT_AUTONOMY_MODE,
        help="runtime confirmation mode; yolo proceeds on non-gated work and asks through the LLM for hard gates",
    )
    parser.add_argument(
        "--runtime-home",
        type=Path,
        default=None,
        help="durable local runtime home; defaults to runs/runtime-home",
    )
    parser.add_argument(
        "--profile-out",
        type=Path,
        default=None,
        help="local profile path to write",
    )
    parser.add_argument(
        "--weave-root",
        type=Path,
        default=None,
        help="ignored local WEAVE root to create or verify",
    )
    parser.add_argument(
        "--skip-weave-root",
        action="store_true",
        help="write only the runtime profile and skip WEAVE root creation",
    )
    parser.add_argument(
        "--foundation-app-id",
        default=DEFAULT_FOUNDATION_APP_ID,
        help="app workspace to create or verify for mandatory Hermes foundation onboarding",
    )
    parser.add_argument(
        "--foundation-app-name",
        default=DEFAULT_FOUNDATION_APP_NAME,
        help="display name for the mandatory Hermes foundation onboarding app workspace",
    )
    parser.add_argument(
        "--skip-foundation-onboarding",
        action="store_true",
        help="create the WEAVE root without generating the Hermes foundation onboarding gateway workdir",
    )
    parser.add_argument(
        "--require-runtime-binary",
        action="store_true",
        help="fail when the selected runtime executable is not on PATH",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate setup inputs and print the profile without writing it",
    )
    args = parser.parse_args(argv)
    resolve_runtime_paths(args)

    try:
        company = parse_frontmatter(PACKAGE_ROOT / "COMPANY.md")
        runtime = args.runtime or company["runtime"]
        hermes_profile = None
        network_install_performed = False
        if runtime == "hermes-default" and args.install_hermes and not args.check:
            hermes_profile = provision_hermes.provision_hermes(
                install_root=args.hermes_install_root,
                repo_url=args.hermes_repo_url,
                commit=args.hermes_commit,
                source_repo=args.hermes_source_repo,
                python=args.hermes_python,
                extras=args.hermes_extras,
                install_deps=not args.hermes_no_install_deps,
                timeout=args.hermes_timeout,
                profile_path=args.hermes_profile_out,
            )
            network_install_performed = True
        elif runtime == "hermes-default":
            hermes_profile = read_hermes_provision_profile(args.hermes_profile_out)
        profile = runtime_profile(
            runtime,
            args.runtime_binary,
            runtime_home=args.runtime_home,
            weave_root=args.weave_root,
            hermes_home=args.gateway_hermes_home,
            hermes_provision_profile=hermes_profile,
            hermes_profile_path=args.hermes_profile_out,
            network_install_performed=network_install_performed,
            runtime_container_image=args.runtime_container_image,
        )
        if args.require_runtime_binary and not profile["runtime"]["binary"]["found"]:
            raise RuntimeSetupError(f"{runtime} binary was not found on PATH")
        gateway_result = None
        gateway_home_channel = args.gateway_home_channel
        if not gateway_home_channel:
            gateway_home_channel = _single_allowed_user(args.gateway_allowed_users)
        if args.gateway_bot_file:
            if runtime != "hermes-default":
                raise RuntimeSetupError("gateway setup is only supported for hermes-default")
            if args.check:
                raise RuntimeSetupError("gateway setup cannot run with --check")
            try:
                gateway_result = setup_gateway.configure_gateway(
                    hermes_home=args.gateway_hermes_home.expanduser(),
                    bot_file=args.gateway_bot_file.expanduser(),
                    allowed_users=args.gateway_allowed_users,
                    group_allowed_users=args.gateway_group_allowed_users,
                    allow_all_users=args.gateway_allow_all_users,
                    home_channel=gateway_home_channel,
                    autonomy_mode=args.autonomy_mode,
                )
            except setup_gateway.GatewaySetupError as exc:
                raise RuntimeSetupError(f"gateway setup failed: {exc}") from exc
            gateway = profile["gateway"]
            if isinstance(gateway, dict):
                gateway["token_loaded"] = gateway_result["telegram_bot_token_configured"]
                gateway["allowlist_configured"] = gateway_result["allowlist_mode"] == "allowed_users"
                gateway["allowlist_mode"] = gateway_result["allowlist_mode"]
                gateway["home_channel_configured"] = gateway_result["home_channel_configured"]
                gateway["autonomy_mode"] = gateway_result["autonomy_mode"]
                gateway["env_written"] = gateway_result["env_written"]
                gateway["env_private_mode"] = gateway_result["env_private_mode"]
        root_status = None
        onboarding_status = None
        plugin_result = None
        refreshed_agent_profile = None
        runtime_home_profile = profile.get("runtime_home")
        if isinstance(runtime_home_profile, dict):
            runtime_home_profile["profile_path"] = str(args.profile_out)
        if args.check:
            print(json.dumps(profile, indent=2, sort_keys=True))
            return 0
        if not args.skip_weave_root:
            if runtime == "hermes-default" and not args.skip_foundation_onboarding:
                onboarding_status = weave_runtime_slice.setup_foundation_onboarding(
                    args.weave_root,
                    args.foundation_app_id,
                    args.foundation_app_name,
                    autonomy_mode=args.autonomy_mode,
                )
                root_status = onboarding_status["root_status"]
                profile["authority"]["autonomy"] = onboarding_status["autonomy"]
                profile["gateway"]["autonomy_mode"] = onboarding_status["autonomy"]["mode"]
                foundation = profile["foundation_onboarding"]
                if isinstance(foundation, dict):
                    foundation.update(
                        {
                            "active": True,
                            "app_id": onboarding_status["app_id"],
                            "app_name": onboarding_status["app_name"],
                            "gate_passed": onboarding_status["foundation_gate"]["passed"],
                            "foundation_gate_path": onboarding_status["foundation_gate_path"],
                            "gateway_workdir": onboarding_status["gateway_workdir"],
                            "gateway_start_cwd": onboarding_status["gateway_start_cwd"],
                            "agents_path": onboarding_status["agents_path"],
                            "soul_path": onboarding_status["soul_path"],
                            "context_path": onboarding_status["context_path"],
                        }
                    )
                if gateway_result or args.configure_gateway_context:
                    gateway_config = configure_hermes_gateway_context(
                        args.gateway_hermes_home.expanduser(),
                        onboarding_status,
                        runtime_home=args.runtime_home,
                    )
                    gateway = profile["gateway"]
                    if isinstance(gateway, dict):
                        gateway["runtime_config_written"] = True
                        gateway["terminal_cwd_configured"] = True
                        gateway["agent_system_prompt_configured"] = gateway_config[
                            "agent_system_prompt_configured"
                        ]
                        gateway["runtime_config_path"] = gateway_config["config_path"]
                        gateway["terminal_cwd"] = gateway_config["terminal_cwd"]
            else:
                root_status = weave_runtime_slice.setup_weave_root(args.weave_root, autonomy_mode=args.autonomy_mode)
                profile["authority"]["autonomy"] = root_status["autonomy"]
            refreshed_agent_profile = refresh_agent_profile_from_environment(args.weave_root)
            if refreshed_agent_profile and root_status:
                root_status["agent_profile"] = refreshed_agent_profile
                if onboarding_status:
                    onboarding_status["root_status"] = root_status
            if runtime == "hermes-default":
                plugin_result = install_weave_runtime_hermes_plugin(
                    args.gateway_hermes_home.expanduser(),
                    weave_root=args.weave_root,
                    runtime_home=args.runtime_home,
                )
                gateway = profile["gateway"]
                if isinstance(gateway, dict):
                    gateway["weave_plugin_installed"] = True
                    gateway["weave_plugin_enabled"] = bool(plugin_result["enabled"])
                    gateway["weave_plugin"] = plugin_result["plugin"]
                    gateway["weave_plugin_dir"] = plugin_result["plugin_dir"]
        args.profile_out.parent.mkdir(parents=True, exist_ok=True)
        args.profile_out.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except RuntimeSetupError as exc:
        print(f"runtime setup failed: {exc}", file=sys.stderr)
        return 1

    container_ready = bool(profile["runtime"].get("container", {}).get("enabled"))
    status = "ready" if profile["runtime"]["binary"]["found"] or container_ready else "profile_written_runtime_binary_missing"
    print(f"runtime setup: {status}")
    print(f"profile: {args.profile_out}")
    print(f"runtime_home: {args.runtime_home}")
    print(f"runtime: {profile['runtime']['id']}")
    print(f"agent: {profile['runtime']['agent_slug']}")
    print(f"runtime_container_enabled: {str(container_ready).lower()}")
    print(f"gateway_setup_required: {str(profile['gateway']['setup_required']).lower()}")
    print(f"gateway_token_loaded: {str(profile['gateway']['token_loaded']).lower()}")
    print(f"gateway_allowlist_mode: {profile['gateway']['allowlist_mode']}")
    print(f"autonomy_mode: {profile['gateway']['autonomy_mode']}")
    print(f"gateway_started: {str(profile['gateway']['gateway_started']).lower()}")
    print(f"gateway_home_channel_configured: {str(profile['gateway'].get('home_channel_configured', False)).lower()}")
    print(f"gateway_runtime_config_written: {str(profile['gateway']['runtime_config_written']).lower()}")
    print(f"gateway_weave_plugin_installed: {str(profile['gateway']['weave_plugin_installed']).lower()}")
    print(f"gateway_weave_plugin_enabled: {str(profile['gateway']['weave_plugin_enabled']).lower()}")
    print(f"foundation_onboarding_active: {str(profile['foundation_onboarding']['active']).lower()}")
    print(f"foundation_gate_passed: {profile['foundation_onboarding']['gate_passed']}")
    if root_status:
        print(f"weave_root: {args.weave_root}")
        print(f"weave_root_schema: {root_status['schema']}")
        print(f"weave_root_git_tracked: {str(root_status['git_tracked']).lower()}")
    if onboarding_status:
        print(f"foundation_app_id: {onboarding_status['app_id']}")
        print(f"foundation_gateway_workdir: {onboarding_status['gateway_workdir']}")
    if refreshed_agent_profile:
        print(f"agent_profile_refreshed: true")
    if profile.get("hermes_provision"):
        hermes = profile["hermes_provision"]
        print(f"hermes_provisioned: {str(bool(hermes.get('source_verified'))).lower()}")
        print(f"hermes_binary_present: {str(bool(hermes.get('binary_present'))).lower()}")
        print(f"hermes_commit: {hermes.get('checked_out_commit')}")
    print(f"network_install_performed: {str(profile['authority']['network_install_performed']).lower()}")
    print("service_installed: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

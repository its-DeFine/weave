#!/usr/bin/env python3
"""Non-secret Hermes provider-auth readiness helpers for WEAVE."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

try:
    import yaml
except ImportError:  # pragma: no cover - keeps the helper usable without PyYAML
    yaml = None


SCHEMA = "weave-provider-auth/v0.1"
STATUS_FILE = "weave-provider-auth.json"
CANARY_PROMPT = "Reply exactly WEAVE_PROVIDER_OK and nothing else."
CANARY_MARKER = "WEAVE_PROVIDER_OK"

PROVIDER_ENV_KEYS = {
    "anthropic": ["ANTHROPIC_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"],
    "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    "gemini": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    "groq": ["GROQ_API_KEY"],
    "mistral": ["MISTRAL_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "openrouter": ["OPENROUTER_API_KEY"],
    "xai": ["XAI_API_KEY"],
}

OAUTH_PROVIDERS = {
    "codex",
    "copilot",
    "nous",
    "nous-portal",
    "portal",
}


class ProviderAuthError(Exception):
    """Raised when provider readiness cannot be recorded or verified."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def status_path(hermes_home: Path) -> Path:
    return hermes_home / STATUS_FILE


def config_path(hermes_home: Path) -> Path:
    return hermes_home / "config.yaml"


def env_path(hermes_home: Path) -> Path:
    return hermes_home / ".env"


def auth_path(hermes_home: Path) -> Path:
    return hermes_home / "auth.json"


def parse_env_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    keys: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if value.strip():
            keys.add(key.strip())
    return keys


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    if yaml is not None:
        loaded = yaml.safe_load(text) or {}
        return loaded if isinstance(loaded, dict) else {}
    data: dict[str, Any] = {}
    current: dict[str, Any] | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith((" ", "\t")):
            if ":" not in raw:
                continue
            key, value = raw.split(":", 1)
            value = value.strip()
            if value:
                data[key.strip()] = value.strip("'\"")
                current = None
            else:
                current = {}
                data[key.strip()] = current
            continue
        if current is None or ":" not in raw:
            continue
        key, value = raw.strip().split(":", 1)
        current[key.strip()] = value.strip().strip("'\"")
    return data


def load_model_config(hermes_home: Path) -> dict[str, Any]:
    config = load_yaml_mapping(config_path(hermes_home))
    model = config.get("model")
    if isinstance(model, dict):
        provider = str(model.get("provider") or "").strip()
        default_model = str(model.get("default") or model.get("model") or "").strip()
        return {
            "configured": bool(provider and default_model),
            "provider": provider,
            "model": default_model,
            "api_mode": str(model.get("api_mode") or "").strip(),
            "base_url_configured": bool(model.get("base_url")),
            "config_shape": "mapping",
        }
    if isinstance(model, str) and model.strip():
        return {
            "configured": False,
            "provider": "",
            "model": model.strip(),
            "api_mode": "",
            "base_url_configured": False,
            "config_shape": "string",
        }
    return {
        "configured": False,
        "provider": "",
        "model": "",
        "api_mode": "",
        "base_url_configured": False,
        "config_shape": "missing_or_empty",
    }


def credential_signal(hermes_home: Path, provider: str) -> dict[str, Any]:
    normalized = provider.strip().lower()
    env_keys = parse_env_keys(env_path(hermes_home))
    expected_keys = PROVIDER_ENV_KEYS.get(normalized, [])
    matched_keys = sorted(key for key in expected_keys if key in env_keys)
    oauth_ready = normalized in OAUTH_PROVIDERS and auth_path(hermes_home).exists()
    return {
        "provider": provider,
        "credential_source": "oauth" if oauth_ready else "env" if matched_keys else "unknown",
        "credential_present": bool(oauth_ready or matched_keys),
        "expected_env_keys": expected_keys,
        "present_env_keys": matched_keys,
        "oauth_auth_file_present": auth_path(hermes_home).exists(),
        "secret_value_printed": False,
    }


def load_recorded_status(hermes_home: Path) -> dict[str, Any]:
    path = status_path(hermes_home)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def status_matches_model(recorded: dict[str, Any], model_config: dict[str, Any]) -> bool:
    return (
        recorded.get("provider") == model_config.get("provider")
        and recorded.get("model") == model_config.get("model")
    )


def provider_auth_status(hermes_home: Path) -> dict[str, Any]:
    hermes_home = hermes_home.expanduser().resolve()
    model_config = load_model_config(hermes_home)
    cred_state = credential_signal(hermes_home, model_config["provider"])
    recorded = load_recorded_status(hermes_home)
    slash_only = recorded.get("mode") == "slash_only"
    canary = recorded.get("canary") if isinstance(recorded.get("canary"), dict) else {}
    canary_verified = bool(
        canary.get("status") == "passed"
        and recorded.get("mode") == "chat_verified"
        and status_matches_model(recorded, model_config)
    )

    if slash_only:
        state = "slash_only"
        chat_ready = False
        blocker = "normal Hermes chat intentionally disabled; deterministic slash commands remain available"
    elif not model_config["configured"]:
        state = "missing_model_config"
        chat_ready = False
        blocker = "Hermes model provider is not configured"
    elif not cred_state["credential_present"]:
        state = "missing_credentials"
        chat_ready = False
        blocker = f"Hermes credentials are missing for provider {model_config['provider']}"
    elif not canary_verified:
        state = "configured_unverified"
        chat_ready = False
        blocker = "Hermes provider credentials exist but the WEAVE canary has not passed"
    else:
        state = "verified"
        chat_ready = True
        blocker = ""

    return {
        "schema": SCHEMA,
        "hermes_home": str(hermes_home),
        "state": state,
        "chat_ready": chat_ready,
        "provider": model_config["provider"] or "unknown",
        "model": model_config["model"] or "unknown",
        "model_config": model_config,
        "credentials": cred_state,
        "canary": canary,
        "blocker": blocker,
        "setup_commands": setup_commands(hermes_home),
        "secret_value_printed": False,
        "recorded_at": utc_now(),
    }


def setup_commands(hermes_home: Path) -> list[str]:
    home = str(hermes_home)
    return [
        f"HERMES_HOME={home} hermes setup --portal",
        f"HERMES_HOME={home} hermes model",
        "weave provider verify",
        "weave onboard --slash-only",
    ]


def write_status_file(hermes_home: Path, payload: dict[str, Any]) -> dict[str, Any]:
    hermes_home.mkdir(parents=True, exist_ok=True)
    hermes_home.chmod(0o700)
    payload = dict(payload)
    payload["schema"] = SCHEMA
    payload["secret_value_printed"] = False
    payload["recorded_at"] = utc_now()
    fd, name = tempfile.mkstemp(prefix=".weave-provider-auth.", dir=str(hermes_home), text=True)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        tmp.chmod(0o600)
        tmp.replace(status_path(hermes_home))
        status_path(hermes_home).chmod(0o600)
    finally:
        if tmp.exists():
            tmp.unlink()
    return payload


def mark_slash_only(hermes_home: Path, *, reason: str = "operator_selected_slash_only") -> dict[str, Any]:
    model_config = load_model_config(hermes_home)
    return write_status_file(
        hermes_home,
        {
            "mode": "slash_only",
            "provider": model_config["provider"] or "unknown",
            "model": model_config["model"] or "unknown",
            "reason": reason,
            "canary": {"status": "not_run"},
            "chat_ready": False,
        },
    )


def run_canary(hermes_home: Path, *, hermes_command: str = "hermes", timeout: int = 90) -> dict[str, Any]:
    status = provider_auth_status(hermes_home)
    if status["state"] in {"missing_model_config", "missing_credentials", "slash_only"}:
        raise ProviderAuthError(status["blocker"])
    env = os.environ.copy()
    env["HERMES_HOME"] = str(hermes_home.expanduser().resolve())
    command = [hermes_command, "chat", "-q", CANARY_PROMPT]
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False, env=env)
    except OSError as exc:
        raise ProviderAuthError(f"could not run Hermes canary command: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ProviderAuthError(f"Hermes canary timed out after {timeout}s") from exc
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    if result.returncode != 0:
        raise ProviderAuthError("Hermes provider canary failed; raw provider output is in Hermes logs")
    if CANARY_MARKER not in combined:
        raise ProviderAuthError("Hermes provider canary did not return the expected marker")
    model_config = load_model_config(hermes_home)
    return write_status_file(
        hermes_home,
        {
            "mode": "chat_verified",
            "provider": model_config["provider"],
            "model": model_config["model"],
            "canary": {
                "status": "passed",
                "marker_seen": True,
                "command": "hermes chat -q",
                "output_stored": False,
                "raw_output_printed": False,
            },
            "chat_ready": True,
        },
    )


def print_status(status: dict[str, Any], output: TextIO = sys.stdout) -> None:
    print("WEAVE Provider Auth", file=output)
    print(f"- state: {status['state']}", file=output)
    print(f"- chat_ready: {str(status['chat_ready']).lower()}", file=output)
    print(f"- provider: {status['provider']}", file=output)
    print(f"- model: {status['model']}", file=output)
    print(f"- credential_source: {status['credentials']['credential_source']}", file=output)
    print(f"- secret_value_printed: {str(status['secret_value_printed']).lower()}", file=output)
    if status["blocker"]:
        print(f"- blocker: {status['blocker']}", file=output)
        print("- next:", file=output)
        for command in status["setup_commands"][:3]:
            print(f"  {command}", file=output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and verify Hermes provider auth for WEAVE.")
    parser.add_argument("--hermes-home", type=Path, default=Path(os.environ.get("HERMES_HOME", "~/.hermes")))
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("status", help="show non-secret provider readiness")
    subparsers.add_parser("mark-slash-only", help="record slash-only mode for deterministic commands")
    verify = subparsers.add_parser("verify", help="run a tiny Hermes model canary and record readiness")
    verify.add_argument("--hermes-command", default="hermes")
    verify.add_argument("--timeout", type=int, default=90)
    return parser


def main(argv: list[str] | None = None, *, output: TextIO = sys.stdout) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    hermes_home = args.hermes_home.expanduser().resolve()
    try:
        if args.command in {None, "status"}:
            print_status(provider_auth_status(hermes_home), output)
            return 0
        if args.command == "mark-slash-only":
            mark_slash_only(hermes_home)
            print_status(provider_auth_status(hermes_home), output)
            return 0
        if args.command == "verify":
            run_canary(hermes_home, hermes_command=args.hermes_command, timeout=args.timeout)
            print_status(provider_auth_status(hermes_home), output)
            return 0
    except ProviderAuthError as exc:
        print(f"provider auth failed: {exc}", file=output)
        print("secret_value_printed: false", file=output)
        return 1
    parser.print_help(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

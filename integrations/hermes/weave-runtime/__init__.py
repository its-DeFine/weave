"""Hermes plugin exposing deterministic WEAVE runtime commands.

The plugin is public-safe and generic. Runtime-specific paths are read from
Hermes config under ``weave_runtime`` or from environment variables.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any
from urllib import request

logger = logging.getLogger(__name__)

COMMANDS = {
    "sources": "/sources",
    "apps": "/apps",
    "app": "/app",
    "blockers": "/blockers",
    "changes": "/changes",
    "next": "/next",
    "transcript": "/transcript",
    "autonomy": "/autonomy",
    "weave-status": "/status",
}

TELEGRAM_MENU_COMMANDS = [
    ("status", "Show WEAVE runtime status."),
    ("sources", "Show WEAVE runtime source map."),
    ("apps", "List WEAVE apps and stages."),
    ("next", "Show next WEAVE action."),
    ("transcript", "Show WEAVE app conversation transcript."),
    ("blockers", "Show WEAVE blockers."),
    ("changes", "Show latest WEAVE changes."),
    ("autonomy", "Show WEAVE autonomy mode."),
    ("weave_status", "Show deterministic WEAVE status."),
]

_REGISTERED_TELEGRAM_CHATS: set[str] = set()


def _config() -> dict[str, Any]:
    try:
        from hermes_cli.config import load_config

        data = load_config()
        return data if isinstance(data, dict) else {}
    except Exception as exc:  # pragma: no cover - depends on Hermes runtime
        logger.debug("could not load Hermes config: %s", exc)
        return {}


def _path_from_config_or_env(config_key: str, env_key: str) -> Path | None:
    value = os.environ.get(env_key)
    if not value:
        runtime = _config().get("weave_runtime", {})
        if isinstance(runtime, dict):
            value = runtime.get(config_key)
    if not isinstance(value, str) or not value.strip():
        return None
    return Path(value).expanduser().resolve()


def _runtime_paths() -> tuple[Path | None, Path | None]:
    repo = _path_from_config_or_env("repo", "WEAVE_RUNTIME_REPO")
    root = _path_from_config_or_env("root", "WEAVE_RUNTIME_ROOT")
    return repo, root


def _module_path_from_runtime_repo(repo: Path, module_name: str) -> Path:
    try:
        repo_root = repo.resolve(strict=True)
        scripts_dir = (repo_root / "scripts").resolve(strict=True)
        module_path = (scripts_dir / f"{module_name}.py").resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("configured WEAVE runtime repo is unavailable") from exc
    if not module_path.is_relative_to(scripts_dir):
        raise RuntimeError("configured WEAVE runtime module path is outside the scripts directory")
    return module_path


def _load_runtime_script_module(repo: Path, module_name: str):
    module_path = _module_path_from_runtime_repo(repo, module_name)
    scripts_dir = str(module_path.parent)
    added_to_path = scripts_dir not in sys.path
    if added_to_path:
        # Keep the trusted runtime scripts directory available only for sibling
        # imports during this load, and never put it at the front of sys.path.
        sys.path.append(scripts_dir)
    try:
        spec = importlib.util.spec_from_file_location(f"_weave_runtime_plugin_{module_name}", module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load WEAVE runtime module")
        module = importlib.util.module_from_spec(spec)
        previous_module = sys.modules.get(spec.name)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            if previous_module is None:
                sys.modules.pop(spec.name, None)
            else:
                sys.modules[spec.name] = previous_module
        return module
    finally:
        if added_to_path:
            try:
                sys.path.remove(scripts_dir)
            except ValueError:  # pragma: no cover - defensive cleanup
                pass


def _load_runtime_module(repo: Path):
    return _load_runtime_script_module(repo, "weave_runtime_slice")


def _dispatch(command_text: str) -> str:
    repo, root = _runtime_paths()
    if repo is None or root is None:
        return "WEAVE runtime command layer is not configured."
    if not (repo / "scripts" / "weave_runtime_slice.py").exists():
        return "WEAVE runtime command layer is unavailable."
    try:
        runtime = _load_runtime_module(repo)
        payload = runtime.dispatch_telegram_command(root, command_text)
    except Exception:
        logger.exception("WEAVE runtime command failed")
        return "WEAVE runtime command failed. Check local runtime logs."
    text = payload.get("text") if isinstance(payload, dict) else None
    return str(text) if text else "WEAVE runtime command returned no output."


def _event_text(event: Any) -> str:
    if event is None:
        return ""
    if isinstance(event, dict):
        return str(event.get("text") or event.get("message") or event.get("content") or "")
    for name in ("text", "message", "content"):
        value = getattr(event, name, "")
        if isinstance(value, str) and value.strip():
            return value
    message = getattr(event, "message", None)
    if message is not None:
        return _event_text(message)
    return ""


def _hermes_setup_gate_message() -> str | None:
    hermes_home = os.environ.get("HERMES_HOME", "").strip()
    if not hermes_home:
        return None
    repo, _root = _runtime_paths()
    if repo is None:
        return None
    try:
        hermes_setup = _load_runtime_script_module(repo, "weave_hermes_setup")
        status = hermes_setup.hermes_setup_status(Path(hermes_home))
    except Exception as exc:
        logger.debug("could not inspect WEAVE Hermes setup status: %s", exc)
        return None
    if status.get("normal_chat_assumed_ready"):
        return None
    state = status.get("state", "unknown")
    blocker = status.get("blocker") or "Hermes setup has not been confirmed."
    return "\n".join(
        [
            "Hermes setup has not been confirmed for WEAVE normal chat yet.",
            "",
            f"- hermes_setup: {state}",
            f"- route_verification_owner: {status.get('route_verification_owner', 'hermes')}",
            f"- blocker: {blocker}",
            "",
            "Deterministic WEAVE commands still work:",
            "- /status",
            "- /apps",
            "- /help",
            "",
            "Complete normal Hermes setup, confirm Hermes itself can chat, then run `weave hermes confirm-ready`.",
        ]
    )


def _csv_ids(name: str) -> set[str]:
    return {item.strip() for item in os.environ.get(name, "").split(",") if item.strip()}


def _is_allowed_telegram_source(source: Any) -> bool:
    platform = getattr(getattr(source, "platform", None), "value", getattr(source, "platform", ""))
    if str(platform).lower() != "telegram":
        return False
    if os.environ.get("GATEWAY_ALLOW_ALL_USERS", "").lower() in {"1", "true", "yes", "on"}:
        return True
    user_id = str(getattr(source, "user_id", "") or "")
    if user_id and user_id in _csv_ids("TELEGRAM_ALLOWED_USERS"):
        return True
    if user_id and user_id in _csv_ids("TELEGRAM_GROUP_ALLOWED_USERS"):
        return True
    return False


def _coerce_chat_id(value: str) -> int | str:
    clean = str(value).strip()
    if clean.lstrip("-").isdigit():
        return int(clean)
    return clean


def _register_telegram_menu_for_event(event: Any) -> None:
    source = getattr(event, "source", None)
    if source is None or not _is_allowed_telegram_source(source):
        return
    chat_id = str(getattr(source, "chat_id", "") or getattr(source, "user_id", "") or "")
    if not chat_id or chat_id in _REGISTERED_TELEGRAM_CHATS:
        return
    bot_value = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_value:
        return
    payload = {
        "scope": {"type": "chat", "chat_id": _coerce_chat_id(chat_id)},
        "commands": [
            {"command": command, "description": description}
            for command, description in TELEGRAM_MENU_COMMANDS
        ],
    }
    url = f"https://api.telegram.org/bot{bot_value}/setMyCommands"
    try:
        req = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
        if result.get("ok") is True:
            _REGISTERED_TELEGRAM_CHATS.add(chat_id)
        else:
            logger.debug("Telegram WEAVE command menu registration was not accepted.")
    except Exception as exc:
        logger.debug("Telegram WEAVE command menu registration failed: %s", exc)


def _command(command_name: str):
    runtime_command = COMMANDS[command_name]

    def _handler(raw_args: str = "") -> str:
        text = f"{runtime_command} {raw_args}".strip()
        return _dispatch(text)

    return _handler


def _status_hook(_event_type: str, _context: dict[str, Any]) -> dict[str, str]:
    return {"decision": "handled", "message": _dispatch("/status")}


def _pre_gateway_dispatch_hook(_event_type: str, context: dict[str, Any]) -> dict[str, str] | None:
    event = context.get("event")
    _register_telegram_menu_for_event(event)
    text = _event_text(event).strip()
    if not text or text.startswith("/"):
        return None
    message = _hermes_setup_gate_message()
    if not message:
        return None
    return {"decision": "handled", "message": message}


def register(ctx) -> None:
    for command_name in sorted(COMMANDS):
        description = "Show deterministic WEAVE runtime state."
        args_hint = ""
        if command_name == "app":
            description = "Show one WEAVE app state."
            args_hint = "<app_id>"
        elif command_name == "changes":
            description = "Show latest WEAVE app changes."
            args_hint = "[app_id]"
        elif command_name == "transcript":
            description = "Show WEAVE app conversation transcript."
            args_hint = "[app_id]"
        elif command_name == "weave-status":
            description = "Show deterministic WEAVE runtime status."
        elif command_name == "sources":
            description = "Show WEAVE runtime source map."
        elif command_name == "apps":
            description = "List WEAVE apps and stages."
        elif command_name == "next":
            description = "Show next deterministic WEAVE action."
        elif command_name == "blockers":
            description = "Show WEAVE blockers."
        elif command_name == "autonomy":
            description = "Show WEAVE autonomy mode."
        ctx.register_command(
            command_name,
            _command(command_name),
            description=description,
            args_hint=args_hint,
        )
    ctx.register_hook("command:status", _status_hook)
    ctx.register_hook("pre_gateway_dispatch", _pre_gateway_dispatch_hook)

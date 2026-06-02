"""Hermes plugin exposing deterministic WEAVE runtime commands.

The plugin is public-safe and generic. Runtime-specific paths are read from
Hermes config under ``weave_runtime`` or from environment variables.
"""

from __future__ import annotations

import importlib
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
    "autonomy": "/autonomy",
    "weave-status": "/status",
}

TELEGRAM_MENU_COMMANDS = [
    ("status", "Show WEAVE runtime status."),
    ("sources", "Show WEAVE runtime source map."),
    ("apps", "List WEAVE apps and stages."),
    ("next", "Show next WEAVE action."),
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


def _load_runtime_module(repo: Path):
    scripts_dir = repo / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    return importlib.import_module("weave_runtime_slice")


def _dispatch(command_text: str) -> str:
    repo, root = _runtime_paths()
    if repo is None or root is None:
        return "WEAVE runtime command layer is not configured."
    if not (repo / "scripts" / "weave_runtime_slice.py").exists():
        return "WEAVE runtime command layer is unavailable."
    try:
        runtime = _load_runtime_module(repo)
        payload = runtime.dispatch_telegram_command(root, command_text)
    except Exception as exc:
        logger.debug("WEAVE runtime command failed: %s", exc)
        return f"WEAVE runtime command failed: {exc}"
    text = payload.get("text") if isinstance(payload, dict) else None
    return str(text) if text else "WEAVE runtime command returned no output."


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


def _pre_gateway_dispatch_hook(_event_type: str, context: dict[str, Any]) -> None:
    _register_telegram_menu_for_event(context.get("event"))


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

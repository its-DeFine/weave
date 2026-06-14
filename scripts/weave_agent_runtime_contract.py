#!/usr/bin/env python3
"""Runtime-neutral WEAVE agent adapter contract.

This module defines the small contract every agent runtime must satisfy before
WEAVE can call it plug-and-play. It is intentionally descriptive and
side-effect-free: probing, invocation, and live provider checks remain outside
this file.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any


CONTRACT_SCHEMA = "weave-agent-runtime-contract/v0.1"
CATALOG_SCHEMA = "weave-agent-runtime-catalog/v0.1"

REQUIRED_METHODS = ("probe", "invoke", "capture_turn", "post_event", "doctor")

SECRET_PATTERNS = (
    re.compile(r"\b[0-9]{6,20}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:sk|pk|rk|ghp|gho|github_pat)_[A-Za-z0-9_=-]{16,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}\b", re.IGNORECASE),
)


class AgentRuntimeContractError(Exception):
    """Raised when a runtime adapter contract is malformed or unsafe."""


def _contains_secret_like_value(value: Any) -> bool:
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in SECRET_PATTERNS)
    if isinstance(value, dict):
        return any(_contains_secret_like_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_secret_like_value(item) for item in value)
    return False


def _method(
    *,
    implemented: bool,
    owner: str,
    effect: str,
    proof: str,
    current_state: str,
    requires_live_runtime: bool = False,
    requires_owner_approval: bool = False,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "implemented": implemented,
        "owner": owner,
        "effect": effect,
        "proof": proof,
        "current_state": current_state,
        "requires_live_runtime": requires_live_runtime,
        "requires_owner_approval": requires_owner_approval,
        "notes": notes or [],
    }


def _base_contract(
    *,
    runtime_id: str,
    adapter_type: str,
    agent_slug: str,
    support_state: str,
    claim: str,
    methods: dict[str, dict[str, Any]],
    current_probe: dict[str, Any],
    unsupported_reason: str = "",
) -> dict[str, Any]:
    contract = {
        "schema": CONTRACT_SCHEMA,
        "runtime_id": runtime_id,
        "adapter_type": adapter_type,
        "agent_slug": agent_slug,
        "support_state": support_state,
        "claim": claim,
        "required_methods": list(REQUIRED_METHODS),
        "methods": methods,
        "current_probe": current_probe,
        "unsupported_reason": unsupported_reason,
        "secret_payload_allowed": False,
        "claim_limits": [
            "Adapter contract presence is not live runtime proof.",
            "Live provider auth, gateway reachability, and service state must be verified separately.",
            "Invocation must not record hidden model chain-of-thought or raw secrets.",
            "External sends, production changes, credentials, and paid work remain owner-gated.",
        ],
    }
    validate_contract(contract)
    return contract


def hermes_contract(
    *,
    agent_slug: str = "ceo-hermes",
    adapter_type: str = "hermes_runtime",
    binary: dict[str, Any] | None = None,
    container_enabled: bool = False,
    hermes_setup_state: str = "unknown",
) -> dict[str, Any]:
    binary = binary or {"found": False, "name": "hermes", "path": None}
    binary_found = binary.get("found") is True
    runtime_available = binary_found or container_enabled
    setup_ready = hermes_setup_state == "operator_confirmed_ready"
    return _base_contract(
        runtime_id="hermes-default",
        adapter_type=adapter_type,
        agent_slug=agent_slug,
        support_state="supported" if runtime_available else "supported_unproven",
        claim=(
            "Hermes is the default supported WEAVE runtime adapter. Current "
            "availability still depends on the binary/container and Hermes setup state."
        ),
        current_probe={
            "binary_found": binary_found,
            "binary_name": binary.get("name"),
            "binary_path_present": bool(binary.get("path")),
            "container_enabled": container_enabled,
            "hermes_setup_state": hermes_setup_state,
            "normal_chat_ready": setup_ready,
        },
        methods={
            "probe": _method(
                implemented=True,
                owner="weave-runtime",
                effect="read-only",
                proof="setup_runtime.find_runtime_binary plus Hermes setup status",
                current_state="available" if runtime_available else "binary_or_container_missing",
            ),
            "invoke": _method(
                implemented=True,
                owner="hermes",
                effect="live-model-call",
                proof="Hermes CLI/gateway invocation path; live proof still requires a separate run",
                current_state="ready" if setup_ready and runtime_available else "requires_hermes_setup_or_runtime",
                requires_live_runtime=True,
                requires_owner_approval=True,
                notes=["Do not treat prompt-pack validation as live Hermes invocation proof."],
            ),
            "capture_turn": _method(
                implemented=True,
                owner="weave-runtime",
                effect="append-only-local-state",
                proof="weave_runtime_slice conversation turn/event ledgers",
                current_state="available",
            ),
            "post_event": _method(
                implemented=True,
                owner="weave-runtime",
                effect="append-only-local-state",
                proof="weave_runtime_slice event ledger",
                current_state="available",
            ),
            "doctor": _method(
                implemented=True,
                owner="weave-runtime",
                effect="read-only",
                proof="setup_runtime --check, weave hermes status, runtime smoke",
                current_state="available",
            ),
        },
    )


def local_fallback_contract(
    *,
    agent_slug: str = "ceo-fallback",
    adapter_type: str = "local_fallback_gateway",
    binary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    binary = binary or {"found": False, "name": "local-fallback", "path": None}
    return _base_contract(
        runtime_id="local-fallback",
        adapter_type=adapter_type,
        agent_slug=agent_slug,
        support_state="fallback_contract_only",
        claim="Local Fallback is a recovery contract, not equivalent to the Hermes default runtime.",
        current_probe={
            "binary_found": binary.get("found") is True,
            "binary_name": binary.get("name"),
            "binary_path_present": bool(binary.get("path")),
        },
        methods={
            "probe": _method(
                implemented=True,
                owner="weave-runtime",
                effect="read-only",
                proof="setup_runtime.find_runtime_binary",
                current_state="available" if binary.get("found") is True else "binary_missing",
            ),
            "invoke": _method(
                implemented=False,
                owner="local-fallback",
                effect="not-implemented",
                proof="no tracked generic fallback invocation adapter exists",
                current_state="unsupported",
            ),
            "capture_turn": _method(
                implemented=True,
                owner="weave-runtime",
                effect="append-only-local-state",
                proof="weave_runtime_slice conversation turn/event ledgers",
                current_state="available",
            ),
            "post_event": _method(
                implemented=True,
                owner="weave-runtime",
                effect="append-only-local-state",
                proof="weave_runtime_slice event ledger",
                current_state="available",
            ),
            "doctor": _method(
                implemented=False,
                owner="weave-runtime",
                effect="not-implemented",
                proof="no local fallback doctor contract exists",
                current_state="unsupported",
            ),
        },
    )


def codex_contract() -> dict[str, Any]:
    return _base_contract(
        runtime_id="codex",
        adapter_type="codex_runtime",
        agent_slug="codex",
        support_state="unsupported",
        claim="Codex is currently profile/provider metadata only, not a WEAVE runtime adapter.",
        unsupported_reason=(
            "No tracked Codex adapter implements probe, invoke, capture_turn, post_event, and doctor."
        ),
        current_probe={
            "binary_found": False,
            "provider_metadata_only": True,
            "live_invocation_path": "missing",
        },
        methods={
            name: _method(
                implemented=False,
                owner="codex",
                effect="not-implemented",
                proof="missing tracked Codex runtime adapter",
                current_state="unsupported",
            )
            for name in REQUIRED_METHODS
        },
    )


def contract_for_runtime(
    runtime_id: str,
    *,
    adapter_type: str = "",
    agent_slug: str = "",
    binary: dict[str, Any] | None = None,
    container_enabled: bool = False,
    hermes_setup_state: str = "unknown",
) -> dict[str, Any]:
    if runtime_id == "hermes-default":
        return hermes_contract(
            agent_slug=agent_slug or "ceo-hermes",
            adapter_type=adapter_type or "hermes_runtime",
            binary=binary,
            container_enabled=container_enabled,
            hermes_setup_state=hermes_setup_state,
        )
    if runtime_id == "local-fallback":
        return local_fallback_contract(
            agent_slug=agent_slug or "ceo-fallback",
            adapter_type=adapter_type or "local_fallback_gateway",
            binary=binary,
        )
    if runtime_id == "codex":
        return codex_contract()
    raise AgentRuntimeContractError(f"unknown runtime adapter contract: {runtime_id}")


def runtime_catalog(current_runtime: str | None = None) -> dict[str, Any]:
    contracts = [
        hermes_contract(),
        local_fallback_contract(),
        codex_contract(),
    ]
    return {
        "schema": CATALOG_SCHEMA,
        "current_runtime": current_runtime or "",
        "required_methods": list(REQUIRED_METHODS),
        "runtimes": {
            contract["runtime_id"]: {
                "adapter_type": contract["adapter_type"],
                "support_state": contract["support_state"],
                "claim": contract["claim"],
                "unsupported_reason": contract["unsupported_reason"],
            }
            for contract in contracts
        },
        "secret_payload_allowed": False,
    }


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise AgentRuntimeContractError(f"schema must be {CONTRACT_SCHEMA}")
    if contract.get("secret_payload_allowed") is not False:
        raise AgentRuntimeContractError("secret payloads must be disabled")
    if _contains_secret_like_value(contract):
        raise AgentRuntimeContractError("runtime contract contains a secret-like value")
    methods = contract.get("methods")
    if not isinstance(methods, dict):
        raise AgentRuntimeContractError("methods must be a mapping")
    missing = [method for method in REQUIRED_METHODS if method not in methods]
    if missing:
        raise AgentRuntimeContractError(f"missing required method(s): {', '.join(missing)}")
    for name in REQUIRED_METHODS:
        method = methods[name]
        if not isinstance(method, dict):
            raise AgentRuntimeContractError(f"method {name} must be a mapping")
        for field in ("implemented", "owner", "effect", "proof", "current_state"):
            if field not in method:
                raise AgentRuntimeContractError(f"method {name} missing {field}")


def validate_catalog(catalog: dict[str, Any]) -> None:
    if catalog.get("schema") != CATALOG_SCHEMA:
        raise AgentRuntimeContractError(f"schema must be {CATALOG_SCHEMA}")
    if catalog.get("secret_payload_allowed") is not False:
        raise AgentRuntimeContractError("secret payloads must be disabled")
    runtimes = catalog.get("runtimes")
    if not isinstance(runtimes, dict):
        raise AgentRuntimeContractError("runtimes must be a mapping")
    for runtime_id in ("hermes-default", "local-fallback", "codex"):
        if runtime_id not in runtimes:
            raise AgentRuntimeContractError(f"catalog missing {runtime_id}")


def redacted_json(value: dict[str, Any]) -> str:
    safe = deepcopy(value)
    if _contains_secret_like_value(safe):
        raise AgentRuntimeContractError("refusing to render secret-like contract data")
    return json.dumps(safe, indent=2, sort_keys=True) + "\n"

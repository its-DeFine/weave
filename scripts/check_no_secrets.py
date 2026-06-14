#!/usr/bin/env python3
"""Scan the repository for secret-like patterns and internal hostnames.

Exits 0 when clean. Exits 1 and prints path:line:matched_pattern for every hit.
False positives are acceptable; false negatives are not.

Usage:
    python3 scripts/check_no_secrets.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# File extensions to scan.
SCAN_EXTENSIONS = {
    ".py", ".md", ".yaml", ".yml", ".json", ".toml", ".env", ".sh",
    ".bash", ".zsh", ".txt", ".cfg", ".ini", ".conf", ".mjs", ".js",
    ".ts", ".tsx", ".jsx",
}

# Filenames to scan regardless of extension.
SCAN_FILENAMES = {".env", ".envrc", "Makefile", "Dockerfile"}

# Directories to skip entirely.
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "runs", "evidence",
    ".workflow",
}

# Secret-like key names (from weave_command_bus.py SECRET_KEY_RE pattern, extended).
SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|secret|token|password|passcode|credential|private[_-]?key"
    r"|seed|2fa|otp|auth[_-]?token|access[_-]?token|bearer|client[_-]?secret"
    r"|webhook[_-]?secret|signing[_-]?key)",
    re.IGNORECASE,
)

# Secret-like values: provider key shapes.
SECRET_VALUE_RE = re.compile(
    r"("
    r"sk-[A-Za-z0-9_-]{20,}"           # OpenAI / Anthropic sk- keys
    r"|sk-ant-[A-Za-z0-9_-]{20,}"      # Anthropic sk-ant-
    r"|sk-or-v1-[A-Za-z0-9_-]{16,}"   # OpenRouter
    r"|sk_live_[A-Za-z0-9]{16,}"       # Stripe live
    r"|sk_test_[A-Za-z0-9]{16,}"       # Stripe test
    r"|gh[pousr]_[A-Za-z0-9_]{20,}"    # GitHub tokens
    r"|glpat-[A-Za-z0-9_-]{20,}"       # GitLab PAT
    r"|xox[baprs]-[A-Za-z0-9-]{12,}"   # Slack tokens
    r"|Bearer\s+[A-Za-z0-9._-]{20,}"   # Bearer tokens
    r"|AIza[A-Za-z0-9_-]{35}"          # Google API keys
    r"|AKIA[A-Z0-9]{16}"               # AWS access key IDs
    r")",
    re.IGNORECASE,
)

# ENV-style assignments: FOO_SECRET=actual_value (not a placeholder).
SECRET_ASSIGNMENT_RE = re.compile(
    r"\b([A-Z0-9_]*(?:API[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSCODE|CREDENTIAL"
    r"|PRIVATE[_-]?KEY|SEED|2FA|OTP)[A-Z0-9_]*)\s*=\s*(?!\$|\{)([\"']?)"
    r"(?!(?:<|your|example|placeholder|xxx|todo|changeme|redacted|true|false|1|0|none|null|empty)\b)"
    r"([^\s\"']{8,})\2",
    re.IGNORECASE,
)

# AWS secret access key (longer value pattern).
AWS_SECRET_RE = re.compile(r"(?i)aws.{0,20}secret.{0,20}=\s*[A-Za-z0-9/+=]{40}")

# Private key material.
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")

# Wallet addresses (ETH-style).
WALLET_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")

# Internal hostnames and user patterns we own. Conservative — flag anything that looks internal.
INTERNAL_HOST_RE = re.compile(
    r"("
    r"weave" + r"-vm\d+"                # internal VM-style hostnames
    r"|agent-ops"                        # agent-ops host
    r"|local-fallback\.[a-z]"                 # local-fallback.internal etc (not local-fallback the product name standalone)
    r"|livepeer-ops"                     # livepeer-ops internal
    r"|100\.\d{1,3}\.\d{1,3}\.\d{1,3}" # private overlay CGNAT range
    r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}" # Private LAN
    r"|192\.168\.\d{1,3}\.\d{1,3}"     # Private LAN
    r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"  # Private LAN
    r"|<PRIVATE_RUNTIME_USER>@[a-z]"                    # private runtime user patterns
    r")",
    re.IGNORECASE,
)

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (SECRET_VALUE_RE, "secret-value"),
    (PRIVATE_KEY_RE, "private-key"),
    (WALLET_RE, "wallet-address"),
    (AWS_SECRET_RE, "aws-secret"),
    (SECRET_ASSIGNMENT_RE, "secret-assignment"),
    (INTERNAL_HOST_RE, "internal-host"),
]


def should_scan(path: Path) -> bool:
    # Skip this script itself to avoid false positives from pattern definitions.
    if path.resolve() == Path(__file__).resolve():
        return False
    return path.suffix in SCAN_EXTENSIONS or path.name in SCAN_FILENAMES


def candidate_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return sorted(path.relative_to(REPO_ROOT) for path in REPO_ROOT.rglob("*") if path.is_file())
    return [Path(line) for line in result.stdout.splitlines() if line]


def scan_file(path: Path) -> list[str]:
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return hits
    for lineno, line in enumerate(text.splitlines(), 1):
        for pattern, label in PATTERNS:
            m = pattern.search(line)
            if not m:
                continue
            if label == "secret-assignment" and path.suffix == ".py":
                lhs = m.group(1)
                # The assignment pattern is for ENV-style keys. Lowercase Python
                # locals such as token_configured/auth_token are not secret
                # material; actual provider-shaped values are still caught by
                # SECRET_VALUE_RE above.
                if lhs != lhs.upper():
                    continue
                if lhs.endswith("_RE") and "re.compile" in line:
                    continue
            hits.append(f"{path}:{lineno}:{label}:{m.group(0)[:60]!r}")
            break  # one hit per line is enough
    return hits


def main() -> int:
    all_hits: list[str] = []
    for relative in candidate_files():
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        path = REPO_ROOT / relative
        if not path.is_file():
            continue
        if not should_scan(path):
            continue
        all_hits.extend(scan_file(path))

    for hit in all_hits:
        print(hit)

    return 1 if all_hits else 0


if __name__ == "__main__":
    raise SystemExit(main())

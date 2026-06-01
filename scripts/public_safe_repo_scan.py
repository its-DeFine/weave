#!/usr/bin/env python3
"""Repo-wide public-safe scan for the public WEAVE repository.

This scan complements ``scripts/check_no_secrets.py`` by catching private
runtime references that are not necessarily credentials: local paths, private
network addresses, private substrate repo references, and host-only runtime
endpoints.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

SCAN_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

ALLOWLIST = {
    ("scripts/weave_runtime_api.py", "loopback-host"),
}

ALLOWLIST_FILES = {
    # These files intentionally contain private-looking strings as scanner or
    # smoke-test fixtures, not as runtime configuration.
    "scripts/context_sync_contract_smoke.py",
    "tests/test_public_safe_repo_scan.py",
}

PRIVATE_DEVICE_NAME = "p" + "c2"
PRIVATE_OVERLAY_VENDOR = "tail" + "scale"
PRIVATE_RUNTIME_HOST_PREFIX = "weave" + "-vm"
PRIVATE_RUNTIME_PLACEHOLDERS = ("<" + "P" + "C2", "<" + "WEAVE" + "_VM")
PRIVATE_ACCESS_TOOL = "machine" + "ctl"
PRIVATE_ROUTE_TERM = "jump" + "-host"

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("local-user-path", re.compile(r"/Users/[A-Za-z0-9_.-]+")),
    ("home-path", re.compile(r"/home/[A-Za-z0-9_.-]+")),
    ("loopback-host", re.compile(r"\b(?:127\.0\.0\.1|localhost|host\.docker\.internal)\b", re.IGNORECASE)),
    ("private-ipv4", re.compile(r"\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168|100\.\d{1,3})\.\d{1,3}\.\d{1,3}\b")),
    ("private-substrate-reference", re.compile(r"\bweave-substrate\b", re.IGNORECASE)),
    ("private-device-name", re.compile(rf"\b{re.escape(PRIVATE_DEVICE_NAME)}\b", re.IGNORECASE)),
    ("private-overlay-vendor", re.compile(re.escape(PRIVATE_OVERLAY_VENDOR), re.IGNORECASE)),
    ("private-runtime-host", re.compile(rf"\b{re.escape(PRIVATE_RUNTIME_HOST_PREFIX)}\d+\b", re.IGNORECASE)),
    ("private-runtime-placeholder", re.compile("|".join(re.escape(item) for item in PRIVATE_RUNTIME_PLACEHOLDERS), re.IGNORECASE)),
    ("private-access-command", re.compile(rf"\b(?:{re.escape(PRIVATE_ACCESS_TOOL)}|ssh\s+-i|scp\s+-r)\b", re.IGNORECASE)),
    ("private-route-term", re.compile(re.escape(PRIVATE_ROUTE_TERM), re.IGNORECASE)),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("credential-like-token", re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|sk-or-v1-[A-Za-z0-9_-]{16,}|sk_live_[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9_]{20,}|Bearer\s+[A-Za-z0-9._-]{20,})\b")),
)


@dataclass(frozen=True)
class ScanHit:
    path: str
    line: int
    label: str
    match: str


def tracked_files() -> list[Path]:
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


def should_scan(path: Path) -> bool:
    if path.as_posix() == "scripts/public_safe_repo_scan.py":
        return False
    return path.suffix in SCAN_EXTENSIONS


def scan_text(text: str, *, path: str) -> list[ScanHit]:
    hits: list[ScanHit] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in PATTERNS:
            if path in ALLOWLIST_FILES or (path, label) in ALLOWLIST:
                continue
            match = pattern.search(line)
            if match:
                hits.append(ScanHit(path=path, line=line_number, label=label, match=match.group(0)))
                break
    return hits


def scan_repo() -> list[ScanHit]:
    hits: list[ScanHit] = []
    for relative in tracked_files():
        if not should_scan(relative):
            continue
        path = REPO_ROOT / relative
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits.extend(scan_text(text, path=relative.as_posix()))
    return hits


def main() -> int:
    hits = scan_repo()
    for hit in hits:
        print(f"{hit.path}:{hit.line}:{hit.label}:{hit.match!r}")
    if hits:
        print(f"public-safe repo scan failed: {len(hits)} finding(s)", file=sys.stderr)
        return 1
    print("public-safe repo scan: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

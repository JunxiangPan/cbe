#!/usr/bin/env python3
"""Verify the CBE self-protection manifest.

The manifest is a plain SHA256SUMS-style file:
    <64-hex>  <repo-relative-path>

`--check` verifies the files. `--write` regenerates the manifest from the
current tree. A mismatch exits 3; it never silently repairs the manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_MANIFEST = "security/SELF_PROTECTION.sha256"
PROTECTED = [
    ".github/workflows/cbe-e2e.yml",
    ".github/workflows/pypi-publish.yml",
    "src/cbe/commands/enforce_no_bypass.py",
    "src/cbe/manifest.py",
    "tools/cbe_contract_guard.py",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_manifest(path: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2 or len(parts[0]) != 64:
            raise ValueError(f"{path}:{line_no}: expected '<sha256>  <path>'")
        digest, relative = parts
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"{path}:{line_no}: unsafe path: {relative}")
        entries.append((digest, relative))
    return entries


def verify(root: Path, manifest: Path) -> dict:
    root = root.resolve()
    entries = _parse_manifest(manifest)
    mismatches = []
    for expected, relative in entries:
        target = root / relative
        if not target.is_file():
            mismatches.append({"path": relative, "expected": expected, "observed": "MISSING"})
            continue
        observed = _sha(target)
        if observed != expected:
            mismatches.append({"path": relative, "expected": expected, "observed": observed})
    return {
        "schema_version": "1",
        "command": "cbe-self-protect",
        "ok": not mismatches,
        "exit_code": 0 if not mismatches else 3,
        "gate_status": "PASS" if not mismatches else "FAIL",
        "manifest": str(manifest),
        "checked": len(entries),
        "mismatches": mismatches,
    }


def write_manifest(root: Path, manifest: Path) -> dict:
    root = root.resolve()
    lines = []
    for relative in PROTECTED:
        target = root / relative
        if not target.is_file():
            raise FileNotFoundError(relative)
        lines.append(f"{_sha(target)}  {relative}")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return {
        "schema_version": "1",
        "command": "cbe-self-protect",
        "ok": True,
        "exit_code": 0,
        "gate_status": "PASS",
        "manifest": str(manifest),
        "protected": PROTECTED,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--write", action="store_true", help="regenerate the manifest")
    parser.add_argument("--check", action="store_true", help="verify (default)")
    args = parser.parse_args(argv)
    root = Path(args.root)
    manifest = Path(args.manifest)
    if args.write:
        result = write_manifest(root, manifest)
    else:
        try:
            result = verify(root, manifest)
        except (OSError, ValueError) as exc:
            result = {
                "schema_version": "1",
                "command": "cbe-self-protect",
                "ok": False,
                "exit_code": 3,
                "gate_status": "FAIL",
                "manifest": str(manifest),
                "checked": 0,
                "mismatches": [{"path": str(manifest), "expected": "valid", "observed": str(exc)}],
            }
    print(json.dumps(result, indent=2))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

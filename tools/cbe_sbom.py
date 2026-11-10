#!/usr/bin/env python3
"""Generate a minimal CycloneDX SBOM for CBE itself."""

from __future__ import annotations

import argparse
import hashlib
import json
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _dep(name: str) -> dict | None:
    try:
        version = metadata.version(name)
    except metadata.PackageNotFoundError:
        return None
    return {
        "type": "library",
        "name": name,
        "version": version,
        "purl": f"pkg:pypi/{name}@{version}",
    }


def build() -> dict:
    component = {
        "type": "application",
        "name": "cbe-review",
        "version": "0.2.0",
        "licenses": [{"license": {"id": "Apache-2.0"}}],
        "purl": "pkg:pypi/cbe-review@0.2.0",
        "hashes": [
            {
                "alg": "SHA-256",
                "content": hashlib.sha256((ROOT / "src/cbe/commands/enforce_no_bypass.py").read_bytes()).hexdigest(),
            }
        ],
    }
    dependencies = [dep for name in ("jsonschema", "pyyaml") if (dep := _dep(name))]
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {"component": component},
        "components": dependencies,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"ok": True, "out": str(target)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

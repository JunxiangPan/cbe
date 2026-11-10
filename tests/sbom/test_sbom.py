"""SBOM shape test."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_sbom_contains_self_and_runtime_dependencies(tmp_path: Path) -> None:
    output = tmp_path / "sbom.json"
    process = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "cbe_sbom.py"), "--out", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["bomFormat"] == "CycloneDX"
    assert data["specVersion"] == "1.5"
    component = data["metadata"]["component"]
    assert component["name"] == "cbe-review"
    assert component["version"] == "0.2.0"
    assert component["licenses"][0]["license"]["id"] == "Apache-2.0"
    names = {item["name"] for item in data["components"]}
    assert {"jsonschema", "pyyaml"}.issubset(names)

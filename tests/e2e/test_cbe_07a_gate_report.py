"""CBE-07a report assembly: warn_count must reach cbe-report and Section B."""

from __future__ import annotations

import json
from pathlib import Path

from _util import fixture, run_script


def test_gate_report_carries_unverifiable_warning(outside_tmp: Path) -> None:
    out = outside_tmp / "gate"
    code, data, _, _ = run_script(
        "tools/cbe_gate.py",
        "--manifest",
        fixture("manifests", "valid_minimal.json"),
        "--package-id",
        "cbe",
        "--package-type",
        "cbe",
        "--package-version",
        "v0.1.0",
        "--tag",
        "v0.1.0",
        "--source-root",
        fixture("bypass", "workflow-dynamic-if-repo"),
        "--out-dir",
        out,
        "--workflows",
    )
    assert code == 0
    assert data is not None
    assert data["warn_count"] == 1
    report = json.loads((out / "cbe-report.json").read_text(encoding="utf-8"))
    assert report["warn_count"] == 1
    assert report["gate_status"] == "PASS"
    body = (out / "cbe-body-section.md").read_text(encoding="utf-8")
    assert "## Section B: AI audit" in body
    assert "warn_count: 1" in body
    assert "UNVERIFIABLE_CONDITION" in body

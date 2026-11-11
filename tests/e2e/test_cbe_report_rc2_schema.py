"""Real CBE report must validate against the contract RC2 CBE schema."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from _util import fixture, run_script
from cbe.paths import schema_path


def test_real_cbe_report_passes_rc2_schema(outside_tmp: Path) -> None:
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
        fixture("bypass", "clean-repo"),
        "--out-dir",
        out,
    )
    assert code == 0
    assert data is not None
    report = json.loads((out / "cbe-report.json").read_text(encoding="utf-8"))
    assert report["schema_version"] == "1"
    assert report["package_id"] == "cbe"
    assert report["producer_id"] == "cbe"
    assert report["gate_status"] == "PASS"

    schema_file = schema_path("v1.7", "cbe-report.schema.json")
    assert hashlib.sha256(schema_file.read_bytes()).hexdigest() == (
        "7824c18c639c9af8fc013739bdc75dba0d6e22c76f0a96ee91a372a581428fe5"
    )
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(report), key=lambda item: list(item.path))
    assert errors == []

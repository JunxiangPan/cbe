"""CBE-02: valid manifests through the CLI."""

from __future__ import annotations

import json
from pathlib import Path

from _util import fixture, run_cbe


def test_valid_full_manifest() -> None:
    code, data, _, _ = run_cbe(
        "validate-manifest",
        "--manifest",
        fixture("manifests", "valid_full.json"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
    )
    assert code == 0
    assert data is not None
    assert data["gate_status"] == "PASS"
    assert data["rule_count"] == 3
    assert data["provider_count"] == 2
    assert data["blocking_rule_count"] == 1
    assert data["blocking_applicable_count"] == 1
    assert data["applicable_rule_count"] == 3


def test_valid_minimal_manifest() -> None:
    code, data, _, _ = run_cbe(
        "validate-manifest",
        "--manifest",
        fixture("manifests", "valid_minimal.json"),
        "--package-type",
        "cbe",
        "--package-version",
        "v0.1.0",
    )
    assert code == 0
    assert data is not None
    assert data["rule_count"] == 1
    assert data["applicable_rule_count"] == 1


def test_lf_and_crlf_hash_are_identical() -> None:
    _, lf, _, _ = run_cbe("validate-manifest", "--manifest", fixture("manifests", "valid_full.json"))
    _, crlf, _, _ = run_cbe("validate-manifest", "--manifest", fixture("manifests", "valid_full_crlf.json"))
    assert lf is not None and crlf is not None
    assert lf["manifest_sha256"] == crlf["manifest_sha256"]


def test_output_writes_the_same_json(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    code, data, _, _ = run_cbe(
        "validate-manifest",
        "--manifest",
        fixture("manifests", "valid_minimal.json"),
        "--output",
        output,
    )
    assert code == 0
    assert data is not None
    assert json.loads(output.read_text(encoding="utf-8")) == data

"""CBF package_type support in CLI, manifest, rule-pack and report schemas."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from cbe.manifest import PACKAGE_TYPES, load_and_inspect

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "e2e" / "fixtures" / "manifests"
REPORT_SCHEMA = ROOT / "src" / "cbe" / "schemas" / "v1.7" / "cbe-report.schema.json"
RULE_SCHEMA = ROOT / "src" / "cbe" / "schemas" / "rule-pack-manifest.v1.schema.json"


def _cbf_manifest(tmp_path: Path) -> Path:
    source = json.loads((FIXTURES / "valid_full.json").read_text(encoding="utf-8"))

    def replace(value):
        if isinstance(value, str):
            return "cbf" if value == "cbs" else value
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        return value

    manifest = replace(copy.deepcopy(source))
    path = tmp_path / "cbf-manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_package_types_include_cbf_and_legacy_values() -> None:
    assert set(PACKAGE_TYPES) >= {"cbs", "cbe", "cbp", "cbm", "cbc", "cbg", "cbf"}


def test_cbf_manifest_is_inspectable_and_applicable(tmp_path: Path) -> None:
    path = _cbf_manifest(tmp_path)
    inspection = load_and_inspect(path, package_type="cbf", package_version="v0.1.0")
    assert inspection.errors == []
    assert inspection.applicable_rules


def test_report_schema_accepts_cbf_package_id() -> None:
    schema = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
    report = {
        "schema_version": "1",
        "package_id": "cbf",
        "producer_id": "cbe",
        "version": "0.3.1",
        "tag": "v0.3.1",
        "gate_status": "PASS",
        "exit_code": 0,
        "applicable_count": 1,
        "skip_count": 0,
        "skip_ratio": 0.0,
        "blocking_skip": False,
        "warn_count": 0,
        "rules_manifest_hash": "a" * 64,
        "sarif_paths": [],
        "evidence_sha256": "b" * 64,
    }
    assert list(Draft202012Validator(schema).iter_errors(report)) == []


def test_rule_pack_schema_accepts_cbf() -> None:
    schema = json.loads(RULE_SCHEMA.read_text(encoding="utf-8"))
    assert "cbf" in schema["properties"]["package_types"]["items"]["enum"]
    assert "cbf" in schema["$defs"]["rule"]["properties"]["package_types"]["items"]["enum"]


def test_cli_accepts_cbf_package_type(tmp_path: Path) -> None:
    path = _cbf_manifest(tmp_path)
    process = subprocess.run(
        [
            sys.executable, "-m", "cbe", "validate-manifest",
            "--manifest", str(path), "--package-type", "cbf",
            "--package-version", "v0.1.0",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stdout + process.stderr

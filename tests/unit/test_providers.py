"""Unit tests for provider execution and result mapping."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from cbe.errors import GateError
from cbe.manifest import load_and_inspect
from cbe.providers import _json_findings, _rule_for_native, _sarif_findings, execute

FIXTURES = Path(__file__).resolve().parents[1] / "e2e" / "fixtures"
ROOT = Path(__file__).resolve().parents[2]


def _inspection(manifest: str, package_type: str, package_version: str = "v0.1.0"):
    inspection = load_and_inspect(
        FIXTURES / "manifests" / manifest,
        package_type=package_type,
        package_version=package_version,
    )
    assert inspection.ruleset is not None
    return inspection


def test_native_id_mapping() -> None:
    ruleset = _inspection("valid_native_ids.json", "cbs").ruleset
    assert ruleset is not None
    assert _rule_for_native(ruleset, "native", "generic-api-key").rule_id == "CBE-SECRET-001"
    assert _rule_for_native(ruleset, "native", "CBE-SECRET-001").rule_id == "CBE-SECRET-001"
    with pytest.raises(Exception):
        _rule_for_native(ruleset, "native", "unknown-rule")


def test_sarif_and_json_findings_are_parsed(tmp_path: Path) -> None:
    ruleset = _inspection("valid_full.json", "cbs").ruleset
    assert ruleset is not None
    sarif = _sarif_findings(FIXTURES / "sarif" / "valid.sarif", ruleset, "gitleaks")
    assert len(sarif) == 1
    assert sarif[0].rule_id == "CBE-SECRET-001"

    provider_json = tmp_path / "provider.json"
    provider_json.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "provider_id": "builtin-manifest",
                "tool": {"name": "fixture"},
                "results": [
                    {
                        "rule_id": "CBE-QUALITY-001",
                        "level": "warning",
                        "message": "fixture",
                        "location": {"path": "src/a.py", "start_line": 1},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    parsed = _json_findings(provider_json, ruleset, "builtin-manifest")
    assert parsed[0].rule_id == "CBE-QUALITY-001"


def test_execute_builtin_provider_passes() -> None:
    inspection = _inspection("valid_minimal.json", "cbe")
    out = Path(tempfile.mkdtemp(prefix="cbe-provider-"))
    try:
        outcome = execute(
            inspection,
            package_type="cbe",
            package_version="v0.1.0",
            source_root=FIXTURES / "bypass" / "clean-repo",
            out_dir=out,
            selected_providers=None,
            all_providers=True,
            exemptions_path=None,
            cli_timeout=None,
            manifest_path=FIXTURES / "manifests" / "valid_minimal.json",
        )
        assert outcome.exit_code == 0
        assert outcome.providers[0].status == "PASS"
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_execute_blocking_exemption_fails() -> None:
    inspection = _inspection("valid_blocking_zero.json", "cbs")
    out = Path(tempfile.mkdtemp(prefix="cbe-provider-"))
    try:
        outcome = execute(
            inspection,
            package_type="cbs",
            package_version="v0.1.0",
            source_root=ROOT,
            out_dir=out,
            selected_providers=None,
            all_providers=True,
            exemptions_path=str(FIXTURES / "exemptions" / "blocking.txt"),
            cli_timeout=None,
            manifest_path=FIXTURES / "manifests" / "valid_blocking_zero.json",
        )
        assert outcome.exit_code == 3
        assert outcome.blocking_skip is True
        assert outcome.error is not None
        assert outcome.error["code"] == "BLOCKING_SKIP"
    finally:
        shutil.rmtree(out, ignore_errors=True)

"""Unit tests for SARIF assembly and rejection paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cbe.errors import GateError
from cbe.manifest import load_and_inspect
from cbe.sarif import build_sarif

FIXTURES = Path(__file__).resolve().parents[1] / "e2e" / "fixtures"


def _ruleset(manifest: str = "valid_full.json"):
    inspection = load_and_inspect(FIXTURES / "manifests" / manifest)
    assert inspection.ruleset is not None
    return inspection.ruleset


def _run_report(path: Path, provider_id: str = "gitleaks", fmt: str = "sarif") -> dict:
    return {
        "providers": [
            {
                "provider_id": provider_id,
                "status": "PASS",
                "sarif_path": str(path) if fmt == "sarif" else None,
                "json_path": str(path) if fmt == "json" else None,
            }
        ],
        "rule_results": [],
    }


def test_valid_sarif_is_merged() -> None:
    ruleset = _ruleset()
    sarif = build_sarif(
        ruleset=ruleset,
        run_report=_run_report(FIXTURES / "sarif" / "valid.sarif"),
        provider_outputs=None,
    )
    assert sarif["version"] == "2.1.0"
    assert len(sarif["runs"]) == 1
    assert sarif["runs"][0]["results"][0]["ruleId"] == "CBE-SECRET-001"


@pytest.mark.parametrize(
    "name,error_code",
    [
        ("cbp_namespace.sarif", "CROSS_NAMESPACE"),
        ("bad_rule_index.sarif", "SARIF_INVALID_RULE_INDEX"),
        ("absolute_path.sarif", "SARIF_INVALID_LOCATION"),
        ("missing_rule.sarif", "RULE_NOT_IN_MANIFEST"),
        ("no_runs.sarif", "SARIF_INVALID"),
    ],
)
def test_invalid_sarif_is_rejected(name: str, error_code: str) -> None:
    ruleset = _ruleset()
    with pytest.raises(GateError) as caught:
        build_sarif(
            ruleset=ruleset,
            run_report=_run_report(FIXTURES / "sarif" / name),
            provider_outputs=None,
        )
    assert caught.value.code == error_code


def test_provider_json_zero_results_is_a_valid_run(tmp_path: Path) -> None:
    provider_json = tmp_path / "provider.json"
    provider_json.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "provider_id": "builtin-manifest",
                "tool": {"name": "fixture"},
                "results": [],
            }
        ),
        encoding="utf-8",
    )
    sarif = build_sarif(
        ruleset=_ruleset("valid_minimal.json"),
        run_report=_run_report(provider_json, "builtin-manifest", "json"),
        provider_outputs=None,
    )
    assert len(sarif["runs"]) == 1
    assert sarif["runs"][0]["results"] == []

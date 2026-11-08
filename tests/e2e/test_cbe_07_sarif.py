"""CBE-07: SARIF assembly/validation and the explicit CBP interop skip."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from _util import ROOT, fixture, run_cbe


def _write_run_report(path: Path, sarif_path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "providers": [
                    {
                        "provider_id": "gitleaks",
                        "status": "PASS",
                        "sarif_path": str(sarif_path),
                        "json_path": None,
                        "artifact_status": "valid",
                    }
                ],
                "rule_results": [],
            }
        ),
        encoding="utf-8",
    )


def test_cbe_sarif_is_emitted_and_valid(outside_tmp: Path) -> None:
    out = outside_tmp / "out"
    out.mkdir()
    code, run_report, _, _ = run_cbe(
        "run-provider",
        "--manifest",
        fixture("manifests", "valid_full.json"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
        "--source-root",
        ROOT,
        "--out-dir",
        out,
        "--all",
    )
    assert code == 3  # blocking finding, but the run report is valid
    assert run_report is not None
    report_path = out / "run.json"
    report_path.write_text(json.dumps(run_report), encoding="utf-8")

    code, data, _, _ = run_cbe(
        "emit-sarif",
        "--manifest",
        fixture("manifests", "valid_full.json"),
        "--run-report",
        report_path,
        "--source-root",
        ROOT,
        "--out",
        out / "merged.sarif",
    )
    assert code == 0
    assert data is not None
    assert data["run_count"] == 2
    assert data["result_count"] == 1
    sarif = json.loads((out / "merged.sarif").read_text(encoding="utf-8"))
    assert sarif["version"] == "2.1.0"
    assert all(
        result["ruleId"].startswith("CBE-")
        for run in sarif["runs"]
        for result in run["results"]
    )


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
def test_invalid_provider_sarif_is_rejected(tmp_path: Path, name: str, error_code: str) -> None:
    run_report = tmp_path / f"run-{name}.json"
    _write_run_report(run_report, fixture("sarif", name))
    code, data, _, _ = run_cbe(
        "emit-sarif",
        "--manifest",
        fixture("manifests", "valid_full.json"),
        "--run-report",
        run_report,
        "--source-root",
        ROOT,
        "--out",
        tmp_path / "merged.sarif",
    )
    assert code == 3
    assert data is not None
    assert data["error"]["code"] == error_code


def test_cbe_07b_is_an_explicit_counted_skip() -> None:
    marker = json.loads(fixture("sarif", "cbp-consumer-skip.json").read_text(encoding="utf-8"))
    assert marker["check_id"] == "CBE-07b"
    assert marker["status"] == "SKIP"
    assert marker["skip_reason"] == "CBP_REPORT_AGGREGATOR_NOT_FIXED"
    assert marker["blocking"] is False
    assert marker["applicable"] is True
    assert marker["counted_in_skip_denominator"] is True

"""CBE-07b: CBP 1.1.0+ consumes CBE SARIF with namespace isolation."""

from __future__ import annotations

import json
from pathlib import Path

from _util import ROOT, fixture, run_cbe, run_cbp_consumer


def test_cbp_consumes_cbe_sarif_without_leaking_cbe_namespace(outside_tmp: Path) -> None:
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
    assert code == 3  # blocking finding; the run report/SARIF are still valid
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
        out / "cbe.sarif",
    )
    assert code == 0
    assert data is not None
    assert data["namespaces"] == ["CBE"]

    findings = run_cbp_consumer(out, "cbe.sarif")
    assert len(findings) == 1
    finding = findings[0]
    assert finding["rule"] == "CBP-EXT-SECRET-001"
    assert finding["rule"].startswith("CBP-")
    assert not finding["rule"].startswith("CBE-")
    assert finding["origin_rule"] == "CBE-SECRET-001"
    assert finding["tool"] == "CBE/gitleaks"

    expected = json.loads(fixture("sarif", "cbp-consumer-expected.json").read_text(encoding="utf-8"))
    assert expected["cbp_version_min"] == "1.1.0"
    assert expected["expected_cbp_rule"] == finding["rule"]
    assert expected["expected_origin_rule"] == finding["origin_rule"]

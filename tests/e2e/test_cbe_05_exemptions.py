"""CBE-05: exemption semantics through run-provider and no-bypass."""

from __future__ import annotations

from pathlib import Path

from _util import ROOT, fixture, run_cbe


def test_run_provider_counts_advisory_exemption(outside_tmp: Path) -> None:
    out = outside_tmp / "out"
    code, data, _, _ = run_cbe(
        "run-provider",
        "--manifest",
        fixture("manifests", "five_advisory.json"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--out-dir",
        out,
        "--all",
        "--exemptions",
        fixture("exemptions", "valid.txt"),
    )
    assert code == 0
    assert data is not None
    assert data["applicable_count"] == 5
    assert data["skip_count"] == 1
    assert data["skip_ratio"] == 0.2
    assert data["blocking_skip"] is False
    skipped = [item for item in data["rule_results"] if item["status"] == "SKIPPED"]
    assert [item["rule_id"] for item in skipped] == ["CBE-QUALITY-001"]


def test_run_provider_blocking_exemption_is_gate_failure(outside_tmp: Path) -> None:
    out = outside_tmp / "out"
    code, data, _, _ = run_cbe(
        "run-provider",
        "--manifest",
        fixture("manifests", "valid_blocking_zero.json"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
        "--source-root",
        ROOT,
        "--out-dir",
        out,
        "--all",
        "--exemptions",
        fixture("exemptions", "blocking.txt"),
    )
    assert code == 3
    assert data is not None
    assert data["blocking_skip"] is True
    assert data["error"]["code"] == "BLOCKING_SKIP"


def test_run_provider_unknown_exemption_is_input_error(outside_tmp: Path) -> None:
    out = outside_tmp / "out"
    code, data, _, _ = run_cbe(
        "run-provider",
        "--manifest",
        fixture("manifests", "valid_minimal.json"),
        "--package-type",
        "cbe",
        "--package-version",
        "v0.1.0",
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--out-dir",
        out,
        "--all",
        "--exemptions",
        fixture("exemptions", "unknown_rule.txt"),
    )
    assert code == 2
    assert data is not None
    assert data["error"]["code"] == "EXEMPTIONS_INVALID"

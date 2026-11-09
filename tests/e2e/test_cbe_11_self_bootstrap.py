"""CBE-11: self-bootstrap harness (baseline CBE against current manifest)."""

from __future__ import annotations

import sys
from pathlib import Path

from _util import fixture, run_script


def test_current_cbe_can_self_check(outside_tmp: Path) -> None:
    code, data, _, _ = run_script(
        "tools/cbe_selfcheck.py",
        "--baseline-python",
        sys.executable,
        "--manifest",
        fixture("manifests", "valid_minimal.json"),
        "--package-type",
        "cbe",
        "--package-version",
        "v0.1.0",
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--out-dir",
        outside_tmp / "selfcheck",
        "--bootstrap",
        "--baseline-label",
        "installed-cbe",
    )
    assert code == 0
    assert data is not None
    assert data["gate_status"] == "PASS"
    assert data["baseline"]["bootstrap"] is True
    assert [item["step"] for item in data["steps"]] == ["validate-manifest", "run-provider"]


def test_missing_baseline_is_precondition_fail(outside_tmp: Path) -> None:
    code, data, _, _ = run_script(
        "tools/cbe_selfcheck.py",
        "--baseline-python",
        outside_tmp / "does-not-exist",
        "--manifest",
        fixture("manifests", "valid_minimal.json"),
        "--package-type",
        "cbe",
        "--package-version",
        "v0.1.0",
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--out-dir",
        outside_tmp / "selfcheck",
    )
    assert code == 3
    assert data is not None
    assert data["gate_status"] == "PRECONDITION_FAIL"
    assert data["error"]["code"] == "BASELINE_UNAVAILABLE"


def test_baseline_failure_is_selfcheck_failure(outside_tmp: Path) -> None:
    code, data, _, _ = run_script(
        "tools/cbe_selfcheck.py",
        "--baseline-python",
        sys.executable,
        "--manifest",
        fixture("manifests", "invalid_missing_rule_id.json"),
        "--package-type",
        "cbe",
        "--package-version",
        "v0.1.0",
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--out-dir",
        outside_tmp / "selfcheck",
    )
    assert code == 3
    assert data is not None
    assert data["gate_status"] == "FAIL"

"""CBE-06: provider execution, empty artifacts, zero findings, native IDs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from _util import ROOT, fixture, run_cbe

PROVIDERS = ROOT / "tests" / "e2e" / "fixtures" / "providers"


def _manifest_with_provider(tmp_path: Path, script: str, *, timeout: int = 300) -> Path:
    base = json.loads(fixture("manifests", "valid_zero_findings.json").read_text(encoding="utf-8"))
    base["providers"]["ok"]["command"] = [
        "python",
        f"tests/e2e/fixtures/providers/{script}",
        "{out}/ok.sarif",
    ]
    base["providers"]["ok"]["timeout_seconds"] = timeout
    path = tmp_path / f"manifest-{script}.json"
    path.write_text(json.dumps(base), encoding="utf-8")
    return path


def test_zero_findings_sarif_is_pass(outside_tmp: Path) -> None:
    out = outside_tmp / "out"
    code, data, _, _ = run_cbe(
        "run-provider",
        "--manifest",
        fixture("manifests", "valid_zero_findings.json"),
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
    assert code == 0
    assert data is not None
    assert data["providers"][0]["status"] == "PASS"
    assert data["providers"][0]["result_count"] == 0
    assert data["sarif_paths"]


@pytest.mark.parametrize(
    "script,artifact_status",
    [
        ("empty.py", "invalid"),
        ("missing.py", "missing"),
        ("invalid_sarif.py", "invalid"),
    ],
)
def test_bad_provider_artifact_is_gate_failure(
    outside_tmp: Path, script: str, artifact_status: str
) -> None:
    out = outside_tmp / "out"
    code, data, _, _ = run_cbe(
        "run-provider",
        "--manifest",
        _manifest_with_provider(outside_tmp, script),
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
    assert code == 3
    assert data is not None
    assert data["providers"][0]["status"] == "FAIL"
    assert data["providers"][0]["artifact_status"] == artifact_status


def test_provider_timeout_is_infra(outside_tmp: Path) -> None:
    out = outside_tmp / "out"
    code, data, _, _ = run_cbe(
        "run-provider",
        "--manifest",
        _manifest_with_provider(outside_tmp, "timeout.py", timeout=1),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
        "--source-root",
        ROOT,
        "--out-dir",
        out,
        "--all",
        "--timeout",
        "1",
    )
    assert code == 3
    assert data is not None
    assert data["gate_status"] == "SKIPPED_INFRA"
    assert data["providers"][0]["infra"] is True


def test_provider_crash_is_gate_failure(outside_tmp: Path) -> None:
    out = outside_tmp / "out"
    code, data, _, _ = run_cbe(
        "run-provider",
        "--manifest",
        _manifest_with_provider(outside_tmp, "crash.py"),
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
    assert code == 3
    assert data is not None
    assert data["gate_status"] == "FAIL"
    assert data["providers"][0]["status"] == "FAIL"


def test_native_provider_id_is_mapped_to_cbe_rule(outside_tmp: Path) -> None:
    out = outside_tmp / "out"
    code, data, _, _ = run_cbe(
        "run-provider",
        "--manifest",
        fixture("manifests", "valid_native_ids.json"),
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
    assert code == 3
    assert data is not None
    assert data["providers"][0]["result_count"] == 1
    assert data["rule_results"][0]["rule_id"] == "CBE-SECRET-001"
    assert data["rule_results"][0]["status"] == "FAIL"

"""0.3.0 multi-gate support and optional CBP report evidence."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/e2e/fixtures/manifests/valid_full.json"


def _write_workflow(root: Path, text: str) -> None:
    path = root / ".github" / "workflows" / "ci.yml"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _run(root: Path, *extra: str) -> tuple[int, dict]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    process = subprocess.run(
        [
            sys.executable, "-m", "cbe", "enforce-no-bypass",
            "--manifest", str(MANIFEST),
            "--source-root", str(root),
            "--package-type", "cbs",
            "--package-version", "v0.1.0",
            "--workflows",
            *extra,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        return process.returncode, json.loads(process.stdout)
    except json.JSONDecodeError:
        return process.returncode, {"raw": process.stdout, "stderr": process.stderr}


BASE = """name: multi
on: [push]
jobs:
  cbp-gate:
    runs-on: ubuntu-latest
    steps:
      - run: echo cbp
  mutation-gate:
    runs-on: ubuntu-latest
    steps:
      - run: echo mutation
  ai-gate:
    runs-on: ubuntu-latest
    steps:
      - run: echo ai
"""


def _multi_root(tmp_path: Path) -> Path:
    _write_workflow(tmp_path, BASE)
    return tmp_path


def test_multi_gate_positive(tmp_path: Path) -> None:
    code, data = _run(_multi_root(tmp_path), "--gate-jobs", "cbp-gate", "mutation-gate", "ai-gate")
    assert code == 0, data
    assert data["gate_jobs"] == ["cbp-gate", "mutation-gate", "ai-gate"]
    assert not [w for w in data["warnings"] if w["code"] == "GATE_JOB_NOT_FOUND"]


def test_multi_gate_missing_gate_strict_fails(tmp_path: Path) -> None:
    _write_workflow(tmp_path, BASE.replace("""  ai-gate:
    runs-on: ubuntu-latest
    steps:
      - run: echo ai
""", ""))
    code, data = _run(tmp_path, "--gate-jobs", "cbp-gate", "mutation-gate", "ai-gate", "--strict")
    assert code == 3, data
    assert any(w["code"] == "GATE_JOB_NOT_FOUND" and "ai-gate" in w["message"] for w in data["warnings"])


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("""  ai-gate:
    if: false
    runs-on: ubuntu-latest
    steps:
      - run: echo ai
""", "WORKFLOW_SKIPS_CBE_GATE"),
        ("""  # ai-gate: disabled
  ai-gate:
    runs-on: ubuntu-latest
    steps:
      - run: echo ai
""", "WORKFLOW_SKIPS_CBE_GATE"),
        ("""  ai-gate:
    needs: missing-job
    runs-on: ubuntu-latest
    steps:
      - run: echo ai
""", "WORKFLOW_SKIPS_CBE_GATE"),
        ("""  ai-gate:
    runs-on: ubuntu-latest
    steps:
      - run: echo ai
        continue-on-error: true
""", ""),
    ],
)
def test_each_gate_bypass_is_detected(tmp_path: Path, mutation: str, reason: str) -> None:
    text = BASE.replace("""  ai-gate:
    runs-on: ubuntu-latest
    steps:
      - run: echo ai
""", mutation)
    _write_workflow(tmp_path, text)
    code, data = _run(tmp_path, "--gate-jobs", "cbp-gate", "mutation-gate", "ai-gate", "--strict")
    assert code == 3, data
    assert data["bypass_attempts"], data
    if reason:
        assert any(item["reason"] == reason for item in data["bypass_attempts"])


def test_local_reusable_empty_gate_is_detected(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "name: empty-shell\non: [push]\njobs:\n  cbp-gate:\n    uses: ./.github/workflows/empty.yml\n",
        encoding="utf-8",
    )
    (workflows / "empty.yml").write_text(
        "name: empty\non: [workflow_call]\njobs: {}\n", encoding="utf-8"
    )
    code, data = _run(tmp_path, "--gate-jobs", "cbp-gate")
    assert code == 3, data
    assert any(item["reason"] == "LOCAL_REUSABLE_GATE_EMPTY" for item in data["bypass_attempts"])


def test_optional_cbp_report_records_manifest_hash(tmp_path: Path) -> None:
    root = _multi_root(tmp_path)
    report = tmp_path / "cbp-report.json"
    report.write_text(
        json.dumps({"schema_version": "1", "manifest_sha256": "a" * 64}), encoding="utf-8"
    )
    code, data = _run(
        root, "--gate-jobs", "cbp-gate", "mutation-gate", "ai-gate",
        "--cbp-report", str(report),
    )
    assert code == 0, data
    assert data["cbp_report"]["manifest_sha256"] == "a" * 64
    assert data["cbp_report"]["sha256"]


def test_absent_cbp_report_changes_nothing(tmp_path: Path) -> None:
    code, data = _run(_multi_root(tmp_path), "--gate-jobs", "cbp-gate", "mutation-gate", "ai-gate")
    assert code == 0, data
    assert "cbp_report" not in data


def test_gates_can_live_in_separate_workflows(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    for name in ("cbp-gate", "mutation-gate", "ai-gate"):
        (workflows / f"{name}.yml").write_text(
            f"name: {name}\non: [push]\njobs:\n  {name}:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo ok\n",
            encoding="utf-8",
        )
    code, data = _run(tmp_path, "--gate-jobs", "cbp-gate", "mutation-gate", "ai-gate")
    assert code == 0, data
    assert data["gate_jobs"] == ["cbp-gate", "mutation-gate", "ai-gate"]


def test_default_gate_job_output_is_unchanged(tmp_path: Path) -> None:
    code, data = _run(_multi_root(tmp_path), "--gate-job", "^cbe[-_]gate$")
    assert code == 0, data
    assert data["gate_job"] == "^cbe[-_]gate$"
    assert "gate_jobs" not in data


def test_cbp_report_artifact_hashes_fallback(tmp_path: Path) -> None:
    root = _multi_root(tmp_path)
    report = tmp_path / "cbp-report.json"
    report.write_text(
        json.dumps({"artifact_hashes": {"quality-manifest.json": "b" * 64}}),
        encoding="utf-8",
    )
    code, data = _run(
        root, "--gate-jobs", "cbp-gate", "mutation-gate", "ai-gate",
        "--cbp-report", str(report),
    )
    assert code == 0, data
    assert data["cbp_report"]["manifest_sha256"] == "b" * 64
    assert data["cbp_report"]["manifest_sha256_source"] == "artifact_hashes.quality-manifest.json"


def test_cbp_report_missing_file_is_input_error(tmp_path: Path) -> None:
    code, data = _run(
        _multi_root(tmp_path), "--gate-jobs", "cbp-gate", "mutation-gate", "ai-gate",
        "--cbp-report", str(tmp_path / "missing.json"),
    )
    assert code == 2, data
    assert data["error"]["code"] == "CBP_REPORT_NOT_FOUND"


def test_no_cbp_import_in_enforce_module() -> None:
    text = (ROOT / "src/cbe/commands/enforce_no_bypass.py").read_text(encoding="utf-8")
    assert "import cbp" not in text
    assert "from cbp" not in text


def test_cbf_privacy_gate_is_checked_as_opaque_job(tmp_path: Path) -> None:
    text = BASE + """  cbf-privacy-gate:
    runs-on: ubuntu-latest
    steps:
      - run: echo cbf
"""
    _write_workflow(tmp_path, text)
    code, data = _run(
        tmp_path,
        "--gate-jobs", "cbp-gate", "mutation-gate", "ai-gate", "cbf-privacy-gate",
    )
    assert code == 0, data
    assert "cbf-privacy-gate" in data["gate_jobs"]
    # CBE does not inspect CBF policy or evidence semantics.
    assert not any(item["kind"] == "cbf" for item in data["bypass_attempts"])


def test_cbf_privacy_gate_skip_is_detected(tmp_path: Path) -> None:
    text = BASE + """  cbf-privacy-gate:
    if: false
    runs-on: ubuntu-latest
    steps:
      - run: echo cbf
"""
    _write_workflow(tmp_path, text)
    code, data = _run(
        tmp_path,
        "--gate-jobs", "cbp-gate", "mutation-gate", "ai-gate", "cbf-privacy-gate",
    )
    assert code == 3, data
    assert any(
        item["reason"] == "WORKFLOW_SKIPS_CBE_GATE"
        and "cbf-privacy-gate" in item["evidence"]
        for item in data["bypass_attempts"]
    )


def test_cbf_privacy_gate_single_gate_job_is_supported(tmp_path: Path) -> None:
    text = BASE + """  cbf-privacy-gate:
    runs-on: ubuntu-latest
    steps:
      - run: echo cbf
"""
    _write_workflow(tmp_path, text)
    code, data = _run(tmp_path, "--gate-job", "^cbf-privacy-gate$")
    assert code == 0, data
    assert data["gate_job"] == "^cbf-privacy-gate$"


def test_single_cbf_gate_job_skip_is_detected(tmp_path: Path) -> None:
    text = BASE + """  cbf-privacy-gate:
    if: false
    runs-on: ubuntu-latest
    steps:
      - run: echo cbf
"""
    _write_workflow(tmp_path, text)
    code, data = _run(tmp_path, "--gate-job", "^cbf-privacy-gate$")
    assert code == 3, data
    assert any(
        item["reason"] == "WORKFLOW_SKIPS_CBE_GATE" and "cbf-privacy-gate" in item["evidence"]
        for item in data["bypass_attempts"]
    )


def test_cbe_source_does_not_import_cbf() -> None:
    for path in (ROOT / "src" / "cbe").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import cbf" not in text
        assert "from cbf" not in text

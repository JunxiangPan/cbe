"""Contract red-line tests: frozen fields and 20% skip behavior."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from cbe.cbp_compat import validate_cbp_manifest
from cbe.errors import EXIT_GATE, EXIT_INPUT, EXIT_PASS, EXIT_SKIP

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "e2e" / "fixtures"
SCHEMA = ROOT / "src" / "cbe" / "schemas" / "v1.7" / "cbe-report.schema.json"
SCHEMA_SHA = "7824c18c639c9af8fc013739bdc75dba0d6e22c76f0a96ee91a372a581428fe5"


def test_frozen_exit_codes() -> None:
    assert (EXIT_PASS, EXIT_INPUT, EXIT_GATE, EXIT_SKIP) == (0, 2, 3, 4)


def test_report_schema_is_frozen_and_sidecar_is_separate() -> None:
    assert hashlib.sha256(SCHEMA.read_bytes()).hexdigest() == SCHEMA_SHA
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["schema_version"]["const"] == "1"
    assert schema["properties"]["gate_status"]["enum"] == [
        "PASS",
        "FAIL",
        "SKIPPED_INFRA",
        "PRECONDITION_FAIL",
        "NOT_UPLOADED",
    ]
    assert schema["properties"]["exit_code"]["enum"] == [0, 2, 3, 4]
    assert schema["additionalProperties"] is False
    assert "signature" not in schema["properties"]
    assert "attestation" not in schema["properties"]


def test_artifact_repository_object_is_required() -> None:
    base = json.loads((FIXTURES / "release-train" / "cbp-quality-manifest-v12.json").read_text())
    assert validate_cbp_manifest(base) == []
    string_repo = dict(base)
    string_repo["artifact_repository"] = "JunxiangPan/cbp-action"
    assert any("artifact_repository" in item for item in validate_cbp_manifest(string_repo))
    bad_scope = dict(base)
    bad_scope["body_hash_scope"] = "full"
    assert any("body_hash_scope" in item for item in validate_cbp_manifest(bad_scope))
    bad_hash = dict(base)
    bad_hash["release_body_hash"] = "sha256:" + "a" * 64
    assert any("release_body_hash" in item for item in validate_cbp_manifest(bad_hash))


def test_twenty_percent_skip_ratio_is_unchanged() -> None:
    base = [
        sys.executable,
        "-m",
        "cbe",
        "enforce-no-bypass",
        "--manifest",
        str(FIXTURES / "manifests" / "five_advisory.json"),
        "--source-root",
        str(FIXTURES / "bypass" / "clean-repo"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    one = subprocess.run(
        [*base, "--exemptions", str(FIXTURES / "exemptions" / "valid.txt")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=False,
    )
    assert one.returncode == 0
    two = subprocess.run(
        [*base, "--exemptions", str(FIXTURES / "exemptions" / "two_valid.txt")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=False,
    )
    assert two.returncode == 4

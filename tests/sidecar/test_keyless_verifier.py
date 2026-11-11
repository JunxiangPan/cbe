"""Keyless verification must fail closed when a bundle/cosign is missing."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import cbe_verify_sidecar as verifier  # noqa: E402


def _report() -> dict:
    return {
        "schema_version": "1",
        "package_id": "cbe",
        "producer_id": "cbe",
        "version": "0.2.0",
        "tag": "v0.2.0",
        "gate_status": "PASS",
        "exit_code": 0,
        "applicable_count": 10,
        "skip_count": 0,
        "skip_ratio": 0.0,
        "blocking_skip": False,
        "warn_count": 0,
        "rules_manifest_hash": "a" * 64,
        "sarif_paths": [],
        "evidence_sha256": "b" * 64,
    }


def _fixtures(tmp_path: Path) -> tuple[list[Path], Path]:
    wheel = tmp_path / "cbe_review-0.2.0-py3-none-any.whl"
    wheel.write_bytes(b"wheel")
    sdist = tmp_path / "cbe_review-0.2.0.tar.gz"
    sdist.write_bytes(b"sdist")
    report = tmp_path / "cbe-report.json"
    report.write_text(json.dumps(_report()), encoding="utf-8")
    manifest = tmp_path / "release-manifest.json"
    manifest.write_text(
        json.dumps({"artifacts": [
            {"name": wheel.name, "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()},
            {"name": sdist.name, "sha256": hashlib.sha256(sdist.read_bytes()).hexdigest()},
        ]}),
        encoding="utf-8",
    )
    attestation = tmp_path / "attestation.json"
    attestation.write_text('{"_type":"https://in-toto.io/Statement/v1","subject":[]}', encoding="utf-8")
    bundles = tmp_path / "bundles"
    bundles.mkdir()
    for file in (wheel, sdist, report, manifest, attestation):
        (bundles / f"{file.name}.bundle").write_text("bundle", encoding="utf-8")
    return [wheel, sdist, report, manifest, attestation], bundles


def _runner(returncode: int = 0):
    def run(cmd, **kwargs):
        run.cmd = cmd
        return SimpleNamespace(returncode=returncode, stdout="Verified OK", stderr="")
    return run


def test_keyless_requires_bundle_dir(tmp_path: Path) -> None:
    files, _ = _fixtures(tmp_path)
    result = verifier.verify_keyless(files, None, cosign="cosign", certificate_identity="x")
    assert result["exit_code"] == 4
    assert result["gate_status"] == "NOT_UPLOADED"
    assert result["error"]["code"] == "NO_BUNDLE_DIR"


def test_keyless_missing_bundle_is_blocked(tmp_path: Path) -> None:
    files, bundles = _fixtures(tmp_path)
    (bundles / f"{files[0].name}.bundle").unlink()
    result = verifier.verify_keyless(files, bundles, cosign=sys.executable, certificate_identity="x")
    assert result["exit_code"] == 4
    assert result["error"]["code"] == "BUNDLE_MISSING"


def test_keyless_missing_cosign_is_blocked(tmp_path: Path) -> None:
    files, bundles = _fixtures(tmp_path)
    result = verifier.verify_keyless(files, bundles, cosign="definitely-not-a-cosign", certificate_identity="x")
    assert result["exit_code"] == 4
    assert result["error"]["code"] == "COSIGN_UNAVAILABLE"


def test_keyless_verifies_every_bundle(tmp_path: Path) -> None:
    files, bundles = _fixtures(tmp_path)
    runner = _runner(0)
    result = verifier.verify_keyless(files, bundles, cosign=sys.executable, certificate_identity="x", runner=runner)
    assert result["exit_code"] == 0
    assert result["mode"] == "sigstore-keyless"
    assert len(result["files"]) == len(files)


def test_keyless_invalid_signature_fails(tmp_path: Path) -> None:
    files, bundles = _fixtures(tmp_path)
    result = verifier.verify_keyless(files, bundles, cosign=sys.executable, certificate_identity="x", runner=_runner(1))
    assert result["exit_code"] == 3
    assert result["error"]["code"] == "SIGNATURE_INVALID"

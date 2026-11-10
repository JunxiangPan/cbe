"""Offline sidecar signing/verification tests (ephemeral keys only)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

cryptography = pytest.importorskip("cryptography")
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[2]
SIGN = ROOT / "tools" / "cbe_sign_sidecar.py"
VERIFY = ROOT / "tools" / "cbe_verify_sidecar.py"


def _keypair(tmp_path: Path, stem: str = "key") -> tuple[Path, Path]:
    key = Ed25519PrivateKey.generate()
    private = tmp_path / f"{stem}-private.pem"
    public = tmp_path / f"{stem}-public.pem"
    private.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    public.write_bytes(
        key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return private, public


def _fixtures(tmp_path: Path) -> tuple[Path, Path, Path]:
    manifest = tmp_path / "manifest.json"
    report = tmp_path / "report.json"
    manifest.write_text('{"schema_version":"1","pack_id":"cbe-core"}\n', encoding="utf-8")
    report.write_text('{"schema_version":"1","gate_status":"PASS","exit_code":0}\n', encoding="utf-8")
    m = hashlib.sha256(manifest.read_bytes()).hexdigest()
    r = hashlib.sha256(report.read_bytes()).hexdigest()
    attestation = tmp_path / "attestation.json"
    attestation.write_text(
        json.dumps(
            {
                "_type": "https://in-toto.io/Statement/v1",
                "subject": [
                    {"name": "manifest.json", "digest": {"sha256": m}},
                    {"name": "report.json", "digest": {"sha256": r}},
                ],
                "predicateType": "https://github.com/JunxiangPan/cbe/attestation/release/v1",
                "predicate": {"schema_version": "1", "gate_status": "PASS", "exit_code": 0, "report_sha256": r},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest, report, attestation


def _run(script: Path, *args: str) -> tuple[int, dict]:
    process = subprocess.run(
        [sys.executable, str(script), *args],
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


def test_sidecar_sign_and_verify(tmp_path: Path) -> None:
    manifest, report, attestation = _fixtures(tmp_path)
    private, public = _keypair(tmp_path)
    signature = tmp_path / "manifest.sig"
    code, data = _run(
        SIGN,
        "--manifest",
        str(manifest),
        "--report",
        str(report),
        "--attestation",
        str(attestation),
        "--private-key",
        str(private),
        "--keyid",
        "ephemeral-test",
        "--version",
        "v0.2.0",
        "--out",
        str(signature),
    )
    assert code == 0, data
    code, data = _run(
        VERIFY,
        "--manifest",
        str(manifest),
        "--report",
        str(report),
        "--signature",
        str(signature),
        "--attestation",
        str(attestation),
        "--public-key",
        str(public),
    )
    assert code == 0, data
    assert data["ok"] is True
    assert data["keyid"] == "ephemeral-test"


def test_sidecar_detects_report_tamper(tmp_path: Path) -> None:
    manifest, report, attestation = _fixtures(tmp_path)
    private, public = _keypair(tmp_path)
    signature = tmp_path / "manifest.sig"
    assert _run(
        SIGN,
        "--manifest",
        str(manifest),
        "--report",
        str(report),
        "--attestation",
        str(attestation),
        "--private-key",
        str(private),
        "--keyid",
        "ephemeral-test",
        "--version",
        "v0.2.0",
        "--out",
        str(signature),
    )[0] == 0
    report.write_text('{"tampered":true}\n', encoding="utf-8")
    code, data = _run(
        VERIFY,
        "--manifest",
        str(manifest),
        "--report",
        str(report),
        "--signature",
        str(signature),
        "--attestation",
        str(attestation),
        "--public-key",
        str(public),
    )
    assert code == 3
    assert data["error"]["code"] == "REPORT_DIGEST_MISMATCH"


def test_sidecar_detects_wrong_public_key(tmp_path: Path) -> None:
    manifest, report, attestation = _fixtures(tmp_path)
    private, _public = _keypair(tmp_path, "signer")
    _other_private, other_public = _keypair(tmp_path, "other")
    signature = tmp_path / "manifest.sig"
    assert _run(
        SIGN,
        "--manifest",
        str(manifest),
        "--report",
        str(report),
        "--attestation",
        str(attestation),
        "--private-key",
        str(private),
        "--keyid",
        "ephemeral-test",
        "--version",
        "v0.2.0",
        "--out",
        str(signature),
    )[0] == 0
    code, data = _run(
        VERIFY,
        "--manifest",
        str(manifest),
        "--report",
        str(report),
        "--signature",
        str(signature),
        "--attestation",
        str(attestation),
        "--public-key",
        str(other_public),
    )
    assert code == 3
    assert data["error"]["code"] == "SIGNATURE_INVALID"

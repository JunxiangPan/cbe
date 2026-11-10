#!/usr/bin/env python3
"""Offline verifier for CBE manifest/report signatures and attestations.

Reads only the manifest, report, sidecar signature, attestation, and public
key. It does not fetch, execute, or trust the CBE producer.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:  # pragma: no cover - environment dependent
    InvalidSignature = Exception  # type: ignore[assignment,misc]
    serialization = None  # type: ignore[assignment]
    Ed25519PublicKey = None  # type: ignore[assignment,misc]

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "sidecar"
SIGNATURE_SCHEMA = SCHEMAS / "manifest-signature.v1.schema.json"
ATTESTATION_SCHEMA = SCHEMAS / "attestation.v1.schema.json"
SIGNED_FIELDS = [
    "schema_version",
    "alg",
    "keyid",
    "subject",
    "manifest_sha256",
    "report_sha256",
    "attestation_sha256",
]


def _fail(code: str, message: str, details: list[Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "command": "cbe-verify-sidecar",
        "ok": False,
        "exit_code": 3,
        "gate_status": "FAIL",
        "error": {"code": code, "message": message, "details": details or []},
    }


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def verify(
    manifest_path: Path,
    report_path: Path,
    signature_path: Path,
    attestation_path: Path,
    public_key_path: Path,
) -> dict[str, Any]:
    if Ed25519PublicKey is None or serialization is None:
        return _fail("VERIFIER_UNAVAILABLE", "cryptography is required: pip install cbe-review[sign]")
    try:
        signature = _load(signature_path)
        attestation = _load(attestation_path)
        signature_schema = _load(SIGNATURE_SCHEMA)
        attestation_schema = _load(ATTESTATION_SCHEMA)
    except (OSError, json.JSONDecodeError) as exc:
        return _fail("SIDECAR_UNREADABLE", str(exc))
    for schema, document, label in (
        (signature_schema, signature, "manifest.sig"),
        (attestation_schema, attestation, "attestation.json"),
    ):
        errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda e: list(e.path))
        if errors:
            return _fail("SIDECAR_SCHEMA_INVALID", f"{label}: {errors[0].message}")
    manifest_sha = _sha(manifest_path)
    report_sha = _sha(report_path)
    attestation_sha = _sha(attestation_path)
    if signature["manifest_sha256"] != manifest_sha:
        return _fail("MANIFEST_DIGEST_MISMATCH", "manifest sha256 does not match manifest.sig")
    if signature["report_sha256"] != report_sha:
        return _fail("REPORT_DIGEST_MISMATCH", "report sha256 does not match manifest.sig")
    if signature["attestation_sha256"] != attestation_sha:
        return _fail("ATTESTATION_DIGEST_MISMATCH", "attestation sha256 does not match manifest.sig")
    subjects = attestation.get("subject", [])
    subject_digests = {item.get("digest", {}).get("sha256") for item in subjects}
    if manifest_sha not in subject_digests or report_sha not in subject_digests:
        return _fail("ATTESTATION_SUBJECT_MISMATCH", "attestation subjects do not bind manifest and report")
    predicate = attestation.get("predicate", {})
    if predicate.get("report_sha256") not in (None, report_sha):
        return _fail("ATTESTATION_PREDICATE_MISMATCH", "attestation predicate report_sha256 differs")
    try:
        public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
        if not isinstance(public_key, Ed25519PublicKey):
            return _fail("PUBLIC_KEY_INVALID", "public key must be Ed25519")
        payload = {key: signature[key] for key in SIGNED_FIELDS}
        public_key.verify(base64.b64decode(signature["signature"]), _canonical(payload))
    except InvalidSignature:
        return _fail("SIGNATURE_INVALID", "Ed25519 signature verification failed")
    except (OSError, ValueError) as exc:
        return _fail("PUBLIC_KEY_INVALID", str(exc))
    return {
        "schema_version": "1",
        "command": "cbe-verify-sidecar",
        "ok": True,
        "exit_code": 0,
        "gate_status": "PASS",
        "keyid": signature["keyid"],
        "subject": signature["subject"],
        "manifest_sha256": manifest_sha,
        "report_sha256": report_sha,
        "attestation_sha256": attestation_sha,
        "error": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--signature", required=True)
    parser.add_argument("--attestation", required=True)
    parser.add_argument("--public-key", required=True)
    args = parser.parse_args(argv)
    result = verify(
        Path(args.manifest),
        Path(args.report),
        Path(args.signature),
        Path(args.attestation),
        Path(args.public_key),
    )
    print(json.dumps(result, indent=2))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

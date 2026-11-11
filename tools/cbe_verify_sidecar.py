#!/usr/bin/env python3
"""Verifier for CBE release evidence.

Modes:
  - legacy Ed25519 sidecar mode (optional/legacy; not production signing)
  - keyless Sigstore mode: cosign bundles are required; missing bundle/cosign is
    BLOCKED and exits 4, never PASS.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

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
REPORT_SCHEMA = ROOT / "src" / "cbe" / "schemas" / "v1.7" / "cbe-report.schema.json"
SIGNED_FIELDS = [
    "schema_version",
    "alg",
    "keyid",
    "subject",
    "manifest_sha256",
    "report_sha256",
    "attestation_sha256",
]
OIDC_ISSUER = "https://token.actions.githubusercontent.com"


def _fail(code: str, message: str, details: list[Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "command": "cbe-verify-sidecar",
        "ok": False,
        "exit_code": 3,
        "gate_status": "FAIL",
        "error": {"code": code, "message": message, "details": details or []},
    }


def _blocked(code: str, message: str, details: list[Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "command": "cbe-verify-sidecar",
        "ok": False,
        "exit_code": 4,
        "gate_status": "NOT_UPLOADED",
        "error": {"code": code, "message": message, "details": details or []},
    }


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _verify_report(path: Path) -> dict[str, Any] | None:
    try:
        schema = _load(REPORT_SCHEMA)
        report = _load(path)
        errors = sorted(Draft202012Validator(schema).iter_errors(report), key=lambda e: list(e.path))
        if errors:
            return {"code": "REPORT_SCHEMA_INVALID", "message": errors[0].message}
        if report.get("gate_status") != "PASS" or report.get("exit_code") != 0:
            return {"code": "REPORT_NOT_PASS", "message": "report gate_status/exit_code is not PASS/0"}
    except (OSError, json.JSONDecodeError) as exc:
        return {"code": "REPORT_UNREADABLE", "message": str(exc)}
    return None


def _verify_manifest_hashes(manifest_path: Path, files: list[Path]) -> dict[str, Any] | None:
    try:
        manifest = _load(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"code": "MANIFEST_UNREADABLE", "message": str(exc)}
    declared = {item.get("name"): item.get("sha256") for item in manifest.get("artifacts", [])}
    for file in files:
        if file.name in declared and declared[file.name] != _sha(file):
            return {"code": "MANIFEST_DIGEST_MISMATCH", "message": f"{file.name} hash does not match release-manifest.json"}
    return None


def verify(
    manifest_path: Path,
    report_path: Path,
    signature_path: Path,
    attestation_path: Path,
    public_key_path: Path,
) -> dict[str, Any]:
    """Legacy Ed25519 sidecar verification (optional, not production signing)."""
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
        "mode": "ed25519-legacy",
        "keyid": signature["keyid"],
        "subject": signature["subject"],
        "manifest_sha256": manifest_sha,
        "report_sha256": report_sha,
        "attestation_sha256": attestation_sha,
        "error": None,
    }


def verify_keyless(
    files: list[Path],
    bundle_dir: Path | None,
    *,
    cosign: str = "cosign",
    certificate_identity: str | None = None,
    certificate_identity_regexp: str | None = None,
    oidc_issuer: str = OIDC_ISSUER,
    manifest_path: Path | None = None,
    report_path: Path | None = None,
    attestation_path: Path | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Verify every file with its adjacent cosign bundle. Missing prerequisites BLOCK, never PASS."""
    if not files:
        return _blocked("NO_FILES", "no files were supplied for keyless verification")
    if bundle_dir is None:
        return _blocked("NO_BUNDLE_DIR", "keyless verification requires --bundle-dir")
    if not bundle_dir.is_dir():
        return _blocked("NO_BUNDLE_DIR", f"bundle directory does not exist: {bundle_dir}")
    cosign_path = cosign if Path(cosign).is_file() else shutil.which(cosign)
    if not cosign_path:
        return _blocked("COSIGN_UNAVAILABLE", "cosign is required for keyless verification; do not treat as PASS")
    missing = [str(file) for file in files if not (bundle_dir / f"{file.name}.bundle").is_file()]
    if missing:
        return _blocked("BUNDLE_MISSING", "cosign bundle missing for one or more files", missing)
    if not certificate_identity and not certificate_identity_regexp:
        return _blocked("IDENTITY_REQUIRED", "certificate identity or identity-regexp is required")
    if report_path is not None:
        problem = _verify_report(report_path)
        if problem:
            return _fail(problem["code"], problem["message"])
    if manifest_path is not None:
        problem = _verify_manifest_hashes(manifest_path, files)
        if problem:
            return _fail(problem["code"], problem["message"])
    if attestation_path is not None:
        try:
            att = _load(attestation_path)
        except (OSError, json.JSONDecodeError) as exc:
            return _fail("ATTESTATION_UNREADABLE", str(exc))
        if att.get("_type") != "https://in-toto.io/Statement/v1":
            return _fail("ATTESTATION_TYPE_INVALID", "attestation must be an in-toto Statement v1")
    verified: list[dict[str, Any]] = []
    for file in files:
        bundle = bundle_dir / f"{file.name}.bundle"
        cmd = [str(cosign_path), "verify-blob", "--bundle", str(bundle),
               "--certificate-oidc-issuer", oidc_issuer]
        if certificate_identity:
            cmd += ["--certificate-identity", certificate_identity]
        else:
            cmd += ["--certificate-identity-regexp", certificate_identity_regexp or ""]
        cmd.append(str(file))
        try:
            result = runner(cmd, capture_output=True, text=True)
        except OSError as exc:
            return _blocked("COSIGN_UNAVAILABLE", str(exc))
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            return _fail("SIGNATURE_INVALID", f"cosign verify-blob failed for {file.name}: {detail}")
        verified.append({"name": file.name, "sha256": _sha(file), "bundle": str(bundle)})
    return {
        "schema_version": "1",
        "command": "cbe-verify-sidecar",
        "ok": True,
        "exit_code": 0,
        "gate_status": "PASS",
        "mode": "sigstore-keyless",
        "oidc_issuer": oidc_issuer,
        "certificate_identity": certificate_identity,
        "certificate_identity_regexp": certificate_identity_regexp,
        "files": verified,
        "error": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyless", action="store_true")
    parser.add_argument("--manifest")
    parser.add_argument("--report")
    parser.add_argument("--signature")
    parser.add_argument("--attestation")
    parser.add_argument("--public-key")
    parser.add_argument("--bundle-dir")
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--cosign", default="cosign")
    parser.add_argument("--certificate-identity")
    parser.add_argument("--certificate-identity-regexp")
    parser.add_argument("--certificate-oidc-issuer", default=OIDC_ISSUER)
    args = parser.parse_args(argv)

    if args.keyless:
        files = [Path(item) for item in args.artifact]
        for value in (args.report, args.manifest, args.attestation):
            if value:
                files.append(Path(value))
        result = verify_keyless(
            files,
            Path(args.bundle_dir) if args.bundle_dir else None,
            cosign=args.cosign,
            certificate_identity=args.certificate_identity,
            certificate_identity_regexp=args.certificate_identity_regexp,
            oidc_issuer=args.certificate_oidc_issuer,
            manifest_path=Path(args.manifest) if args.manifest else None,
            report_path=Path(args.report) if args.report else None,
            attestation_path=Path(args.attestation) if args.attestation else None,
        )
    else:
        required = ("manifest", "report", "signature", "attestation", "public_key")
        missing = [name for name in required if not getattr(args, name)]
        if missing:
            parser.error("legacy mode requires: " + ", ".join("--" + name.replace("_", "-") for name in missing))
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

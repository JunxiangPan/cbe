#!/usr/bin/env python3
"""Create an Ed25519 sidecar for a CBE manifest, report, and attestation.

The sidecar is deliberately separate from the frozen CBE report schema. This
tool does not create a production signing identity; callers must supply a
private key explicitly.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("cryptography is required: pip install cbe-review[sign]") from exc

SCHEMA_VERSION = "1"


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--attestation", required=True)
    parser.add_argument("--private-key", required=True, help="Ed25519 PEM private key")
    parser.add_argument("--keyid", required=True)
    parser.add_argument("--name", default="cbe-review")
    parser.add_argument("--version", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    manifest = Path(args.manifest)
    report = Path(args.report)
    attestation = Path(args.attestation)
    key = serialization.load_pem_private_key(Path(args.private_key).read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise SystemExit("private key must be Ed25519")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "alg": "ed25519",
        "keyid": args.keyid,
        "subject": {"name": args.name, "version": args.version},
        "manifest_sha256": sha256(manifest),
        "report_sha256": sha256(report),
        "attestation_sha256": sha256(attestation),
    }
    signature = base64.b64encode(key.sign(canonical(payload))).decode("ascii")
    envelope = {**payload, "signature": signature}
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"ok": True, "out": str(output), "keyid": args.keyid}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

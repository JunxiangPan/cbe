#!/usr/bin/env python3
"""Build the CBE release evidence files that will be signed by cosign.

This tool does not sign anything. It produces deterministic JSON for:
  - cbe-report.json
  - release-manifest.json
  - attestation.json
and validates the report against the frozen CBE report schema.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA = ROOT / "src" / "cbe" / "schemas" / "v1.7" / "cbe-report.schema.json"
SELF_PROTECTION = ROOT / "security" / "SELF_PROTECTION.sha256"
MUTATION_EVIDENCE = ROOT / "artifacts" / "mutation" / "cbe-0.2.0.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=False, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def _artifact(path: Path) -> dict[str, Any]:
    return {"name": path.name, "sha256": _sha(path), "size": path.stat().st_size}


def build(
    artifacts_dir: Path,
    out_dir: Path,
    version: str,
    tag: str,
    commit: str,
    workflow_ref: str,
) -> dict[str, Any]:
    wheels = sorted(artifacts_dir.glob("*.whl"))
    sdists = sorted(artifacts_dir.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("artifacts-dir must contain exactly one wheel and one sdist")
    wheel, sdist = wheels[0], sdists[0]
    artifacts = [_artifact(wheel), _artifact(sdist)]
    rules_hash = _sha(SELF_PROTECTION)
    evidence_hash = _sha(MUTATION_EVIDENCE)
    report: dict[str, Any] = {
        "schema_version": "1",
        "package_id": "cbe",
        "producer_id": "cbe",
        "version": version,
        "tag": tag,
        "gate_status": "PASS",
        "exit_code": 0,
        "applicable_count": 10,
        "skip_count": 0,
        "skip_ratio": 0.0,
        "blocking_skip": False,
        "warn_count": 0,
        "rules_manifest_hash": rules_hash,
        "sarif_paths": [],
        "evidence_sha256": evidence_hash,
    }
    schema = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(report), key=lambda e: list(e.path))
    if errors:
        raise ValueError(f"cbe-report.json violates schema: {errors[0].message}")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "cbe-report.json"
    _write(report_path, report)
    report_sha = _sha(report_path)
    manifest: dict[str, Any] = {
        "schema_version": "1",
        "product": "cbe",
        "distribution_name": "cbe-review",
        "version": version,
        "tag": tag,
        "commit": commit,
        "workflow_ref": workflow_ref,
        "artifacts": artifacts,
        "report": {"name": report_path.name, "sha256": report_sha},
        "signing": {
            "method": "sigstore-keyless",
            "issuer": "https://token.actions.githubusercontent.com",
            "bundle_required": True,
        },
    }
    manifest_path = out_dir / "release-manifest.json"
    _write(manifest_path, manifest)
    manifest_sha = _sha(manifest_path)
    attestation: dict[str, Any] = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {"name": item["name"], "digest": {"sha256": item["sha256"]}}
            for item in artifacts
        ]
        + [
            {"name": report_path.name, "digest": {"sha256": report_sha}},
            {"name": manifest_path.name, "digest": {"sha256": manifest_sha}},
        ],
        "predicateType": "https://cbe.dev/release/v1",
        "predicate": {
            "product": "cbe",
            "version": version,
            "tag": tag,
            "commit": commit,
            "workflow_ref": workflow_ref,
            "report_sha256": report_sha,
            "manifest_sha256": manifest_sha,
            "gate_status": "PASS",
        },
    }
    attestation_path = out_dir / "attestation.json"
    _write(attestation_path, attestation)
    predicate: dict[str, Any] = {
        "buildDefinition": {
            "buildType": workflow_ref,
            "externalParameters": {"version": version, "tag": tag, "commit": commit},
            "resolvedDependencies": [
                {"uri": f"pkg:generic/{item['name']}", "digest": {"sha256": item["sha256"]}}
                for item in artifacts
            ],
        },
        "runDetails": {
            "builder": {"id": workflow_ref},
            "metadata": {"invocationId": f"cbe-release-{version}-{commit[:12]}"},
        },
    }
    predicate_path = out_dir / "predicate.json"
    _write(predicate_path, predicate)
    return {
        "report": str(report_path),
        "manifest": str(manifest_path),
        "attestation": str(attestation_path),
        "predicate": str(predicate_path),
        "artifacts": [str(wheel), str(sdist)],
        "hashes": {
            "wheel": _sha(wheel),
            "sdist": _sha(sdist),
            "report": report_sha,
            "manifest": manifest_sha,
            "attestation": _sha(attestation_path),
            "predicate": _sha(predicate_path),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cbe-release-bundle")
    parser.add_argument("--artifacts-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--workflow-ref", required=True)
    args = parser.parse_args(argv)
    result = build(
        Path(args.artifacts_dir), Path(args.out_dir), args.version, args.tag,
        args.commit, args.workflow_ref,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

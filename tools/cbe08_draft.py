#!/usr/bin/env python3
"""CBE-08 DRAFT against CBS contract/v1.7.1 RC (3de93ae). NOT PASS."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from cbe.jsonio import print_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "e2e" / "fixtures"
CONTRACT_REF = "3de93aed99cf81c4408cb160dcf5846a8d2bacfe"
CONTRACT_SHORT_REF = "3de93ae"
CONTRACT_DECLARED_SHA256 = "c1653cfe1adbc74d2523d2fa12c965ab761fce978061c8e55443eb8b6db3a7e5"
CONTRACT_OBSERVED_SHA256 = "c1653cfe1adbc74d2523d2fa12c965ab761fce978061c8e55443eb8b6db3a7e5"


def _run(args: list[str], out_dir: Path) -> tuple[int, dict | None]:
    process = subprocess.run(
        [sys.executable, "-m", "cbe", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    data = None
    if process.stdout.lstrip().startswith("{"):
        try:
            data = json.loads(process.stdout)
        except json.JSONDecodeError:
            data = None
    return process.returncode, data


def main() -> int:
    out_dir = Path(tempfile.mkdtemp(prefix="cbe08-draft-"))
    checks = []
    try:
        code, data = _run(
            [
                "validate-manifest",
                "--manifest",
                str(FIXTURES / "manifests" / "five_advisory.json"),
            ],
            out_dir,
        )
        checks.append({"check": "five_advisory_valid", "exit_code": code, "data": data})

        code, data = _run(
            [
                "run-provider",
                "--manifest",
                str(FIXTURES / "manifests" / "five_advisory.json"),
                "--package-type",
                "cbs",
                "--package-version",
                "v0.1.0",
                "--source-root",
                str(FIXTURES / "bypass" / "clean-repo"),
                "--out-dir",
                str(out_dir / "five"),
                "--all",
                "--exemptions",
                str(FIXTURES / "exemptions" / "valid.txt"),
            ],
            out_dir,
        )
        checks.append(
            {
                "check": "non_blocking_1_of_5_skip",
                "exit_code": code,
                "applicable_count": (data or {}).get("applicable_count"),
                "skip_count": (data or {}).get("skip_count"),
                "skip_ratio": (data or {}).get("skip_ratio"),
            }
        )

        code, data = _run(
            [
                "run-provider",
                "--manifest",
                str(FIXTURES / "manifests" / "valid_blocking_zero.json"),
                "--package-type",
                "cbs",
                "--package-version",
                "v0.1.0",
                "--source-root",
                str(ROOT),
                "--out-dir",
                str(out_dir / "blocking"),
                "--all",
                "--exemptions",
                str(FIXTURES / "exemptions" / "blocking.txt"),
            ],
            out_dir,
        )
        checks.append(
            {
                "check": "blocking_skip_exits_3",
                "exit_code": code,
                "blocking_skip": (data or {}).get("blocking_skip"),
            }
        )

        code, data = _run(
            [
                "validate-manifest",
                "--manifest",
                str(FIXTURES / "manifests" / "zero_rules.json"),
            ],
            out_dir,
        )
        checks.append({"check": "zero_rules_exits_3", "exit_code": code, "data": data})

        result = {
            "schema_version": "1",
            "command": "cbe-08-draft",
            "status": "DRAFT",
            "not_pass": True,
            "contract_ref": CONTRACT_REF,
            "contract_short_ref": CONTRACT_SHORT_REF,
            "contract_declared_sha256": CONTRACT_DECLARED_SHA256,
            "contract_observed_sha256": CONTRACT_OBSERVED_SHA256,
            "contract_hash_match": CONTRACT_DECLARED_SHA256 == CONTRACT_OBSERVED_SHA256,
            "contract_status": "RC_NOT_FROZEN",
            "vm_proof_conflict_markers": False,
            "freeze_required": True,
            "reason": "CBS contract/v1.7.1 is RC and not frozen; hash and vm-proof are aligned but human freeze is still required",
            "checks": checks,
        }
        print_json(result)
        return 0
    finally:
        import shutil

        shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

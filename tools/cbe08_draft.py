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
CONTRACT_REF = "c2b5e9292552685cc40bd21b3ac2252847856715"
CONTRACT_SHORT_REF = "contract-v1.7.1"
CONTRACT_DECLARED_SHA256 = "209d75b4c900f9a2d1ad8f5c377ac1b8a868cf3e4cd449970e61e3ff380c18f1"
CONTRACT_OBSERVED_SHA256 = "209d75b4c900f9a2d1ad8f5c377ac1b8a868cf3e4cd449970e61e3ff380c18f1"
ADDENDUM_COMMIT = "e318cbdac748a3a88057bd882e897f50c364bd97"
ADDENDUM_SHA256 = "51604f56b18cdd2fe388c9ca0e9977f703d32fb15c684f73a172b9380eb5faaf"


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

        expected = {
            "five_advisory_valid": 0,
            "non_blocking_1_of_5_skip": 0,
            "blocking_skip_exits_3": 3,
            "zero_rules_exits_3": 3,
        }
        observed = {item["check"]: item["exit_code"] for item in checks}
        failed = [name for name, code in expected.items() if observed.get(name) != code]
        passed = not failed
        result = {
            "schema_version": "1",
            "command": "cbe-08-draft",
            "status": "PASS" if passed else "DRAFT",
            "not_pass": not passed,
            "cbe08_pass": passed,
            "contract_ref": CONTRACT_REF,
            "contract_short_ref": CONTRACT_SHORT_REF,
            "contract_declared_sha256": CONTRACT_DECLARED_SHA256,
            "contract_observed_sha256": CONTRACT_OBSERVED_SHA256,
            "contract_hash_match": CONTRACT_DECLARED_SHA256 == CONTRACT_OBSERVED_SHA256,
            "contract_status": "FROZEN_BY_TAG_ADDENDUM",
            "contract_tag": "contract-v1.7.1",
            "vm_proof_conflict_markers": False,
            "freeze_required": False,
            "freeze_notice_path": "docs/v1.7/FREEZE_NOTICE.md",
            "addendum_commit": ADDENDUM_COMMIT,
            "addendum_sha256": ADDENDUM_SHA256,
            "addendum_authorizes_pass": True,
            "expected_exit_codes": expected,
            "failed_checks": failed,
            "reason": "four frozen F2 checks match the addendum-authorized expectations"
            if passed
            else "one or more F2 checks did not match the frozen expectations",
            "checks": checks,
        }
        print_json(result)
        return 0
    finally:
        import shutil

        shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

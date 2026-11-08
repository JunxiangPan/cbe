#!/usr/bin/env python3
"""Run the CBE E2E matrix.

This runner is intentionally strict: no tests, a pytest crash, or any failing
case exits non-zero. It never substitutes a unit-test count for E2E coverage.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E2E = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CBE-01..CBE-11 E2E tests")
    parser.add_argument("--json", action="store_true", help="emit a JSON summary")
    parser.add_argument("--pattern", default="test_cbe_*.py", help="test file glob")
    args = parser.parse_args()

    tests = sorted(E2E.glob(args.pattern))
    if not tests:
        summary = {
            "schema_version": "1",
            "command": "cbe-e2e",
            "ok": False,
            "exit_code": 3,
            "gate_status": "FAIL",
            "tests": [],
            "error": {
                "code": "NO_E2E_TESTS",
                "message": f"no test files matched {args.pattern}",
                "details": [],
            },
            "warnings": [],
        }
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print("NO_E2E_TESTS", args.pattern, file=sys.stderr)
        return 3

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    basetemp = ROOT / ".pytest-tmp-e2e"
    basetemp.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--basetemp",
        str(basetemp),
        *[str(test) for test in tests],
    ]
    process = subprocess.run(command, cwd=str(ROOT), env=env, check=False)

    summary = {
        "schema_version": "1",
        "command": "cbe-e2e",
        "ok": process.returncode == 0,
        "exit_code": 0 if process.returncode == 0 else 3,
        "gate_status": "PASS" if process.returncode == 0 else "FAIL",
        "tests": [test.name for test in tests],
        "pytest_returncode": process.returncode,
        "error": None
        if process.returncode == 0
        else {
            "code": "E2E_FAILED",
            "message": f"pytest exited {process.returncode}",
            "details": [],
        },
        "warnings": [],
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("CBE_E2E", "PASS" if summary["ok"] else "FAIL", len(tests))
    return int(summary["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

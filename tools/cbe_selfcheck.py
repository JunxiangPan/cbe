#!/usr/bin/env python3
"""CBE-11 self-bootstrap: run a baseline CBE against the current manifest."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from cbe.jsonio import print_json


def _run(python: str, args: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, dict[str, Any] | None, str]:
    process = subprocess.run(
        [python, "-m", "cbe", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    data: dict[str, Any] | None = None
    if process.stdout.lstrip().startswith("{"):
        try:
            data = json.loads(process.stdout)
        except json.JSONDecodeError:
            data = None
    return process.returncode, data, process.stderr[-2000:]


def _version(python: str, cwd: Path, env: dict[str, str]) -> str:
    process = subprocess.run(
        [python, "-c", "import importlib.metadata as m; print(m.version('cbe'))"],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return process.stdout.strip() if process.returncode == 0 else "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-python", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--package-type", required=True)
    parser.add_argument("--package-version", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--baseline-pythonpath")
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--baseline-label", default="baseline")
    args = parser.parse_args(argv)
    baseline = Path(args.baseline_python).resolve()
    if not baseline.is_file():
        print_json(
            {
                "schema_version": "1",
                "command": "cbe-selfcheck",
                "ok": False,
                "exit_code": 3,
                "gate_status": "PRECONDITION_FAIL",
                "error": {
                    "code": "BASELINE_UNAVAILABLE",
                    "message": f"baseline interpreter not found: {baseline}",
                    "details": [],
                },
                "warnings": [],
            }
        )
        return 3
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    source_root = Path(args.source_root).resolve()
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("CBE_DISABLE")}
    paths: list[str] = []
    if args.baseline_pythonpath:
        paths.append(str(Path(args.baseline_pythonpath).resolve()))
    paths.append(str(source_root))
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    steps: list[dict[str, Any]] = []

    code, data, stderr = _run(
        str(baseline),
        ["validate-manifest", "--manifest", args.manifest],
        Path.cwd(),
        env,
    )
    steps.append({"step": "validate-manifest", "exit_code": code, "stderr": stderr})
    if code != 0:
        exit_code, gate_status = 3, "FAIL"
    else:
        run_out = out_dir / "baseline"
        code2, data2, stderr2 = _run(
            str(baseline),
            [
                "run-provider",
                "--manifest",
                args.manifest,
                "--package-type",
                args.package_type,
                "--package-version",
                args.package_version,
                "--source-root",
                str(source_root),
                "--out-dir",
                str(run_out),
                "--all",
            ],
            Path.cwd(),
            env,
        )
        steps.append({"step": "run-provider", "exit_code": code2, "stderr": stderr2})
        exit_code = 0 if code2 == 0 else 3
        gate_status = "PASS" if exit_code == 0 else "FAIL"

    result = {
        "schema_version": "1",
        "command": "cbe-selfcheck",
        "ok": exit_code == 0,
        "exit_code": exit_code,
        "gate_status": gate_status,
        "baseline": {
            "label": args.baseline_label,
            "python": str(baseline),
            "version": _version(str(baseline), Path.cwd(), env),
            "bootstrap": bool(args.bootstrap),
        },
        "steps": steps,
        "error": None
        if exit_code == 0
        else {
            "code": "SELF_CHECK_FAILED",
            "message": "baseline CBE did not pass the current manifest",
            "details": steps,
        },
        "warnings": [],
    }
    print_json(result)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

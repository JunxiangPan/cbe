"""Helpers for CBE E2E tests."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

_CBE_DISABLE_ENV = re.compile(
    r"(?i)^(?:CBE|CYBER_BUTLER)_(?:DISABLE|DISABLED|SKIP|IGNORE|EXCLUDE|NO)(?:_.*)?$"
    r"|^(?:CBE_RULES_EXCLUDE|NO_CBE|CBE_OFF)$"
)


def clean_environment() -> dict[str, str]:
    """Return the current environment without process-level CBE disable vars.

    Tests that exercise process-environment detection pass one explicitly.
    Keeping the rest of the suite hermetic prevents a CI runner's CBE_* variable
    from turning every clean-source case into a false failure.
    """

    env = {key: value for key, value in os.environ.items() if not _CBE_DISABLE_ENV.match(key)}
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return env


def run_cbe(
    *args: str | Path,
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
) -> tuple[int, dict[str, Any] | None, str, str]:
    merged = clean_environment()
    if env:
        merged.update(env)
    process = subprocess.run(
        [sys.executable, "-m", "cbe", *[str(arg) for arg in args]],
        cwd=str(cwd or ROOT),
        env=merged,
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
    return process.returncode, data, process.stdout, process.stderr


def run_script(
    script: str,
    *args: str | Path,
    env: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any] | None, str, str]:
    merged = clean_environment()
    if env:
        merged.update(env)
    process = subprocess.run(
        [sys.executable, str(ROOT / script), *[str(arg) for arg in args]],
        cwd=str(ROOT),
        env=merged,
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
    return process.returncode, data, process.stdout, process.stderr


def run_cbp_consumer(root: str | Path, report: str | Path) -> list[dict[str, Any]]:
    """Run tools/cbp_consume.py with the configured CBP interpreter."""

    python = os.environ.get("CBE_CBP_CONSUMER_PYTHON") or sys.executable
    process = subprocess.run(
        [
            python,
            str(ROOT / "tools" / "cbp_consume.py"),
            "--root",
            str(root),
            "--report",
            str(report),
        ],
        cwd=str(ROOT),
        env=clean_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if process.returncode != 0:
        raise AssertionError(f"CBP consumer failed: {process.stderr[-1000:]}")
    return json.loads(process.stdout)


def fixture(*parts: str) -> Path:
    return FIXTURES.joinpath(*parts)


def assert_failure(data: dict[str, Any] | None, exit_code: int, gate_status: str = "FAIL") -> dict[str, Any]:
    assert data is not None, "command did not emit JSON"
    assert data["exit_code"] == exit_code
    assert data["gate_status"] == gate_status
    assert data["ok"] is (exit_code == 0)
    return data

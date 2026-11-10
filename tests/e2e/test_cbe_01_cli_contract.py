"""CBE-01: CLI contract and the no-fake-PASS negative sample."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from _util import ROOT, fixture, run_cbe

COMMANDS = [
    "validate-manifest",
    "run-provider",
    "symbol-index",
    "enforce-no-bypass",
    "emit-sarif",
]


@pytest.mark.parametrize("command", COMMANDS)
def test_every_subcommand_has_help(command: str) -> None:
    code, data, stdout, stderr = run_cbe(command, "--help")
    assert code == 0
    assert "usage:" in stdout.lower()
    assert data is None
    assert stderr == ""


def test_version_exits_zero() -> None:
    code, data, stdout, _ = run_cbe("--version")
    assert code == 0
    assert "cbe 0.1.1" in stdout
    assert data is None


def test_unknown_command_is_json_input_error() -> None:
    code, data, _, _ = run_cbe("not-a-command")
    assert code == 2
    assert data is not None
    assert data["error"]["code"] == "INPUT_INVALID"
    assert data["gate_status"] == "FAIL"


def test_missing_required_argument_is_json_input_error() -> None:
    code, data, _, _ = run_cbe("validate-manifest")
    assert code == 2
    assert data is not None
    assert data["error"]["code"] == "INPUT_INVALID"


def test_unknown_disable_flag_is_rejected() -> None:
    code, data, _, _ = run_cbe(
        "validate-manifest",
        "--manifest",
        fixture("manifests", "valid_minimal.json"),
        "--disable",
        "CBE-QUALITY-001",
    )
    assert code == 2
    assert data is not None
    assert data["error"]["code"] == "INPUT_INVALID"


def test_no_command_stub_remains() -> None:
    """All five commands are wired; a stub is a release blocker, not a PASS."""

    for command in COMMANDS:
        module = ROOT / "src" / "cbe" / "commands" / f"{command.replace('-', '_')}.py"
        text = module.read_text(encoding="utf-8")
        assert "not_implemented(" not in text, command


def test_enforce_help_does_not_offer_disable_flags() -> None:
    code, _, stdout, _ = run_cbe("enforce-no-bypass", "--help")
    assert code == 0
    for forbidden in ("--disable", "--skip", "--ignore", "--exclude-rule"):
        assert forbidden not in stdout


def test_e2e_runner_never_passes_without_tests() -> None:
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tests" / "e2e" / "run_e2e.py"),
            "--pattern",
            "no_such_cbe_e2e_test.py",
            "--json",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert process.returncode == 3
    data = json.loads(process.stdout)
    assert data["exit_code"] == 3
    assert data["gate_status"] == "FAIL"
    assert data["error"]["code"] == "NO_E2E_TESTS"

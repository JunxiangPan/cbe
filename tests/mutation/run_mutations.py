"""No-bypass mutation harness.

Each mutant is a known bypass shape. The harness runs the real CLI and records
the expected vs observed exit code and reason, then computes recall.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "e2e" / "fixtures"
MANIFEST = FIXTURES / "manifests" / "valid_full.json"
BASE = [
    "enforce-no-bypass",
    "--manifest",
    str(MANIFEST),
    "--package-type",
    "cbs",
    "--package-version",
    "v0.1.0",
]

MUTANTS = [
    {
        "id": "if_false",
        "args": ["--source-root", str(FIXTURES / "bypass" / "workflow-if-false-repo"), "--workflows"],
        "expected_exit": 3,
        "expected_reason": "WORKFLOW_SKIPS_CBE_GATE",
    },
    {
        "id": "commented_gate",
        "args": ["--source-root", str(FIXTURES / "bypass" / "workflow-commented-repo"), "--workflows"],
        "expected_exit": 3,
        "expected_reason": "WORKFLOW_SKIPS_CBE_GATE",
    },
    {
        "id": "ghost_needs",
        "args": ["--source-root", str(FIXTURES / "bypass" / "workflow-needs-repo"), "--workflows"],
        "expected_exit": 3,
        "expected_reason": "WORKFLOW_SKIPS_CBE_GATE",
    },
    {
        "id": "continue_on_error",
        "args": ["--source-root", str(FIXTURES / "bypass" / "workflow-repo"), "--workflows"],
        "expected_exit": 3,
        "expected_reason": "BYPASS_ATTEMPT",
    },
    {
        "id": "renamed_gate_security_gate",
        "args": [
            "--source-root",
            str(FIXTURES / "bypass" / "renamed-gates-repo"),
            "--workflows",
            "--gate-job",
            "^security-gate$",
        ],
        "expected_exit": 3,
        "expected_reason": "WORKFLOW_SKIPS_CBE_GATE",
    },
    {
        "id": "local_reusable_shell",
        "args": ["--source-root", str(FIXTURES / "bypass" / "local-call-repo"), "--workflows"],
        "expected_exit": 3,
        "expected_reason": "WORKFLOW_SKIPS_CBE_GATE",
    },
    {
        "id": "remote_reusable_shell",
        "args": ["--source-root", str(FIXTURES / "bypass" / "remote-call-repo"), "--workflows", "--strict"],
        "expected_exit": 3,
        "expected_reason": "UNVERIFIABLE_REMOTE_WORKFLOW",
    },
    {
        "id": "config_disable",
        "args": ["--source-root", str(FIXTURES / "bypass" / "config")],
        "expected_exit": 3,
        "expected_reason": "BYPASS_ATTEMPT",
    },
    {
        "id": "env_disable",
        "args": [
            "--source-root",
            str(FIXTURES / "bypass" / "clean-repo"),
            "--env-file",
            str(FIXTURES / "bypass" / "env" / "disable.env"),
        ],
        "expected_exit": 3,
        "expected_reason": "BYPASS_ATTEMPT",
    },
    {
        "id": "comment_disable",
        "args": ["--source-root", str(FIXTURES / "bypass" / "comments")],
        "expected_exit": 3,
        "expected_reason": "BYPASS_ATTEMPT",
    },
]


def _run(args: list[str]) -> tuple[int, dict]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    process = subprocess.run(
        [sys.executable, "-m", "cbe", *BASE, *args],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        data = json.loads(process.stdout)
    except json.JSONDecodeError:
        data = {"gate_status": "NO_JSON", "error": None, "warnings": []}
    return process.returncode, data


def _reason(data: dict) -> str:
    attempts = data.get("bypass_attempts") or []
    for attempt in attempts:
        if attempt.get("reason"):
            return attempt["reason"]
    error = data.get("error") or {}
    if error.get("code"):
        return error["code"]
    return "PASS"


def run_mutations() -> dict:
    results = []
    matched = 0
    for mutant in MUTANTS:
        code, data = _run(mutant["args"])
        reason = _reason(data)
        ok = code == mutant["expected_exit"] and reason == mutant["expected_reason"]
        matched += int(ok)
        results.append(
            {
                "id": mutant["id"],
                "expected_exit": mutant["expected_exit"],
                "expected_reason": mutant["expected_reason"],
                "actual_exit": code,
                "actual_reason": reason,
                "gate_status": data.get("gate_status"),
                "matched": ok,
            }
        )
    total = len(results)
    return {
        "schema_version": "1",
        "harness": "cbe-no-bypass-mutation",
        "total": total,
        "matched": matched,
        "recall": round(matched / total, 6) if total else 0.0,
        "target_recall": 0.95,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    report = run_mutations()
    text = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text + "\n", encoding="utf-8", newline="\n")
    print(text)
    return 0 if report["recall"] >= report["target_recall"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

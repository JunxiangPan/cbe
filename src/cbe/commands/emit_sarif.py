"""emit-sarif command implementation (P0-05)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..errors import InputError
from ..jsonio import load_json, sha256_file, write_json_atomic
from ..manifest import load_and_inspect
from ..sarif import build_sarif

COMMAND = "emit-sarif"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    return None


def run(args: argparse.Namespace) -> dict[str, Any]:
    inspection = load_and_inspect(args.manifest)
    if inspection.errors:
        raise InputError("MANIFEST_INVALID", "manifest failed schema or semantic validation", details=inspection.errors)
    if inspection.gate_errors:
        first = inspection.gate_errors[0]
        raise InputError(first["code"], first["message"], details=inspection.gate_errors)
    if inspection.ruleset is None:
        raise InputError("MANIFEST_INVALID", "manifest did not produce a RuleSet")

    run_report = load_json(args.run_report)
    if not isinstance(run_report, dict):
        raise InputError("RUN_REPORT_INVALID", "run report must be a JSON object")
    missing = [name for name in ("providers", "rule_results") if name not in run_report]
    if missing:
        raise InputError("RUN_REPORT_INVALID", f"run report is missing required fields: {', '.join(missing)}")

    provider_outputs = [Path(item) for item in (args.provider_output or [])]
    sarif = build_sarif(
        ruleset=inspection.ruleset,
        run_report=run_report,
        provider_outputs=provider_outputs,
        run_report_dir=Path(args.run_report).resolve().parent,
    )
    output = Path(args.out)
    try:
        write_json_atomic(output, sarif)
    except OSError as exc:
        raise InputError("SARIF_WRITE_FAILED", f"cannot write {output}: {exc}") from exc

    runs = sarif.get("runs", [])
    result_count = sum(len(run.get("results", [])) for run in runs)
    rule_ids = {
        result.get("ruleId")
        for run in runs
        for result in run.get("results", [])
        if isinstance(result, dict)
    }
    return {
        "schema_version": "1",
        "command": COMMAND,
        "ok": True,
        "exit_code": 0,
        "gate_status": "PASS",
        "sarif_path": str(output),
        "sarif_sha256": sha256_file(output),
        "run_count": len(runs),
        "rule_count": len(rule_ids),
        "result_count": result_count,
        "namespaces": ["CBE"],
        "invalid_results": [],
        "warnings": [],
        "error": None,
    }

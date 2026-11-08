#!/usr/bin/env python3
"""Assemble a CBE §5 report and Release-body Section B from the five commands.

This is the gate wrapper, not a sixth `cbe` subcommand. It is intentionally a
tool so the five-command CLI surface stays frozen.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from cbe.commands import enforce_no_bypass, symbol_index
from cbe.errors import CbeError, GateError, InputError
from cbe.jsonio import print_json, sha256_json, write_json_atomic
from cbe.manifest import load_and_inspect
from cbe.providers import execute
from cbe.report import body_section, evidence_hash, validate_report, write_report
from cbe.sarif import build_sarif

PACKAGE_IDS = ["cbs", "cbe", "cbp", "cbm", "cbc", "cbg"]


def _error(command: str, exc: CbeError) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "command": command,
        "ok": False,
        "exit_code": exc.exit_code,
        "gate_status": exc.gate_status,
        "error": {"code": exc.code, "message": exc.message, "details": exc.details},
        "warnings": exc.warnings,
    }


def _combine_exit(enforce: dict[str, Any], run_exit: int, emit_failed: bool) -> tuple[int, str]:
    codes = [int(enforce["exit_code"]), int(run_exit)]
    if emit_failed:
        codes.append(3)
    if 2 in codes:
        return 2, "FAIL"
    if 3 in codes:
        if run_exit == 3 and not emit_failed and int(enforce["exit_code"]) == 0:
            # The only 3 is a pure infra result from the provider run.
            if enforce.get("warnings") is not None:
                pass
        return 3, "FAIL"
    if 4 in codes:
        return 4, "FAIL"
    return 0, "PASS"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble CBE report and body evidence")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--package-id", choices=PACKAGE_IDS, default="cbs")
    parser.add_argument("--package-type", choices=PACKAGE_IDS, required=True)
    parser.add_argument("--package-version", required=True, metavar="vX.Y.Z")
    parser.add_argument("--tag", required=True, metavar="vX.Y.Z")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--exemptions")
    parser.add_argument("--workflows", action="store_true")
    parser.add_argument("--exclude-workflow", action="append")
    args = parser.parse_args(argv)

    try:
        inspection = load_and_inspect(
            args.manifest,
            package_type=args.package_type,
            package_version=args.package_version,
        )
        if inspection.errors:
            raise InputError("MANIFEST_INVALID", "manifest failed schema or semantic validation", details=inspection.errors)
        if inspection.gate_errors:
            first = inspection.gate_errors[0]
            raise GateError(first["code"], first["message"], details=inspection.gate_errors)
        if inspection.ruleset is None:
            raise InputError("MANIFEST_INVALID", "manifest did not produce a RuleSet")

        out_dir = Path(args.out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        root = Path(args.source_root).resolve()

        index, index_warnings = symbol_index.build_index(root)
        index_path = out_dir / "symbol-index.json"
        write_json_atomic(index_path, index)
        index_sha256 = sha256_json(index)

        enforce_args = SimpleNamespace(
            manifest=args.manifest,
            source_root=args.source_root,
            package_type=args.package_type,
            package_version=args.package_version,
            config=None,
            env_file=None,
            exemptions=args.exemptions,
            workflows=args.workflows,
            exclude_workflow=args.exclude_workflow,
            output=None,
        )
        enforce = enforce_no_bypass.run(enforce_args)

        outcome = execute(
            inspection,
            package_type=args.package_type,
            package_version=args.package_version,
            source_root=root,
            out_dir=out_dir,
            selected_providers=None,
            all_providers=True,
            exemptions_path=args.exemptions,
            cli_timeout=None,
            manifest_path=args.manifest,
        )

        run_report = {
            "providers": [provider.as_dict() for provider in outcome.providers],
            "rule_results": outcome.rule_results,
        }
        emit_error: CbeError | None = None
        sarif_abs: Path | None = out_dir / "cbe.sarif"
        try:
            sarif = build_sarif(
                ruleset=inspection.ruleset,
                run_report=run_report,
                provider_outputs=None,
                run_report_dir=out_dir,
            )
            write_json_atomic(sarif_abs, sarif)
        except CbeError as exc:
            emit_error = exc
            sarif_abs = None

        exit_code, gate_status = _combine_exit(enforce, outcome.exit_code, emit_error is not None)
        if exit_code == 3 and outcome.exit_code == 3 and outcome.gate_status == "SKIPPED_INFRA" and int(enforce["exit_code"]) == 0 and emit_error is None:
            gate_status = "SKIPPED_INFRA"
        warnings = list(enforce.get("warnings") or []) + list(index_warnings)
        warn_count = len(warnings)
        sarif_paths = ["cbe.sarif"] if sarif_abs is not None else []

        report: dict[str, Any] = {
            "schema_version": "1",
            "package_id": args.package_id,
            "producer_id": "cbe",
            "version": args.package_version,
            "tag": args.tag,
            "gate_status": gate_status,
            "exit_code": exit_code,
            "applicable_count": outcome.applicable_count,
            "skip_count": outcome.skip_count,
            "skip_ratio": outcome.skip_ratio,
            "blocking_skip": outcome.blocking_skip,
            "warn_count": warn_count,
            "rules_manifest_hash": inspection.manifest_sha256,
            "sarif_paths": sarif_paths,
            "evidence_sha256": "0" * 64,
        }
        report["evidence_sha256"] = evidence_hash(
            report,
            manifest_sha256=inspection.manifest_sha256,
            symbol_index_sha256=index_sha256,
            sarif_paths=[str(sarif_abs)] if sarif_abs is not None else [],
        )
        validate_report(report)
        body = body_section(report, warnings)
        report_path, body_path = write_report(report, body, out_dir)

        summary = {
            "schema_version": "1",
            "command": "cbe-gate",
            "ok": exit_code == 0,
            "exit_code": exit_code,
            "gate_status": gate_status,
            "report_path": str(report_path),
            "body_path": str(body_path),
            "sarif_paths": sarif_paths,
            "warn_count": warn_count,
            "warnings": warnings,
            "error": None
            if exit_code == 0
            else {
                "code": "CBE_GATE_FAILED",
                "message": "CBE gate did not pass",
                "details": [],
            },
        }
        print_json(summary)
        return exit_code
    except CbeError as exc:
        print_json(_error("cbe-gate", exc))
        return exc.exit_code
    except Exception as exc:  # noqa: BLE001 - boundary must emit JSON
        print_json(_error("cbe-gate", InputError("INTERNAL_ERROR", str(exc))))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

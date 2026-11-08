"""validate-manifest command implementation (P0-03)."""

from __future__ import annotations

import argparse
from typing import Any

from ..manifest import load_and_inspect

COMMAND = "validate-manifest"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    return None


def run(args: argparse.Namespace) -> dict[str, Any]:
    inspection = load_and_inspect(
        args.manifest,
        package_type=getattr(args, "package_type", None),
        package_version=getattr(args, "package_version", None),
    )

    exit_code = 2 if inspection.errors else 3 if inspection.gate_errors else 0
    gate_status = "PASS" if exit_code == 0 else "FAIL"

    result: dict[str, Any] = {
        "schema_version": "1",
        "command": COMMAND,
        "ok": exit_code == 0,
        "exit_code": exit_code,
        "gate_status": gate_status,
        "manifest_path": str(args.manifest),
        "manifest_sha256": inspection.manifest_sha256,
        "schema_version_seen": inspection.schema_version_seen,
        "pack_id": inspection.pack_id,
        "pack_version": inspection.pack_version,
        "rule_count": inspection.rule_count,
        "provider_count": inspection.provider_count,
        "blocking_rule_count": inspection.blocking_rule_count,
        "blocking_applicable_count": inspection.blocking_applicable_count,
        "advisory_rule_count": inspection.advisory_rule_count,
        "applicable_rule_count": inspection.applicable_rule_count,
        "not_applicable_rule_count": inspection.not_applicable_rule_count,
        "enabled_providers": inspection.enabled_providers,
        "errors": inspection.errors,
        "gate_errors": inspection.gate_errors,
        "warnings": inspection.warnings,
        "error": None,
    }

    if exit_code == 2:
        result["error"] = {
            "code": "MANIFEST_INVALID",
            "message": "manifest failed schema or semantic validation",
            "details": inspection.errors,
        }
    elif exit_code == 3:
        first = inspection.gate_errors[0]
        result["error"] = {
            "code": first["code"],
            "message": first["message"],
            "details": inspection.gate_errors,
        }

    return result

"""run-provider command implementation (P0-05)."""

from __future__ import annotations

import argparse
from typing import Any

from ..manifest import load_and_inspect
from ..providers import execute

COMMAND = "run-provider"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    return None


def run(args: argparse.Namespace) -> dict[str, Any]:
    inspection = load_and_inspect(
        args.manifest,
        package_type=args.package_type,
        package_version=args.package_version,
    )
    outcome = execute(
        inspection,
        package_type=args.package_type,
        package_version=args.package_version,
        source_root=args.source_root,
        out_dir=args.out_dir,
        selected_providers=args.provider,
        all_providers=args.all,
        exemptions_path=args.exemptions,
        cli_timeout=args.timeout,
        manifest_path=args.manifest,
    )
    return {
        "schema_version": "1",
        "command": COMMAND,
        "ok": outcome.exit_code == 0,
        "exit_code": outcome.exit_code,
        "gate_status": outcome.gate_status,
        "package_type": args.package_type,
        "package_version": args.package_version,
        "source_root": str(args.source_root),
        "providers": [provider.as_dict() for provider in outcome.providers],
        "rule_results": outcome.rule_results,
        "applicable_count": outcome.applicable_count,
        "skip_count": outcome.skip_count,
        "not_applicable_count": outcome.not_applicable_count,
        "skip_ratio": outcome.skip_ratio,
        "blocking_skip": outcome.blocking_skip,
        "warn_count": outcome.warn_count,
        "sarif_paths": outcome.sarif_paths,
        "json_paths": outcome.json_paths,
        "error": outcome.error,
        "warnings": [],
    }

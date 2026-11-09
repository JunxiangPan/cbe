#!/usr/bin/env python3
"""F4 baseline selector for CBE RC evidence."""

from __future__ import annotations

import argparse
import json
import sys

from cbe.baseline import load_releases, select_baseline
from cbe.errors import CbeError
from cbe.jsonio import print_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--releases", required=True)
    parser.add_argument("--current-version", required=True)
    parser.add_argument("--baseline")
    args = parser.parse_args(argv)
    try:
        releases = load_releases(args.releases)
        baseline = select_baseline(
            releases,
            current_version=args.current_version,
            explicit=args.baseline,
        )
        print_json(
            {
                "schema_version": "1",
                "command": "cbe-baseline",
                "ok": True,
                "exit_code": 0,
                "gate_status": "PASS",
                "current_version": args.current_version,
                "baseline": baseline.as_dict(),
                "error": None,
                "warnings": [],
            }
        )
        return 0
    except CbeError as exc:
        print_json(
            {
                "schema_version": "1",
                "command": "cbe-baseline",
                "ok": False,
                "exit_code": exc.exit_code,
                "gate_status": exc.gate_status,
                "error": {"code": exc.code, "message": exc.message, "details": exc.details},
                "warnings": [],
            }
        )
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())

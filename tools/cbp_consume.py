#!/usr/bin/env python3
"""Consume a CBE SARIF with CBP's report aggregator and print JSON findings.

Run this with the CBP interpreter you want to prove:
  <cbp-python> tools/cbp_consume.py --root out --report cbe.sarif
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cbp.report_aggregator import aggregate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    findings = aggregate(Path(args.root), [args.report])
    print(json.dumps(findings, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

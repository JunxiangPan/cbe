#!/usr/bin/env python3
"""F5/F6 release-train component report and CBP 1.2.0 manifest compatibility."""

from __future__ import annotations

import argparse
import json

from cbe.cbp_compat import validate_cbp_manifest
from cbe.errors import CbeError
from cbe.jsonio import print_json
from cbe.release_train import body_section, classify, components, load_release_train, status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-train", required=True)
    parser.add_argument("--cbp-manifest")
    parser.add_argument("--expected-repository")
    args = parser.parse_args(argv)
    try:
        data = load_release_train(args.release_train)
        component_list = components(data)
        not_uploaded, evidence_absent, infra = classify(component_list)
        cbp_problems: list[str] = []
        if args.cbp_manifest:
            manifest = json.loads(open(args.cbp_manifest, encoding="utf-8").read())
            cbp_problems = validate_cbp_manifest(
                manifest, expected_repository=args.expected_repository
            )
            if cbp_problems:
                print_json(
                    {
                        "schema_version": "1",
                        "command": "cbe-release-train",
                        "ok": False,
                        "exit_code": 2,
                        "gate_status": "FAIL",
                        "components": [item.as_dict() for item in component_list],
                        "not_uploaded": not_uploaded,
                        "evidence_absent": evidence_absent,
                        "infrastructure_failures": infra,
                        "skip_count": 0,
                        "applicable_count": 0,
                        "skip_ratio": 0.0,
                        "counted_in_skip_denominator": False,
                        "body_section_md": body_section(component_list),
                        "error": {
                            "code": "CBP_MANIFEST_INVALID",
                            "message": "; ".join(cbp_problems),
                            "details": cbp_problems,
                        },
                        "warnings": [],
                    }
                )
                return 2
        exit_code, gate_status = status(component_list)
        body = body_section(component_list)
        print_json(
            {
                "schema_version": "1",
                "command": "cbe-release-train",
                "ok": exit_code == 0,
                "exit_code": exit_code,
                "gate_status": gate_status,
                "components": [item.as_dict() for item in component_list],
                "not_uploaded": not_uploaded,
                "evidence_absent": evidence_absent,
                "infrastructure_failures": infra,
                "skip_count": 0,
                "applicable_count": 0,
                "skip_ratio": 0.0,
                "counted_in_skip_denominator": False,
                "cbp_manifest_checked": bool(args.cbp_manifest),
                "body_section_md": body,
                "error": None
                if exit_code == 0
                else {
                    "code": gate_status,
                    "message": "release train has an infrastructure or precondition failure",
                    "details": [],
                },
                "warnings": [],
            }
        )
        return exit_code
    except CbeError as exc:
        print_json(
            {
                "schema_version": "1",
                "command": "cbe-release-train",
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

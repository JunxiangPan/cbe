"""CBE command-line skeleton.

The first commit freezes the interface: five subcommands, `--help` on every
command, one JSON object on stdout, and the contract exit codes 0/2/3/4.
Command bodies are implemented in the next commit.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from typing import Any

from . import __version__
from .commands import (
    emit_sarif,
    enforce_no_bypass,
    run_provider,
    symbol_index,
    validate_manifest,
)
from .errors import (
    EXIT_GATE,
    EXIT_INPUT,
    EXIT_PASS,
    EXIT_SKIP,
    CbeError,
    InternalError,
    InputError,
    PASS,
    FAIL,
    PRECONDITION_FAIL,
    SKIPPED_INFRA,
)
from .jsonio import print_json, write_json_atomic

COMMANDS = {
    "validate-manifest": validate_manifest,
    "run-provider": run_provider,
    "symbol-index": symbol_index,
    "enforce-no-bypass": enforce_no_bypass,
    "emit-sarif": emit_sarif,
}

EXIT_EPILOG = (
    "exit codes: 0 PASS; 2 input/format error; "
    "3 gate failure or SKIPPED_INFRA; 4 SKIP ratio above 20%."
)

VALID_GATE_STATUSES = {PASS, FAIL, SKIPPED_INFRA, PRECONDITION_FAIL}


def base_envelope(command: str, exit_code: int, gate_status: str) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "command": command,
        "ok": exit_code == EXIT_PASS,
        "exit_code": exit_code,
        "gate_status": gate_status,
        "error": None,
        "warnings": [],
    }


def error_envelope(command: str, exc: CbeError) -> dict[str, Any]:
    envelope = base_envelope(command, exc.exit_code, exc.gate_status)
    envelope["error"] = {
        "code": exc.code,
        "message": exc.message,
        "details": exc.details,
    }
    envelope["warnings"] = exc.warnings
    return envelope


class JsonArgumentParser(argparse.ArgumentParser):
    """Argparse that never prints usage text for errors.

    Usage errors still exit 2, but stdout receives a single JSON object so a CI
    parser never has to grep stderr.
    """

    def error(self, message: str) -> None:  # type: ignore[override]
        command = self.prog.rsplit(" ", 1)[-1] if " " in self.prog else "cbe"
        envelope = base_envelope(command, EXIT_INPUT, FAIL)
        envelope["error"] = {
            "code": "INPUT_INVALID",
            "message": message,
            "details": [],
        }
        print_json(envelope)
        raise SystemExit(EXIT_INPUT)


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON (default; accepted for compatibility)",
    )
    parser.add_argument(
        "--format",
        choices=["json"],
        default="json",
        help="output format; only json is supported",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="also write the JSON response to PATH atomically",
    )


def _add_package_options(parser: argparse.ArgumentParser, *, required: bool = True) -> None:
    parser.add_argument(
        "--package-type",
        required=required,
        choices=["cbs", "cbe", "cbp", "cbm", "cbc", "cbg"],
        help="target package type",
    )
    parser.add_argument(
        "--package-version",
        required=required,
        metavar="vX.Y.Z",
        help="target package version",
    )


def build_parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(
        prog="cbe",
        description="Cyber-Butler Enforcement gate",
        epilog=EXIT_EPILOG,
    )
    parser.add_argument("--version", action="version", version=f"cbe {__version__}")

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=JsonArgumentParser,
    )

    validate_parser = subparsers.add_parser(
        "validate-manifest",
        help="validate a CBE rule-pack manifest",
        description="Validate a rule-pack manifest against schema v1 and its semantic rules.",
        epilog=EXIT_EPILOG,
    )
    _add_common_options(validate_parser)
    validate_parser.add_argument("--manifest", required=True, metavar="PATH")
    validate_parser.add_argument(
        "--package-type",
        choices=["cbs", "cbe", "cbp", "cbm", "cbc", "cbg"],
        help="optional applicability context",
    )
    validate_parser.add_argument(
        "--package-version",
        metavar="vX.Y.Z",
        help="optional applicability context; requires --package-type",
    )
    validate_parser.set_defaults(_handler=validate_manifest.run)

    run_parser = subparsers.add_parser(
        "run-provider",
        help="execute enabled providers and verify their artifacts",
        description="Run providers declared by the manifest and verify SARIF/JSON output.",
        epilog=EXIT_EPILOG,
    )
    _add_common_options(run_parser)
    run_parser.add_argument("--manifest", required=True, metavar="PATH")
    _add_package_options(run_parser)
    run_parser.add_argument("--source-root", required=True, metavar="PATH")
    run_parser.add_argument("--out-dir", required=True, metavar="PATH")
    provider_group = run_parser.add_mutually_exclusive_group(required=True)
    provider_group.add_argument("--all", action="store_true", help="run every enabled provider")
    provider_group.add_argument(
        "--provider",
        action="append",
        metavar="ID",
        help="run one provider id; repeatable; unselected applicable rules count as SKIPPED",
    )
    run_parser.add_argument("--exemptions", metavar="PATH")
    run_parser.add_argument("--timeout", type=int, metavar="SECONDS")
    run_parser.set_defaults(_handler=run_provider.run)

    symbol_parser = subparsers.add_parser(
        "symbol-index",
        help="build a deterministic symbol index",
        description="Build a deterministic source symbol index used as coverage evidence.",
        epilog=EXIT_EPILOG,
    )
    _add_common_options(symbol_parser)
    symbol_parser.add_argument("--source-root", required=True, metavar="PATH")
    symbol_parser.add_argument("--out", required=True, metavar="PATH")
    symbol_parser.add_argument("--include", action="append", metavar="GLOB")
    symbol_parser.add_argument("--exclude", action="append", metavar="GLOB")
    symbol_parser.add_argument("--language", action="append", metavar="LANG")
    symbol_parser.set_defaults(_handler=symbol_index.run)

    bypass_parser = subparsers.add_parser(
        "enforce-no-bypass",
        help="reject attempts to disable rules outside explicit exemptions",
        description="Scan config, comments, environment, and target workflows for rule-disable attempts.",
        epilog=EXIT_EPILOG,
    )
    _add_common_options(bypass_parser)
    bypass_parser.add_argument("--manifest", required=True, metavar="PATH")
    bypass_parser.add_argument("--source-root", required=True, metavar="PATH")
    _add_package_options(bypass_parser)
    bypass_parser.add_argument("--config", action="append", metavar="PATH")
    bypass_parser.add_argument("--env-file", action="append", metavar="PATH")
    bypass_parser.add_argument("--exemptions", metavar="PATH")
    bypass_parser.add_argument(
        "--workflows",
        action="store_true",
        help="scan target repository .github/workflows; CBE's own workflow must be excluded explicitly",
    )
    bypass_parser.add_argument(
        "--exclude-workflow",
        action="append",
        metavar="GLOB",
        help="workflow path/glob to exclude; repeatable",
    )
    bypass_parser.set_defaults(_handler=enforce_no_bypass.run)

    sarif_parser = subparsers.add_parser(
        "emit-sarif",
        help="merge provider evidence into SARIF 2.1.0",
        description="Map provider findings to CBE rule ids and emit a valid SARIF 2.1.0 log.",
        epilog=EXIT_EPILOG,
    )
    _add_common_options(sarif_parser)
    sarif_parser.add_argument("--manifest", required=True, metavar="PATH")
    sarif_parser.add_argument("--run-report", required=True, metavar="PATH")
    sarif_parser.add_argument("--source-root", required=True, metavar="PATH")
    sarif_parser.add_argument("--out", required=True, metavar="PATH")
    sarif_parser.add_argument("--provider-output", action="append", metavar="PATH")
    sarif_parser.set_defaults(_handler=emit_sarif.run)

    return parser


def _normalize_result(command: str, result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise InternalError(f"{command} handler did not return an object")

    envelope = base_envelope(
        command,
        int(result.get("exit_code", EXIT_GATE)),
        str(result.get("gate_status", FAIL)),
    )
    envelope.update(result)
    envelope["schema_version"] = "1"
    envelope["command"] = command
    envelope["warnings"] = list(envelope.get("warnings") or [])

    exit_code = envelope["exit_code"]
    gate_status = envelope["gate_status"]
    if exit_code not in {EXIT_PASS, EXIT_INPUT, EXIT_GATE, EXIT_SKIP}:
        raise InternalError(f"invalid exit_code from {command}: {exit_code}")
    if gate_status not in VALID_GATE_STATUSES:
        raise InternalError(f"invalid gate_status from {command}: {gate_status}")
    if exit_code == EXIT_PASS and gate_status != PASS:
        raise InternalError("exit 0 requires gate_status PASS")
    if exit_code == EXIT_INPUT and gate_status == PASS:
        raise InternalError("exit 2 cannot be PASS")
    if exit_code == EXIT_SKIP and gate_status != FAIL:
        raise InternalError("exit 4 requires gate_status FAIL")
    if exit_code == EXIT_GATE and gate_status == PASS:
        raise InternalError("exit 3 cannot be PASS")

    if exit_code == EXIT_PASS:
        envelope["error"] = None
        envelope["ok"] = True
    else:
        envelope["ok"] = False
        if envelope.get("error") is None:
            envelope["error"] = {
                "code": "GATE_FAILED",
                "message": f"{command} failed",
                "details": [],
            }
    return envelope


def _emit(result: dict[str, Any], output: str | None) -> int:
    if output:
        try:
            write_json_atomic(output, result)
        except OSError as exc:
            failed = error_envelope(
                str(result.get("command", "cbe")),
                InputError("OUTPUT_WRITE_FAILED", f"cannot write {output}: {exc}"),
            )
            print_json(failed)
            return EXIT_INPUT
    print_json(result)
    return int(result["exit_code"])


def _validate_args(args: argparse.Namespace) -> None:
    command = str(args.command)
    if command == "validate-manifest":
        has_type = bool(getattr(args, "package_type", None))
        has_version = bool(getattr(args, "package_version", None))
        if has_type != has_version:
            raise InputError(
                "PACKAGE_CONTEXT_INCOMPLETE",
                "--package-type and --package-version must be supplied together",
            )
    if command in {"run-provider", "enforce-no-bypass"}:
        timeout = getattr(args, "timeout", None)
        if timeout is not None and timeout < 1:
            raise InputError("TIMEOUT_INVALID", "--timeout must be a positive integer")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = str(args.command)
    output = getattr(args, "output", None)

    try:
        _validate_args(args)
        result = _normalize_result(command, args._handler(args))
    except CbeError as exc:
        result = error_envelope(command, exc)
    except KeyboardInterrupt:
        result = error_envelope(command, InternalError("interrupted"))
    except Exception as exc:  # noqa: BLE001 - the boundary must always emit JSON
        if os.environ.get("CBE_DEBUG") == "1":
            traceback.print_exc(file=sys.stderr)
        result = error_envelope(command, InternalError(str(exc)))

    return _emit(result, output)


if __name__ == "__main__":
    raise SystemExit(main())

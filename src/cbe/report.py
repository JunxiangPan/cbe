"""CBE report assembly and Release-body Section B helper."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .errors import InputError
from .jsonio import sha256_file, sha256_json, write_json_atomic

REPORT_SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "v1.7" / "cbe-report.schema.json"


def warning_counts(warnings: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for warning in warnings:
        code = warning.get("code") if isinstance(warning, dict) else None
        if isinstance(code, str) and code:
            counts[code] += 1
    return dict(sorted(counts.items()))


def body_section(report: dict[str, Any], warnings: list[dict[str, Any]]) -> str:
    counts = warning_counts(warnings)
    lines = [
        "## Section A: Gate evidence (blocking)",
        "",
        f"- package_id: `{report['package_id']}`",
        f"- producer_id: `{report['producer_id']}`",
        f"- version: `{report['version']}`",
        f"- tag: `{report['tag']}`",
        f"- gate_status: **{report['gate_status']}**",
        f"- applicable_count: {report['applicable_count']}",
        f"- skip_count: {report['skip_count']}",
        f"- skip_ratio: {report['skip_ratio']:.2%}",
        f"- blocking_skip: {str(report['blocking_skip']).lower()}",
        f"- rules_manifest_hash: `{report['rules_manifest_hash']}`",
        "",
        "## Section B: AI audit (non-blocking)",
        "",
        f"- warn_count: {report['warn_count']}",
    ]
    if counts:
        for code, count in counts.items():
            lines.append(f"- `{code}`: {count}")
    else:
        lines.append("- warning types: none")
    lines.append("")
    lines.append("Section B is audit-only; it does not replace Section A.")
    return "\n".join(lines) + "\n"


def validate_report(report: dict[str, Any]) -> None:
    try:
        schema = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InputError("REPORT_SCHEMA_UNAVAILABLE", f"cannot read report schema: {exc}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(report), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        raise InputError("REPORT_INVALID", f"report schema error at {list(first.path)}: {first.message}")


def evidence_hash(report: dict[str, Any], *, manifest_sha256: str, symbol_index_sha256: str, sarif_paths: list[str]) -> str:
    payload = dict(report)
    payload.pop("evidence_sha256", None)
    payload["manifest_sha256"] = manifest_sha256
    payload["symbol_index_sha256"] = symbol_index_sha256
    payload["sarif"] = [
        {"path": path, "sha256": sha256_file(path)} if Path(path).is_file() else {"path": path, "sha256": None}
        for path in sarif_paths
    ]
    return sha256_json(payload)


def write_report(report: dict[str, Any], body: str, out_dir: Path) -> tuple[Path, Path]:
    report_path = out_dir / "cbe-report.json"
    body_path = out_dir / "cbe-body-section.md"
    write_json_atomic(report_path, report)
    body_path.write_text(body, encoding="utf-8", newline="\n")
    return report_path, body_path

"""Unit tests for CBE report assembly (B-32)."""

from __future__ import annotations

from pathlib import Path

from cbe.errors import InputError
from cbe.report import body_section, evidence_hash, validate_report, warning_counts, write_report


def _report() -> dict:
    return {
        "schema_version": "1",
        "package_id": "cbe",
        "producer_id": "cbe",
        "version": "v0.1.0",
        "tag": "v0.1.0",
        "gate_status": "PASS",
        "exit_code": 0,
        "applicable_count": 2,
        "skip_count": 0,
        "skip_ratio": 0.0,
        "blocking_skip": False,
        "warn_count": 1,
        "rules_manifest_hash": "a" * 64,
        "sarif_paths": [],
        "evidence_sha256": "b" * 64,
    }


def test_warning_counts_and_body_section() -> None:
    warnings = [
        {"code": "UNVERIFIABLE_CONDITION"},
        {"code": "UNVERIFIABLE_CONDITION"},
        {"code": "UNVERIFIABLE_NEEDS_CHAIN"},
    ]
    assert warning_counts(warnings) == {
        "UNVERIFIABLE_CONDITION": 2,
        "UNVERIFIABLE_NEEDS_CHAIN": 1,
    }
    body = body_section(_report(), warnings)
    assert "## Section B: AI audit" in body
    assert "warn_count: 1" in body
    assert "`UNVERIFIABLE_CONDITION`: 2" in body


def test_report_schema_accepts_valid_and_rejects_missing() -> None:
    report = _report()
    validate_report(report)
    broken = dict(report)
    del broken["warn_count"]
    try:
        validate_report(broken)
    except InputError as exc:
        assert exc.code == "REPORT_INVALID"
    else:
        raise AssertionError("missing warn_count should fail")


def test_evidence_hash_is_deterministic_and_64_hex(tmp_path: Path) -> None:
    report = _report()
    sarif = tmp_path / "a.sarif"
    sarif.write_text("{}", encoding="utf-8")
    first = evidence_hash(report, manifest_sha256="c" * 64, symbol_index_sha256="d" * 64, sarif_paths=[str(sarif)])
    second = evidence_hash(report, manifest_sha256="c" * 64, symbol_index_sha256="d" * 64, sarif_paths=[str(sarif)])
    assert first == second
    assert len(first) == 64
    assert all(char in "0123456789abcdef" for char in first)


def test_write_report_writes_both_files(tmp_path: Path) -> None:
    report = _report()
    report_path, body_path = write_report(report, "body\n", tmp_path)
    assert report_path.is_file()
    assert body_path.read_text(encoding="utf-8") == "body\n"

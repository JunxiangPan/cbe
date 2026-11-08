"""Unit tests for the shared exemption parser."""

from __future__ import annotations

from pathlib import Path

from cbe.exemptions import parse_exemptions
from cbe.manifest import load_and_inspect

FIXTURES = Path(__file__).resolve().parents[1] / "e2e" / "fixtures"


def _context():
    inspection = load_and_inspect(
        FIXTURES / "manifests" / "valid_full.json",
        package_type="cbs",
        package_version="v0.1.0",
    )
    assert inspection.ruleset is not None
    applicable = {
        item["rule_id"]
        for item in inspection.applicable_rules
        if item.get("status") == "APPLICABLE"
    }
    return inspection.ruleset, applicable


def test_advisory_exemption_is_counted() -> None:
    ruleset, applicable = _context()
    exemptions, errors = parse_exemptions(str(FIXTURES / "exemptions" / "valid.txt"), ruleset, applicable)
    assert errors == []
    assert len(exemptions) == 1
    assert exemptions[0].rule_id == "CBE-QUALITY-001"
    assert exemptions[0].counted is True


def test_blocking_exemption_is_not_counted() -> None:
    ruleset, applicable = _context()
    exemptions, errors = parse_exemptions(str(FIXTURES / "exemptions" / "blocking.txt"), ruleset, applicable)
    assert errors == []
    assert exemptions[0].blocking is True
    assert exemptions[0].counted is False


def test_unknown_rule_and_missing_reason_are_input_errors() -> None:
    ruleset, applicable = _context()
    _, unknown = parse_exemptions(str(FIXTURES / "exemptions" / "unknown_rule.txt"), ruleset, applicable)
    assert unknown[0]["code"] == "EXEMPTION_UNKNOWN_RULE"
    _, missing = parse_exemptions(str(FIXTURES / "exemptions" / "missing_reason.txt"), ruleset, applicable)
    assert missing[0]["code"] == "EXEMPTION_REASON_MISSING"

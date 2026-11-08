"""CBE-03: invalid manifests through the CLI."""

from __future__ import annotations

import pytest

from _util import fixture, run_cbe


@pytest.mark.parametrize(
    "name,error_code",
    [
        ("invalid_missing_rule_id.json", "required"),
        ("invalid_missing_title.json", "required"),
        ("invalid_missing_severity.json", "required"),
        ("invalid_missing_gate.json", "required"),
        ("invalid_missing_provider.json", "required"),
        ("invalid_missing_version_constraint.json", "required"),
        ("invalid_missing_schema_version.json", "required"),
        ("invalid_rule_id_cbp.json", "pattern"),
        ("invalid_rule_id_lower.json", "pattern"),
        ("invalid_severity.json", "enum"),
        ("invalid_gate.json", "enum"),
        ("invalid_version_constraint.json", "pattern"),
        ("invalid_schema_version.json", "const"),
        ("invalid_pack_id.json", "pattern"),
        ("additional_property.json", "additionalProperties"),
    ],
)
def test_schema_invalid_manifest(name: str, error_code: str) -> None:
    code, data, _, _ = run_cbe("validate-manifest", "--manifest", fixture("manifests", name))
    assert code == 2
    assert data is not None
    assert data["gate_status"] == "FAIL"
    assert any(error["code"] == error_code for error in data["errors"])


@pytest.mark.parametrize(
    "name,error_code",
    [
        ("duplicate_rule_id.json", "DUPLICATE_RULE_ID"),
        ("blocking_warning.json", "GATE_SEVERITY_MISMATCH"),
        ("blocking_partial_scope.json", "BLOCKING_RULE_PARTIAL_SCOPE"),
        ("invalid_provider.json", "UNKNOWN_PROVIDER"),
    ],
)
def test_semantic_invalid_manifest(name: str, error_code: str) -> None:
    code, data, _, _ = run_cbe("validate-manifest", "--manifest", fixture("manifests", name))
    assert code == 2
    assert data is not None
    assert any(error["code"] == error_code for error in data["errors"])


def test_zero_rules_is_gate_failure() -> None:
    code, data, _, _ = run_cbe(
        "validate-manifest",
        "--manifest",
        fixture("manifests", "zero_rules.json"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
    )
    assert code == 3
    assert data is not None
    assert data["gate_status"] == "FAIL"
    assert data["error"]["code"] == "NO_RULES"


def test_blocking_rule_not_applicable_is_gate_failure() -> None:
    code, data, _, _ = run_cbe(
        "validate-manifest",
        "--manifest",
        fixture("manifests", "blocking_version_not_applicable.json"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
    )
    assert code == 3
    assert data is not None
    assert data["blocking_applicable_count"] == 0
    assert data["error"]["code"] == "BLOCKING_RULE_NOT_APPLICABLE"

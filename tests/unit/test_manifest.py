"""Manifest validator unit tests (P0-03)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cbe.cli import main
from cbe.manifest import Version, constraint_matches, parse_constraint

FIXTURES = Path(__file__).resolve().parents[1] / "e2e" / "fixtures" / "manifests"


def run_cli(capsys, *args: str) -> tuple[int, dict]:
    code = main(list(args))
    captured = capsys.readouterr()
    return code, json.loads(captured.out)


def manifest(name: str) -> str:
    return str(FIXTURES / name)


def test_valid_full_manifest(capsys) -> None:
    code, data = run_cli(
        capsys,
        "validate-manifest",
        "--manifest",
        manifest("valid_full.json"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
    )
    assert code == 0
    assert data["gate_status"] == "PASS"
    assert data["rule_count"] == 3
    assert data["provider_count"] == 2
    assert data["blocking_rule_count"] == 1
    assert data["blocking_applicable_count"] == 1
    assert data["advisory_rule_count"] == 2
    assert data["applicable_rule_count"] == 3
    assert data["not_applicable_rule_count"] == 0
    assert data["enabled_providers"] == ["builtin-manifest", "gitleaks"]
    assert data["errors"] == []
    assert data["gate_errors"] == []


def test_valid_full_cbe_context_has_one_not_applicable(capsys) -> None:
    code, data = run_cli(
        capsys,
        "validate-manifest",
        "--manifest",
        manifest("valid_full.json"),
        "--package-type",
        "cbe",
        "--package-version",
        "v0.1.0",
    )
    assert code == 0
    assert data["blocking_rule_count"] == data["blocking_applicable_count"] == 1
    assert data["applicable_rule_count"] == 2
    assert data["not_applicable_rule_count"] == 1


def test_crlf_and_lf_have_the_same_hash(capsys) -> None:
    _, lf = run_cli(capsys, "validate-manifest", "--manifest", manifest("valid_full.json"))
    _, crlf = run_cli(capsys, "validate-manifest", "--manifest", manifest("valid_full_crlf.json"))
    assert lf["manifest_sha256"] == crlf["manifest_sha256"]


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
def test_schema_invalid_manifest(capsys, name: str, error_code: str) -> None:
    code, data = run_cli(capsys, "validate-manifest", "--manifest", manifest(name))
    assert code == 2
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
def test_semantic_invalid_manifest(capsys, name: str, error_code: str) -> None:
    code, data = run_cli(capsys, "validate-manifest", "--manifest", manifest(name))
    assert code == 2
    assert any(error["code"] == error_code for error in data["errors"])


def test_zero_rules_is_gate_failure(capsys) -> None:
    code, data = run_cli(
        capsys,
        "validate-manifest",
        "--manifest",
        manifest("zero_rules.json"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
    )
    assert code == 3
    assert data["gate_status"] == "FAIL"
    assert data["error"]["code"] == "NO_RULES"
    assert data["gate_errors"][0]["code"] == "NO_RULES"


def test_zero_applicable_rules_is_gate_failure(capsys) -> None:
    code, data = run_cli(
        capsys,
        "validate-manifest",
        "--manifest",
        manifest("valid_minimal.json"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
    )
    assert code == 3
    assert data["error"]["code"] == "NO_APPLICABLE_CHECKS"


def test_blocking_rule_not_applicable_is_gate_failure(capsys) -> None:
    code, data = run_cli(
        capsys,
        "validate-manifest",
        "--manifest",
        manifest("blocking_version_not_applicable.json"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
    )
    assert code == 3
    assert data["blocking_rule_count"] == 1
    assert data["blocking_applicable_count"] == 0
    assert data["applicable_rule_count"] == 1
    assert data["not_applicable_rule_count"] == 1
    assert data["error"]["code"] == "BLOCKING_RULE_NOT_APPLICABLE"
    assert data["gate_errors"][0]["code"] == "BLOCKING_RULE_NOT_APPLICABLE"


def test_package_context_must_be_paired(capsys) -> None:
    code, data = run_cli(
        capsys,
        "validate-manifest",
        "--manifest",
        manifest("valid_minimal.json"),
        "--package-type",
        "cbe",
    )
    assert code == 2
    assert data["error"]["code"] == "PACKAGE_CONTEXT_INCOMPLETE"


def test_duplicate_json_keys_rejected(capsys, tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema_version": "1", "schema_version": "1"}', encoding="utf-8")
    code, data = run_cli(capsys, "validate-manifest", "--manifest", str(path))
    assert code == 2
    assert data["error"]["code"] == "JSON_INVALID"
    assert "duplicate" in data["error"]["message"]


def test_bom_rejected(capsys, tmp_path: Path) -> None:
    path = tmp_path / "bom.json"
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps({"schema_version": "1"}).encode("utf-8"))
    code, data = run_cli(capsys, "validate-manifest", "--manifest", str(path))
    assert code == 2
    assert data["error"]["code"] == "BOM_NOT_ALLOWED"


def test_output_writes_atomically(capsys, tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    code, data = run_cli(
        capsys,
        "validate-manifest",
        "--manifest",
        manifest("valid_minimal.json"),
        "--output",
        str(output),
    )
    assert code == 0
    assert json.loads(output.read_text(encoding="utf-8")) == data


def test_version_ordering_and_constraints() -> None:
    assert Version.parse("1.0.0-rc.1") < Version.parse("1.0.0")
    assert Version.parse("1.0.0-alpha") < Version.parse("1.0.0-beta")
    assert Version.parse("1.0.0") < Version.parse("1.0.1")

    constraint = parse_constraint(">=0.1.0 <2.0.0")
    assert constraint_matches(Version.parse("0.1.0"), constraint)
    assert constraint_matches(Version.parse("1.9.9"), constraint)
    assert not constraint_matches(Version.parse("2.0.0"), constraint)
    assert not constraint_matches(Version.parse("0.0.9"), constraint)

    star = parse_constraint("*")
    assert constraint_matches(Version.parse("99.0.0"), star)


@pytest.mark.parametrize("value", ["^0.1", ">=0.1", "1.0.0", ">=1.0.0 || <2.0.0"])
def test_invalid_constraints_raise(value: str) -> None:
    with pytest.raises(ValueError):
        parse_constraint(value)

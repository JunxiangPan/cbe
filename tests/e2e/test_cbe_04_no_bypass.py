"""CBE-04: no-bypass enforcement and exemption semantics."""

from __future__ import annotations

from pathlib import Path

import pytest

from _util import fixture, run_cbe

MANIFEST = fixture("manifests", "valid_full.json")
BASE = [
    "enforce-no-bypass",
    "--manifest",
    MANIFEST,
    "--package-type",
    "cbs",
    "--package-version",
    "v0.1.0",
]


def test_config_disable_attempts_fail() -> None:
    code, data, _, _ = run_cbe(*BASE, "--source-root", fixture("bypass", "config"))
    assert code == 3
    assert data is not None
    assert data["gate_status"] == "FAIL"
    assert len(data["bypass_attempts"]) == 2
    assert {attempt["kind"] for attempt in data["bypass_attempts"]} == {"config"}


def test_comment_disable_attempts_fail() -> None:
    code, data, _, _ = run_cbe(*BASE, "--source-root", fixture("bypass", "comments"))
    assert code == 3
    assert data is not None
    assert len(data["bypass_attempts"]) == 3
    assert {attempt["kind"] for attempt in data["bypass_attempts"]} == {"comment"}


def test_env_file_disable_attempt_fails() -> None:
    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--env-file",
        fixture("bypass", "env", "disable.env"),
    )
    assert code == 3
    assert data is not None
    assert len(data["bypass_attempts"]) == 1
    assert data["bypass_attempts"][0]["kind"] == "env"
    assert "CBE_DISABLE_RULE" in data["bypass_attempts"][0]["evidence"]


def test_process_env_disable_attempt_fails() -> None:
    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        fixture("bypass", "clean-repo"),
        env={"CBE_DISABLE_RULE": "1"},
    )
    assert code == 3
    assert data is not None
    assert any(attempt["path"] == "<process-env>" for attempt in data["bypass_attempts"])


def test_workflow_disable_attempt_fails() -> None:
    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        fixture("bypass", "workflow-repo"),
        "--workflows",
    )
    assert code == 3
    assert data is not None
    assert len(data["bypass_attempts"]) == 1
    assert data["bypass_attempts"][0]["kind"] == "workflow"
    assert data["scanned"]["workflows"] == 1


@pytest.mark.parametrize(
    "repo",
    [
        "workflow-if-false-repo",
        "workflow-needs-repo",
        "workflow-commented-repo",
    ],
)
def test_workflow_skips_cbe_gate(repo: str) -> None:
    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        fixture("bypass", repo),
        "--workflows",
    )
    assert code == 3
    assert data is not None
    assert data["gate_status"] == "FAIL"
    assert any(
        attempt["reason"] == "WORKFLOW_SKIPS_CBE_GATE" for attempt in data["bypass_attempts"]
    ), data["bypass_attempts"]


def test_reachable_cbe_gate_passes() -> None:
    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        fixture("bypass", "reachable-repo"),
        "--workflows",
    )
    assert code == 0
    assert data is not None
    assert data["gate_status"] == "PASS"
    assert data["bypass_attempts"] == []
    assert data["scanned"]["workflows"] == 1


@pytest.mark.parametrize(
    "repo,warning_code",
    [
        ("workflow-dynamic-if-repo", "UNVERIFIABLE_CONDITION"),
        ("workflow-dynamic-needs-repo", "UNVERIFIABLE_NEEDS_CHAIN"),
        ("workflow-env-call-repo", "UNVERIFIABLE_CONDITION"),
        ("workflow-dynamic-comparison-repo", "UNVERIFIABLE_CONDITION"),
    ],
)
def test_unverifiable_workflow_conditions_warn_without_failing(repo: str, warning_code: str) -> None:
    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        fixture("bypass", repo),
        "--workflows",
    )
    assert code == 0
    assert data is not None
    assert data["gate_status"] == "PASS"
    assert data["bypass_attempts"] == []
    assert any(warning["code"] == warning_code for warning in data["warnings"])
    assert data["warn_count"] == len(data["warnings"])


@pytest.mark.parametrize(
    "repo",
    [
        "workflow-negated-true-repo",
        "workflow-comparison-false-repo",
    ],
)
def test_statically_false_expressions_are_gate_skips(repo: str) -> None:
    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        fixture("bypass", repo),
        "--workflows",
    )
    assert code == 3
    assert data is not None
    assert any(
        attempt["reason"] == "WORKFLOW_SKIPS_CBE_GATE" for attempt in data["bypass_attempts"]
    )


def test_statically_true_gate_condition_passes() -> None:
    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        fixture("bypass", "workflow-static-true-repo"),
        "--workflows",
    )
    assert code == 0
    assert data is not None
    assert data["bypass_attempts"] == []
    assert data["warnings"] == []


def test_clean_repository_passes() -> None:
    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--workflows",
    )
    assert code == 0
    assert data is not None
    assert data["gate_status"] == "PASS"
    assert data["bypass_attempts"] == []
    assert data["scanned"]["workflows"] == 1


def test_blocking_exemption_is_a_gate_failure() -> None:
    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--exemptions",
        fixture("exemptions", "blocking.txt"),
    )
    assert code == 3
    assert data is not None
    assert data["blocking_skip"] is True
    assert data["error"]["code"] == "BLOCKING_SKIP"


def test_unknown_exemption_rule_is_input_error() -> None:
    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--exemptions",
        fixture("exemptions", "unknown_rule.txt"),
    )
    assert code == 2
    assert data is not None
    assert data["error"]["code"] == "EXEMPTIONS_INVALID"
    assert any(error["code"] == "EXEMPTION_UNKNOWN_RULE" for error in data["error"]["details"])


def test_one_of_five_advisories_is_twenty_percent() -> None:
    code, data, _, _ = run_cbe(
        "enforce-no-bypass",
        "--manifest",
        fixture("manifests", "five_advisory.json"),
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
        "--exemptions",
        fixture("exemptions", "valid.txt"),
    )
    assert code == 0
    assert data is not None
    assert data["applicable_count"] == 5
    assert data["skip_count"] == 1
    assert data["skip_ratio"] == 0.2


def test_two_of_five_advisories_exits_4() -> None:
    code, data, _, _ = run_cbe(
        "enforce-no-bypass",
        "--manifest",
        fixture("manifests", "five_advisory.json"),
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--package-type",
        "cbs",
        "--package-version",
        "v0.1.0",
        "--exemptions",
        fixture("exemptions", "two_valid.txt"),
    )
    assert code == 4
    assert data is not None
    assert data["skip_count"] == 2
    assert data["skip_ratio"] == 0.4
    assert data["error"]["code"] == "SKIP_RATIO_EXCEEDED"


def test_not_applicable_exemption_is_not_counted() -> None:
    code, data, _, _ = run_cbe(
        "enforce-no-bypass",
        "--manifest",
        MANIFEST,
        "--source-root",
        fixture("bypass", "clean-repo"),
        "--package-type",
        "cbe",
        "--package-version",
        "v0.1.0",
        "--exemptions",
        fixture("exemptions", "not_applicable.txt"),
    )
    assert code == 0
    assert data is not None
    assert data["skip_count"] == 0
    assert any(warning["code"] == "EXEMPTION_NOT_APPLICABLE" for warning in data["warnings"])


def test_cbe_self_workflow_requires_explicit_exclusion(tmp_path: Path) -> None:
    repo = tmp_path / "cbe-like"
    (repo / "src" / "cbe").mkdir(parents=True)
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / "pyproject.toml").write_text('[project]\nname = "cbe"\n', encoding="utf-8")
    (repo / "src" / "cbe" / "cli.py").write_text("", encoding="utf-8")
    (repo / ".github" / "workflows" / "cbe-e2e.yml").write_text(
        "name: cbe-e2e\non: [push]\njobs:\n  gate:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - run: cbe --help\n        continue-on-error: true\n",
        encoding="utf-8",
    )

    code, data, _, _ = run_cbe(*BASE, "--source-root", repo, "--workflows")
    assert code == 2
    assert data is not None
    assert data["error"]["code"] == "SELF_WORKFLOW_EXCLUSION_REQUIRED"

    code, data, _, _ = run_cbe(
        *BASE,
        "--source-root",
        repo,
        "--workflows",
        "--exclude-workflow",
        ".github/workflows/cbe-e2e.yml",
    )
    assert code == 0
    assert data is not None
    assert data["bypass_attempts"] == []
    assert data["scanned"]["workflows"] == 0

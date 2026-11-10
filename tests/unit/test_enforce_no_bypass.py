"""Unit coverage for the no-bypass scanner and workflow recursion."""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from cbe.commands import enforce_no_bypass as enb

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests" / "e2e" / "fixtures" / "manifests" / "valid_full.json"
FIXTURES = ROOT / "tests" / "e2e" / "fixtures"


def _args(source: Path, **overrides: object) -> SimpleNamespace:
    base = dict(
        manifest=str(MANIFEST),
        source_root=str(source),
        package_type="cbs",
        package_version="v0.1.0",
        config=None,
        env_file=None,
        exemptions=None,
        workflows=True,
        exclude_workflow=None,
        strict=False,
        gate_job=enb.DEFAULT_GATE_JOB,
        fetch_remote=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _state() -> enb.ScanState:
    return enb.ScanState()


def test_default_constants_and_attempt_serialization() -> None:
    assert enb.DEFAULT_GATE_JOB == r"^cbe[-_]gate$"
    attempt = enb.BypassAttempt("comment", "a.py", 4, "CBE-QUALITY-001", "x" * 300)
    data = attempt.as_dict()
    assert data["action"] == "FAIL"
    assert len(data["evidence"]) == 200
    assert enb._as_list("x") == ["x"]
    assert enb._as_list(3) == []
    assert enb._strip_expression("${{ true }}") == "true"
    assert enb._first_rule_id("CBE-QUALITY-001", "*") == "CBE-QUALITY-001"
    assert enb._first_rule_id("no id", "fallback") == "fallback"


def test_scan_state_deduplicates() -> None:
    state = _state()
    first = enb.BypassAttempt("env", "<process-env>", 0, "*", "CBE_DISABLE")
    state.add(first)
    state.add(enb.BypassAttempt("env", "<process-env>", 0, "*", "CBE_DISABLE"))
    assert len(state.attempts) == 1


def test_clean_repository_run_passes_and_reports_scan_counts() -> None:
    data = enb.run(_args(FIXTURES / "bypass" / "clean-repo"))
    assert data["exit_code"] == 0
    assert data["gate_status"] == "PASS"
    assert data["bypass_attempts"] == []
    assert data["scanned"]["workflows"] == 1
    assert data["strict"] is False
    assert data["gate_job"] == enb.DEFAULT_GATE_JOB


def test_config_comment_and_env_bypasses_are_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CBE_DISABLE_RULE", "1")
    data = enb.run(_args(FIXTURES / "bypass" / "config", workflows=False))
    assert data["exit_code"] == 3
    assert data["error"]["code"] == "BYPASS_ATTEMPT"
    assert len(data["bypass_attempts"]) >= 1

    monkeypatch.delenv("CBE_DISABLE_RULE", raising=False)
    data = enb.run(_args(FIXTURES / "bypass" / "comments", workflows=False))
    assert data["exit_code"] == 3
    assert {item["kind"] for item in data["bypass_attempts"]} == {"comment"}

    data = enb.run(
        _args(
            FIXTURES / "bypass" / "clean-repo",
            workflows=False,
            env_file=[str(FIXTURES / "bypass" / "env" / "disable.env")],
        )
    )
    assert data["exit_code"] == 3
    assert any(item["kind"] == "env" for item in data["bypass_attempts"])


def test_config_false_and_empty_are_not_bypasses(tmp_path: Path) -> None:
    (tmp_path / "cbe.yml").write_text(
        "disable: false\nskip: []\nenabled: false\nCBE-QUALITY-001: true\n",
        encoding="utf-8",
    )
    state = _state()
    enb._scan_configs(tmp_path, None, state)
    assert state.configs == 1
    assert [item.kind for item in state.attempts] == ["config"]


def test_config_missing_explicit_file_raises(tmp_path: Path) -> None:
    with pytest.raises(Exception) as exc:
        enb._scan_configs(tmp_path, [str(tmp_path / "absent.yml")], _state())
    assert getattr(exc.value, "code", "") == "CONFIG_NOT_FOUND"


def test_env_file_missing_and_binary_warn(tmp_path: Path) -> None:
    with pytest.raises(Exception) as exc:
        enb._scan_env([str(tmp_path / "absent.env")], _state())
    assert getattr(exc.value, "code", "") == "ENV_FILE_NOT_FOUND"

    binary = tmp_path / "binary.env"
    binary.write_bytes(b"CBE_DISABLE\x00\n")
    state = _state()
    enb._scan_env([str(binary)], state)
    assert any(item["code"] == "ENV_FILE_BINARY_SKIPPED" for item in state.warnings)


def test_comments_warn_for_inline_skipped_and_noqa(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text(
        "# SKIPPED: CBE-QUALITY-001 reason=x\n"
        "# noqa CBE-QUALITY-001\n",
        encoding="utf-8",
    )
    state = _state()
    enb._scan_comments(tmp_path, state)
    assert any(item["code"] == "INLINE_EXEMPTION_IGNORED" for item in state.warnings)
    assert any(item.rule_id == "CBE-QUALITY-001" for item in state.attempts)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, "true"),
        (True, "true"),
        (False, "false"),
        (2, "true"),
        (0, "false"),
        ("true", "true"),
        ("!false", "true"),
        ("1 == 2", "false"),
        ("true && false", "false"),
        ("false || true", "true"),
        ("${{ inputs.ok }}", "unknown"),
        ("github.ref == 'x'", "unknown"),
        ("not-an-expression", "unknown"),
    ],
)
def test_evaluate_condition(value: object, expected: str) -> None:
    status, _reason = enb._evaluate_condition(value)
    assert status == expected


def test_literal_value_rejects_non_literal() -> None:
    with pytest.raises(ValueError):
        enb._literal_value("inputs.x")


def test_job_reachability_variants() -> None:
    jobs = {
        "a": {},
        "b": {"needs": "a"},
        "c": {"needs": "missing"},
        "d": {"if": "false"},
        "e": {"needs": "d"},
        "f": {"needs": "f"},
        "g": {"if": "inputs.x"},
    }
    assert enb._job_reachability("a", jobs).status == "reachable"
    assert enb._job_reachability("b", jobs).status == "reachable"
    assert enb._job_reachability("c", jobs).status == "unreachable"
    assert enb._job_reachability("d", jobs).status == "unreachable"
    assert enb._job_reachability("e", jobs).status == "unreachable"
    assert enb._job_reachability("f", jobs).status == "reachable"
    assert enb._job_reachability("g", jobs).status == "unknown"


def test_workflow_parse_binary_and_no_jobs(tmp_path: Path) -> None:
    state = _state()
    enb._scan_workflows(tmp_path, None, state, re.compile(enb.DEFAULT_GATE_JOB))
    assert state.workflows == 0

    wf = tmp_path / ".github" / "workflows" / "bad.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text("jobs: [", encoding="utf-8")
    enb._scan_workflows(tmp_path, None, state, re.compile(enb.DEFAULT_GATE_JOB))
    assert any(item["code"] == "WORKFLOW_PARSE_FAILED" for item in state.warnings)

    binary = tmp_path / ".github" / "workflows" / "binary.yml"
    binary.write_bytes(b"\x00")
    enb._scan_workflows(tmp_path, None, state, re.compile(enb.DEFAULT_GATE_JOB))
    assert any(item["code"] == "WORKFLOW_BINARY_SKIPPED" for item in state.warnings)


def test_no_matching_gate_job_warns(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows" / "x.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text("jobs:\n  other:\n    runs-on: ubuntu-latest\n", encoding="utf-8")
    state = _state()
    enb._scan_workflows(tmp_path, None, state, re.compile(enb.DEFAULT_GATE_JOB))
    assert any(item["code"] == "GATE_JOB_NOT_FOUND" for item in state.warnings)


def test_one_matching_gate_avoids_global_missing_warning(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "gate.yml").write_text(
        "jobs:\n  cbp-gate:\n    runs-on: ubuntu-latest\n", encoding="utf-8"
    )
    (workflows / "other.yml").write_text(
        "jobs:\n  build:\n    runs-on: ubuntu-latest\n", encoding="utf-8"
    )
    state = _state()
    enb._scan_workflows(tmp_path, None, state, re.compile("^cbp-gate$"))
    assert not any(item["code"] == "GATE_JOB_NOT_FOUND" for item in state.warnings)
    assert state.gate_jobs == 1


def test_commented_gate_is_bypass() -> None:
    state = _state()
    enb._scan_workflow_jobs(
        "x.yml",
        "jobs:\n  other:\n    runs-on: ubuntu-latest\n# cbe-gate:\n",
        state,
        re.compile(enb.DEFAULT_GATE_JOB),
    )
    assert any(item.reason == "WORKFLOW_SKIPS_CBE_GATE" for item in state.attempts)


def test_renamed_gate_regex_and_invalid_regex() -> None:
    data = enb.run(
        _args(
            FIXTURES / "bypass" / "renamed-gates-repo",
            gate_job="^security-gate$",
        )
    )
    assert data["exit_code"] == 3
    assert data["gate_job"] == "^security-gate$"

    data = enb.run(_args(FIXTURES / "bypass" / "clean-repo", gate_job="["))
    assert data["exit_code"] == 2
    assert data["error"]["code"] == "INVALID_GATE_JOB_REGEX"


def test_strict_dynamic_condition_fails() -> None:
    data = enb.run(
        _args(FIXTURES / "bypass" / "workflow-dynamic-if-repo", strict=True)
    )
    assert data["exit_code"] == 3
    assert data["error"]["code"] == "UNVERIFIABLE_CONDITION"
    assert data["strict"] is True


def test_strict_remote_workflow_fails() -> None:
    data = enb.run(
        _args(FIXTURES / "bypass" / "remote-call-repo", strict=True)
    )
    assert data["exit_code"] == 3
    assert data["error"]["code"] == "UNVERIFIABLE_REMOTE_WORKFLOW"


def test_local_reusable_workflow_is_followed() -> None:
    data = enb.run(_args(FIXTURES / "bypass" / "local-call-repo"))
    assert data["scanned"]["workflows"] == 2
    assert data["exit_code"] == 3


def test_local_workflow_errors_are_unverifiable(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows" / "ci.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text(
        "jobs:\n  call:\n    uses: ./.github/workflows/missing.yml\n",
        encoding="utf-8",
    )
    state = _state()
    enb._scan_workflows(tmp_path, None, state, re.compile(enb.DEFAULT_GATE_JOB))
    assert any(item["code"] == "UNVERIFIABLE_LOCAL_WORKFLOW" for item in state.warnings)

    state = _state()
    enb._scan_workflows(tmp_path, ["*.yml"], state, re.compile(enb.DEFAULT_GATE_JOB))
    assert state.workflows == 0


def test_exemptions_invalid_blocking_and_skip_ratio() -> None:
    data = enb.run(
        _args(
            FIXTURES / "bypass" / "clean-repo",
            exemptions=str(FIXTURES / "exemptions" / "unknown_rule.txt"),
        )
    )
    assert data["exit_code"] == 2
    assert data["error"]["code"] == "EXEMPTIONS_INVALID"

    data = enb.run(
        _args(
            FIXTURES / "bypass" / "clean-repo",
            exemptions=str(FIXTURES / "exemptions" / "blocking.txt"),
        )
    )
    assert data["exit_code"] == 3
    assert data["blocking_skip"] is True


def test_inspection_failure_for_invalid_manifest(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    data = enb.run(_args(FIXTURES / "bypass" / "clean-repo", manifest=str(bad)))
    assert data["exit_code"] == 2
    assert data["error"]["code"] == "MANIFEST_INVALID"


REMOTE_USE = "example-org/example-repo/.github/workflows/gate.yml@v1"


def _remote_root(tmp_path: Path) -> Path:
    wf = tmp_path / ".github" / "workflows" / "ci.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text(
        "jobs:\n  call:\n    uses: "
        + REMOTE_USE
        + "\n",
        encoding="utf-8",
    )
    return tmp_path


def test_remote_workflow_default_warns_and_strict_fails(tmp_path: Path) -> None:
    root = _remote_root(tmp_path)
    data = enb.run(_args(root))
    assert data["exit_code"] == 0
    assert any(item["code"] == "UNVERIFIABLE_REMOTE_WORKFLOW" for item in data["warnings"])

    data = enb.run(_args(root, strict=True))
    assert data["exit_code"] == 3
    assert data["error"]["code"] == "UNVERIFIABLE_REMOTE_WORKFLOW"


def test_remote_workflow_fetch_if_false_detected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _remote_root(tmp_path)
    content = (
        "on: [push]\n"
        "jobs:\n"
        "  cbe-gate:\n"
        "    if: false\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo skipped\n"
    )
    monkeypatch.setattr(enb, "_fetch_remote_workflow", lambda use: content)
    data = enb.run(_args(root, fetch_remote=True))
    assert data["exit_code"] == 3
    assert any(item["reason"] == "WORKFLOW_SKIPS_CBE_GATE" for item in data["bypass_attempts"])
    assert data["scanned"]["workflows"] == 2


def test_remote_workflow_fetch_ghost_needs_detected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _remote_root(tmp_path)
    content = (
        "on: [push]\n"
        "jobs:\n"
        "  cbe-gate:\n"
        "    needs: ghost\n"
        "    runs-on: ubuntu-latest\n"
    )
    monkeypatch.setattr(enb, "_fetch_remote_workflow", lambda use: content)
    data = enb.run(_args(root, fetch_remote=True))
    assert data["exit_code"] == 3
    assert any(item["reason"] == "WORKFLOW_SKIPS_CBE_GATE" for item in data["bypass_attempts"])


def test_remote_workflow_empty_shell_fails_strict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _remote_root(tmp_path)
    monkeypatch.setattr(enb, "_fetch_remote_workflow", lambda use: "name: shell\non: [push]\njobs: {}\n")
    data = enb.run(_args(root, fetch_remote=True, strict=True))
    assert data["exit_code"] == 3
    assert data["error"]["code"] == "GATE_JOB_NOT_FOUND"


def test_remote_workflow_network_failure_warns_and_strict_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _remote_root(tmp_path)

    def fail(use: str) -> str:
        raise enb.RemoteWorkflowError("network failure")

    monkeypatch.setattr(enb, "_fetch_remote_workflow", fail)
    data = enb.run(_args(root, fetch_remote=True))
    assert data["exit_code"] == 0
    assert any("network failure" in item["message"] for item in data["warnings"])

    data = enb.run(_args(root, fetch_remote=True, strict=True))
    assert data["exit_code"] == 3
    assert data["error"]["code"] == "UNVERIFIABLE_REMOTE_WORKFLOW"


def test_remote_workflow_auth_failure_warns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _remote_root(tmp_path)

    def fail(use: str) -> str:
        raise enb.RemoteWorkflowError("auth failure: HTTP 403")

    monkeypatch.setattr(enb, "_fetch_remote_workflow", fail)
    data = enb.run(_args(root, fetch_remote=True))
    assert data["exit_code"] == 0
    assert any("auth failure" in item["message"] for item in data["warnings"])


def test_skip_ratio_early_warnings_do_not_change_20_percent_gate() -> None:
    manifest = FIXTURES / "manifests" / "five_advisory.json"
    args = _args(
        FIXTURES / "bypass" / "clean-repo",
        manifest=str(manifest),
        exemptions=str(FIXTURES / "exemptions" / "valid.txt"),
    )
    data = enb.run(args)
    assert data["exit_code"] == 0
    assert any(item["code"] == "SKIP_RATIO_EARLY_WARNING_15" for item in data["warnings"])

    args = _args(
        FIXTURES / "bypass" / "clean-repo",
        manifest=str(manifest),
        exemptions=str(FIXTURES / "exemptions" / "two_valid.txt"),
    )
    data = enb.run(args)
    assert data["exit_code"] == 4
    assert data["error"]["code"] == "SKIP_RATIO_EXCEEDED"


def test_local_workflow_accepts_windows_backslashes(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows" / "child.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text("jobs:\n  cbe-gate:\n    if: false\n    runs-on: ubuntu-latest\n", encoding="utf-8")
    target, error = enb._resolve_local_workflow(
        tmp_path, r".\.github\workflows\child.yml"
    )
    assert error == ""
    assert target == wf.resolve()


def test_cbp_gate_job_can_be_selected_separately(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows" / "cross.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text(
        "jobs:\n"
        "  cbe-gate:\n"
        "    runs-on: ubuntu-latest\n"
        "  cbp-gate:\n"
        "    if: false\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    data = enb.run(_args(tmp_path, gate_job="^cbp-gate$"))
    assert data["exit_code"] == 3
    assert any(item["reason"] == "WORKFLOW_SKIPS_CBE_GATE" for item in data["bypass_attempts"])


class _Response:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, limit: int = -1) -> bytes:
        return self.data


def test_fetch_remote_workflow_success(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout: int):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return _Response(b"jobs: {}\n")

    monkeypatch.setattr(enb.urllib.request, "urlopen", fake_urlopen)
    text = enb._fetch_remote_workflow(REMOTE_USE, timeout=5)
    assert text == "jobs: {}\n"
    assert "raw.githubusercontent.com" in str(captured["url"])
    assert captured["timeout"] == 5


@pytest.mark.parametrize("kind", ["auth", "http", "network"])
def test_fetch_remote_workflow_errors(
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    def fail(request, timeout: int):
        if kind == "network":
            raise enb.urllib.error.URLError("offline")
        raise enb.urllib.error.HTTPError("u", 403 if kind == "auth" else 404, kind, {}, None)

    monkeypatch.setattr(enb.urllib.request, "urlopen", fail)
    with pytest.raises(enb.RemoteWorkflowError) as caught:
        enb._fetch_remote_workflow(REMOTE_USE)
    assert kind in str(caught.value)


def test_fetch_remote_workflow_size_and_encoding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        enb.urllib.request,
        "urlopen",
        lambda request, timeout: _Response(b"x" * 2_000_001),
    )
    with pytest.raises(enb.RemoteWorkflowError):
        enb._fetch_remote_workflow(REMOTE_USE)

    monkeypatch.setattr(
        enb.urllib.request,
        "urlopen",
        lambda request, timeout: _Response(b"\xff\xfe"),
    )
    with pytest.raises(enb.RemoteWorkflowError):
        enb._fetch_remote_workflow(REMOTE_USE)


def test_remote_reference_parse_and_unsupported() -> None:
    assert enb._parse_remote_use("nope") is None
    assert enb._parse_remote_use("owner/repo/.github/workflows/x.yml@v1") is not None
    with pytest.raises(enb.RemoteWorkflowError):
        enb._fetch_remote_workflow("nope")


def test_remote_nested_local_workflow_is_followed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _remote_root(tmp_path)
    calls: list[str] = []

    def fetcher(use: str) -> str:
        calls.append(use)
        if use.endswith("gate.yml@v1"):
            return (
                "jobs:\n"
                "  delegate:\n"
                "    uses: ./.github/workflows/child.yml\n"
            )
        if use.endswith("child.yml@v1"):
            return (
                "jobs:\n"
                "  cbe-gate:\n"
                "    if: false\n"
                "    runs-on: ubuntu-latest\n"
            )
        raise enb.RemoteWorkflowError("unexpected")

    monkeypatch.setattr(enb, "_fetch_remote_workflow", fetcher)
    data = enb.run(_args(root, fetch_remote=True))
    assert data["exit_code"] == 3
    assert data["scanned"]["workflows"] == 3
    assert any(item["reason"] == "WORKFLOW_SKIPS_CBE_GATE" for item in data["bypass_attempts"])
    assert any("child.yml@v1" in item for item in calls)


def test_remote_local_reference_outside_workflows_is_unverifiable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _remote_root(tmp_path)

    def fetcher(use: str) -> str:
        return "jobs:\n  delegate:\n    uses: ./actions/local\n"

    monkeypatch.setattr(enb, "_fetch_remote_workflow", fetcher)
    data = enb.run(_args(root, fetch_remote=True, strict=True))
    assert data["exit_code"] == 3
    assert any(item["code"] == "UNVERIFIABLE_LOCAL_WORKFLOW" for item in data["warnings"])


def test_remote_unsupported_reference_warns(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows" / "ci.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text("jobs:\n  call:\n    uses: not-a-workflow\n", encoding="utf-8")
    data = enb.run(_args(tmp_path, fetch_remote=True, strict=True))
    assert data["exit_code"] == 3
    assert any("unsupported remote reusable workflow" in item["message"] for item in data["warnings"])

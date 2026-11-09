"""CBE-08 frozen F2 checks must all match the addendum expectations."""

from __future__ import annotations

from _util import run_script


def test_frozen_f2_checks_pass() -> None:
    code, data, _, _ = run_script("tools/cbe08_draft.py")
    assert code == 0
    assert data is not None
    assert data["status"] == "PASS"
    assert data["not_pass"] is False
    assert data["cbe08_pass"] is True
    assert data["failed_checks"] == []
    observed = {item["check"]: item["exit_code"] for item in data["checks"]}
    assert observed == {
        "five_advisory_valid": 0,
        "non_blocking_1_of_5_skip": 0,
        "blocking_skip_exits_3": 3,
        "zero_rules_exits_3": 3,
    }
    assert data["addendum_commit"] == "e318cbdac748a3a88057bd882e897f50c364bd97"
    assert data["addendum_authorizes_pass"] is True

"""CBE-09: F4 previous-stable baseline selection."""

from __future__ import annotations

from _util import fixture, run_script

RELEASES = fixture("releases", "releases.json")
NO_BASELINE = fixture("releases", "releases_no_baseline.json")


def test_selects_highest_eligible_stable() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_baseline.py",
        "--releases",
        RELEASES,
        "--current-version",
        "v0.1.0",
    )
    assert code == 0
    assert data is not None
    assert data["baseline"]["tag"] == "v0.0.9"
    assert data["baseline"]["source"] == "stable"
    assert data["baseline"]["eligible"] is True


def test_no_eligible_stable_is_precondition_fail() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_baseline.py",
        "--releases",
        NO_BASELINE,
        "--current-version",
        "v0.1.0",
    )
    assert code == 3
    assert data is not None
    assert data["gate_status"] == "PRECONDITION_FAIL"
    assert data["error"]["code"] == "NO_ELIGIBLE_BASELINE"


def test_explicit_tag_is_recorded_as_explicit() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_baseline.py",
        "--releases",
        RELEASES,
        "--current-version",
        "v0.1.0",
        "--baseline",
        "v0.0.5",
    )
    assert code == 0
    assert data is not None
    assert data["baseline"]["tag"] == "v0.0.5"
    assert data["baseline"]["source"] == "explicit_tag"


def test_explicit_commit_is_a_bootstrap_not_a_stable() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_baseline.py",
        "--releases",
        RELEASES,
        "--current-version",
        "v0.1.0",
        "--baseline",
        "a" * 40,
    )
    assert code == 0
    assert data is not None
    assert data["baseline"]["source"] == "explicit_commit"
    assert "bootstrap" in data["baseline"]["reason"]


def test_current_version_cannot_be_the_explicit_baseline() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_baseline.py",
        "--releases",
        RELEASES,
        "--current-version",
        "v0.1.0",
        "--baseline",
        "v0.1.0",
    )
    assert code == 2
    assert data is not None
    assert data["error"]["code"] == "BASELINE_IS_CURRENT"

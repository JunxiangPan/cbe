"""Unit tests for CBE-09 F4 baseline selection."""

from __future__ import annotations

from pathlib import Path

import pytest

from cbe.baseline import load_releases, select_baseline
from cbe.errors import InputError, PreconditionError

FIXTURES = Path(__file__).resolve().parents[1] / "e2e" / "fixtures" / "releases"


def test_selects_v009_for_v010() -> None:
    selected = select_baseline(load_releases(FIXTURES / "releases.json"), current_version="v0.1.0")
    assert selected.tag == "v0.0.9"
    assert selected.source == "stable"


def test_no_eligible_is_precondition_fail() -> None:
    with pytest.raises(PreconditionError) as caught:
        select_baseline(load_releases(FIXTURES / "releases_no_baseline.json"), current_version="v0.1.0")
    assert caught.value.code == "NO_ELIGIBLE_BASELINE"
    assert caught.value.exit_code == 3


def test_explicit_current_is_input_error() -> None:
    with pytest.raises(InputError) as caught:
        select_baseline(
            load_releases(FIXTURES / "releases.json"),
            current_version="v0.1.0",
            explicit="v0.1.0",
        )
    assert caught.value.code == "BASELINE_IS_CURRENT"


def test_explicit_commit_is_bootstrap() -> None:
    selected = select_baseline(
        load_releases(FIXTURES / "releases.json"),
        current_version="v0.1.0",
        explicit="a" * 40,
    )
    assert selected.source == "explicit_commit"
    assert "bootstrap" in selected.reason

"""Unit tests for CBE-10 F5/F6 release-train handling."""

from __future__ import annotations

from pathlib import Path

from cbe.release_train import body_section, classify, components, load_release_train, status

FIXTURES = Path(__file__).resolve().parents[1] / "e2e" / "fixtures" / "release-train"


def test_not_uploaded_is_visible_not_pass() -> None:
    data = load_release_train(FIXTURES / "not-uploaded.json")
    items = components(data)
    not_uploaded, evidence_absent, infra = classify(items)
    assert not_uploaded == ["cbm", "cbc"]
    assert evidence_absent == []
    assert infra == []
    assert status(items) == (0, "PASS")
    body = body_section(items)
    assert "## NOT_UPLOADED" in body
    assert "NOT_UPLOADED is not PASS" in body


def test_declared_attached_phrase() -> None:
    body = body_section(components(load_release_train(FIXTURES / "declared-attached.json")))
    assert "declared as attached but not uploaded" in body


def test_infra_is_exit_3_skipped_infra() -> None:
    items = components(load_release_train(FIXTURES / "infra.json"))
    assert status(items) == (3, "SKIPPED_INFRA")
    assert "## Infrastructure failures" in body_section(items)

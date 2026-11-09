"""Unit tests for CBP 1.2.0 manifest compatibility."""

from __future__ import annotations

import json
from pathlib import Path

from cbe.cbp_compat import validate_cbp_manifest
from cbe.paths import schema_path

FIXTURES = Path(__file__).resolve().parents[1] / "e2e" / "fixtures" / "release-train"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_cbp_manifest_has_no_problems() -> None:
    assert validate_cbp_manifest(_load("cbp-quality-manifest-v12.json")) == []


def test_full_body_scope_is_rejected() -> None:
    problems = validate_cbp_manifest(_load("cbp-quality-manifest-full.json"))
    assert any("body_hash_scope" in item for item in problems)


def test_object_artifact_repository_is_rejected_against_cbp_120_shape() -> None:
    problems = validate_cbp_manifest(_load("cbp-quality-manifest-object-repo.json"))
    assert any("artifact_repository" in item for item in problems)


def test_cbc_event_is_not_a_manifest_field() -> None:
    problems = validate_cbp_manifest(_load("cbp-quality-manifest-cbc-event-field.json"))
    assert any("cbc_event" in item for item in problems)


def test_schemas_are_bundled_in_package() -> None:
    assert schema_path("v1.7", "cbe-report.schema.json").is_file()

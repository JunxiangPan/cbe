"""Unit tests for CBP quality-manifest compatibility under contract RC2."""

from __future__ import annotations

import hashlib
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


def test_bare_string_artifact_repository_is_rejected() -> None:
    problems = validate_cbp_manifest(_load("cbp-quality-manifest-string-repo.json"))
    assert any("artifact_repository" in item for item in problems)


def test_incomplete_object_artifact_repository_is_rejected() -> None:
    problems = validate_cbp_manifest(_load("cbp-quality-manifest-object-repo.json"))
    assert any("run_id" in item for item in problems)


def test_schema_version_must_be_string_one() -> None:
    problems = validate_cbp_manifest(_load("cbp-quality-manifest-schema-version-number.json"))
    assert any("schema_version" in item for item in problems)


def test_cbc_event_is_not_a_manifest_field() -> None:
    problems = validate_cbp_manifest(_load("cbp-quality-manifest-cbc-event-field.json"))
    assert any("cbc_event" in item for item in problems)


def test_schemas_are_bundled_in_package() -> None:
    path = schema_path("v1.7", "cbe-report.schema.json")
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "2b3e1c5a77a7f520b80d01fefa328c9353fffc5d65e87782ca90d193839c0e74"
    )

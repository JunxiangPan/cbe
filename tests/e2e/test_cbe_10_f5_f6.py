"""CBE-10: F5/F6 component status and CBP 1.2.0 manifest compatibility."""

from __future__ import annotations

from _util import fixture, run_script

TRAIN = fixture("release-train")
CBP_V12 = TRAIN / "cbp-quality-manifest-v12.json"


def test_not_uploaded_is_visible_and_not_counted() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_train.py",
        "--release-train",
        TRAIN / "not-uploaded.json",
        "--cbp-manifest",
        CBP_V12,
    )
    assert code == 0
    assert data is not None
    assert data["not_uploaded"] == ["cbm", "cbc"]
    assert data["skip_count"] == 0
    assert data["applicable_count"] == 0
    assert data["counted_in_skip_denominator"] is False
    assert "## NOT_UPLOADED" in data["body_section_md"]
    assert "NOT_UPLOADED is not PASS" in data["body_section_md"]


def test_declared_attached_uses_the_exact_phrase() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_train.py",
        "--release-train",
        TRAIN / "declared-attached.json",
    )
    assert code == 0
    assert data is not None
    assert "declared as attached but not uploaded" in data["body_section_md"]


def test_evidence_absent_is_visible() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_train.py",
        "--release-train",
        TRAIN / "evidence-absent.json",
    )
    assert code == 0
    assert data is not None
    assert data["evidence_absent"] == ["cbm"]
    assert "EVIDENCE_ABSENT" in data["body_section_md"]


def test_infrastructure_failure_is_exit_3_and_not_counted() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_train.py",
        "--release-train",
        TRAIN / "infra.json",
    )
    assert code == 3
    assert data is not None
    assert data["gate_status"] == "SKIPPED_INFRA"
    assert data["infrastructure_failures"] == ["cbm"]
    assert data["skip_count"] == 0
    assert "## Infrastructure failures" in data["body_section_md"]


def test_cbp_body_scope_full_is_rejected() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_train.py",
        "--release-train",
        TRAIN / "not-uploaded.json",
        "--cbp-manifest",
        TRAIN / "cbp-quality-manifest-full.json",
    )
    assert code == 2
    assert data is not None
    assert data["error"]["code"] == "CBP_MANIFEST_INVALID"
    assert any("body_hash_scope" in item for item in data["error"]["details"])


def test_cbp_rc2_object_repository_is_canonical() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_train.py",
        "--release-train",
        TRAIN / "not-uploaded.json",
        "--cbp-manifest",
        CBP_V12,
    )
    assert code == 0
    assert data is not None
    assert data["cbp_manifest_checked"] is True


def test_cbp_rc2_bare_string_repository_is_rejected() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_train.py",
        "--release-train",
        TRAIN / "not-uploaded.json",
        "--cbp-manifest",
        TRAIN / "cbp-quality-manifest-string-repo.json",
    )
    assert code == 2
    assert data is not None
    assert any("artifact_repository" in item for item in data["error"]["details"])


def test_cbp_rc2_incomplete_object_is_rejected() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_train.py",
        "--release-train",
        TRAIN / "not-uploaded.json",
        "--cbp-manifest",
        TRAIN / "cbp-quality-manifest-object-repo.json",
    )
    assert code == 2
    assert data is not None
    assert any("run_id" in item for item in data["error"]["details"])


def test_cbp_schema_version_must_be_string_one() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_train.py",
        "--release-train",
        TRAIN / "not-uploaded.json",
        "--cbp-manifest",
        TRAIN / "cbp-quality-manifest-schema-version-number.json",
    )
    assert code == 2
    assert data is not None
    assert any("schema_version" in item for item in data["error"]["details"])


def test_cbc_event_is_not_a_private_manifest_field() -> None:
    code, data, _, _ = run_script(
        "tools/cbe_train.py",
        "--release-train",
        TRAIN / "not-uploaded.json",
        "--cbp-manifest",
        TRAIN / "cbp-quality-manifest-cbc-event-field.json",
    )
    assert code == 2
    assert data is not None
    assert any("cbc_event" in item for item in data["error"]["details"])

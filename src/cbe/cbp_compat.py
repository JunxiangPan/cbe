"""CBP quality-manifest compatibility checks for contract RC2.

Contract RC2 makes ``artifact_repository`` an object:
``{repository, run_id, artifact_name}``. A bare ``owner/repo`` string is no
longer canonical. CBP 1.2.2 is not released yet, so the object shape is verified
with fixtures only, not claimed as a CBP 1.2.2 PASS.
"""

from __future__ import annotations

import re
from typing import Any

HASH_RE = re.compile(r"^[a-f0-9]{64}$")
REQUIRED = (
    "schema_version",
    "package_id",
    "producer_id",
    "version",
    "gate_status",
    "applicable_gate_count",
    "skip_count",
    "skip_ratio",
    "blocking_skip",
    "gates",
    "artifact_hashes",
    "release_body_hash",
    "evidence_sha256",
    "body_hash_scope",
)
ALLOWED = set(REQUIRED) | {
    "artifact_repository",
    "ci_run_id",
    "ci_commit_sha",
    "generated_at",
    "generated_by",
}
GATE_STATUS = {"PASS", "FAIL", "SKIPPED_INFRA", "PRECONDITION_FAIL"}


def validate_cbp_manifest(
    manifest: Any,
    *,
    expected_repository: str | None = None,
    require_body_scope: bool = True,
) -> list[str]:
    if not isinstance(manifest, dict):
        return ["manifest: must be a JSON object"]
    problems: list[str] = []
    unknown = sorted(set(manifest) - ALLOWED)
    if unknown:
        problems.append("manifest: unexpected key(s) " + ", ".join(unknown))
    for field in REQUIRED:
        if field not in manifest:
            problems.append(f"{field}: required field is missing")
    if manifest.get("schema_version") != "1":
        problems.append("schema_version: must be the string '1'")
    if manifest.get("producer_id") not in (None, "cbp"):
        problems.append("producer_id: must be 'cbp' when present")
    package_id = manifest.get("package_id")
    if not isinstance(package_id, str) or not package_id:
        problems.append("package_id: non-empty string required")
    version = manifest.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"v?[0-9]+\.[0-9]+\.[0-9]+", version):
        problems.append("version: vX.Y.Z required")
    if manifest.get("gate_status") not in GATE_STATUS:
        problems.append("gate_status: unsupported value")
    for name in ("applicable_gate_count", "skip_count"):
        value = manifest.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            problems.append(f"{name}: non-negative integer required")
    ratio = manifest.get("skip_ratio")
    if not isinstance(ratio, (int, float)) or isinstance(ratio, bool) or not 0 <= ratio <= 1:
        problems.append("skip_ratio: number in [0, 1] required")
    if not isinstance(manifest.get("blocking_skip"), bool):
        problems.append("blocking_skip: boolean required")
    if not isinstance(manifest.get("gates"), list):
        problems.append("gates: array required")

    if require_body_scope and "body_hash_scope" not in manifest:
        problems.append("body_hash_scope: required field is missing")
    scope = manifest.get("body_hash_scope")
    if "body_hash_scope" in manifest and scope != "base":
        problems.append("body_hash_scope: must be exactly 'base'; 'full' is unsupported")

    repository = manifest.get("artifact_repository")
    if repository is not None:
        if not isinstance(repository, dict):
            problems.append(
                "artifact_repository: object {repository, run_id, artifact_name} required; "
                "a bare owner/repo string is not canonical under contract RC2"
            )
        else:
            extra = sorted(set(repository) - {"repository", "run_id", "artifact_name"})
            if extra:
                problems.append("artifact_repository: unexpected key(s) " + ", ".join(extra))
            repo_name = repository.get("repository")
            if not isinstance(repo_name, str) or not repo_name.strip() or "/" not in repo_name:
                problems.append("artifact_repository.repository: owner/repo string required")
            run_id = repository.get("run_id")
            if not isinstance(run_id, (str, int)) or isinstance(run_id, bool) or not str(run_id).strip():
                problems.append("artifact_repository.run_id: non-empty string or integer required")
            artifact_name = repository.get("artifact_name")
            if not isinstance(artifact_name, str) or not artifact_name.strip():
                problems.append("artifact_repository.artifact_name: non-empty string required")
            if expected_repository and isinstance(repo_name, str) and repo_name != expected_repository:
                problems.append(
                    f"artifact_repository.repository: {repo_name!r} != expected {expected_repository!r}"
                )

    hashes = manifest.get("artifact_hashes")
    if not isinstance(hashes, dict):
        problems.append("artifact_hashes: object required")
    elif any(not isinstance(value, str) or not HASH_RE.fullmatch(value) for value in hashes.values()):
        problems.append("artifact_hashes: values must be bare 64 lowercase hex")
    for name in ("release_body_hash", "evidence_sha256"):
        value = manifest.get(name)
        if not isinstance(value, str) or not HASH_RE.fullmatch(value):
            problems.append(f"{name}: bare 64 lowercase hex required")
    return problems

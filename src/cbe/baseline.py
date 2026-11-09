"""F4 previous-stable baseline selection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .errors import InputError, PreconditionError
from .jsonio import load_json
from .manifest import Version

from .paths import schema_path

RELEASES_SCHEMA = schema_path("v1.7", "releases.schema.json")


@dataclass
class Baseline:
    tag: str | None
    version: str | None
    commit: str
    source: str  # stable | explicit_tag | explicit_commit
    published_at: str = ""
    eligible: bool = True
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "version": self.version,
            "commit": self.commit,
            "source": self.source,
            "published_at": self.published_at,
            "eligible": self.eligible,
            "reason": self.reason,
        }


def _schema() -> dict[str, Any]:
    try:
        return json.loads(RELEASES_SCHEMA.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InputError("RELEASES_SCHEMA_UNAVAILABLE", f"cannot read releases schema: {exc}") from exc


def _erratum(release: dict[str, Any]) -> bool:
    body = str(release.get("body", ""))
    if body.lstrip().startswith("ERRATUM:"):
        return True
    return any(str(label).lower() == "erratum" for label in release.get("labels", []))


def _gate_passed(release: dict[str, Any]) -> bool:
    status = release.get("gate_status")
    if not isinstance(status, dict):
        return False
    # CBE baseline requires CBE PASS; if CBP evidence is present it must also pass.
    if status.get("cbe") != "PASS":
        return False
    if "cbp" in status and status.get("cbp") != "PASS":
        return False
    return True


def load_releases(path: str | Path) -> list[dict[str, Any]]:
    data = load_json(path)
    errors = sorted(Draft202012Validator(_schema()).iter_errors(data), key=lambda item: list(item.path))
    if errors:
        raise InputError("RELEASES_INVALID", f"releases file is invalid: {errors[0].message}")
    return data["releases"]


def _stable_candidates(releases: list[dict[str, Any]], current_version: str) -> list[dict[str, Any]]:
    current = Version.parse(current_version.lstrip("v"))
    candidates: list[dict[str, Any]] = []
    for release in releases:
        tag = release.get("tag")
        if not isinstance(tag, str) or not tag.startswith("v"):
            continue
        try:
            version = Version.parse(tag[1:])
        except ValueError:
            continue
        if version.prerelease:
            continue
        if release.get("prerelease") is True:
            continue
        if version == current:
            continue
        if _erratum(release) or not _gate_passed(release):
            continue
        candidates.append(release)
    candidates.sort(
        key=lambda item: (
            Version.parse(item["tag"][1:]),
            str(item.get("published_at", "")),
        ),
        reverse=True,
    )
    return candidates


def select_baseline(
    releases: list[dict[str, Any]],
    *,
    current_version: str,
    explicit: str | None = None,
) -> Baseline:
    current_normalized = current_version.lstrip("v")
    if explicit:
        text = explicit.strip()
        if text.startswith("v"):
            for release in releases:
                if release.get("tag") == text:
                    if release.get("version") == current_normalized or text == f"v{current_normalized}":
                        raise InputError("BASELINE_IS_CURRENT", "explicit baseline is the current version")
                    return Baseline(
                        tag=text,
                        version=str(release.get("version", text[1:])),
                        commit=str(release.get("commit", "")),
                        source="explicit_tag",
                        published_at=str(release.get("published_at", "")),
                        eligible=not _erratum(release) and _gate_passed(release),
                        reason="explicit baseline; eligibility is recorded, not inferred",
                    )
            raise InputError("BASELINE_TAG_NOT_FOUND", f"baseline tag not found: {text}")
        if len(text) == 40 and all(char in "0123456789abcdef" for char in text.lower()):
            return Baseline(
                tag=None,
                version=None,
                commit=text.lower(),
                source="explicit_commit",
                eligible=True,
                reason="explicit commit bootstrap; not a previous stable version",
            )
        raise InputError("BASELINE_INVALID", "explicit baseline must be vX.Y.Z or a 40-hex commit")

    candidates = _stable_candidates(releases, current_normalized)
    if not candidates:
        raise PreconditionError(
            "NO_ELIGIBLE_BASELINE",
            "no eligible previous stable release and no explicit --baseline",
        )
    selected = candidates[0]
    return Baseline(
        tag=selected["tag"],
        version=str(selected["version"]),
        commit=str(selected["commit"]),
        source="stable",
        published_at=str(selected.get("published_at", "")),
        eligible=True,
    )

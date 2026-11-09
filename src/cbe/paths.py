"""Locate bundled schemas in editable checkouts and installed wheels."""

from __future__ import annotations

from pathlib import Path


def schema_path(*parts: str) -> Path:
    package = Path(__file__).resolve().parent / "schemas"
    checkout = Path(__file__).resolve().parents[2] / "schemas"
    for base in (package, checkout):
        candidate = base.joinpath(*parts)
        if candidate.is_file():
            return candidate
    return package.joinpath(*parts)

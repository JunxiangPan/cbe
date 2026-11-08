"""Unit tests for the deterministic symbol index."""

from __future__ import annotations

import json
from pathlib import Path

from cbe.commands.symbol_index import build_index
from cbe.jsonio import sha256_json

FIXTURE = Path(__file__).resolve().parents[1] / "e2e" / "fixtures" / "source-tree"


def test_symbol_index_is_deterministic_and_complete() -> None:
    first, warnings = build_index(FIXTURE)
    second, _ = build_index(FIXTURE)
    assert sha256_json(first) == sha256_json(second)
    assert len(first["files"]) == 4
    assert any(item["path"] == "pkg/mod.py" for item in first["files"])
    assert any(item["language"] == "powershell" for item in first["files"])
    assert any(warning["code"] == "PYTHON_PARSE_FAILED" for warning in warnings)

    python = next(item for item in first["files"] if item["path"] == "pkg/mod.py")
    names = {symbol["qualified_name"] for symbol in python["symbols"]}
    assert {"Greeter", "Greeter.hello", "Greeter.hello.inner", "top_level"} <= names

    powershell = next(item for item in first["files"] if item["path"] == "scripts/tool.ps1")
    assert {symbol["name"] for symbol in powershell["symbols"]} == {"Get-Thing", "Widget"}


def test_symbol_index_file_hashes_are_sha256() -> None:
    index, _ = build_index(FIXTURE)
    for item in index["files"]:
        assert len(item["sha256"]) == 64
        assert all(char in "0123456789abcdef" for char in item["sha256"])
    assert json.dumps(index)  # serializable

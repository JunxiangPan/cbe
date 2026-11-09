"""CBE-08 contract-hash guard: pin 6835789 / 209d75b4, fail on drift."""

from __future__ import annotations

import json
from pathlib import Path

from _util import fixture, run_script

PIN = fixture("contract", "v1.7.1-pin.json")


def test_guard_matches_pinned_contract() -> None:
    code, data, _, _ = run_script("tools/cbe_contract_guard.py", "--pin", PIN)
    assert code == 0
    assert data is not None
    assert data["gate_status"] == "PINNED"
    assert data["pin"]["commit"] == "683578964fb14518b2bd81d3fd49766b66feb851"
    assert data["pin"]["contract_sha256"] == "209d75b4c900f9a2d1ad8f5c377ac1b8a868cf3e4cd449970e61e3ff380c18f1"
    assert data["observed"]["commit"] == data["pin"]["commit"]
    assert data["observed"]["contract_sha256"] == data["pin"]["contract_sha256"]
    assert data["observed"]["vm_proof_clean"] is True
    assert data["pin"]["frozen"] is False


def test_guard_fails_when_pinned_commit_moves(tmp_path: Path) -> None:
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    pin["commit"] = "0" * 40
    path = tmp_path / "moved.json"
    path.write_text(json.dumps(pin), encoding="utf-8")
    code, data, _, _ = run_script("tools/cbe_contract_guard.py", "--pin", path)
    assert code == 3
    assert data is not None
    assert data["error"]["code"] == "CONTRACT_CHANGED"
    assert any(item["field"] == "commit" for item in data["error"]["details"])


def test_guard_fails_when_contract_hash_changes(tmp_path: Path) -> None:
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    pin["contract_sha256"] = "0" * 64
    path = tmp_path / "hash-changed.json"
    path.write_text(json.dumps(pin), encoding="utf-8")
    code, data, _, _ = run_script("tools/cbe_contract_guard.py", "--pin", path)
    assert code == 3
    assert data is not None
    assert data["error"]["code"] == "CONTRACT_CHANGED"
    assert any(item["field"] == "contract_sha256" for item in data["error"]["details"])

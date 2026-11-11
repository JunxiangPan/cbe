"""Tamper tests for the CBE self-protection manifest."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "cbe_self_protect.py"
PROTECTED = [
    ".github/workflows/cbe-e2e.yml",
    ".github/workflows/pypi-publish.yml",
    ".github/workflows/sign-release.yml",
    "src/cbe/commands/enforce_no_bypass.py",
    "src/cbe/manifest.py",
    "tools/cbe_contract_guard.py",
    "tools/cbe_release_bundle.py",
    "tools/cbe_verify_sidecar.py",
]


def _run(root: Path, manifest: Path, *args: str) -> tuple[int, dict]:
    process = subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root), "--manifest", str(manifest), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        data = json.loads(process.stdout)
    except json.JSONDecodeError:
        data = {}
    return process.returncode, data


def _copy_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for relative in PROTECTED:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return root


def _init(tmp_path: Path) -> tuple[Path, Path]:
    root = _copy_root(tmp_path)
    manifest = root / "security" / "SELF_PROTECTION.sha256"
    code, _ = _run(root, manifest, "--write")
    assert code == 0
    return root, manifest


def test_repository_manifest_matches() -> None:
    manifest = ROOT / "security" / "SELF_PROTECTION.sha256"
    code, data = _run(ROOT, manifest)
    assert code == 0, data
    assert data["ok"] is True


def test_tamper_workflow_is_detected(tmp_path: Path) -> None:
    root, manifest = _init(tmp_path)
    target = root / ".github" / "workflows" / "cbe-e2e.yml"
    target.write_text(target.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")
    code, data = _run(root, manifest)
    assert code == 3
    assert any(item["path"] == ".github/workflows/cbe-e2e.yml" for item in data["mismatches"])


def test_tamper_gate_script_is_detected(tmp_path: Path) -> None:
    root, manifest = _init(tmp_path)
    target = root / "src" / "cbe" / "commands" / "enforce_no_bypass.py"
    target.write_text(target.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")
    code, data = _run(root, manifest)
    assert code == 3
    assert any(
        item["path"] == "src/cbe/commands/enforce_no_bypass.py" for item in data["mismatches"]
    )


def test_tamper_contract_guard_is_detected(tmp_path: Path) -> None:
    root, manifest = _init(tmp_path)
    target = root / "tools" / "cbe_contract_guard.py"
    target.write_text(target.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")
    code, data = _run(root, manifest)
    assert code == 3
    assert any(item["path"] == "tools/cbe_contract_guard.py" for item in data["mismatches"])

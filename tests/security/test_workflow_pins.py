"""Supply-chain checks for CBE workflows."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
SHA_RE = re.compile(r"^[^@]+@[0-9a-f]{40}$")


def _documents() -> list[tuple[str, dict]]:
    result = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        result.append((path.name, yaml.safe_load(path.read_text(encoding="utf-8"))))
    return result


def test_third_party_actions_are_pinned_to_sha() -> None:
    for name, document in _documents():
        for job in (document.get("jobs") or {}).values():
            for step in job.get("steps") or []:
                uses = step.get("uses")
                if not uses or str(uses).startswith("./"):
                    continue
                assert SHA_RE.fullmatch(str(uses)), f"{name}: unpinned action {uses}"


def test_no_self_hosted_runner() -> None:
    for name, document in _documents():
        for job in (document.get("jobs") or {}).values():
            runs_on = job.get("runs-on")
            assert "self-hosted" not in str(runs_on), f"{name}: self-hosted runner"


def test_coverage_gate_is_80() -> None:
    text = (WORKFLOWS / "cbe-e2e.yml").read_text(encoding="utf-8")
    assert "--cov-fail-under=80" in text
    assert "--cov-fail-under=60" not in text

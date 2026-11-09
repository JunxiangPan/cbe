#!/usr/bin/env python3
"""Fail when the pinned CBS contract tag/bytes change.

This is a guard, not a CBE-08 PASS. CBE-08 stays DRAFT per CBS FREEZE_NOTICE.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from cbe.jsonio import print_json

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
USER_AGENT = "cbe-contract-guard/0.1"


def _get(url: str, timeout: int = 20) -> bytes:
    command = [
        "curl",
        "-fsSL",
        "--max-time",
        str(timeout),
        "-H",
        f"User-Agent: {USER_AGENT}",
        "-H",
        "Accept: application/vnd.github+json",
    ]
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        command += ["-H", f"Authorization: Bearer {token}"]
    command.append(url)
    process = subprocess.run(command, capture_output=True, check=False)
    if process.returncode != 0:
        message = process.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"curl exited {process.returncode}: {message[-500:]}")
    return process.stdout


def _head_sha(repo: str, branch: str) -> str:
    data = json.loads(_get(f"{API}/repos/{repo}/commits/{branch}"))
    sha = data.get("sha")
    if not isinstance(sha, str) or len(sha) != 40:
        raise ValueError("GitHub response did not contain a full commit SHA")
    return sha


def _tag_commit(repo: str, tag: str) -> str:
    data = json.loads(_get(f"{API}/repos/{repo}/git/ref/tags/{tag}"))
    obj = data.get("object") or {}
    sha = obj.get("sha")
    kind = obj.get("type")
    if not isinstance(sha, str) or len(sha) != 40:
        raise ValueError("tag ref did not contain a full object SHA")
    # Resolve an annotated tag to its commit; lightweight tags are commits.
    while kind == "tag":
        tag_data = json.loads(_get(f"{API}/repos/{repo}/git/tags/{sha}"))
        obj = tag_data.get("object") or {}
        sha = obj.get("sha")
        kind = obj.get("type")
        if not isinstance(sha, str) or len(sha) != 40:
            raise ValueError("annotated tag did not contain a full object SHA")
    return sha


def _resolve_ref(pin: dict[str, Any]) -> str:
    if pin.get("ref_type") == "tag":
        return _tag_commit(pin["repo"], pin["tag"])
    return _head_sha(pin["repo"], pin["branch"])


def has_conflict_markers(text: str) -> bool:
    return any(
        line.startswith(("<<<<<<<", ">>>>>>>", "|||||||")) or line.strip() == "======="
        for line in text.splitlines()
    )


def _error(code: str, message: str, details: list[Any]) -> int:
    print_json(
        {
            "schema_version": "1",
            "command": "cbe-contract-guard",
            "ok": False,
            "exit_code": 3,
            "gate_status": "FAIL",
            "error": {"code": code, "message": message, "details": details},
            "warnings": [],
        }
    )
    return 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pin", required=True)
    args = parser.parse_args(argv)
    pin = json.loads(Path(args.pin).read_text(encoding="utf-8"))
    try:
        observed_commit = _resolve_ref(pin)
        contract_bytes = _get(f"{RAW}/{pin['repo']}/{observed_commit}/{pin['contract_path']}")
        vm_bytes = _get(f"{RAW}/{pin['repo']}/{observed_commit}/{pin['vm_proof_path']}")
        addendum_bytes = _get(
            f"{RAW}/{pin['repo']}/{pin['addendum_commit']}/{pin['addendum_path']}"
        )
    except (RuntimeError, ValueError, KeyError, OSError) as exc:
        return _error(
            "CONTRACT_GUARD_UNAVAILABLE",
            f"cannot read the pinned CBS contract: {exc}",
            [{"pin": str(args.pin)}],
        )
    observed_sha = hashlib.sha256(contract_bytes).hexdigest()
    addendum_sha = hashlib.sha256(addendum_bytes).hexdigest()
    addendum_text = addendum_bytes.decode("utf-8", errors="replace")
    addendum_authorizes_pass = (
        "CBE-08 may be evaluated" in addendum_text
        and "status PASS is permitted" in addendum_text
    )
    vm_text = vm_bytes.decode("utf-8", errors="replace")
    vm_conflict = has_conflict_markers(vm_text)
    changes: list[dict[str, Any]] = []
    if observed_commit != pin["commit"]:
        changes.append(
            {
                "field": "commit",
                "pinned": pin["commit"],
                "observed": observed_commit,
                "action": "update the pin, CBE-08 draft, and audit package only after review",
            }
        )
    if observed_sha != pin["contract_sha256"]:
        changes.append(
            {
                "field": "contract_sha256",
                "pinned": pin["contract_sha256"],
                "observed": observed_sha,
                "action": "contract bytes changed; update CBE-08 draft and audit package",
            }
        )
    if vm_conflict:
        changes.append(
            {
                "field": "vm_proof",
                "pinned": "clean",
                "observed": "conflict markers",
                "action": "CBS must resolve vm-proof.yml conflicts",
            }
        )
    if addendum_sha != pin["addendum_sha256"]:
        changes.append(
            {
                "field": "addendum_sha256",
                "pinned": pin["addendum_sha256"],
                "observed": addendum_sha,
                "action": "the CBE-08 addendum changed; re-review authorization before flipping PASS",
            }
        )
    if not addendum_authorizes_pass:
        changes.append(
            {
                "field": "addendum_authorization",
                "pinned": "CBE-08 may be evaluated; status PASS is permitted",
                "observed": "authorization phrase missing",
                "action": "do not report CBE-08 PASS",
            }
        )
    if changes:
        return _error(
            "CONTRACT_CHANGED",
            "the pinned CBS contract no longer matches CBE's pin",
            changes,
        )
    print_json(
        {
            "schema_version": "1",
            "command": "cbe-contract-guard",
            "ok": True,
            "exit_code": 0,
            "gate_status": "PINNED",
            "pin": {
                "repo": pin["repo"],
                "ref_type": pin.get("ref_type", "branch"),
                "tag": pin.get("tag"),
                "branch": pin.get("branch"),
                "commit": pin["commit"],
                "contract_sha256": pin["contract_sha256"],
                "frozen": bool(pin.get("frozen", False)),
                "addendum_commit": pin["addendum_commit"],
                "addendum_sha256": pin["addendum_sha256"],
                "cbe08_pass_authorized": bool(pin.get("cbe08_pass_authorized", False)),
            },
            "observed": {
                "commit": observed_commit,
                "contract_sha256": observed_sha,
                "vm_proof_clean": not vm_conflict,
                "addendum_sha256": addendum_sha,
                "addendum_authorizes_pass": addendum_authorizes_pass,
            },
            "error": None,
            "warnings": [],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

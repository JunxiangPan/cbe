"""Strict exemption-file parsing shared by no-bypass and provider runs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import InputError
from .manifest import RuleSet
from .walk import read_text

EXEMPTION_RE = re.compile(
    r"^SKIPPED:\s+(CBE-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3})\s+reason=(.*)$"
)


@dataclass
class Exemption:
    rule_id: str
    reason: str
    line: int
    blocking: bool
    applicable: bool
    counted: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "reason": self.reason,
            "line": self.line,
            "blocking": self.blocking,
            "applicable": self.applicable,
            "counted": self.counted,
        }


def parse_exemptions(
    path: str | None,
    ruleset: RuleSet,
    applicable_ids: set[str],
) -> tuple[list[Exemption], list[dict[str, Any]]]:
    if not path:
        return [], []
    file_path = Path(path)
    if not file_path.is_file():
        raise InputError("EXEMPTIONS_NOT_FOUND", f"exemptions file not found: {path}")
    text = read_text(file_path)
    if text is None:
        raise InputError("EXEMPTIONS_NOT_UTF8", f"exemptions file is not UTF-8 text: {path}")

    exemptions: list[Exemption] = []
    errors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = EXEMPTION_RE.match(stripped)
        if not match:
            errors.append(
                {
                    "path": str(file_path),
                    "line": line_no,
                    "code": "EXEMPTION_FORMAT",
                    "message": "expected: SKIPPED: <CBE-rule-id> reason=<non-empty>",
                }
            )
            continue
        rule_id, reason = match.group(1), match.group(2).strip()
        if not reason:
            errors.append(
                {
                    "path": str(file_path),
                    "line": line_no,
                    "code": "EXEMPTION_REASON_MISSING",
                    "message": "reason must be non-empty",
                }
            )
            continue
        if len(reason) > 200 or any(ord(char) < 32 for char in reason):
            errors.append(
                {
                    "path": str(file_path),
                    "line": line_no,
                    "code": "EXEMPTION_REASON_INVALID",
                    "message": "reason must be <=200 printable characters",
                }
            )
            continue
        rule = ruleset.rule(rule_id)
        if rule is None:
            errors.append(
                {
                    "path": str(file_path),
                    "line": line_no,
                    "code": "EXEMPTION_UNKNOWN_RULE",
                    "message": f"rule does not exist in the manifest: {rule_id}",
                }
            )
            continue
        if rule_id in seen:
            errors.append(
                {
                    "path": str(file_path),
                    "line": line_no,
                    "code": "EXEMPTION_DUPLICATE",
                    "message": f"duplicate exemption for: {rule_id}",
                }
            )
            continue
        seen.add(rule_id)
        blocking = rule.gate == "blocking"
        applicable = rule_id in applicable_ids
        exemptions.append(
            Exemption(
                rule_id=rule_id,
                reason=reason,
                line=line_no,
                blocking=blocking,
                applicable=applicable,
                counted=applicable and not blocking,
            )
        )
    return exemptions, errors

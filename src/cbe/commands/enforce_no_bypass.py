"""enforce-no-bypass: reject rule-disable attempts and apply explicit exemptions."""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

from ..errors import InputError
from ..manifest import Inspection, RuleSet, load_and_inspect
from ..walk import (
    exclude_matches,
    is_cbe_repository,
    iter_source_files,
    read_text,
    resolve_source_root,
    workflow_files,
)

COMMAND = "enforce-no-bypass"

RULE_ID_RE = re.compile(r"\bCBE-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3}\b")
EXEMPTION_RE = re.compile(
    r"^SKIPPED:\s+(CBE-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3})\s+reason=(.*)$"
)
COMMENT_RE = re.compile(
    r"(?i)(?:\bcbe\b|\bcyber[-_ ]?butler\b)\s*(?:[:#-]\s*)?(?:disable|skip|ignore|off)\b"
)
NOQA_RE = re.compile(
    r"(?i)\b(?:noqa|nosec)\b[^\n]*\b(CBE-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3})\b"
)
ENV_RE = re.compile(
    r"(?i)^(?:CBE|CYBER_BUTLER)_(?:DISABLE|DISABLED|SKIP|IGNORE|EXCLUDE|NO)(?:_.*)?$"
    r"|^(?:CBE_RULES_EXCLUDE|NO_CBE|CBE_OFF)$"
)
DISABLE_KEY_RE = re.compile(r"(?i)\b[\"']?(?:disable|disabled|skip|ignore|exclude)[\"']?\s*[:=]")
DISABLE_FALSE_RE = re.compile(
    r"(?i)\b[\"']?(?:disable|disabled|skip|ignore|exclude)[\"']?\s*[:=]\s*[\"']?(?:false|no|0)[\"']?\b"
)
DISABLE_EMPTY_RE = re.compile(
    r"(?i)\b[\"']?(?:disable|disabled|skip|ignore|exclude)[\"']?\s*[:=]\s*(?:\[\]|\{\}|\"\"|'')"
)
ENABLED_FALSE_RE = re.compile(
    r"(?i)\b[\"']?enabled[\"']?\s*[:=]\s*[\"']?(?:false|no|0)[\"']?\b"
)

DEFAULT_CONFIG_PATHS = (
    "cbe.yml",
    "cbe.yaml",
    "cbe.toml",
    "cbe.json",
    ".cbe/config.yml",
    ".cbe/config.yaml",
    ".cbe/config.toml",
    ".cbe/config.json",
)
CBE_WORKFLOW = ".github/workflows/cbe-e2e.yml"
CBE_GATE_JOB_RE = re.compile(r"(?i)^cbe[-_]gate$")
COMMENTED_GATE_RE = re.compile(r"(?im)^\s*#\s*cbe[-_]gate\s*:")


@dataclass
class BypassAttempt:
    kind: str
    path: str
    line: int
    rule_id: str
    evidence: str
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "path": self.path,
            "line": self.line,
            "rule_id": self.rule_id,
            "evidence": self.evidence[:200],
            "reason": self.reason,
            "action": "FAIL",
        }


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


@dataclass
class ScanState:
    attempts: list[BypassAttempt] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    files: int = 0
    configs: int = 0
    env_vars: int = 0
    workflows: int = 0

    def add(self, attempt: BypassAttempt) -> None:
        key = (attempt.kind, attempt.path, attempt.line, attempt.rule_id)
        if not any((item.kind, item.path, item.line, item.rule_id) == key for item in self.attempts):
            self.attempts.append(attempt)


def _warn(state: ScanState, code: str, message: str, *, path: str = "", line: int = 0) -> None:
    item = {"code": code, "message": message}
    if path:
        item["path"] = path
    if line:
        item["line"] = line
    if item not in state.warnings:
        state.warnings.append(item)


def _first_rule_id(text: str, fallback: str = "*") -> str:
    match = RULE_ID_RE.search(text)
    return match.group(0) if match else fallback


def _scan_configs(root: Path, explicit: Iterable[str] | None, state: ScanState) -> None:
    paths: list[Path] = []
    if explicit:
        for raw in explicit:
            path = Path(raw)
            if not path.is_file():
                raise InputError("CONFIG_NOT_FOUND", f"config file not found: {raw}")
            paths.append(path)
    else:
        paths = [root / relative for relative in DEFAULT_CONFIG_PATHS if (root / relative).is_file()]

    for path in paths:
        text = read_text(path)
        if text is None:
            _warn(state, "CONFIG_BINARY_SKIPPED", "config is not UTF-8 text", path=str(path))
            continue
        state.configs += 1
        all_ids = RULE_ID_RE.findall(text)
        fallback = all_ids[0] if all_ids else "*"
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "//", ";")):
                continue
            lower = stripped.lower()
            if DISABLE_FALSE_RE.search(lower) or DISABLE_EMPTY_RE.search(lower):
                continue
            if DISABLE_KEY_RE.search(lower) or ENABLED_FALSE_RE.search(lower):
                state.add(
                    BypassAttempt(
                        kind="config",
                        path=str(path),
                        line=line_no,
                        rule_id=_first_rule_id(stripped, fallback),
                        evidence=stripped,
                    )
                )


def _scan_comments(root: Path, state: ScanState) -> None:
    for path in iter_source_files(root):
        text = read_text(path)
        if text is None:
            continue
        state.files += 1
        relative = path.relative_to(root.resolve()).as_posix()
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if "SKIPPED:" in stripped:
                _warn(
                    state,
                    "INLINE_EXEMPTION_IGNORED",
                    "inline SKIPPED text is not an exemption; use the exemptions file",
                    path=relative,
                    line=line_no,
                )
            if COMMENT_RE.search(stripped):
                state.add(
                    BypassAttempt(
                        kind="comment",
                        path=relative,
                        line=line_no,
                        rule_id=_first_rule_id(stripped),
                        evidence=stripped,
                    )
                )
                continue
            noqa = NOQA_RE.search(stripped)
            if noqa:
                state.add(
                    BypassAttempt(
                        kind="comment",
                        path=relative,
                        line=line_no,
                        rule_id=noqa.group(1),
                        evidence=stripped,
                    )
                )


def _scan_env(env_files: Iterable[str] | None, state: ScanState) -> None:
    for name in sorted(os.environ):
        if ENV_RE.match(name):
            state.env_vars += 1
            state.add(
                BypassAttempt(
                    kind="env",
                    path="<process-env>",
                    line=0,
                    rule_id="*",
                    evidence=name,
                )
            )

    for raw in env_files or []:
        path = Path(raw)
        if not path.is_file():
            raise InputError("ENV_FILE_NOT_FOUND", f"env file not found: {raw}")
        text = read_text(path)
        if text is None:
            _warn(state, "ENV_FILE_BINARY_SKIPPED", "env file is not UTF-8 text", path=str(path))
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            name = stripped.split("=", 1)[0].strip()
            if ENV_RE.match(name):
                state.env_vars += 1
                state.add(
                    BypassAttempt(
                        kind="env",
                        path=str(path),
                        line=line_no,
                        rule_id="*",
                        evidence=name,
                    )
                )


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return []


def _literal_false(value: Any) -> bool:
    if value is False:
        return True
    if isinstance(value, bool):
        return value is False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value == 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text.startswith("${{") and text.endswith("}}"):
            text = text[3:-2].strip()
        return text in {"false", "0", "no"}
    return False


def _job_unreachable(job_name: str, jobs: dict[str, Any], seen: set[str] | None = None) -> bool:
    """A job cannot run if its if is literal false or a dependency is unreachable."""

    visited = set(seen or ())
    if job_name in visited:
        return False
    visited.add(job_name)
    job = jobs.get(job_name)
    if not isinstance(job, dict):
        return True
    if _literal_false(job.get("if")):
        return True
    for dependency in _as_list(job.get("needs")):
        if not isinstance(dependency, str):
            continue
        if dependency not in jobs:
            return True
        if _job_unreachable(dependency, jobs, visited):
            return True
    return False


def _line_for(text: str, needle: str) -> int:
    for line_no, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return line_no
    return 0


def _scan_workflow_jobs(relative: str, text: str, state: ScanState) -> None:
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        _warn(state, "WORKFLOW_PARSE_FAILED", f"cannot parse workflow: {exc}", path=relative)
        return
    if not isinstance(document, dict):
        return
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return

    for job_name in jobs:
        if not isinstance(job_name, str) or not CBE_GATE_JOB_RE.match(job_name):
            continue
        if _job_unreachable(job_name, jobs):
            state.add(
                BypassAttempt(
                    kind="workflow",
                    path=relative,
                    line=_line_for(text, f"{job_name}:"),
                    rule_id="*",
                    evidence=f"job={job_name} is unreachable",
                    reason="WORKFLOW_SKIPS_CBE_GATE",
                )
            )

    for match in COMMENTED_GATE_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        state.add(
            BypassAttempt(
                kind="workflow",
                path=relative,
                line=line_no,
                rule_id="*",
                evidence=match.group(0).strip(),
                reason="WORKFLOW_SKIPS_CBE_GATE",
            )
        )


def _scan_workflows(root: Path, patterns: Iterable[str] | None, state: ScanState) -> None:
    excluded = list(patterns or [])
    if is_cbe_repository(root) and not exclude_matches(CBE_WORKFLOW, excluded):
        raise InputError(
            "SELF_WORKFLOW_EXCLUSION_REQUIRED",
            "scanning CBE itself requires --exclude-workflow .github/workflows/cbe-e2e.yml",
        )

    for path in workflow_files(root):
        relative = path.relative_to(root).as_posix()
        if exclude_matches(relative, excluded):
            continue
        text = read_text(path)
        if text is None:
            _warn(state, "WORKFLOW_BINARY_SKIPPED", "workflow is not UTF-8 text", path=relative)
            continue
        state.workflows += 1
        _scan_workflow_jobs(relative, text, state)
        for line_no, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            if (
                re.search(r"\bcontinue-on-error\s*:\s*true\b", lowered)
                or re.search(r"\|\|\s*true\b", lowered)
                or re.search(r"\bif\s*:\s*always\s*\(\s*\)", lowered)
            ):
                state.add(
                    BypassAttempt(
                        kind="workflow",
                        path=relative,
                        line=line_no,
                        rule_id="*",
                        evidence=line.strip(),
                    )
                )


def _parse_exemptions(
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


def _inspection_failure(inspection: Inspection) -> dict[str, Any] | None:
    if not inspection.errors:
        return None
    return {
        "schema_version": "1",
        "command": COMMAND,
        "ok": False,
        "exit_code": 2,
        "gate_status": "FAIL",
        "bypass_attempts": [],
        "exemptions": [],
        "scanned": {"files": 0, "configs": 0, "env_vars": 0, "workflows": 0},
        "applicable_count": 0,
        "skip_count": 0,
        "not_applicable_count": 0,
        "skip_ratio": 0.0,
        "blocking_skip": False,
        "error": {
            "code": "MANIFEST_INVALID",
            "message": "manifest failed schema or semantic validation",
            "details": inspection.errors,
        },
        "warnings": [],
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    inspection = load_and_inspect(
        args.manifest,
        package_type=args.package_type,
        package_version=args.package_version,
    )
    failure = _inspection_failure(inspection)
    if failure is not None:
        return failure

    assert inspection.ruleset is not None
    ruleset = inspection.ruleset
    applicable_ids = {
        item["rule_id"]
        for item in inspection.applicable_rules
        if item.get("status") == "APPLICABLE"
    }
    applicable_rules = [rule for rule in (ruleset.rule(rule_id) for rule_id in applicable_ids) if rule]
    advisory_count = sum(1 for rule in applicable_rules if rule.gate == "advisory")
    blocking_count = sum(1 for rule in applicable_rules if rule.gate == "blocking")

    exemptions, exemption_errors = _parse_exemptions(args.exemptions, ruleset, applicable_ids)
    if exemption_errors:
        return {
            "schema_version": "1",
            "command": COMMAND,
            "ok": False,
            "exit_code": 2,
            "gate_status": "FAIL",
            "bypass_attempts": [],
            "exemptions": [],
            "scanned": {"files": 0, "configs": 0, "env_vars": 0, "workflows": 0},
            "applicable_count": advisory_count,
            "skip_count": 0,
            "not_applicable_count": inspection.not_applicable_rule_count or 0,
            "skip_ratio": 0.0,
            "blocking_skip": False,
            "error": {
                "code": "EXEMPTIONS_INVALID",
                "message": "exemption file is invalid",
                "details": exemption_errors,
            },
            "warnings": inspection.warnings,
        }

    root = resolve_source_root(args.source_root)
    state = ScanState(warnings=list(inspection.warnings))
    _scan_configs(root, args.config, state)
    _scan_comments(root, state)
    _scan_env(args.env_file, state)
    if args.workflows:
        _scan_workflows(root, args.exclude_workflow, state)

    skip_count = sum(1 for exemption in exemptions if exemption.counted)
    blocking_skip = any(exemption.blocking for exemption in exemptions) or any(
        error.get("code") == "BLOCKING_RULE_NOT_APPLICABLE" for error in inspection.gate_errors
    )
    not_applicable_count = inspection.not_applicable_rule_count or 0
    skip_ratio = (skip_count / advisory_count) if advisory_count else 0.0

    for exemption in exemptions:
        if not exemption.applicable:
            _warn(
                state,
                "EXEMPTION_NOT_APPLICABLE",
                f"exemption is not applicable to {args.package_type} {args.package_version}: {exemption.rule_id}",
            )
    if advisory_count == 0 and not inspection.gate_errors:
        _warn(state, "NO_ADVISORY_CHECKS", "no applicable advisory check; skip_ratio is 0 by definition")

    exit_code = 0
    error: dict[str, Any] | None = None
    if state.attempts:
        exit_code = 3
        error = {
            "code": "BYPASS_ATTEMPT",
            "message": "rule-disable attempt detected",
            "details": [attempt.as_dict() for attempt in state.attempts],
        }
    elif blocking_skip:
        exit_code = 3
        error = {
            "code": "BLOCKING_SKIP",
            "message": "a blocking rule or check was skipped",
            "details": inspection.gate_errors,
        }
    elif inspection.gate_errors:
        exit_code = 3
        first = inspection.gate_errors[0]
        error = {"code": first["code"], "message": first["message"], "details": inspection.gate_errors}
    elif advisory_count and skip_count * 5 > advisory_count:
        exit_code = 4
        error = {
            "code": "SKIP_RATIO_EXCEEDED",
            "message": f"skip ratio {skip_count}/{advisory_count} is above 20%",
            "details": [{"path": "$.skip_ratio", "code": "SKIP_RATIO_EXCEEDED", "message": "> 0.20"}],
        }

    return {
        "schema_version": "1",
        "command": COMMAND,
        "ok": exit_code == 0,
        "exit_code": exit_code,
        "gate_status": "PASS" if exit_code == 0 else "FAIL",
        "bypass_attempts": [attempt.as_dict() for attempt in state.attempts],
        "exemptions": [exemption.as_dict() for exemption in exemptions],
        "scanned": {
            "files": state.files,
            "configs": state.configs,
            "env_vars": state.env_vars,
            "workflows": state.workflows,
        },
        "applicable_count": advisory_count,
        "skip_count": skip_count,
        "not_applicable_count": not_applicable_count,
        "skip_ratio": round(skip_ratio, 6),
        "blocking_skip": blocking_skip,
        "blocking_applicable_count": blocking_count,
        "error": error,
        "warnings": state.warnings,
    }

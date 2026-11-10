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
from ..exemptions import parse_exemptions
from ..manifest import Inspection, load_and_inspect
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
DEFAULT_GATE_JOB = r"^cbe[-_]gate$"
STRICT_UNVERIFIABLE_CODES = {
    "UNVERIFIABLE_CONDITION",
    "UNVERIFIABLE_NEEDS_CHAIN",
    "UNVERIFIABLE_REMOTE_WORKFLOW",
    "UNVERIFIABLE_LOCAL_WORKFLOW",
    "GATE_JOB_NOT_FOUND",
}


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


@dataclass(frozen=True)
class Reachability:
    status: str  # reachable | unreachable | unknown
    reason: str = ""
    needs_unknown: bool = False


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


def _strip_expression(value: str) -> str:
    text = value.strip()
    if text.startswith("${{") and text.endswith("}}"):
        text = text[3:-2].strip()
    return text


def _literal_value(token: str) -> Any:
    text = token.strip()
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if re.fullmatch(r"-?[0-9]+", text):
        return int(text)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    raise ValueError(text)


def _evaluate_condition(value: Any) -> tuple[str, str]:
    """Evaluate a literal GitHub Actions condition.

    Returns ("true" | "false" | "unknown", reason). Dynamic contexts
    (inputs.*, vars.*, github.*, functions) are unknown, never a silent PASS.
    """

    if value is None:
        return ("true", "")
    if isinstance(value, bool):
        return ("true" if value else "false", "")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return ("true" if value != 0 else "false", "")
    if not isinstance(value, str):
        return ("unknown", f"unsupported if value: {type(value).__name__}")

    expression = _strip_expression(value)
    if not expression:
        return ("true", "")
    lowered = expression.lower()
    if lowered in {"true", "false"}:
        return (lowered, "")
    if re.fullmatch(r"-?[0-9]+", expression):
        return ("true" if int(expression) != 0 else "false", "")

    dynamic_markers = (
        "inputs.",
        "vars.",
        "github.",
        "secrets.",
        "env.",
        "needs.",
        "matrix.",
        "steps.",
        "always(",
        "success(",
        "failure(",
        "cancelled(",
        "hashfiles(",
        "__import__",
        "system(",
        "popen(",
        "subprocess",
        "eval(",
        "exec(",
    )
    if any(marker in lowered for marker in dynamic_markers):
        return ("unknown", f"dynamic expression: {expression}")

    for separator, combine in (("||", any), ("&&", all)):
        parts = [part.strip() for part in expression.split(separator)]
        if len(parts) > 1:
            values: list[bool] = []
            for part in parts:
                status, _reason = _evaluate_condition(part)
                if status == "unknown":
                    return ("unknown", f"cannot evaluate: {expression}")
                values.append(status == "true")
            return ("true" if combine(values) else "false", "")

    if expression.startswith("!"):
        status, _reason = _evaluate_condition(expression[1:].strip())
        if status == "unknown":
            return ("unknown", f"cannot evaluate: {expression}")
        return ("false" if status == "true" else "true", "")

    comparison = re.fullmatch(r"(.+?)\s*(==|!=)\s*(.+)", expression)
    if comparison:
        left_token, operator, right_token = comparison.groups()
        try:
            left = _literal_value(left_token)
            right = _literal_value(right_token)
        except ValueError:
            return ("unknown", f"cannot evaluate comparison: {expression}")
        equal = left == right
        result = equal if operator == "==" else not equal
        return ("true" if result else "false", "")

    return ("unknown", f"cannot evaluate expression: {expression}")


def _job_reachability(job_name: str, jobs: dict[str, Any], seen: set[str] | None = None) -> Reachability:
    """Return whether a job can run, using only statically evaluable conditions."""

    visited = set(seen or ())
    if job_name in visited:
        return Reachability("reachable", "dependency cycle")
    visited.add(job_name)
    job = jobs.get(job_name)
    if not isinstance(job, dict):
        return Reachability("unreachable", f"job not found: {job_name}")

    own_status = "true"
    own_reason = ""
    if job.get("if") is not None:
        own_status, own_reason = _evaluate_condition(job.get("if"))
        if own_status == "false":
            return Reachability("unreachable", f"literal false if: {job.get('if')}")

    needs_unknown = False
    for dependency in _as_list(job.get("needs")):
        if not isinstance(dependency, str):
            continue
        if dependency not in jobs:
            return Reachability("unreachable", f"missing needs job: {dependency}")
        dependency_status = _job_reachability(dependency, jobs, visited)
        if dependency_status.status == "unreachable":
            return Reachability("unreachable", f"needs {dependency}: {dependency_status.reason}")
        if dependency_status.status == "unknown":
            needs_unknown = True

    if own_status == "unknown" or needs_unknown:
        reason = own_reason if own_status == "unknown" else "needs chain is unverifiable"
        return Reachability("unknown", reason, needs_unknown)
    return Reachability("reachable")


def _line_for(text: str, needle: str) -> int:
    for line_no, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return line_no
    return 0


def _workflow_job_uses(document: dict[str, Any]) -> list[str]:
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return []
    uses: list[str] = []
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        value = job.get("uses")
        if isinstance(value, str) and value.strip():
            uses.append(value.strip())
    return uses


def _resolve_local_workflow(root: Path, raw: str) -> tuple[Path | None, str]:
    if not raw.startswith("./.github/workflows/"):
        return None, "local workflow must be under ./.github/workflows/"
    target = (root / raw[2:]).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None, "local workflow escapes the source root"
    if target.suffix.lower() not in {".yml", ".yaml"}:
        return None, "local workflow is not a YAML file"
    if not target.is_file():
        return None, "local workflow file is missing"
    return target, ""


def _commented_gate_lines(text: str, gate_job_re: re.Pattern[str]) -> Iterable[tuple[int, str]]:
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        body = stripped[1:].strip()
        match = re.match(r"([A-Za-z0-9_.-]+)\s*:", body)
        if match and gate_job_re.search(match.group(1)):
            yield line_no, line.strip()


def _scan_workflow_jobs(
    relative: str,
    text: str,
    state: ScanState,
    gate_job_re: re.Pattern[str],
) -> dict[str, Any] | None:
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        _warn(state, "WORKFLOW_PARSE_FAILED", f"cannot parse workflow: {exc}", path=relative)
        return None
    if not isinstance(document, dict):
        return None
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return document

    matched = False
    for job_name, job in jobs.items():
        if not isinstance(job_name, str) or not gate_job_re.search(job_name):
            continue
        matched = True
        line_no = _line_for(text, f"{job_name}:")
        reachability = _job_reachability(job_name, jobs)
        if reachability.status == "unreachable":
            state.add(
                BypassAttempt(
                    kind="workflow",
                    path=relative,
                    line=line_no,
                    rule_id="*",
                    evidence=f"job={job_name} is unreachable: {reachability.reason}",
                    reason="WORKFLOW_SKIPS_CBE_GATE",
                )
            )
            continue
        if reachability.status == "unknown":
            own_status = "true"
            if isinstance(job, dict) and job.get("if") is not None:
                own_status, _reason = _evaluate_condition(job.get("if"))
            if own_status == "unknown":
                _warn(
                    state,
                    "UNVERIFIABLE_CONDITION",
                    f"{job_name} if condition cannot be statically evaluated: {job.get('if')}",
                    path=relative,
                    line=line_no,
                )
            if reachability.needs_unknown:
                _warn(
                    state,
                    "UNVERIFIABLE_NEEDS_CHAIN",
                    f"{job_name} needs chain contains a condition that cannot be statically evaluated",
                    path=relative,
                    line=line_no,
                )
            if own_status != "unknown" and not reachability.needs_unknown:
                _warn(
                    state,
                    "UNVERIFIABLE_CONDITION",
                    f"{job_name} reachability cannot be statically determined",
                    path=relative,
                    line=line_no,
                )

    if not matched:
        _warn(
            state,
            "GATE_JOB_NOT_FOUND",
            f"no job matches gate-job regex {gate_job_re.pattern!r}; use --gate-job for renamed gates",
            path=relative,
        )

    for line_no, evidence in _commented_gate_lines(text, gate_job_re):
        state.add(
            BypassAttempt(
                kind="workflow",
                path=relative,
                line=line_no,
                rule_id="*",
                evidence=evidence,
                reason="WORKFLOW_SKIPS_CBE_GATE",
            )
        )
    return document


def _scan_workflows(
    root: Path,
    patterns: Iterable[str] | None,
    state: ScanState,
    gate_job_re: re.Pattern[str],
) -> None:
    excluded = list(patterns or [])
    if is_cbe_repository(root) and not exclude_matches(CBE_WORKFLOW, excluded):
        raise InputError(
            "SELF_WORKFLOW_EXCLUSION_REQUIRED",
            "scanning CBE itself requires --exclude-workflow .github/workflows/cbe-e2e.yml",
        )

    seen: set[str] = set()

    def scan(path: Path) -> None:
        relative = path.relative_to(root).as_posix()
        if relative in seen or exclude_matches(relative, excluded):
            return
        seen.add(relative)
        text = read_text(path)
        if text is None:
            _warn(state, "WORKFLOW_BINARY_SKIPPED", "workflow is not UTF-8 text", path=relative)
            return
        state.workflows += 1
        document = _scan_workflow_jobs(relative, text, state, gate_job_re)
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
        if not isinstance(document, dict):
            return
        for use in _workflow_job_uses(document):
            line_no = _line_for(text, use)
            if use.startswith("./"):
                target, error = _resolve_local_workflow(root, use)
                if error:
                    _warn(
                        state,
                        "UNVERIFIABLE_LOCAL_WORKFLOW",
                        f"cannot inspect local reusable workflow {use}: {error}",
                        path=relative,
                        line=line_no,
                    )
                elif target is not None:
                    scan(target)
            else:
                _warn(
                    state,
                    "UNVERIFIABLE_REMOTE_WORKFLOW",
                    f"remote reusable workflow is not fetched: {use}",
                    path=relative,
                    line=line_no,
                )

    for path in workflow_files(root):
        scan(path)


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
        "warn_count": 0,
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

    gate_job_pattern = getattr(args, "gate_job", DEFAULT_GATE_JOB) or DEFAULT_GATE_JOB
    try:
        gate_job_re = re.compile(gate_job_pattern)
    except re.error as exc:
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
            "warn_count": len(inspection.warnings),
            "strict": bool(getattr(args, "strict", False)),
            "gate_job": gate_job_pattern,
            "error": {
                "code": "INVALID_GATE_JOB_REGEX",
                "message": f"invalid --gate-job regex: {exc}",
                "details": [],
            },
            "warnings": inspection.warnings,
        }

    exemptions, exemption_errors = parse_exemptions(args.exemptions, ruleset, applicable_ids)
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
            "warn_count": len(inspection.warnings),
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
        _scan_workflows(root, args.exclude_workflow, state, gate_job_re)

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
    strict_warnings = (
        [warning for warning in state.warnings if warning.get("code") in STRICT_UNVERIFIABLE_CODES]
        if getattr(args, "strict", False)
        else []
    )
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
    elif strict_warnings:
        exit_code = 3
        first = next(
            (warning for warning in strict_warnings if warning.get("code") != "GATE_JOB_NOT_FOUND"),
            strict_warnings[0],
        )
        error = {
            "code": first["code"],
            "message": "strict mode: an unverifiable gate condition cannot be treated as PASS",
            "details": strict_warnings,
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
        "strict": bool(getattr(args, "strict", False)),
        "gate_job": gate_job_pattern,
        "warn_count": len(state.warnings),
        "error": error,
        "warnings": state.warnings,
    }

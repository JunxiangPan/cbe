"""Provider execution, artifact validation, and rule-result assembly (P0-05)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from .errors import GateError, InputError
from .exemptions import Exemption, parse_exemptions
from .jsonio import load_json, sha256_json
from .manifest import Inspection, Rule, RuleSet

from .paths import schema_path

PROVIDER_SCHEMA_PATH = schema_path("provider-output.v1.schema.json")


class ProviderError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class Finding:
    rule_id: str
    level: str
    message: str
    path: str
    line: int
    column: int
    provider_id: str


@dataclass
class ProviderResult:
    provider_id: str
    status: str
    process_exit_code: int = 0
    artifact_status: str = "none"
    sarif_path: str | None = None
    json_path: str | None = None
    result_count: int = 0
    namespace_ok: bool = True
    infra: bool = False
    error: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": self.status,
            "process_exit_code": self.process_exit_code,
            "artifact_status": self.artifact_status,
            "sarif_path": self.sarif_path,
            "json_path": self.json_path,
            "result_count": self.result_count,
            "namespace_ok": self.namespace_ok,
            "infra": self.infra,
            "error": self.error,
        }


@dataclass
class RunOutcome:
    providers: list[ProviderResult] = field(default_factory=list)
    rule_results: list[dict[str, Any]] = field(default_factory=list)
    applicable_count: int = 0
    skip_count: int = 0
    not_applicable_count: int = 0
    skip_ratio: float = 0.0
    blocking_skip: bool = False
    warn_count: int = 0
    sarif_paths: list[str] = field(default_factory=list)
    json_paths: list[str] = field(default_factory=list)
    exit_code: int = 0
    gate_status: str = "PASS"
    error: dict[str, Any] | None = None


def _provider_dir(out_dir: Path, provider_id: str) -> Path:
    safe = "".join(char if char.isalnum() or char in {"_", "-", "."} else "_" for char in provider_id)
    directory = out_dir / safe
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _expand(command: Iterable[str], values: dict[str, str]) -> list[str]:
    expanded: list[str] = []
    for token in command:
        for key, value in values.items():
            token = token.replace("{" + key + "}", value)
        expanded.append(token)
    return expanded


def _relative(out_dir: Path, path: Path) -> str:
    try:
        return path.relative_to(out_dir).as_posix()
    except ValueError:
        return path.as_posix()


def _rule_for_native(ruleset: RuleSet, provider_id: str, native_id: str) -> Rule:
    direct = ruleset.rule(native_id)
    if direct is not None and direct.provider == provider_id:
        return direct
    for rule in ruleset.rules:
        if rule.provider == provider_id and native_id in rule.provider_rule_ids:
            return rule
    raise ProviderError("UNMAPPED_PROVIDER_RULE", f"provider rule is not mapped to a CBE rule: {native_id}")


def _sarif_findings(path: Path, ruleset: RuleSet, provider_id: str) -> list[Finding]:
    try:
        data = load_json(path)
    except InputError as exc:
        raise ProviderError("PROVIDER_ARTIFACT_INVALID", f"SARIF is not valid JSON: {exc.message}") from exc
    if not isinstance(data, dict) or data.get("version") != "2.1.0":
        raise ProviderError("PROVIDER_ARTIFACT_INVALID", "SARIF version must be 2.1.0")
    runs = data.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ProviderError("PROVIDER_ARTIFACT_INVALID", "SARIF has no runs")
    findings: list[Finding] = []
    for run in runs:
        tool = run.get("tool") if isinstance(run, dict) else None
        driver = tool.get("driver") if isinstance(tool, dict) else None
        if not isinstance(driver, dict) or not isinstance(driver.get("name"), str):
            raise ProviderError("PROVIDER_ARTIFACT_INVALID", "SARIF run has no tool.driver.name")
        results = run.get("results", [])
        if not isinstance(results, list):
            raise ProviderError("PROVIDER_ARTIFACT_INVALID", "SARIF results must be an array")
        for result in results:
            if not isinstance(result, dict):
                raise ProviderError("PROVIDER_ARTIFACT_INVALID", "SARIF result must be an object")
            native_id = result.get("ruleId")
            if not isinstance(native_id, str) or not native_id:
                raise ProviderError("PROVIDER_ARTIFACT_INVALID", "SARIF result has no ruleId")
            rule = _rule_for_native(ruleset, provider_id, native_id)
            level = result.get("level", "warning")
            if level not in {"error", "warning", "note"}:
                raise ProviderError("PROVIDER_ARTIFACT_INVALID", f"invalid SARIF level: {level}")
            message = result.get("message", {}).get("text", "")
            if not isinstance(message, str) or not message:
                raise ProviderError("PROVIDER_ARTIFACT_INVALID", "SARIF result has no message.text")
            locations = result.get("locations", [])
            if not isinstance(locations, list) or not locations:
                raise ProviderError("PROVIDER_ARTIFACT_INVALID", "SARIF result has no locations")
            physical = locations[0].get("physicalLocation", {})
            artifact = physical.get("artifactLocation", {})
            region = physical.get("region", {})
            uri = artifact.get("uri", "")
            if not isinstance(uri, str) or not uri:
                raise ProviderError("PROVIDER_ARTIFACT_INVALID", "SARIF result has no artifact URI")
            findings.append(
                Finding(
                    rule_id=rule.rule_id,
                    level=level,
                    message=message,
                    path=uri.replace("\\", "/"),
                    line=max(1, int(region.get("startLine", 1) or 1)),
                    column=max(1, int(region.get("startColumn", 1) or 1)),
                    provider_id=provider_id,
                )
            )
    return findings


def _json_findings(path: Path, ruleset: RuleSet, provider_id: str) -> list[Finding]:
    try:
        data = load_json(path)
    except InputError as exc:
        raise ProviderError("PROVIDER_ARTIFACT_INVALID", f"provider JSON is not valid: {exc.message}") from exc
    try:
        schema = json.loads(PROVIDER_SCHEMA_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InputError("PROVIDER_SCHEMA_UNAVAILABLE", f"cannot read provider schema: {exc}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda item: list(item.path))
    if errors:
        raise ProviderError("PROVIDER_ARTIFACT_INVALID", f"provider JSON schema error: {errors[0].message}")

    findings: list[Finding] = []
    for result in data.get("results", []):
        native_id = result.get("provider_rule_id") or result.get("rule_id", "")
        rule = _rule_for_native(ruleset, provider_id, native_id)
        location = result.get("location", {})
        findings.append(
            Finding(
                rule_id=rule.rule_id,
                level=result.get("level", "warning"),
                message=result.get("message", ""),
                path=str(location.get("path", "")).replace("\\", "/"),
                line=max(1, int(location.get("start_line", 1) or 1)),
                column=max(1, int(location.get("start_column", 1) or 1)),
                provider_id=provider_id,
            )
        )
    return findings


def _artifact_files(directory: Path, suffix: str) -> list[Path]:
    return sorted(directory.glob(f"*{suffix}"))


def _validate_artifact(path: Path, ruleset: RuleSet, provider_id: str, fmt: str) -> list[Finding]:
    if not path.is_file():
        raise ProviderError("PROVIDER_ARTIFACT_MISSING", f"declared {fmt} artifact is missing: {path.name}")
    if path.stat().st_size == 0:
        raise ProviderError("PROVIDER_ARTIFACT_EMPTY", f"declared {fmt} artifact is empty: {path.name}")
    if fmt == "sarif":
        return _sarif_findings(path, ruleset, provider_id)
    return _json_findings(path, ruleset, provider_id)


def _run_one(
    *,
    provider_id: str,
    spec: dict[str, Any],
    ruleset: RuleSet,
    source_root: Path,
    out_dir: Path,
    manifest_path: Path,
    package_type: str,
    package_version: str,
    cli_timeout: int | None,
) -> tuple[ProviderResult, list[Finding]]:
    directory = _provider_dir(out_dir, provider_id)
    if spec.get("kind") == "builtin":
        if provider_id != "builtin-manifest":
            result = ProviderResult(provider_id=provider_id, status="FAIL", error=f"unknown builtin provider: {provider_id}")
            return result, []
        artifact = directory / "builtin-manifest.json"
        artifact.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "provider_id": provider_id,
                    "tool": {"name": "cbe-builtin", "version": "0.3.0"},
                    "results": [],
                }
            ),
            encoding="utf-8",
        )
        result = ProviderResult(
            provider_id=provider_id,
            status="PASS",
            artifact_status="valid",
            json_path=_relative(out_dir, artifact),
        )
        result.result_count = 0
        return result, []

    if spec.get("kind") != "exec":
        return ProviderResult(provider_id=provider_id, status="FAIL", error=f"unknown provider kind: {spec.get('kind')}"), []

    command = spec.get("command")
    if not isinstance(command, list) or not command:
        return ProviderResult(provider_id=provider_id, status="FAIL", error="provider command is missing"), []

    manifest_timeout = int(spec.get("timeout_seconds", 300))
    effective_timeout = manifest_timeout
    if cli_timeout is not None:
        if cli_timeout > manifest_timeout:
            raise InputError("TIMEOUT_TOO_HIGH", f"--timeout exceeds manifest timeout for {provider_id}")
        effective_timeout = cli_timeout

    expanded = _expand(
        [str(item) for item in command],
        {
            "out": str(directory),
            "source_root": str(source_root),
            "package_type": package_type,
            "package_version": package_version,
            "manifest": str(manifest_path),
        },
    )
    try:
        process = subprocess.run(
            expanded,
            cwd=str(source_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=effective_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        result = ProviderResult(provider_id=provider_id, status="SKIPPED_INFRA", infra=True, error="provider timeout")
        return result, []
    except OSError as exc:
        result = ProviderResult(provider_id=provider_id, status="FAIL", error=f"provider command failed: {exc}")
        return result, []

    if process.returncode not in {0, 1}:
        stderr = (process.stderr or "").strip()[:500]
        result = ProviderResult(
            provider_id=provider_id,
            status="FAIL",
            process_exit_code=process.returncode,
            error=f"provider exited {process.returncode}: {stderr}",
        )
        return result, []

    findings: list[Finding] = []
    sarif_path: Path | None = None
    json_path: Path | None = None
    for fmt in spec.get("output_formats", []):
        suffix = ".sarif" if fmt == "sarif" else ".json"
        candidates = _artifact_files(directory, suffix)
        if not candidates:
            result = ProviderResult(
                provider_id=provider_id,
                status="FAIL",
                process_exit_code=process.returncode,
                artifact_status="missing",
                error=f"declared {fmt} artifact is missing",
            )
            return result, []
        selected = candidates[0]
        try:
            findings.extend(_validate_artifact(selected, ruleset, provider_id, fmt))
        except ProviderError as exc:
            result = ProviderResult(
                provider_id=provider_id,
                status="FAIL",
                process_exit_code=process.returncode,
                artifact_status="invalid",
                error=f"{exc.code}: {exc.message}",
            )
            return result, []
        if fmt == "sarif":
            sarif_path = selected
        else:
            json_path = selected

    result = ProviderResult(
        provider_id=provider_id,
        status="PASS",
        process_exit_code=process.returncode,
        artifact_status="valid",
        sarif_path=_relative(out_dir, sarif_path) if sarif_path else None,
        json_path=_relative(out_dir, json_path) if json_path else None,
        result_count=len(findings),
    )
    return result, findings


def execute(
    inspection: Inspection,
    *,
    package_type: str,
    package_version: str,
    source_root: str | Path,
    out_dir: str | Path,
    selected_providers: Iterable[str] | None,
    all_providers: bool,
    exemptions_path: str | None,
    cli_timeout: int | None,
    manifest_path: str | Path,
) -> RunOutcome:
    if inspection.errors:
        raise InputError("MANIFEST_INVALID", "manifest failed schema or semantic validation", details=inspection.errors)
    if not inspection.ruleset:
        raise InputError("MANIFEST_INVALID", "manifest did not produce a RuleSet")
    if inspection.gate_errors:
        first = inspection.gate_errors[0]
        raise GateError(first["code"], first["message"], details=inspection.gate_errors)

    ruleset = inspection.ruleset
    root = Path(source_root).resolve()
    if not root.is_dir():
        raise InputError("SOURCE_ROOT_NOT_FOUND", f"source root is not a directory: {source_root}")
    output = Path(out_dir).resolve()
    if output.is_relative_to(root):
        raise InputError("OUT_DIR_INSIDE_SOURCE", "--out-dir must not be inside --source-root")
    output.mkdir(parents=True, exist_ok=True)

    applicable_ids = {
        item["rule_id"]
        for item in inspection.applicable_rules
        if item.get("status") == "APPLICABLE"
    }
    applicable_rules = [rule for rule in (ruleset.rule(rule_id) for rule_id in applicable_ids) if rule]
    enabled_providers = sorted({rule.provider for rule in applicable_rules})
    selected = set(selected_providers or [])
    if selected - set(enabled_providers):
        raise InputError("PROVIDER_NOT_ENABLED", f"selected provider is not enabled: {sorted(selected - set(enabled_providers))}")
    if not all_providers and not selected:
        raise InputError("PROVIDER_REQUIRED", "use --all or --provider")

    exemptions, exemption_errors = parse_exemptions(exemptions_path, ruleset, applicable_ids)
    if exemption_errors:
        raise InputError("EXEMPTIONS_INVALID", "exemption file is invalid", details=exemption_errors)
    exemption_by_rule = {exemption.rule_id: exemption for exemption in exemptions}

    outcome = RunOutcome()
    findings: list[Finding] = []
    for provider_id in enabled_providers:
        if not all_providers and provider_id not in selected:
            outcome.providers.append(
                ProviderResult(provider_id=provider_id, status="SKIPPED", error="provider not selected")
            )
            continue
        result, provider_findings = _run_one(
            provider_id=provider_id,
            spec=ruleset.providers.get(provider_id, {}),
            ruleset=ruleset,
            source_root=root,
            out_dir=output,
            manifest_path=Path(manifest_path).resolve(),
            package_type=package_type,
            package_version=package_version,
            cli_timeout=cli_timeout,
        )
        outcome.providers.append(result)
        findings.extend(provider_findings)
        if result.sarif_path:
            outcome.sarif_paths.append(result.sarif_path)
        if result.json_path:
            outcome.json_paths.append(result.json_path)

    findings_by_rule: dict[str, list[Finding]] = {}
    for finding in findings:
        findings_by_rule.setdefault(finding.rule_id, []).append(finding)

    provider_by_id = {provider.provider_id: provider for provider in outcome.providers}
    advisory_applicable = 0
    for rule in applicable_rules:
        if rule.gate == "advisory":
            advisory_applicable += 1
        provider = provider_by_id.get(rule.provider)
        exemption = exemption_by_rule.get(rule.rule_id)
        reason = ""
        if exemption is not None:
            status = "SKIPPED"
            reason = exemption.reason
            if rule.gate == "blocking":
                outcome.blocking_skip = True
            elif exemption.applicable:
                outcome.skip_count += 1
        elif provider is None or provider.status == "SKIPPED":
            status = "SKIPPED"
            reason = "provider-not-selected"
            if rule.gate == "blocking":
                outcome.blocking_skip = True
            else:
                outcome.skip_count += 1
        elif provider.status == "SKIPPED_INFRA":
            status = "FAIL"
            reason = "provider-timeout"
        elif provider.status == "FAIL":
            status = "FAIL"
            reason = provider.error or "provider-failed"
        elif findings_by_rule.get(rule.rule_id):
            status = "FAIL"
            reason = "findings"
            if rule.gate == "advisory":
                outcome.warn_count += len(findings_by_rule[rule.rule_id])
        else:
            status = "PASS"
        outcome.rule_results.append(
            {
                "rule_id": rule.rule_id,
                "provider": rule.provider,
                "severity": rule.severity,
                "gate": rule.gate,
                "status": status,
                "reason": reason,
                "finding_count": len(findings_by_rule.get(rule.rule_id, [])),
            }
        )

    outcome.applicable_count = advisory_applicable
    outcome.not_applicable_count = inspection.not_applicable_rule_count or 0
    outcome.skip_ratio = (outcome.skip_count / outcome.applicable_count) if outcome.applicable_count else 0.0

    hard_failures = [provider for provider in outcome.providers if provider.status in {"FAIL", "SKIPPED_INFRA"}]
    blocking_rule_failures = [
        result for result in outcome.rule_results if result["gate"] == "blocking" and result["status"] == "FAIL"
    ]
    if any(provider.infra for provider in hard_failures) and not any(
        provider.status == "FAIL" for provider in hard_failures
    ) and not blocking_rule_failures:
        outcome.exit_code = 3
        outcome.gate_status = "SKIPPED_INFRA"
        outcome.error = {
            "code": "PROVIDER_TIMEOUT",
            "message": "a provider did not complete because of infrastructure",
            "details": [provider.as_dict() for provider in hard_failures],
        }
    elif hard_failures or blocking_rule_failures or outcome.blocking_skip:
        outcome.exit_code = 3
        outcome.gate_status = "FAIL"
        first_provider = next((provider for provider in hard_failures if provider.status == "FAIL"), None)
        first_blocking = next((item for item in blocking_rule_failures if item["status"] == "FAIL"), None)
        code = (
            first_provider.error.split(":", 1)[0]
            if first_provider and ":" in first_provider.error
            else (first_provider.error if first_provider else "BLOCKING_RULE_FAILED")
        )
        if outcome.blocking_skip and not hard_failures and not blocking_rule_failures:
            code = "BLOCKING_SKIP"
        outcome.error = {
            "code": code,
            "message": "provider or blocking-rule failure",
            "details": [item for item in outcome.rule_results if item["status"] == "FAIL"],
        }
    elif outcome.applicable_count and outcome.skip_count * 5 > outcome.applicable_count:
        outcome.exit_code = 4
        outcome.gate_status = "FAIL"
        outcome.error = {
            "code": "SKIP_RATIO_EXCEEDED",
            "message": f"skip ratio {outcome.skip_count}/{outcome.applicable_count} is above 20%",
            "details": [],
        }

    outcome.skip_ratio = round(outcome.skip_ratio, 6)
    return outcome

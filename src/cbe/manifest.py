"""Manifest loading, schema validation, semantic checks, and applicability."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import total_ordering
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from .errors import InputError
from .jsonio import load_json, sha256_json

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "rule-pack-manifest.v1.schema.json"

PACKAGE_TYPES = ("cbs", "cbe", "cbp", "cbm", "cbc", "cbg")
GATE_VALUES = {"blocking", "advisory"}
SEVERITY_VALUES = {"error", "warning", "note"}

SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$"
)
COMPARATOR_RE = re.compile(r"^(>=|>|<=|<|=)(.+)$")


@total_ordering
@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    prerelease: str = ""

    @classmethod
    def parse(cls, value: str) -> "Version":
        match = SEMVER_RE.match(value)
        if not match:
            raise ValueError(f"not a SemVer 2.0.0 version: {value}")
        major, minor, patch, prerelease, _build = match.groups()
        return cls(int(major), int(minor), int(patch), prerelease or "")

    def _compare_prerelease(self, other: "Version") -> int:
        if self.prerelease == other.prerelease:
            return 0
        if not self.prerelease:
            return 1
        if not other.prerelease:
            return -1
        left = self.prerelease.split(".")
        right = other.prerelease.split(".")
        for a, b in zip(left, right):
            if a == b:
                continue
            a_num = a.isdigit()
            b_num = b.isdigit()
            if a_num and b_num:
                return -1 if int(a) < int(b) else 1
            if a_num != b_num:
                return -1 if a_num else 1
            return -1 if a < b else 1
        return -1 if len(left) < len(right) else 1

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        mine = (self.major, self.minor, self.patch)
        theirs = (other.major, other.minor, other.patch)
        if mine != theirs:
            return mine < theirs
        return self._compare_prerelease(other) < 0


def parse_constraint(value: str) -> tuple[str, list[tuple[str, Version]]]:
    """Parse `*` or a space-separated AND list of comparators."""

    text = value.strip()
    if text == "*":
        return ("*", [])
    if not text:
        raise ValueError("empty version constraint")
    parsed: list[tuple[str, Version]] = []
    for part in text.split():
        match = COMPARATOR_RE.match(part)
        if not match:
            raise ValueError(f"invalid comparator: {part}")
        operator, raw = match.groups()
        parsed.append((operator, Version.parse(raw)))
    return (text, parsed)


def constraint_matches(version: Version, constraint: tuple[str, list[tuple[str, Version]]]) -> bool:
    operator, comparators = constraint
    if operator == "*":
        return True
    for op, expected in comparators:
        if op == ">=" and not (version >= expected):
            return False
        if op == ">" and not (version > expected):
            return False
        if op == "<=" and not (version <= expected):
            return False
        if op == "<" and not (version < expected):
            return False
        if op == "=" and not (version == expected):
            return False
    return True


@dataclass(frozen=True)
class Rule:
    """Validated in-memory rule shared by the manifest validator and P0-04."""

    rule_id: str
    title: str
    severity: str
    gate: str
    provider: str
    version_constraint: str
    package_types: tuple[str, ...]
    provider_rule_ids: tuple[str, ...]
    sarif: dict[str, Any] | None
    raw: dict[str, Any]


@dataclass
class Applicability:
    package_type: str
    package_version: str
    applicable: list[Rule] = field(default_factory=list)
    not_applicable: list[Rule] = field(default_factory=list)
    applicable_count: int = 0
    advisory_applicable_count: int = 0
    blocking_applicable_count: int = 0
    gate_errors: list[dict[str, str]] = field(default_factory=list)


@dataclass
class RuleSet:
    """The single in-memory model produced after manifest validation."""

    manifest: dict[str, Any]
    manifest_sha256: str
    rules: list[Rule] = field(default_factory=list)
    providers: dict[str, dict[str, Any]] = field(default_factory=dict)
    enabled_providers: list[str] = field(default_factory=list)
    blocking_rule_count: int = 0
    advisory_rule_count: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_manifest(
        cls,
        manifest: dict[str, Any],
        *,
        manifest_sha256: str,
        errors: list[dict[str, Any]] | None = None,
        warnings: list[dict[str, Any]] | None = None,
    ) -> "RuleSet":
        raw_rules = manifest.get("rules") if isinstance(manifest.get("rules"), list) else []
        providers = manifest.get("providers") if isinstance(manifest.get("providers"), dict) else {}
        rules: list[Rule] = []
        for item in raw_rules:
            if not isinstance(item, dict) or not isinstance(item.get("rule_id"), str):
                continue
            package_types = item.get("package_types") if isinstance(item.get("package_types"), list) else []
            native_ids = item.get("provider_rule_ids") if isinstance(item.get("provider_rule_ids"), list) else []
            rules.append(
                Rule(
                    rule_id=item["rule_id"],
                    title=str(item.get("title", "")),
                    severity=str(item.get("severity", "")),
                    gate=str(item.get("gate", "")),
                    provider=str(item.get("provider", "")),
                    version_constraint=str(item.get("version_constraint", "")),
                    package_types=tuple(str(value) for value in package_types),
                    provider_rule_ids=tuple(str(value) for value in native_ids),
                    sarif=item.get("sarif") if isinstance(item.get("sarif"), dict) else None,
                    raw=item,
                )
            )
        return cls(
            manifest=manifest,
            manifest_sha256=manifest_sha256,
            rules=rules,
            providers=dict(providers),
            enabled_providers=sorted({rule.provider for rule in rules if rule.provider}),
            blocking_rule_count=sum(1 for rule in rules if rule.gate == "blocking"),
            advisory_rule_count=sum(1 for rule in rules if rule.gate == "advisory"),
            errors=list(errors or []),
            warnings=list(warnings or []),
        )

    def rule(self, rule_id: str) -> Rule | None:
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def applicable(self, package_type: str, package_version: str) -> Applicability:
        try:
            version = Version.parse(package_version.lstrip("v"))
        except ValueError as exc:
            raise InputError("INVALID_PACKAGE_VERSION", str(exc)) from exc

        result = Applicability(package_type=package_type, package_version=package_version)
        for rule in self.rules:
            try:
                constraint = parse_constraint(rule.version_constraint)
            except ValueError:
                continue
            matches = package_type in rule.package_types and constraint_matches(version, constraint)
            if matches:
                result.applicable.append(rule)
                if rule.gate == "advisory":
                    result.advisory_applicable_count += 1
                elif rule.gate == "blocking":
                    result.blocking_applicable_count += 1
            else:
                result.not_applicable.append(rule)
                if rule.gate == "blocking":
                    result.gate_errors.append(
                        _error(
                            "$.rules",
                            "BLOCKING_RULE_NOT_APPLICABLE",
                            f"blocking rule is not applicable to {package_type} {package_version}: {rule.rule_id}",
                        )
                    )

        result.applicable_count = len(result.applicable)
        if not self.rules:
            result.gate_errors.append(_error("$.rules", "NO_RULES", "manifest has no rules"))
        elif result.applicable_count == 0:
            result.gate_errors.append(
                _error("$.rules", "NO_APPLICABLE_CHECKS", "no applicable rule for the supplied package context")
            )
        return result


@dataclass
class Inspection:
    manifest: dict[str, Any]
    manifest_sha256: str
    schema_version_seen: Any
    pack_id: Any
    pack_version: Any
    rule_count: int = 0
    provider_count: int = 0
    blocking_rule_count: int = 0
    advisory_rule_count: int = 0
    applicable_rule_count: int | None = None
    blocking_applicable_count: int | None = None
    not_applicable_rule_count: int | None = None
    enabled_providers: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    gate_errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    applicable_rules: list[dict[str, Any]] = field(default_factory=list)
    ruleset: RuleSet | None = None


def _json_path(parts: Iterable[Any]) -> str:
    out = "$"
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += f".{part}"
    return out


def _error(path: str, code: str, message: str) -> dict[str, str]:
    return {"path": path, "code": code, "message": message}


def load_schema() -> dict[str, Any]:
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except OSError as exc:  # pragma: no cover - packaging failure
        raise InputError("SCHEMA_UNAVAILABLE", f"cannot read manifest schema: {exc}") from exc


def _schema_errors(manifest: Any) -> list[dict[str, str]]:
    validator = Draft202012Validator(load_schema())
    return [
        _error(_json_path(error.path), str(error.validator), error.message)
        for error in sorted(validator.iter_errors(manifest), key=lambda item: list(item.path))
    ]


def _unique_names(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def _semantic_errors(manifest: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    rules = manifest.get("rules")
    providers = manifest.get("providers")
    top_types = manifest.get("package_types")
    if not isinstance(rules, list) or not isinstance(providers, dict):
        return errors, warnings
    if not isinstance(top_types, list):
        top_types = []

    rule_ids = [rule.get("rule_id") for rule in rules if isinstance(rule, dict)]
    for duplicate in _unique_names(str(rule_id) for rule_id in rule_ids if isinstance(rule_id, str)):
        errors.append(_error("$.rules", "DUPLICATE_RULE_ID", f"duplicate rule_id: {duplicate}"))

    provider_rule_ids: list[str] = []
    sarif_names: list[str] = []
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            continue
        path = f"$.rules[{index}]"
        provider_id = rule.get("provider")
        if isinstance(provider_id, str) and provider_id not in providers:
            errors.append(
                _error(f"{path}.provider", "UNKNOWN_PROVIDER", f"provider not declared: {provider_id}")
            )

        gate = rule.get("gate")
        severity = rule.get("severity")
        if gate == "blocking" and severity != "error":
            errors.append(
                _error(f"{path}.severity", "GATE_SEVERITY_MISMATCH", "blocking rule requires severity=error")
            )
        if gate == "advisory" and severity not in {"warning", "note"}:
            errors.append(
                _error(
                    f"{path}.severity",
                    "GATE_SEVERITY_MISMATCH",
                    "advisory rule requires severity=warning or note",
                )
            )

        rule_types = rule.get("package_types")
        if isinstance(rule_types, list):
            extra = [item for item in rule_types if item not in top_types]
            if extra:
                errors.append(
                    _error(
                        f"{path}.package_types",
                        "PACKAGE_SCOPE_NOT_SUBSET",
                        f"package_types not in top-level set: {', '.join(map(str, extra))}",
                    )
                )
            if gate == "blocking" and set(rule_types) != set(top_types):
                errors.append(
                    _error(
                        f"{path}.package_types",
                        "BLOCKING_RULE_PARTIAL_SCOPE",
                        "blocking rule package_types must equal top-level package_types",
                    )
                )

        native_ids = rule.get("provider_rule_ids")
        if isinstance(native_ids, list):
            for native in native_ids:
                if isinstance(native, str):
                    if native in provider_rule_ids:
                        errors.append(
                            _error(
                                f"{path}.provider_rule_ids",
                                "DUPLICATE_PROVIDER_RULE_ID",
                                f"provider_rule_id used by more than one rule: {native}",
                            )
                        )
                    provider_rule_ids.append(native)

        sarif = rule.get("sarif")
        if isinstance(sarif, dict) and isinstance(sarif.get("name"), str):
            if sarif["name"] in sarif_names:
                errors.append(
                    _error(f"{path}.sarif.name", "DUPLICATE_SARIF_NAME", f"duplicate sarif.name: {sarif['name']}")
                )
            sarif_names.append(sarif["name"])

        constraint = rule.get("version_constraint")
        if isinstance(constraint, str):
            try:
                parse_constraint(constraint)
            except ValueError as exc:
                errors.append(_error(f"{path}.version_constraint", "INVALID_VERSION_CONSTRAINT", str(exc)))

    referenced = {
        rule.get("provider")
        for rule in rules
        if isinstance(rule, dict) and isinstance(rule.get("provider"), str)
    }
    for provider_id in sorted(set(providers) - referenced):
        warnings.append(
            _error(f"$.providers.{provider_id}", "UNUSED_PROVIDER", f"provider is not referenced by any rule: {provider_id}")
        )
    return errors, warnings


def inspect_manifest(
    manifest: Any,
    *,
    package_type: str | None = None,
    package_version: str | None = None,
) -> Inspection:
    schema_errors = _schema_errors(manifest)
    if not isinstance(manifest, dict):
        return Inspection(
            manifest={} if not isinstance(manifest, dict) else manifest,
            manifest_sha256=sha256_json(manifest),
            schema_version_seen=None,
            pack_id=None,
            pack_version=None,
            errors=schema_errors,
        )

    semantic_errors, warnings = _semantic_errors(manifest) if not schema_errors else ([], [])
    manifest_sha256 = sha256_json(manifest)
    ruleset = RuleSet.from_manifest(
        manifest,
        manifest_sha256=manifest_sha256,
        errors=schema_errors + semantic_errors,
        warnings=warnings,
    )
    inspection = Inspection(
        manifest=manifest,
        manifest_sha256=manifest_sha256,
        schema_version_seen=manifest.get("schema_version"),
        pack_id=manifest.get("pack_id"),
        pack_version=manifest.get("pack_version"),
        rule_count=len(ruleset.rules),
        provider_count=len(ruleset.providers),
        blocking_rule_count=ruleset.blocking_rule_count,
        advisory_rule_count=ruleset.advisory_rule_count,
        enabled_providers=ruleset.enabled_providers,
        errors=ruleset.errors,
        warnings=ruleset.warnings,
        ruleset=ruleset,
    )

    if inspection.errors:
        return inspection

    if package_type is not None and package_version is not None:
        try:
            applicability = ruleset.applicable(package_type, package_version)
        except InputError as exc:
            inspection.errors.append(_error("$.package_version", exc.code, exc.message))
            return inspection

        inspection.applicable_rule_count = applicability.applicable_count
        inspection.blocking_applicable_count = applicability.blocking_applicable_count
        inspection.not_applicable_rule_count = len(applicability.not_applicable)
        inspection.gate_errors.extend(applicability.gate_errors)
        for rule in applicability.applicable:
            inspection.applicable_rules.append(
                {"rule_id": rule.rule_id, "gate": rule.gate, "status": "APPLICABLE"}
            )
        for rule in applicability.not_applicable:
            inspection.applicable_rules.append(
                {"rule_id": rule.rule_id, "gate": rule.gate, "status": "NOT_APPLICABLE"}
            )
    elif not ruleset.rules:
        inspection.gate_errors.append(_error("$.rules", "NO_RULES", "manifest has no rules"))

    return inspection


def load_and_inspect(
    path: str | Path,
    *,
    package_type: str | None = None,
    package_version: str | None = None,
) -> Inspection:
    return inspect_manifest(load_json(path), package_type=package_type, package_version=package_version)

"""SARIF 2.1.0 assembly and validation for CBE (P0-05)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import GateError, InputError
from .jsonio import load_json, sha256_json
from .manifest import Rule, RuleSet

SARIF_SCHEMA = "https://docs.oasis-open.org/sarif/sarif/v2.1.0/cos02/schemas/sarif-schema-2.1.0.json"
SARIF_VERSION = "2.1.0"


def _rule_for_native(ruleset: RuleSet, provider_id: str, native_id: str) -> Rule:
    if native_id.startswith(("CBP-", "CBG-")):
        raise GateError("CROSS_NAMESPACE", f"result uses another namespace: {native_id}")
    direct = ruleset.rule(native_id)
    if direct is not None and direct.provider == provider_id:
        return direct
    for rule in ruleset.rules:
        if rule.provider == provider_id and native_id in rule.provider_rule_ids:
            return rule
    raise GateError("RULE_NOT_IN_MANIFEST", f"result rule is not in the manifest: {native_id}")


def _valid_uri(uri: str) -> bool:
    normalized = uri.replace("\\", "/")
    if not normalized or normalized.startswith("/") or normalized.startswith("../"):
        return False
    if len(normalized) >= 2 and normalized[1] == ":":
        return False
    return "/../" not in normalized


def _result(
    *,
    rule: Rule,
    rule_index: int,
    level: str,
    message: str,
    path: str,
    line: int,
    column: int,
    provider_id: str,
    suppression: str | None,
) -> dict[str, Any]:
    if not _valid_uri(path):
        raise GateError("SARIF_INVALID_LOCATION", f"result location is not a relative URI: {path}")
    if not message:
        raise GateError("SARIF_INVALID_RESULT", f"result for {rule.rule_id} has no message")
    if level not in {"error", "warning", "note"}:
        raise GateError("SARIF_INVALID_RESULT", f"invalid level for {rule.rule_id}: {level}")
    result: dict[str, Any] = {
        "ruleId": rule.rule_id,
        "ruleIndex": rule_index,
        "level": level,
        "message": {"text": message},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": path.replace("\\", "/")},
                    "region": {"startLine": max(1, line), "startColumn": max(1, column)},
                }
            }
        ],
        "partialFingerprints": {
            "cbe/v1": sha256_json(
                {
                    "rule_id": rule.rule_id,
                    "provider": provider_id,
                    "path": path.replace("\\", "/"),
                    "line": max(1, line),
                    "column": max(1, column),
                }
            )
        },
        "properties": {"cbe/provider": provider_id},
    }
    if suppression:
        result["suppressions"] = [{"kind": "external", "justification": suppression}]
    return result


def _read_sarif(
    path: Path,
    ruleset: RuleSet,
    provider_id: str,
    *,
    suppression_by_rule: dict[str, str],
) -> tuple[list[dict[str, Any]], list[Rule]]:
    try:
        data = load_json(path)
    except InputError as exc:
        raise GateError("SARIF_INVALID", f"cannot parse {path}: {exc.message}") from exc
    if not isinstance(data, dict) or data.get("version") != SARIF_VERSION:
        raise GateError("SARIF_INVALID", f"{path} is not SARIF 2.1.0")
    runs = data.get("runs")
    if not isinstance(runs, list) or not runs:
        raise GateError("SARIF_INVALID", f"{path} has no runs")
    results: list[dict[str, Any]] = []
    rules: dict[str, Rule] = {}
    for run in runs:
        driver = run.get("tool", {}).get("driver", {})
        driver_rules = driver.get("rules", [])
        if not isinstance(driver_rules, list):
            raise GateError("SARIF_INVALID", f"{path} driver.rules is not an array")
        for item in run.get("results", []):
            if not isinstance(item, dict):
                raise GateError("SARIF_INVALID", f"{path} has a non-object result")
            native_id = item.get("ruleId")
            if not isinstance(native_id, str) or not native_id:
                raise GateError("SARIF_INVALID", f"{path} has a result without ruleId")
            rule = _rule_for_native(ruleset, provider_id, native_id)
            rule_index = item.get("ruleIndex")
            if rule_index is not None:
                if not isinstance(rule_index, int) or rule_index < 0 or rule_index >= len(driver_rules):
                    raise GateError("SARIF_INVALID_RULE_INDEX", f"{path} has an invalid ruleIndex: {rule_index}")
            level = item.get("level", rule.severity)
            message = item.get("message", {}).get("text", "")
            locations = item.get("locations", [])
            if not isinstance(locations, list) or not locations:
                raise GateError("SARIF_INVALID_RESULT", f"{path} has a result without locations")
            physical = locations[0].get("physicalLocation", {})
            artifact = physical.get("artifactLocation", {})
            region = physical.get("region", {})
            uri = artifact.get("uri", "")
            if not isinstance(uri, str):
                raise GateError("SARIF_INVALID_RESULT", f"{path} has a non-string artifact URI")
            rules[rule.rule_id] = rule
            results.append(
                _result(
                    rule=rule,
                    rule_index=0,  # replaced when the run is assembled
                    level=level,
                    message=str(message),
                    path=uri,
                    line=int(region.get("startLine", 1) or 1),
                    column=int(region.get("startColumn", 1) or 1),
                    provider_id=provider_id,
                    suppression=suppression_by_rule.get(rule.rule_id),
                )
            )
    return results, list(rules.values())


def _read_provider_json(
    path: Path,
    ruleset: RuleSet,
    provider_id: str,
    *,
    suppression_by_rule: dict[str, str],
) -> tuple[list[dict[str, Any]], list[Rule]]:
    try:
        data = load_json(path)
    except InputError as exc:
        raise GateError("SARIF_INVALID", f"cannot parse {path}: {exc.message}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise GateError("SARIF_INVALID", f"{path} is not a provider JSON result file")
    results: list[dict[str, Any]] = []
    rules: dict[str, Rule] = {}
    for item in data["results"]:
        native_id = item.get("provider_rule_id") or item.get("rule_id", "")
        rule = _rule_for_native(ruleset, provider_id, str(native_id))
        location = item.get("location", {})
        rules[rule.rule_id] = rule
        results.append(
            _result(
                rule=rule,
                rule_index=0,
                level=str(item.get("level", rule.severity)),
                message=str(item.get("message", "")),
                path=str(location.get("path", "")),
                line=int(location.get("start_line", 1) or 1),
                column=int(location.get("start_column", 1) or 1),
                provider_id=provider_id,
                suppression=suppression_by_rule.get(rule.rule_id),
            )
        )
    return results, list(rules.values())


def build_sarif(
    *,
    ruleset: RuleSet,
    run_report: dict[str, Any],
    provider_outputs: list[Path] | None,
    run_report_dir: Path | None = None,
) -> dict[str, Any]:
    providers = run_report.get("providers")
    if not isinstance(providers, list) or not providers:
        raise InputError("RUN_REPORT_INVALID", "run report has no providers")
    rule_results = run_report.get("rule_results", [])
    if not isinstance(rule_results, list):
        raise InputError("RUN_REPORT_INVALID", "run report rule_results must be an array")
    suppression_by_rule = {
        item["rule_id"]: f"SKIPPED: {item['rule_id']} reason={item.get('reason', '')}"
        for item in rule_results
        if isinstance(item, dict) and item.get("status") == "SKIPPED" and item.get("rule_id")
    }

    overrides = {path.name: path for path in (provider_outputs or [])}
    runs: list[dict[str, Any]] = []
    total_results = 0
    seen_rules: dict[str, Rule] = {}

    for provider in providers:
        if not isinstance(provider, dict):
            raise InputError("RUN_REPORT_INVALID", "run report provider entry must be an object")
        provider_id = provider.get("provider_id")
        if not isinstance(provider_id, str) or not provider_id:
            raise InputError("RUN_REPORT_INVALID", "run report provider has no provider_id")
        if provider.get("status") != "PASS":
            if provider.get("status") == "SKIPPED":
                continue
            raise GateError("PROVIDER_NOT_VALID", f"provider is not PASS in run report: {provider_id}")
        artifact = provider.get("sarif_path") or provider.get("json_path")
        if not artifact:
            raise GateError("PROVIDER_ARTIFACT_MISSING", f"provider has no artifact in run report: {provider_id}")
        artifact_path = Path(str(artifact))
        if not artifact_path.is_absolute():
            artifact_path = (run_report_dir or Path.cwd()) / artifact_path
        if provider_outputs:
            replacement = overrides.get(artifact_path.name)
            if replacement is not None:
                artifact_path = replacement
        if not artifact_path.is_file():
            raise GateError("PROVIDER_ARTIFACT_MISSING", f"provider artifact not found: {artifact_path}")

        if artifact_path.suffix.lower() == ".sarif":
            results, rules = _read_sarif(
                artifact_path,
                ruleset,
                provider_id,
                suppression_by_rule=suppression_by_rule,
            )
        else:
            results, rules = _read_provider_json(
                artifact_path,
                ruleset,
                provider_id,
                suppression_by_rule=suppression_by_rule,
            )

        rule_list = sorted(rules, key=lambda item: item.rule_id)
        rule_index = {rule.rule_id: index for index, rule in enumerate(rule_list)}
        for result in results:
            result["ruleIndex"] = rule_index[result["ruleId"]]
        for rule in rule_list:
            seen_rules[rule.rule_id] = rule
        total_results += len(results)
        runs.append(
            {
                "tool": {
                    "driver": {
                        "name": f"CBE/{provider_id}",
                        "informationUri": "https://github.com/JunxiangPan/cbe",
                        "rules": [
                            {
                                "id": rule.rule_id,
                                "name": rule.rule_id,
                                "shortDescription": {"text": rule.title or rule.rule_id},
                                "defaultConfiguration": {"level": rule.severity},
                                "properties": {"cbe/gate": rule.gate, "cbe/provider": provider_id},
                            }
                            for rule in rule_list
                        ],
                    }
                },
                "automationDetails": {"id": f"cbe/{provider_id}"},
                "results": results,
            }
        )

    if not runs:
        raise GateError("NO_PROVIDER_OUTPUT", "no provider produced SARIF evidence")
    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": runs,
        "properties": {
            "cbe/rule_count": len(seen_rules),
            "cbe/result_count": total_results,
            "cbe/namespaces": ["CBE"],
        },
    }

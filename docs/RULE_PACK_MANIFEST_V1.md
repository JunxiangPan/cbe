# CBE rule-pack manifest v1

Schema: `schemas/rule-pack-manifest.v1.schema.json`
Draft status: frozen for P0; F2 blocking-set amendment pending in CBS.

## Top-level shape

```json
{
  "schema_version": "1",
  "pack_id": "cbe-core",
  "pack_version": "0.1.0",
  "description": "optional",
  "package_types": ["cbs", "cbe"],
  "providers": {},
  "rules": []
}
```

- `schema_version` is the string `"1"`.
- `pack_id` matches `^[a-z][a-z0-9-]{1,63}$`.
- `pack_version` is SemVer 2.0.0.
- `package_types` is a non-empty unique subset of
  `cbs/cbe/cbp/cbm/cbc/cbg/cbf`.
- `providers` is an object keyed by provider id; at least one provider.
- `rules` is an array; zero rules is schema-valid but a gate failure (exit 3
  `NO_RULES`).

## Provider

```json
{
  "builtin-manifest": {
    "kind": "builtin",
    "output_formats": ["json"]
  },
  "gitleaks": {
    "kind": "exec",
    "command": ["gitleaks", "detect", "--no-git", "--report-format", "sarif", "--report-path", "{out}/gitleaks.sarif"],
    "timeout_seconds": 300,
    "output_formats": ["sarif"]
  }
}
```

- `kind`: `builtin` or `exec`.
- `exec` requires `command` (argv array, no shell). `builtin` forbids `command`.
- `output_formats`: non-empty subset of `sarif`, `json`; every declared format
  must exist after the run.
- Placeholders in `command`: `{out}`, `{source_root}`, `{package_type}`,
  `{package_version}`, `{manifest}`. No shell expansion.
- `timeout_seconds`: 1..3600. A CLI `--timeout` may only lower it.

## Rule

```json
{
  "rule_id": "CBE-SECRET-001",
  "title": "No hardcoded secrets",
  "severity": "error",
  "gate": "blocking",
  "provider": "gitleaks",
  "provider_rule_ids": ["generic-api-key"],
  "version_constraint": ">=0.1.0 <2.0.0",
  "package_types": ["cbs", "cbe"],
  "tags": ["security"],
  "sarif": {
    "name": "NoHardcodedSecrets",
    "short_description": "Hardcoded secret detected",
    "help_uri": "https://example.invalid/cbe/CBE-SECRET-001"
  }
}
```

- `rule_id` matches `^CBE-[A-Z][A-Z0-9]*(-[A-Z0-9]+)*-[0-9]{3}$`; `CBP-*` and
  `CBG-*` are rejected.
- `severity`: `error | warning | note`.
- `gate`: `blocking | advisory`.
- `provider` must exist in `providers`.
- `provider_rule_ids` maps native provider ids to this CBE rule; globally
  unique.
- `version_constraint`: `*` or space-separated comparators
  (`>=`, `>`, `<=`, `<`, `=`), each with a full `X.Y.Z`. No `^`, `~`, `x`,
  `||`, comma, or partial version.
- `package_types` must be a subset of top-level `package_types`.
- `sarif.name` is optional but unique when present.

## Semantic checks (S01–S14)

| ID | Check | Failure |
|---|---|---|
| S01 | Unknown top-level/rule/provider fields rejected | exit 2 |
| S02 | `rule_id` unique and CBE-only | exit 2 |
| S03 | `rules[].provider` exists | exit 2 |
| S04 | `provider_rule_ids` globally unique | exit 2 |
| S05 | Rule `package_types` ⊆ top-level | exit 2 |
| S06 | blocking ⇒ severity error; advisory ⇒ warning/note | exit 2 |
| S07 | blocking rule `package_types` == top-level `package_types` | exit 2 |
| S08 | `sarif.name` unique | exit 2 |
| S09 | zero rules | exit 3 `NO_RULES` |
| S10 | zero applicable rules for the supplied context | exit 3 `NO_APPLICABLE_CHECKS` |
| S11 | unused provider | warning, not blocking |
| S12 | duplicate JSON keys | exit 2 |
| S13 | version constraint grammar | exit 2 |
| S14 | canonical hash | `sha256` of JCS, 64 lowercase hex |

## Canonical hash

`rules_manifest_hash = sha256(JCS(manifest))`, bare 64 lowercase hex.
For the manifest data model (objects, arrays, strings, integers, booleans,
null), JCS ordering plus compact separators is sufficient. Floats are rejected.
The same bytes must hash identically under LF/CRLF and different indentation.

## `gate` and F2

This schema allows `gate: "blocking"`. The F2 amendment defines the blocking
set as the three structural checks plus every blocking rule. Until CBS applies
that amendment, CBE-08 results are implementation-consistent but not
contract-literal; do not call them F2-conformant.

## Implementation status

The schema and fixtures are frozen in commit 1. The validator is implemented in
commit 2 (`src/cbe/manifest.py`, `src/cbe/commands/validate_manifest.py`) with
unit tests in `tests/unit/test_manifest.py`. The other four command bodies are
still skeleton stubs and return exit 3 `NOT_IMPLEMENTED`, never PASS.

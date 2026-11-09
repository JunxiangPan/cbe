# CBE CLI v1

Status: interface frozen in commit 1. All five subcommands are implemented:
`validate-manifest`, `enforce-no-bypass`, `symbol-index`, `run-provider`, and
`emit-sarif`. `tools/cbe_gate.py` assembles the CBE report and Section B.
CBE-07b is a real assertion against released CBP 1.2.0 (`CBP-EXT-*` mapping);
`tools/cbe_baseline.py`, `tools/cbe_train.py`, and `tools/cbe_selfcheck.py`
cover CBE-09/10/11. CBE-08 remains DRAFT against CBS `contract/v1.7.1` RC.

## Global contract

```text
cbe <command> [options]
```

- Normal operation writes one JSON object to stdout.
- Logs/progress go to stderr. `--help` is the only text stdout mode.
- `--help` exits 0; `--version` exits 0.
- `--output PATH` atomically writes the same JSON response.
- `--json` is accepted for compatibility; JSON is the default.
- `--format` only accepts `json`; any other value exits 2.
- Exit codes: `0 PASS`, `2 input/format error`, `3 gate failure or
  SKIPPED_INFRA`, `4 SKIP ratio > 20%`.
- No command has `--disable`, `--skip`, `--ignore`, or `--exclude-rule`.
- Unhandled exceptions are caught at the boundary and returned as exit 3
  `INTERNAL_ERROR` JSON. Exit 1 is never emitted.

### Exit precedence

```text
2 input
  > 3 PRECONDITION_FAIL
  > 3 definite FAIL (rule failure, bypass, provider artifact invalid, blocking SKIP)
  > 3 pure infra SKIPPED_INFRA
  > 4 skip_ratio > 0.20
  > 0 PASS
```

A definite FAIL wins over infra; pure infra emits `SKIPPED_INFRA`. A report with
`exit_code` not in `{0,2,3,4}` is an input error (2) when consumed.

### Envelope

```json
{
  "schema_version": "1",
  "command": "validate-manifest",
  "ok": true,
  "exit_code": 0,
  "gate_status": "PASS",
  "error": null,
  "warnings": []
}
```

Error object:

```json
{
  "code": "MANIFEST_SCHEMA_INVALID",
  "message": "manifest failed schema validation",
  "details": [
    {"path": "$.rules[0].severity", "code": "ENUM", "message": "..."}
  ]
}
```

## 1. validate-manifest

```text
cbe validate-manifest --manifest PATH
    [--package-type TYPE --package-version vX.Y.Z]
    [--output PATH] [--help]
```

- `--manifest` required; `-` is stdin.
- `--package-type` and `--package-version` must be supplied together.
- Exit 0: valid. Exit 2: schema/semantic error. Exit 3: zero rules, zero
  applicable rules, or a blocking rule not applicable in the supplied context
  (`blocking_skip=true`).
- Output keys: `manifest_path`, `manifest_sha256`, `schema_version_seen`,
  `pack_id`, `pack_version`, `rule_count`, `provider_count`,
  `blocking_rule_count`, `blocking_applicable_count`, `advisory_rule_count`,
  `applicable_rule_count`, `not_applicable_rule_count`, `enabled_providers`,
  `errors`, `gate_errors`, `warnings`.

`blocking_rule_count` is the manifest total. `blocking_applicable_count` is the
count applicable to the supplied package context. S07 makes them equal for a
valid manifest; both are emitted so CBE-03 can assert that S07 actually ran.

## 2. run-provider

```text
cbe run-provider --manifest PATH
    --package-type TYPE --package-version vX.Y.Z
    --source-root PATH --out-dir PATH
    (--all | --provider ID ...)
    [--exemptions PATH] [--timeout SECONDS]
    [--output PATH] [--help]
```

Provider protocol:

| Condition | Result |
|---|---|
| exit 0, artifact valid | PASS |
| exit 1, artifact valid | findings, still a valid run |
| exit >= 2 | exit 3 provider failure |
| missing / zero-byte / unparseable artifact | exit 3 |
| valid SARIF/JSON with zero results | PASS |
| timeout, network outage, 504, registry 5xx | exit 3 `SKIPPED_INFRA` |
| native id without mapping | exit 3 `UNMAPPED_PROVIDER_RULE` |
| non-CBE id in published SARIF | exit 3 `CROSS_NAMESPACE` |

- `--all` and `--provider` are mutually exclusive and required.
- `--timeout` may only lower the manifest timeout; a larger value exits 2.
- `--out-dir` must not be inside `--source-root`.
- Unselected applicable providers become `SKIPPED reason=provider-not-selected`
  and count in the denominator; a partial run cannot pretend to PASS.
- Output keys: `package_type`, `package_version`, `source_root`, `providers`,
  `rule_results`, `applicable_count`, `skip_count`, `not_applicable_count`,
  `skip_ratio`, `blocking_skip`, `warn_count`, `sarif_paths`, `json_paths`.

## 3. symbol-index

```text
cbe symbol-index --source-root PATH --out PATH
    [--include GLOB ...] [--exclude GLOB ...]
    [--language LANG ...] [--output PATH] [--help]
```

- Emits deterministic JSON (no timestamps); files sorted by POSIX path, symbols
  by `line,column,name`; JCS SHA-256.
- Default excludes: `.git/**`, `**/node_modules/**`, `**/.venv/**`,
  `**/__pycache__/**`. User excludes cannot remove these.
- Symlink escaping the source root → exit 3. Internal symlinks are skipped with
  a warning.
- Zero files → exit 3 `NO_SOURCE_FILES`.
- Output keys: `source_root`, `index_path`, `index_sha256`, `file_count`,
  `symbol_count`, `languages`, `excluded_count`, `symlink_skipped_count`,
  `warnings`.

## 4. enforce-no-bypass

```text
cbe enforce-no-bypass --manifest PATH --source-root PATH
    --package-type TYPE --package-version vX.Y.Z
    [--config PATH ...] [--env-file PATH ...]
    [--exemptions PATH] [--workflows]
    [--exclude-workflow GLOB ...]
    [--output PATH] [--help]
```

Detection matrix:

| kind | Object | Failure |
|---|---|---|
| config | CBE-scoped files: `cbe.yml`, `.cbe/config.*`, files with a top-level `cbe:`; keys `disable/skip/ignore/exclude/enabled:false` | exit 3 |
| comment | source comments `cbe: disable|skip|ignore|off` | exit 3 |
| env | process env or `--env-file`: `CBE_DISABLE*`, `CBE_SKIP*`, `CBE_IGNORE*`, `CBE_RULES_EXCLUDE`, `NO_CBE` | exit 3 |
| workflow-swallow | target `.github/workflows/*.yml` gate/publish steps with `continue-on-error: true`, `|| true`, `if: always()` | exit 3 |
| workflow-skip | target `.github/workflows/*.yml` where the `cbe-gate` job is unreachable: literal `if: false`, evaluable-false `!true`/`1 == 2`, a `needs` chain that reaches an unreachable job, a missing dependency, or a commented-out `cbe-gate:` job | exit 3, `reason=WORKFLOW_SKIPS_CBE_GATE`; dynamic conditions only warn |
| cli | `--disable/--skip/--ignore/--exclude-rule` | exit 2 |
| manifest | `enabled: false`, unknown field | exit 2 |

Static-analysis limits:

- Conditions that need runtime context (`inputs.*`, `vars.*`, `github.*`,
  `secrets.*`, `env.*`, `needs.*`, matrix/steps, and functions such as
  `always()`) are not evaluated. A `cbe-gate` job with such an `if` emits
  warning `UNVERIFIABLE_CONDITION`; exit stays 0 unless another bypass exists.
- A `needs` chain that contains such a condition emits warning
  `UNVERIFIABLE_NEEDS_CHAIN`; it is never silently treated as reachable.
- Literal expressions that can be evaluated (`!true`, `1 == 2`, `true && false`)
  are evaluated. A statically false gate condition is `WORKFLOW_SKIPS_CBE_GATE`
  exit 3. A statically true condition is reachable.
- These warnings mean “not proven”, not “safe”. They do not upgrade the
  workflow to PASS coverage.

Workflow scope:

- `--workflows` scans only the target repository's `.github/workflows/`.
- CBE's own gate workflow is never scanned implicitly.
- When the target is CBE itself (detected by `pyproject.toml` naming `cbe` plus
  `src/cbe/cli.py`), the command exits 2
  `SELF_WORKFLOW_EXCLUSION_REQUIRED` unless the caller passes
  `--exclude-workflow .github/workflows/cbe-e2e.yml`.
- It never silently scans CBE's own workflow and never silently skips an
  un-excluded workflow. CBE-04 covers both refusal and excluded-pass.

Exemption grammar (dedicated file only; inline source comments are not honored):

```text
SKIPPED: CBE-QUALITY-001 reason=legacy fixture, tracked in ISSUE-42
```

- One entry per line; `#` starts a comment; blank lines ignored.
- Unknown rule, duplicate, missing reason, or bad format → exit 2. An exemption
  for a rule that does not exist is an input error, never a warning.
- Blocking rule exemption → exit 3, `blocking_skip=true`.
- Non-applicable exemption → SKIPPED, not in denominator, warning.
- Applicable advisory exemption → counted in `skip_count`.
- `applicable_count` is the F2 denominator: applicable advisory rules only.
  `blocking_applicable_count` is reported separately and never enters the
  denominator.
- Output keys: `bypass_attempts`, `exemptions`, `scanned`,
  `applicable_count`, `skip_count`, `not_applicable_count`, `skip_ratio`,
  `blocking_skip`, `blocking_applicable_count`, `warn_count`, `warnings`.
- `warn_count == len(warnings)` and includes `UNVERIFIABLE_CONDITION`,
  `UNVERIFIABLE_NEEDS_CHAIN`, `EXEMPTION_NOT_APPLICABLE`, `NO_ADVISORY_CHECKS`,
  and manifest warnings. It is machine-readable output, not stderr-only.
- Each `bypass_attempts[]` entry includes `reason`. A skipped gate job carries
  `reason=WORKFLOW_SKIPS_CBE_GATE`; `continue-on-error`/`|| true` entries carry
  an empty reason and remain generic workflow bypasses.

## 5. emit-sarif

```text
cbe emit-sarif --manifest PATH --run-report PATH
    --source-root PATH --out PATH
    [--provider-output PATH ...]
    [--output PATH] [--help]
```

SARIF requirements:

- `$schema` is the OASIS SARIF 2.1.0 schema; `version` is `"2.1.0"`.
- One run per enabled provider; `tool.driver.name = "CBE/<provider>"`.
- Published `ruleId` values are `CBE-*` only; CBP/CBG → exit 3.
- `ruleIndex` is within the driver rules array; `level` is
  `error/warning/note`; `message.text` is non-empty.
- Locations are relative POSIX URIs under `--source-root`; absolute paths,
  `..`, and backslashes → exit 3.
- Findings matching an exemption carry a SARIF `suppression` with the exact
  `SKIPPED: ...` justification; the result is not deleted.
- Output keys: `sarif_path`, `sarif_sha256`, `run_count`, `rule_count`,
  `result_count`, `namespaces`, `invalid_results`, `warnings`.

Interop acceptance for P0-05 (CBP side, not a CBE command): CBE SARIF is
consumed by CBP 1.1.0. CBP maps foreign `CBE-*` IDs to `CBP-EXT-*` in its
`rule` field and retains the original in `origin_rule`; CBP output carries only
`CBP-*`. CBE-07b is a real assertion of that namespace isolation. `--rules-path`
itself remains CBP P0-06, not a CBE subcommand.

## Report assembly (not a sixth subcommand)

`tools/cbe_gate.py` calls the five commands and assembles the §5 report.
F2 skip counts and report/body assembly live there. F4 baseline selection,
F5 infra classification, and F6 NOT_UPLOADED integration remain pending; they
are not implemented by this tool yet.

- Report fields (all required, no extra fields):
  `schema_version`, `package_id`, `producer_id`, `version`, `tag`,
  `gate_status`, `exit_code`, `applicable_count`, `skip_count`, `skip_ratio`,
  `blocking_skip`, `warn_count`, `rules_manifest_hash`, `sarif_paths`,
  `evidence_sha256`.
- `package_id` is the subject package; `producer_id` is `cbe`.
- Hashes are bare 64 lowercase hex.
- `applicable_count == 0` → exit 3, never 0.
- `skip_count * 5 > applicable_count` → exit 4; exactly 20% passes.
- `blocking_skip=true` → exit 3.
- `SKIPPED_INFRA` and `NOT_UPLOADED` never enter the skip ratio.
- `warn_count` is the sum of command warnings, including
  `UNVERIFIABLE_CONDITION` / `UNVERIFIABLE_NEEDS_CHAIN`. `tools/cbe_gate.py`
  writes it into `cbe-report.json` and Section B of `cbe-body-section.md`.
  CBS Release-body integration (consuming the CBE fragment) remains a CBS-side
  pending item; CBE-local report/body visibility is implemented.

F4 baseline and release-train handling are specified in
`CONTRACT_AMENDMENTS_PROPOSED.md` and `DECISIONS.md`; F4 self-bootstrap remains
pending because CBE has no stable predecessor yet.

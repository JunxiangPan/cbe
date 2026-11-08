# CBE — Cyber-Butler Enforcement gate

CBE is the rule-pack manifest, provider execution, no-bypass enforcement, and
SARIF evidence gate for the Cyber-Butler release train. It is a sibling project
to `public-release` (CBS), `cbp-action-release` (CBP), and `cbm`.

Status: **commit 7**. Commit 1 froze the manifest schema, the five CLI
interfaces, and the E2E fixtures. Commit 2 added the manifest validator
(P0-03). Commit 3 added `enforce-no-bypass` (P0-04), the `RuleSet` shared model,
`run_e2e.py`, and CBE-01..CBE-04 E2E. Commit 4 added workflow gate-skip
detection (P0-04.5). Commit 5 added static-analysis warnings. Commit 6 added the
restricted-evaluator security evidence, `warn_count`, and the CBE-07a/b split.
Commit 7 adds the dynamic-comparison test, the B-32 consequence text, the
Ubuntu+Windows CI matrix, and the coverage gate. `run-provider`,
`symbol-index`, and `emit-sarif` still return exit 3 `NOT_IMPLEMENTED`; actual
rule packs are not part of this repository yet.

## Runtime dependencies

CBE is **not** zero-runtime-dependency. It declares:

| Dependency | Used by | Notes |
|---|---|---|
| `jsonschema>=4.20` | `validate-manifest`; any command that loads a manifest | core dependency |
| `pyyaml>=6.0` | `enforce-no-bypass --workflows` | target GitHub Actions YAML parsing; currently a core dependency, not an optional extra |

Both are in `pyproject.toml`. The workflow parser reads only the target
repository's `.github/workflows/`; it does not execute workflow YAML or any
GitHub expression.

## CI

`.github/workflows/cbe-e2e.yml` runs on `ubuntu-latest` and `windows-latest`
with Python 3.10. Each job runs `tests/e2e/run_e2e.py` and a unit-test coverage
gate (`--cov=cbe --cov-fail-under=60`). The gate covers measured unit-test
coverage; E2E commands run in subprocesses and are not counted by coverage.

## Scope of the first commit

- `schemas/rule-pack-manifest.v1.schema.json`
- `schemas/v1.7/release-train.schema.json`
- `schemas/v1.7/cbe-report.schema.json` (CBE-local proposal; CBS schema update pending)
- `src/cbe/` CLI skeleton (five subcommands, `--help`, JSON envelope, exit codes)
- `tests/e2e/fixtures/` (manifests, providers, bypass cases, exemptions, releases, SARIF, release-train)
- `docs/` decisions, contract amendment patches, CLI/manifest/E2E/boundary specs

No security rule implementation is included in the first commit.

## Commit 2 scope

- `src/cbe/manifest.py`: manifest schema + semantic checks S01–S14,
  applicability, canonical hash.
- `src/cbe/commands/validate_manifest.py`: P0-03 command, including
  `blocking_applicable_count` and `gate_errors`.
- `tests/unit/test_manifest.py`: 34 tests covering valid/invalid fixtures,
  mixed LF/CRLF hashes, semantic failures, gate failures, duplicate keys, BOM,
  and version constraints.

## Commit 3 scope

- `src/cbe/manifest.py`: `RuleSet` / `Rule` / `Applicability` shared model; the
  manifest validator and no-bypass command consume the same in-memory model.
- `src/cbe/walk.py`: deterministic, bounded source walk with symlink-escape
  rejection and CBE self-repository detection.
- `src/cbe/commands/enforce_no_bypass.py`: config/comment/env/workflow
  detection, strict exemption parser, F2 denominator, blocking skip, and the
  CBE self-workflow guard.
- `tests/e2e/run_e2e.py` + CBE-01..CBE-04 E2E; `.github/workflows/cbe-e2e.yml`.
- Negative sample: `run-provider`, `symbol-index`, and `emit-sarif` return exit 3
  `NOT_IMPLEMENTED`, never `PASS`.

## Commit 4 scope

- PyYAML job-graph parsing for GitHub Actions workflows.
- Detection of a `cbe-gate` job skipped by literal `if: false`,
  `${{ false }}` reachability through `needs`, a missing dependency, or a
  commented-out job. Exit 3 with `reason=WORKFLOW_SKIPS_CBE_GATE`.
- CBE-04 subcases: direct `if: false`, unreachable `needs`, commented-out job,
  and a reachable `cbe-gate` control.

## Commit 5 scope

- Literal condition evaluation: `!true`, `1 == 2`, `true && false` are
  evaluated; a statically false gate is `WORKFLOW_SKIPS_CBE_GATE`.
- Dynamic conditions (`inputs.*`, `vars.*`, `github.*`, functions) emit
  `UNVERIFIABLE_CONDITION`; dynamic `needs` chains emit
  `UNVERIFIABLE_NEEDS_CHAIN`. These are warnings, never silent passes.
- B-30 static-analysis limits, B-31 CBP `report_aggregator.py` interop block,
  and CBE-08 “rewrite, not re-assert” wording.
- Runtime dependencies documented: jsonschema + PyYAML.

## Commit 6 scope

- Restricted condition evaluator evidence: `env.FOO()` and
  `__import__('os')...` are `UNVERIFIABLE_CONDITION`, never executed.
- `warn_count` in `enforce-no-bypass` JSON, equal to `len(warnings)`.
- B-32: `warn_count` must flow into `cbe-report.json` and Release body Section B
  in P0-05; not claimed before that wiring exists.
- CBE-07 split: 07a (CBE output `CBE-*`) must PASS; 07b (CBP consumes and
  preserves) explicit SKIP `CBP_REPORT_AGGREGATOR_NOT_FIXED`, counted in
  `skip_count`, visible.

`run-provider`, `symbol-index`, and `emit-sarif` remain skeleton stubs in this
commit.

## Commands

```text
cbe validate-manifest
cbe run-provider
cbe symbol-index
cbe enforce-no-bypass
cbe emit-sarif
```

Every command supports `--help`, writes a single JSON object to stdout, and uses
only `0 / 2 / 3 / 4` as exit codes. See `docs/CLI_V1.md`.

## Contract source

The only contract source is:

```text
public-release/docs/v1.7/CONTRACT.md @ commit 4a437df
sha256 a561f19e0a8e4dba92af82400b5696da18e000ba5362571cb0b40243b9a3afca
```

`public-release` is read-only from CBE. The three required amendments (F2
blocking set, hash format, report identity) are staged as an applicable patch in
`docs/CONTRACT_AMENDMENTS_PROPOSED.md`; they are not in force until CBS applies
them.

## First run

```bash
python -m pip install -e .
cbe --help
cbe validate-manifest --help
```

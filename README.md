# CBE — Cyber-Butler Enforcement gate

CBE is the rule-pack manifest, provider execution, no-bypass enforcement, and
SARIF evidence gate for the Cyber-Butler release train. It is a sibling project
to `public-release` (CBS), `cbp-action-release` (CBP), and `cbm`.

Status: **0.1.0 RC candidate — not released, no tag, no release**. Commit 1
froze the manifest schema, the five CLI interfaces, and the E2E fixtures. Commit
2 added the manifest validator (P0-03). Commit 3 added `enforce-no-bypass`
(P0-04). Commit 4 added workflow gate-skip detection (P0-04.5). Commit 5 added
static-analysis warnings. Commit 6 added the restricted-evaluator evidence and
`warn_count`. Commit 7 added the Ubuntu+Windows CI matrix and coverage gate.
Commit 8 implemented P0-05 (`symbol-index`, `run-provider`, `emit-sarif`,
`tools/cbe_gate.py`). Commit 9 made CBE-07b a real CBP 1.1.0 assertion. Commit
10 is the 0.1.0 RC candidate: CBE-07b re-run on CBP 1.2.0 RC, CBE-09/10/11
implemented, CBE-08 kept DRAFT, CBP 1.2.0 manifest fields aligned, and schemas
bundled in the wheel. Commit 13 pins the released CBP 1.2.0 from PyPI. CBE-08 is
**not PASS**; no tag/release exists.

## 0.1.0 RC inputs

- CBP 1.2.0 official: tag/main `5ebd0eb…`; PyPI wheel
  `188639bb47e5a8940defbdb5ba3c4270ae89ad68503d283b611cb2a00497da2e`,
  sdist `08392b2af6b3ff29dc21cfe5db0f23d628307ccac06b9035639f32da6343defd`.
  CBE-07b passes with the installed official wheel; the project pin is
  `cbp-action==1.2.0`. Earlier 1.2.0 RC candidates also passed.
- CBS `contract/v1.7.1` RC: commit `3de93ae`; declared and observed contract
  SHA256 both `c1653c…`; `vm-proof.yml` is clean. The contract is still
  **NOT FROZEN**. CBE-08 remains DRAFT.
- CBE: `0.1.0` package version, no tag, no release.

## Runtime dependencies

CBE is **not** zero-runtime-dependency. It declares:

| Dependency | Used by | Notes |
|---|---|---|
| `jsonschema>=4.20` | `validate-manifest`; any command that loads a manifest | core dependency |
| `pyyaml>=6.0` | `enforce-no-bypass --workflows` | target GitHub Actions YAML parsing; currently a core dependency, not an optional extra |
| `cbp-action==1.2.0` | CBE-07b cross-repo assertion | test-only `e2e` extra; not a CBE runtime dependency |

Both are in `pyproject.toml`. The workflow parser reads only the target
repository's `.github/workflows/`; it does not execute workflow YAML or any
GitHub expression.

## CI

`.github/workflows/cbe-e2e.yml` runs on `ubuntu-latest` and `windows-latest`
with Python 3.10. Each job installs `.[e2e]` (including `cbp-action==1.2.0`
for CBE-07b), runs `tests/e2e/run_e2e.py`, and enforces a 60% unit-test
coverage gate (`--cov=cbe --cov-fail-under=60`). The gate covers measured
unit-test coverage; E2E commands run in subprocesses and are not counted by
coverage.

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
- CBE-07 split: 07a (CBE output `CBE-*`) must PASS; 07b introduced as an
  explicit SKIP and converted to a real CBP 1.1.0 assertion in commit 9.

## Commit 7 scope

- Dynamic comparison test `inputs.foo == inputs.bar` -> `UNVERIFIABLE_CONDITION`.
- B-32 consequence text.
- Ubuntu+Windows CI matrix and unit coverage gate.

## Commit 8 scope

- `symbol-index`: deterministic Python/PowerShell symbol index with file hashes.
- `run-provider`: manifest-driven provider execution, SARIF/JSON validation,
  zero findings vs empty artifact, native ID mapping, exemptions, F2 counts.
- `emit-sarif`: merged SARIF 2.1.0 with `CBE-*` rule IDs and namespace checks.
- `tools/cbe_gate.py`: assembles `cbe-report.json` and
  `cbe-body-section.md`; `warn_count` and warning codes reach Section B.
- CBE-05/06/07/07a E2E.

## Commit 9 scope

- CBE-07b is a real assertion against CBP 1.1.0, installed via the `e2e` extra.
- CBE emits `CBE-SECRET-001`; CBP emits `CBP-EXT-SECRET-001` in `rule` and
  retains `origin_rule: CBE-SECRET-001`.
- The old “CBP preserves CBE-*” assumption is retired; CBP namespace isolation
  is the actual contract.
- CI installs `.[e2e]` on Ubuntu and Windows.

## Commit 10 scope (0.1.0 RC candidate)

- CBE-07b re-run against CBP 1.2.0 RC `5da8b87`, `bb8d4d6`, and `855fed7` in
  temporary venvs; wheel hashes recorded in `artifacts/rc-0.1.0/`.
- CBE-09 F4 baseline selector; CBE-10 F5/F6 release-train and CBP 1.2.0
  manifest checks; CBE-11 self-bootstrap harness.
- CBE-08 kept DRAFT against CBS `contract/v1.7.1` RC `04c9f8b`; no PASS claim.
- CBP 1.2.0 fields: `body_hash_scope=base`, `artifact_repository` string,
  no private `cbc_event` manifest field.
- Schemas bundled in the wheel; installed-wheel smoke test passes.
- RC audit package at `artifacts/rc-0.1.0/`; no tag, no release.

## Commit 11 scope (RC closeout)

- CBE-08 draft re-pinned to CBS `contract/v1.7.1` RC `3de93ae`; declared and
  observed contract hash both `c1653c…`; `vm-proof.yml` has no conflict markers;
  status remains **DRAFT — NOT PASS**.
- CBE-07b re-run on CBP 1.2.0 RC `855fed7`; wheel
  `9469a8e980a536e9481e0b14239cd4857a5cd6173a61043d47645b82cf3b4d51`;
  `CBE-SECRET-001` → `CBP-EXT-SECRET-001`, `origin_rule` retained.
- RC audit package and SHA256SUMS updated; no tag, no release.

## Commit 12 scope (contract guard)

- `tests/e2e/fixtures/contract/v1.7.1-pin.json` pins `3de93ae` / `c1653c…`.
- `tools/cbe_contract_guard.py` fetches the current `contract/v1.7.1` head,
  contract bytes, and `vm-proof.yml`; drift exits 3 `CONTRACT_CHANGED`.
- `tests/e2e/test_cbe_08_contract_guard.py` proves the pinned case and simulated
  commit/hash drift. Guard `PINNED` is **not** CBE-08 PASS.
- CBE-07b re-run on CBP 1.2.0 RC `855fed7`; audit package refreshed.

## Commit 13 scope (CBP 1.2.0 official)

- `pyproject.toml` `e2e` extra pins `cbp-action==1.2.0` (released, not RC).
- PyPI wheel `188639bb…` and sdist `08392b2a…` downloaded and hash-checked.
- CBE-07b re-run with the installed official 1.2.0: `CBE-SECRET-001` →
  `CBP-EXT-SECRET-001`, `origin_rule: CBE-SECRET-001`.
- Audit package records the official dependency evidence; CBE-08 remains DRAFT.

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

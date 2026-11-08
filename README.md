# CBE — Cyber-Butler Enforcement gate

CBE is the rule-pack manifest, provider execution, no-bypass enforcement, and
SARIF evidence gate for the Cyber-Butler release train. It is a sibling project
to `public-release` (CBS), `cbp-action-release` (CBP), and `cbm`.

Status: **commit 2 in progress**. Commit 1 froze the manifest schema, the five
CLI interfaces, and the E2E fixtures. Commit 2 adds the manifest validator
(P0-03) and its unit tests. The other four command bodies still return exit 3
`NOT_IMPLEMENTED`; actual rule packs are not part of this repository yet.

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

`run-provider`, `symbol-index`, `enforce-no-bypass`, and `emit-sarif` remain
skeleton stubs in this commit.

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

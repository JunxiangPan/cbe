# CBE — Cyber-Butler Enforcement gate

**Who it is for:** platform, security, and release engineers who need a
deterministic gate between “CI passed” and “this artifact may ship”.

**What it solves:** CBE turns rule-pack manifests into an enforceable release
gate: it validates the pack, runs providers, rejects disable/skip attempts,
emits SARIF, and produces a machine-readable gate report plus a Release-body
fragment. It is a sibling of CBS, CBP, and CBM, not a replacement for them.

**How to start:**

```bash
python -m pip install cbe-review
cbe --help
cbe validate-manifest --manifest rules.json \
  --package-type cbs --package-version v1.7.0
```

> **Important:** `pip install cbe` installs a **different project** (Crossroads
> Bank for Enterprises). This project is distributed as **`cbe-review`**. Its
> import package and CLI are still `cbe`.

## Install

```bash
python -m pip install cbe-review
```

Requires Python 3.10+. Runtime dependencies: `jsonschema` and `pyyaml`.

From a GitHub Release, use the attached
`cbe_review-0.1.1-py3-none-any.whl` (or the sdist).

## Quick start

```bash
# Validate a rule pack
cbe validate-manifest --manifest rules.json

# Run providers and write evidence
cbe run-provider --manifest rules.json --source-root . --out-dir out --all

# Enforce no-bypass rules
cbe enforce-no-bypass --manifest rules.json --source-root . \
  --package-type cbs --package-version v1.7.0 --workflows

# Build a symbol index / merge SARIF
cbe symbol-index --source-root . --out out/symbol-index.json
cbe emit-sarif --manifest rules.json --run-report out/run.json \
  --source-root . --out out/cbe.sarif
```

Exit codes: `0 PASS`, `2 input/format error`, `3 gate failure or
SKIPPED_INFRA`, `4 skip ratio > 20%`.

## What CBE checks

- Rule-pack schema and semantics, including canonical manifest hash.
- Provider execution and SARIF/JSON artifact validation.
- No-bypass controls across config, source comments, environment, and GitHub
  Actions workflows.
- Workflow gate-job reachability, including local reusable-workflow
  delegation.
- CBE report identity, counts, skip ratio, and Release-body Section B.

Dynamic workflow expressions are not guessed. By default they are reported as
`UNVERIFIABLE_*` warnings; use `enforce-no-bypass --strict` to turn the
unverifiable conditions into exit 3.

## Project links

- Homepage / repository: <https://github.com/JunxiangPan/cbe>
- Issues: <https://github.com/JunxiangPan/cbe/issues>
- CLI reference: [docs/CLI_V1.md](docs/CLI_V1.md)
- Rule-pack schema: [docs/RULE_PACK_MANIFEST_V1.md](docs/RULE_PACK_MANIFEST_V1.md)
- E2E matrix: [docs/E2E_MATRIX_V1.md](docs/E2E_MATRIX_V1.md)
- Boundaries: [docs/BOUNDARIES_V1.md](docs/BOUNDARIES_V1.md)
- 0.1.1 metadata/licensing note: [docs/CBE-0.1.1_METADATA.md](docs/CBE-0.1.1_METADATA.md)

Topics: `release-gate`, `sarif`, `supply-chain`, `provenance`, `python`.

## Status and compatibility

CBE 0.1.0 is released on GitHub and PyPI
([`cbe-review==0.1.0`](https://pypi.org/project/cbe-review/0.1.0/)).
This tree is **0.1.1**, adding Apache-2.0 licensing and complete package
metadata.

**0.1.0 metadata is immutable.** PyPI metadata (license, classifiers, project
URLs, author) cannot be changed after upload; the corrections in 0.1.1 take
effect only in the new release. The 0.1.0 artifacts and `v0.1.0` tag are
unchanged.

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Development

```bash
python -m pip install -e ".[e2e]"
pytest
pytest tests/unit --cov=cbe --cov-fail-under=60
```

The CI matrix runs Ubuntu and Windows on Python 3.10. The gate covers unit
coverage; E2E commands run in subprocesses and are not counted by coverage.

# CBE 0.1.0 — Release Notes

Status: **ready for human approval — NOT tagged, NOT released, NOT uploaded to PyPI.**

CBE (Cyber-Butler Enforcement gate) 0.1.0 is the first stable CBE release. It
provides the rule-pack manifest, provider execution, no-bypass enforcement,
SARIF evidence, and the CBE report/body fragment for the Cyber-Butler release
train.

Distribution identity:

```text
PyPI distribution: cbe-review
Import package:    cbe
CLI:               cbe
package_id:        cbe
producer_id:       cbe
```

The `cbe` PyPI name belongs to `azizo-b/CBE` and is **not used**.

## Highlights

- Five CLI commands: `validate-manifest`, `enforce-no-bypass`,
  `symbol-index`, `run-provider`, `emit-sarif`.
- Manifest schema and semantic validation; provider SARIF/JSON validation;
  native provider ID mapping; deterministic exemptions.
- No-bypass enforcement across config, comments, environment, and GitHub
  Actions workflows; dynamic workflow conditions are explicit warnings.
- CBE report and Release-body Section B assembly with `warn_count`.
- F4 baseline selection, F5/F6 release-train handling, and self-bootstrap
  harness.
- CBE-08 **PASS** against frozen `contract-v1.7.1`; authorized by
  `FREEZE_NOTICE_ADDENDUM.md`.
- CBE-07b **PASS** on CBP 1.2.2; CBE-10 **PASS** with the real CBP 1.2.2
  quality manifest.
- Schemas bundled in the wheel; installed-wheel smoke test passes.

## Verification

```text
Tests:      176 passed = 74 unit + 102 E2E
Coverage:   71.89% (gate 60%)
CI:         Ubuntu + Windows success
Run:        https://github.com/JunxiangPan/cbe/actions/runs/42648086977
Source:     4561e8338a09a7e681b08fc0c2b38fcff2d56e70
```

Contract and upstream pins:

```text
CBS contract: tag contract-v1.7.1 / c2b5e9 / 209d75b4…
CBE-08 addendum: e318cbd / 51604f56…
CBP: cbp-action==1.2.2
```

## Artifacts

| File | SHA256 | Size |
|---|---|---|
| `cbe_review-0.1.0-py3-none-any.whl` | `87f0ad40a6cffdf4f9c657e6cc972a0f93787259c52445a1c112a5c7753599a7` | 52,090 B |
| `cbe_review-0.1.0.tar.gz` | `a77c653d178d5d0ab179da73c92184d9a54d5104ca5202f41574588979b68854` | 46,253 B |

Install from the wheel:

```bash
python -m pip install cbe_review-0.1.0-py3-none-any.whl
cbe --help
```

If and when PyPI publication is approved:

```bash
python -m pip install cbe-review==0.1.0
```

Runtime dependencies: `jsonschema>=4.20`, `pyyaml>=6.0`. Python >= 3.10.
Test-only `e2e` extra pins `cbp-action==1.2.2`.

## PyPI status

`cbe-review` is currently unclaimed on PyPI. Status: **PENDING HUMAN
APPROVAL**. Do not upload the old `cbe` name; it belongs to a different
project.

## Evidence

- [CBE-08 PASS](evidence/cbe-08-frozen.json)
- [Contract guard](evidence/contract-guard.json)
- [CBE-07b on CBP 1.2.2](evidence/cbp-1.2.2-official.json)
- [Real CBP 1.2.2 quality manifest](evidence/cbp-1.2.2-quality-manifest.json)
- [CBE-10 F5/F6 + RC2 fields](evidence/cbe-10-f5-f6.json)
- [Real CBE report vs RC2 schema](evidence/cbe-report-rc2.validation.json)

## Release boundary

No release tag, GitHub Release, or PyPI upload exists. Human approval is
required before any of them is created. See `RELEASE_RUNBOOK.md`.

# CBE 0.1.0 — Release Notes

Status: **ready for human approval — NOT tagged, NOT released, NOT uploaded to PyPI.**

CBE (Cyber-Butler Enforcement gate) 0.1.0 is the first stable CBE release. It
provides the rule-pack manifest, provider execution, no-bypass enforcement,
SARIF evidence, and the CBE report/body fragment for the Cyber-Butler release
train.

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
Run:        https://github.com/JunxiangPan/cbe/actions/runs/42634308910
Source:     d820001ec1120408b4d76db323e9153465359805
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
| `cbe-0.1.0-py3-none-any.whl` | `966fabf110eb2909722670f23c4b22efdca773b1cd1381bd4fcc90e02266fa6e` | 51,764 B |
| `cbe-0.1.0.tar.gz` | `bc474810fabce42397f75fa68dace3182f9308ab0681b53597c56220493daaff` | 45,983 B |

Install from the wheel:

```bash
python -m pip install cbe-0.1.0-py3-none-any.whl
cbe --help
```

Runtime dependencies: `jsonschema>=4.20`, `pyyaml>=6.0`. Python >= 3.10.
Test-only `e2e` extra pins `cbp-action==1.2.2`.

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

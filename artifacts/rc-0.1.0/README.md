# CBE 0.1.0 RC audit package

Status: **RC candidate — NOT released, no tag, no GitHub release, no PyPI upload.**
Human audit is required before any tag or publish.

## Inputs

| Input | Ref | Evidence |
|---|---|---|
| CBP 1.2.0 RC (requested baseline) | `5da8b87` | wheel `40b0f5f827acefe4f5f9a5891a5d70be9d53557435acd721706c6a9f01fff320`, sdist `e30fa831…` |
| CBP 1.2.0 RC (later candidate) | `bb8d4d6` | wheel `06f8c3d383d39ae4e42cee2a69abdaebdc15cae9fce63a65baf05da4d0998285`, sdist `49592d6b…` |
| CBS contract RC | `04c9f8b` | declared `19b37f…` != observed `c1653c…`; not frozen; `vm-proof.yml` has conflict markers |

CBP RC wheels were installed only in temporary venvs. The project
`cbp-action==1.1.0` pin is unchanged.

## Results

| Check | Status | Evidence |
|---|---|---|
| CBE-01..CBE-07a | PASS | CI + local E2E |
| CBE-07b on CBP 1.2.0 RC | PASS on both RC candidates | `evidence/cbp-1.2.0-rc-*.json` |
| CBE-08 F2 | **DRAFT — not PASS** | `evidence/cbe-08-draft.json`, `docs/CBE-08_DRAFT.md` |
| CBE-09 F4 baseline | implemented; no stable CBE yet | `evidence/cbe-09-baseline.json` |
| CBE-10 F5/F6 + CBP 1.2.0 fields | PASS | `evidence/cbe-10-f5-f6.json` |
| CBE-11 self-bootstrap | bootstrap PASS; not a stable claim | `evidence/cbe-11-selfcheck.json` |
| Wheel install | PASS; schemas bundled | installed-wheel smoke test |

## Boundaries

- CBE-08 must stay DRAFT until CBS freezes `contract/v1.7.1` and the contract
  hash is consistent. The observed RC contract hash differs from the declared
  candidate hash, and `vm-proof.yml` still has conflict markers.
- CBP 1.2.0 RC uses `artifact_repository` as an `owner/repo` string; the CBS RC
  contract sketches an object. CBE follows CBP 1.2.0 RC and records the mismatch
  (B-33). No private union.
- `cbc-event` is CBP's JSONL event stream, not a manifest field. CBE rejects a
  private `cbc_event` manifest key.
- There is no previous stable CBE, so CBE-09/CBE-11 evidence is explicit
  `bootstrap=true`, never a fake stable baseline.

## CI

- Ubuntu: success
- Windows: success
- Run: https://github.com/JunxiangPan/cbe/actions/runs/42544634996
- 164 tests = 71 unit + 93 E2E
- Coverage: 71.82% (gate 60%)

## Release discipline

No tag, no GitHub release, no PyPI upload was created. Do not create one until
a human audits this package.

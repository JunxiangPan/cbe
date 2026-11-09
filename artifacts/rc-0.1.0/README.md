# CBE 0.1.0 RC audit package

Status: **RC candidate — NOT released, no tag, no GitHub release, no PyPI upload.**
Human audit is required before any tag or publish.

## Inputs

| Input | Ref | Evidence |
|---|---|---|
| CBP 1.2.0 official | `v1.2.0` / `5ebd0eb` | wheel `188639bb47e5a8940defbdb5ba3c4270ae89ad68503d283b611cb2a00497da2e`, sdist `08392b2a…` |
| CBP 1.2.2 | not released | object shape is fixture-tested only; no CBP 1.2.2 PASS |
| CBS contract RC2 | `6835789` | declared and observed `209d75b4…`; `vm-proof.yml` clean; **NOT FROZEN** |
| RC2 CBE report schema | `2b3e1c5a…` | real CBE report validates with zero errors |

CBE's `e2e` extra pins the released `cbp-action==1.2.0`. CBP 1.2.2 has not been
released; it will be pinned only after release. RC wheels are historical
evidence only.

## Results

| Check | Status | Evidence |
|---|---|---|
| CBE-01..CBE-07a | PASS | CI + local E2E |
| CBE-07b on CBP 1.2.0 official | PASS | `evidence/cbp-1.2.0-official.json` |
| CBE-08 F2 | **DRAFT — not PASS** | `evidence/cbe-08-draft.json`, `docs/CBE-08_DRAFT.md` |
| CBE-08 contract hash guard | **PINNED** to `6835789` / `209d75b4…`; not a PASS | `evidence/contract-guard.json` |
| Real CBE report vs RC2 schema | PASS; schema `2b3e1c5a…` | `evidence/cbe-report-rc2.validation.json` |
| Real CBE report vs RC2 schema | PASS | `evidence/cbe-report-rc2.validation.json` |
| CBE-09 F4 baseline | implemented; no stable CBE yet | `evidence/cbe-09-baseline.json` |
| CBE-10 F5/F6 + RC2 manifest fields | **FIXTURE PASS**; CBP 1.2.2 pending | `evidence/cbe-10-f5-f6.json` |
| CBE-11 self-bootstrap | bootstrap PASS; not a stable claim | `evidence/cbe-11-selfcheck.json` |
| Wheel install | PASS; schemas bundled | installed-wheel smoke test |

## Boundaries

- CBE-08 must stay DRAFT until CBS freezes `contract/v1.7.1`. RC2 hash and
  `vm-proof.yml` are aligned, but the contract still says **RC2, NOT FROZEN**.
  The guard passing means “the pin is intact”, **not** “CBE-08 PASS”.
- The guard fails with `CONTRACT_CHANGED` if the branch moves, the contract
  bytes change, or `vm-proof.yml` gets conflict markers.
- RC2 makes `artifact_repository` the object
  `{repository, run_id, artifact_name}`. CBE accepts it and rejects bare
  strings. CBP 1.2.2 is not released, so this is fixture evidence only; no
  CBP 1.2.2 PASS is claimed. B-33 is resolved on the contract side.
- `schema_version` must be the string `"1"`; numeric `1` is rejected.
- `NOT_UPLOADED` is supported and is not PASS, not SKIP, and not counted.
- There is no previous stable CBE, so CBE-09/CBE-11 evidence is explicit
  `bootstrap=true`, never a fake stable baseline.

## CI

- Ubuntu: success
- Windows: success
- Run: https://github.com/JunxiangPan/cbe/actions/runs/42617711567
- 174 tests = 74 unit + 100 E2E
- Coverage: 71.89% (gate 60%)
- Installed dependency: `cbp-action==1.2.0` (official)
- CBE wheel: `04e0b915da9d282d5dc4d6c8f79fd216d14be93c5d1136ab641494ed24adfe5a`

## Release discipline

No tag, no GitHub release, no PyPI upload was created. Do not create one until
a human audits this package.

# CBE 0.1.0 RC audit package

Status: **RC candidate — NOT released, no tag, no GitHub release, no PyPI upload.**
Human audit is required before any tag or publish.

## Inputs

| Input | Ref | Evidence |
|---|---|---|
| CBP 1.2.2 official | `v1.2.2` / `d4bfefb` | wheel `2b73b4a4…`, sdist `91974398…`, manifest `228594d0…` |
| CBP 1.2.0 official (historical) | `v1.2.0` / `5ebd0eb` | wheel `188639bb…` |
| CBS contract frozen | `tag contract-v1.7.1` / `c2b5e9` | hash `209d75b4…`; freeze baseline `6835789`; `vm-proof.yml` clean |
| RC2 CBE report schema | `2b3e1c5a…` | real CBE report validates with zero errors |

CBE's `e2e` extra pins the released `cbp-action==1.2.2`. The CBP
1.2.2 quality manifest is the real Release asset; no CBP 1.2.2 gate PASS is
claimed by CBE.

## Results

| Check | Status | Evidence |
|---|---|---|
| CBE-01..CBE-07a | PASS | CI + local E2E |
| CBE-07b on CBP 1.2.2 official | PASS | `evidence/cbp-1.2.2-official.json` |
| CBE-08 F2 | **DRAFT — not PASS** | `evidence/cbe-08-frozen.json`, `docs/CBE-08_DRAFT.md` |
| CBE-08 contract guard | **PINNED** to tag `contract-v1.7.1` / `c2b5e9` / `209d75b4…`; not a PASS | `evidence/contract-guard.json` |
| Real CBE report vs RC2 schema | PASS; schema `2b3e1c5a…` | `evidence/cbe-report-rc2.validation.json` |
| CBE-09 F4 baseline | implemented; no stable CBE yet | `evidence/cbe-09-baseline.json` |
| CBE-10 F5/F6 + RC2 manifest fields | **PASS** with real CBP 1.2.2 manifest | `evidence/cbe-10-f5-f6.json` |
| CBE-11 self-bootstrap | bootstrap PASS; not a stable claim | `evidence/cbe-11-selfcheck.json` |
| Wheel install | PASS; schemas bundled | installed-wheel smoke test |

## Boundaries

- CBS has frozen `contract/v1.7.1` at tag `contract-v1.7.1`, but its
  `docs/v1.7/FREEZE_NOTICE.md` explicitly says **“CBE-08 remains DRAFT; do not
  report PASS.”** Therefore CBE-08 stays DRAFT. This is a contract instruction,
  not a missing freeze; flipping it would be a false PASS.
- The guard pins the immutable tag, not the moving branch. It fails with
  `CONTRACT_CHANGED` if the tag/commit/hash changes or `vm-proof.yml` gets
  conflict markers.
- RC2 makes `artifact_repository` the object
  `{repository, run_id, artifact_name}`. CBE accepts the real CBP 1.2.2
  manifest and rejects bare strings. B-33 is resolved by RC2 + CBP 1.2.2.
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

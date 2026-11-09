# CBE 0.1.0 RC audit package

Status: **RC candidate — NOT released, no tag, no GitHub release, no PyPI upload.**
Human audit is required before any tag or publish.

## Inputs

| Input | Ref | Evidence |
|---|---|---|
| CBP 1.2.2 official | `v1.2.2` / `d4bfefb` | wheel `2b73b4a4…`, sdist `91974398…`, manifest `228594d0…` |
| CBP 1.2.0 official (historical) | `v1.2.0` / `5ebd0eb` | wheel `188639bb…` |
| CBS contract frozen | `tag contract-v1.7.1` / `c2b5e9` | hash `209d75b4…`; freeze baseline `6835789`; `vm-proof.yml` clean |
| CBS CBE-08 addendum | `e318cbd` | `FREEZE_NOTICE_ADDENDUM.md` sha256 `51604f56…`; authorizes PASS if four checks match |
| RC2 CBE report schema | `2b3e1c5a…` | real CBE report validates with zero errors |

CBE's `e2e` extra pins the released `cbp-action==1.2.2`. The CBP
1.2.2 quality manifest is the real Release asset; no CBP 1.2.2 gate PASS is
claimed by CBE.

## Results

| Check | Status | Evidence |
|---|---|---|
| CBE-01..CBE-07a | PASS | CI + local E2E |
| CBE-07b on CBP 1.2.2 official | PASS | `evidence/cbp-1.2.2-official.json` |
| CBE-08 F2 | **PASS**; four frozen checks match | `evidence/cbe-08-frozen.json`, `docs/CBE-08_PASS.md` |
| CBE-08 contract guard | **PINNED** to tag `contract-v1.7.1` / `c2b5e9` / `209d75b4…` and addendum `e318cbd` / `51604f56…` | `evidence/contract-guard.json` |
| Real CBE report vs RC2 schema | PASS; schema `2b3e1c5a…` | `evidence/cbe-report-rc2.validation.json` |
| CBE-09 F4 baseline | implemented; no stable CBE yet | `evidence/cbe-09-baseline.json` |
| CBE-10 F5/F6 + RC2 manifest fields | **PASS** with real CBP 1.2.2 manifest | `evidence/cbe-10-f5-f6.json` |
| CBE-11 self-bootstrap | bootstrap PASS; not a stable claim | `evidence/cbe-11-selfcheck.json` |
| Wheel install | PASS; schemas bundled | installed-wheel smoke test |

## Boundaries

- CBS froze `contract/v1.7.1` at tag `contract-v1.7.1`. The original
  `FREEZE_NOTICE.md` kept CBE-08 DRAFT, but the post-freeze
  `FREEZE_NOTICE_ADDENDUM.md` at `e318cbd` authorizes PASS when the four frozen
  F2 checks match. All four match, so CBE-08 is PASS.
- The guard pins the immutable tag and the addendum commit/hash. It fails with
  `CONTRACT_CHANGED` if the tag/commit/hash, addendum hash, authorization
  phrase, or `vm-proof.yml` cleanliness changes.
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
- Run: https://github.com/JunxiangPan/cbe/actions/runs/42629122113
- 174 tests = 74 unit + 100 E2E
- Coverage: 71.89% (gate 60%)
- Installed dependency: `cbp-action==1.2.2` (official)
- CBE wheel: `4e8abc21c1600d9ce231d14ccee0effda65c570c5548bd49b37c51981019c0c7`
- CBE issue #1: CLOSED (CBP 1.2.2 / RC2 consumer upgrade)

## Release discipline

No tag, no GitHub release, no PyPI upload was created. Do not create one until
a human audits this package.

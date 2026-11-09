# CBE 0.1.0 RC audit package

Status: **RC candidate — NOT released, no tag, no GitHub release, no PyPI upload.**
Human audit is required before any tag or publish.

## Inputs

| Input | Ref | Evidence |
|---|---|---|
| CBP 1.2.0 RC (final candidate) | `855fed7` | wheel `9469a8e980a536e9481e0b14239cd4857a5cd6173a61043d47645b82cf3b4d51`, sdist `98b8916c…` |
| CBP 1.2.0 RC (earlier candidates) | `5da8b87`, `bb8d4d6` | wheels `40b0f5…`, `06f8c3…` |
| CBS contract RC | `3de93ae` | declared and observed `c1653cfe…`; `vm-proof.yml` clean; **NOT FROZEN** |

CBP RC wheels were installed only in temporary venvs. The project
`cbp-action==1.1.0` pin is unchanged.

## Results

| Check | Status | Evidence |
|---|---|---|
| CBE-01..CBE-07a | PASS | CI + local E2E |
| CBE-07b on CBP 1.2.0 RC | PASS on `855fed7` (also earlier RC candidates) | `evidence/cbp-1.2.0-rc-*.json` |
| CBE-08 F2 | **DRAFT — not PASS** | `evidence/cbe-08-draft.json`, `docs/CBE-08_DRAFT.md` |
| CBE-09 F4 baseline | implemented; no stable CBE yet | `evidence/cbe-09-baseline.json` |
| CBE-10 F5/F6 + CBP 1.2.0 fields | PASS | `evidence/cbe-10-f5-f6.json` |
| CBE-11 self-bootstrap | bootstrap PASS; not a stable claim | `evidence/cbe-11-selfcheck.json` |
| Wheel install | PASS; schemas bundled | installed-wheel smoke test |

## Boundaries

- CBE-08 must stay DRAFT until CBS freezes `contract/v1.7.1`. The `3de93ae`
  contract hash and `vm-proof.yml` are now aligned, but the contract still says
  **RC, NOT FROZEN**; human freeze has not happened.
- CBP 1.2.0 RC uses `artifact_repository` as an `owner/repo` string; the CBS RC
  contract sketches an object. CBE follows CBP 1.2.0 RC and records the mismatch
  (B-33). No private union.
- `cbc-event` is CBP's JSONL event stream, not a manifest field. CBE rejects a
  private `cbc_event` manifest key.
- There is no previous stable CBE, so CBE-09/CBE-11 evidence is explicit
  `bootstrap=true`, never a fake stable baseline.

## CI

Status: **PENDING** — fill after the RC closeout commit is pushed.

## Release discipline

No tag, no GitHub release, no PyPI upload was created. Do not create one until
a human audits this package.

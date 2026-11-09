# CBE 0.1.0 RC audit package

Status: **RC candidate — NOT released, no tag, no GitHub release, no PyPI upload.**
Human audit is required before any tag or publish.

## Inputs

| Input | Ref | Evidence |
|---|---|---|
| CBP 1.2.0 official | `v1.2.0` / `5ebd0eb` | wheel `188639bb47e5a8940defbdb5ba3c4270ae89ad68503d283b611cb2a00497da2e`, sdist `08392b2a…` |
| CBP 1.2.0 RC (historical) | `855fed7`, `5da8b87`, `bb8d4d6` | wheels `9469a8e9…`, `40b0f5…`, `06f8c3…` |
| CBS contract RC | `3de93ae` | declared and observed `c1653cfe…`; `vm-proof.yml` clean; **NOT FROZEN** |

CBE's `e2e` extra now pins the released `cbp-action==1.2.0`. RC wheels are
historical evidence only; the project pin is no longer 1.1.0/RC.

## Results

| Check | Status | Evidence |
|---|---|---|
| CBE-01..CBE-07a | PASS | CI + local E2E |
| CBE-07b on CBP 1.2.0 official | PASS | `evidence/cbp-1.2.0-official.json` |
| CBE-08 F2 | **DRAFT — not PASS** | `evidence/cbe-08-draft.json`, `docs/CBE-08_DRAFT.md` |
| CBE-08 contract hash guard | **PINNED** to `3de93ae` / `c1653c…`; not a PASS | `evidence/contract-guard.json` |
| CBE-09 F4 baseline | implemented; no stable CBE yet | `evidence/cbe-09-baseline.json` |
| CBE-10 F5/F6 + CBP 1.2.0 fields | PASS | `evidence/cbe-10-f5-f6.json` |
| CBE-11 self-bootstrap | bootstrap PASS; not a stable claim | `evidence/cbe-11-selfcheck.json` |
| Wheel install | PASS; schemas bundled | installed-wheel smoke test |

## Boundaries

- CBE-08 must stay DRAFT until CBS freezes `contract/v1.7.1`. The `3de93ae`
  contract hash and `vm-proof.yml` are aligned, but the contract still says
  **RC, NOT FROZEN**; human freeze has not happened. The guard passing means
  “the pin is intact”, **not** “CBE-08 PASS”.
- The guard fails with `CONTRACT_CHANGED` if `contract/v1.7.1` moves, the
  contract bytes change, or `vm-proof.yml` gets conflict markers.
- CBP 1.2.0 uses `artifact_repository` as an `owner/repo` string; the CBS RC
  contract sketches an object. CBE follows CBP 1.2.0 and records the mismatch
  (B-33). No private union.
- `cbc-event` is CBP's JSONL event stream, not a manifest field. CBE rejects a
  private `cbc_event` manifest key.
- There is no previous stable CBE, so CBE-09/CBE-11 evidence is explicit
  `bootstrap=true`, never a fake stable baseline.

## CI

Status: **PENDING** — fill after the CBP 1.2.0 official commit is pushed.

## Release discipline

No tag, no GitHub release, no PyPI upload was created. Do not create one until
a human audits this package.

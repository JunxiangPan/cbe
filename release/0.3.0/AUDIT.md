# CBE 0.3.0 Staging Audit

Status: **SIGNED STAGING AUDIT PASS — RELEASE DECISION PENDING.**

## Build / signing

```text
version: 0.3.0
commit:  d1c7343eb55c1cfe2c1991d2de2ba9478d7850f0
branch:  0.3.0-dev
signing run: https://github.com/JunxiangPan/cbe/actions/runs/43101056675
mode: stage_only=true
tag_created: false
release_created: false
pypi_uploaded: false
```

## Verification

| Check | Result |
|---|---|
| Cosign wheel/sdist/report/attestation/manifest | 5/5 `Verified OK` |
| CBE keyless verifier | exit 0, PASS, 5 files |
| Tests | 272 passed |
| Coverage | 81.91% (gate 80%) |
| Mutation | 10/10, recall 1.0 |
| CBP v1.3.2 cross-review | PASS |
| Clean CBE-only install | PASS; `cbp` module absent |
| Default `--gate-job` | 0.2.0 output/semantics preserved |
| Report schema | unchanged |

## Source audit

The signed stream audit run was stage-only. No `v0.3.0` tag, GitHub Release,
or PyPI upload exists. The signed `evidence/release-manifest.json` is
authoritative; the root `RELEASE_MANIFEST.json` is an unsigned staging wrapper.

## External controls

- CBE `main` branch protection is not configured.
- Required checks are not enforced.
- Tag protection is not observed.
- These are recorded, not claimed as fixed.

## Decision

**No 0.3.0 release yet.** Owner review and a release decision are required.

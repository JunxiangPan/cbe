# CBE 0.3.0 Release Readiness

Status: **RELEASED — SIGNED via GitHub OIDC keyless cosign/sigstore.**

## 1. Signature

**SIGNED — Sigstore keyless.**

- GitHub OIDC cosign bundles for wheel, sdist, `cbe-report.json`,
  `attestation.json`, and `release-manifest.json`.
- Workflow: `.github/workflows/sign-release.yml`
- Stage-only run: <https://github.com/JunxiangPan/cbe/actions/runs/43101056675>
- Identity: `.../sign-release.yml@refs/heads/0.3.0-dev`
- CBE keyless verifier: 5 files PASS.
- Ed25519 sidecar: optional/legacy only; not production.

## 2. Release state

```text
v0.3.0 tag:      d1c7343
GitHub Release:  https://github.com/JunxiangPan/cbe/releases/tag/v0.3.0
PyPI 0.3.0:      https://pypi.org/project/cbe-review/0.3.0/
```

Signed assets verified before and after publication.

## 3. CBE checks

| Check | Result |
|---|---|
| Tests | **272 passed** |
| Coverage | **81.91%** (gate 80%) |
| Mutation | **10/10, recall 1.0** |
| CBP v1.3.2 cross-review | **PASS** |
| Default 0.2.0 behavior | preserved |
| `--gate-jobs` | cbp-gate / mutation-gate / ai-gate |
| `--cbp-report` | optional; no CBP import |
| Report schema | unchanged |

## 4. External controls

- CBE `main` branch protection: **not configured**.
- Required checks: **not enforced**.
- Tag protection: not configured/observed.
- These remain external and are recorded, not claimed as fixed.

## 5. Artifacts

```text
wheel: 2dcfbfa28661... (see evidence/release-manifest.json)
sdist: cdcfb5395c40... (see evidence/release-manifest.json)
```

Use the signed evidence manifest for exact SHA256 values.

## 6. Release gate

- [x] 0.3.0 multi-gate code/tests
- [x] Signed keyless staging
- [x] CBE keyless verifier PASS
- [x] re-audit signed staging
- [x] owner release approval
- [x] external controls recorded

**Released.**

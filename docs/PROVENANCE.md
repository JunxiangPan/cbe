# CBE 0.2.0 provenance

Status: **RELEASED — SIGNED via GitHub OIDC keyless Sigstore.**

- Tag: `v0.2.0` -> `8c1452ed99c4a1010eba2ecd632c837007e22df1`
- Release: <https://github.com/JunxiangPan/cbe/releases/tag/v0.2.0>
- PyPI: <https://pypi.org/project/cbe-review/0.2.0/>
- Signing workflow: `.github/workflows/sign-release.yml` (run `42982598114`)
- Production signature: Sigstore keyless bundles for wheel, sdist,
  `cbe-report.json`, `attestation.json`, `release-manifest.json`
- Cosign: 5/5 `verify-blob` Verified OK; SLSA v1 attestations for wheel/sdist
- CBE keyless verifier: 5 files PASS
- Ed25519 sidecar: optional/legacy only, not production signing.
- Old tags `v0.1.0` / `v0.1.1` unchanged; old distribution name `cbe` never
  uploaded.
- Branch/tag protection remains external; see `release/0.2.0/READINESS.md`.

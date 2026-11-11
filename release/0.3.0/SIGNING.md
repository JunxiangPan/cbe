# CBE 0.3.0 signing (staging)

Status: **SIGNED via GitHub OIDC keyless cosign/sigstore.**

- Workflow run: <https://github.com/JunxiangPan/cbe/actions/runs/43101056675>
- Identity: `https://github.com/JunxiangPan/cbe/.github/workflows/sign-release.yml@refs/heads/0.3.0-dev`
- Issuer: `https://token.actions.githubusercontent.com`
- Signed: wheel, sdist, `cbe-report.json`, `attestation.json`,
  `release-manifest.json`.
- Each has a mandatory `.bundle`; `.sig`/`.pem` are present.
- SLSA v1 attestation bundles: `attestation-wheel.json`, `attestation-sdist.json`.
- CBE keyless verifier: 5 files PASS.

Production signature = Sigstore keyless bundle. Ed25519 is optional/legacy only.

No tag/release/PyPI was created by this staging run (`stage_only=true`).

# CBE 0.3.0 signed staging

Status: **RELEASED — SIGNED via Sigstore keyless.**

- Sigstore keyless bundles verified.
- No `v0.3.0` tag, GitHub Release, or PyPI upload.
- Distribution remains `cbe-review`; import/CLI remain `cbe`.

## Signed build

```text
version: 0.3.0
commit:  d1c7343eb55c1cfe2c1991d2de2ba9478d7850f0
branch:  0.3.0-dev
workflow run: https://github.com/JunxiangPan/cbe/actions/runs/43101056675
```

Production signature: **Sigstore keyless cosign bundle** from GitHub OIDC.
Ed25519 is optional/legacy only, not production.

## Verification

```bash
cosign verify-blob \
  --bundle dist/cbe_review-0.3.0-py3-none-any.whl.bundle \
  --certificate-identity-regexp \
    'https://github.com/JunxiangPan/cbe/.github/workflows/sign-release.yml@refs/heads/0.3.0-dev' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  dist/cbe_review-0.3.0-py3-none-any.whl
```

The signed `evidence/release-manifest.json` is authoritative for hashes.
This root `RELEASE_MANIFEST.json` is an unsigned staging wrapper.

## Layout

```text
dist/       wheel, sdist, bundles, sig, pem
evidence/   cbe-report, attestation, signed release-manifest, SLSA attestations
```

## Boundaries

- no tag/release/PyPI;
- branch/tag protection remains external;
- report schema unchanged;
- old tags/assets untouched.

# CBE signing and attestation

Status: **RELEASED — SIGNED via GitHub OIDC keyless cosign/sigstore.**

Release: <https://github.com/JunxiangPan/cbe/releases/tag/v0.2.0>
Tag: `v0.2.0` -> `8c1452e`
PyPI: <https://pypi.org/project/cbe-review/0.2.0/>

CBE 0.2.0 production signing is **GitHub OIDC keyless cosign/sigstore**.

The Ed25519 sidecar remains an optional/legacy mechanism. It is not the
production signature and must never be described as one.

## Production signature (Sigstore keyless)

Signed files on the `v0.2.0` Release:

- `cbe_review-0.2.0-py3-none-any.whl`
- `cbe_review-0.2.0.tar.gz`
- `cbe-report.json`
- `attestation.json`
- `release-manifest.json`

Each file has:

- `<file>.bundle` — Sigstore bundle (certificate + signature + transparency
  proof), mandatory;
- `<file>.sig` / `<file>.pem` — detached signature/certificate, optional
  convenience copies.

The signing workflow is `.github/workflows/sign-release.yml`. It builds once,
generates the evidence files, signs with GitHub OIDC, runs `cosign verify-blob`
and the CBE keyless verifier **before** creating the tag/release. It does not
create a tag if signing or verification fails.

Verify:

```bash
cosign verify-blob \
  --bundle cbe_review-0.2.0-py3-none-any.whl.bundle \
  --certificate-identity-regexp \
    'https://github.com/JunxiangPan/cbe/.github/workflows/sign-release.yml@refs/heads/main' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  cbe_review-0.2.0-py3-none-any.whl
```

The certificate identity is the signing workflow at the branch/ref that
triggered the OIDC token; it is not a long-lived key.

## CBE verifier

```bash
python tools/cbe_verify_sidecar.py --keyless \
  --bundle-dir . \
  --artifact cbe_review-0.2.0-py3-none-any.whl \
  --artifact cbe_review-0.2.0.tar.gz \
  --report cbe-report.json \
  --manifest release-manifest.json \
  --attestation attestation.json \
  --certificate-identity-regexp \
    'https://github.com/JunxiangPan/cbe/.github/workflows/sign-release.yml@.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

If any bundle is missing, or `cosign` is unavailable, the verifier exits 4
with `BLOCKED`/`NOT_UPLOADED`; it never returns PASS for unsigned evidence.

## Legacy Ed25519 sidecar (optional)

The old sidecar is retained for offline/legacy verification only:

- `manifest.sig` — JSON envelope, Ed25519 over canonical fields;
- `attestation.json` — in-toto Statement v1 with manifest/report digests;
- schemas under `schemas/sidecar/`.

`tools/cbe_sign_sidecar.py` only signs when a real private key is supplied.
No production `manifest.sig` is generated or claimed. The legacy verifier is
still available without `--keyless`.

## Boundaries

- No fake signature, certificate, or bundle is produced.
- The frozen CBE report schema is unchanged.
- A Sigstore bundle is not an Ed25519 signature; do not describe one as the
  other.

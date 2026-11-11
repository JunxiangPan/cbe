# CBE 0.2.0 Release Readiness

Status: **SIGNED — Sigstore keyless (GitHub OIDC); CBP v1.3.2 PASS; branch/tag
protection remains external.**

Production signature is the Sigstore keyless cosign bundle, **not** Ed25519.
The Ed25519 sidecar is retained as optional/legacy only.

CBP v1.3.2 review: [artifacts/cbp-review/1.3.2.md](../../artifacts/cbp-review/1.3.2.md).
CBP tag `63cc8f0` contains the real `cbp-gate`; CBE cross-check exits 0 with
`--gate-job '^cbp-gate$' --exclude-workflow '.github/workflows/e2e-payload.yml' --strict`.
The post-tag docs HEAD `2708339` was not used as the release identity.

---

## 1. Signature model

Signed by `.github/workflows/sign-release.yml` with GitHub OIDC keyless cosign:

- `cbe_review-0.2.0-py3-none-any.whl`
- `cbe_review-0.2.0.tar.gz`
- `cbe-report.json`
- `attestation.json`
- `release-manifest.json`

Each file has a mandatory `<file>.bundle`; optional `<file>.sig` / `.pem`.
The workflow runs `cosign verify-blob` and the CBE keyless verifier **before**
creating the tag/release. If OIDC/cosign fails, it stops; no tag.

No fabricated signature or attestation is produced. A Sigstore bundle is not
an Ed25519 signature and is never described as one.

## 2. CBE verifier

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

Missing bundle or missing `cosign` returns exit 4 (`BLOCKED`/`NOT_UPLOADED`),
never PASS. Tampered bundle/signature returns exit 3.

The legacy Ed25519 verifier remains available without `--keyless`; it is not
the production signature.

## 3. Branch protection

**NOT CONFIGURED — external.**

```text
GET /repos/JunxiangPan/cbe/branches/main/protection
-> 404 Branch not protected

rulesets: []
tag protection: not observed
```

Consequences:

- `main` can be force-pushed/deleted by someone with permission.
- Required review/checks are not enforced.
- The self-protection manifest can be changed together with a protected file;
  CI detects drift only when it runs.

This is recorded in the release notes; it is not replaced by the signing
workflow.

## 4. Required checks

**NOT ENFORCED.**

Intended contexts:

```text
e2e (ubuntu-latest)
e2e (windows-latest)
```

They are green for this candidate but are not required checks while `main` is
unprotected. The `pypi` environment has required reviewer `JunxiangPan`.

## 5. Remote parent-call reachability

**PARTIAL / EXPLICIT BOUNDARY.**

Implemented: local and (opt-in) remote reusable-workflow recursive scanning;
unfetched/network/auth/404/parse failures are `UNVERIFIABLE_REMOTE_WORKFLOW`
and `--strict` exits 3.

Not implemented: parent-call reachability is not propagated into the child.
A skipped parent call can remain a false-negative boundary. CBE 0.2.0 does not
claim full remote reusable call-graph closure.

## 6. Release gate

- [x] CBE self-audit (252 tests, mutation 10/10, self-protection, contract)
- [x] CBP v1.3.2 tag-level review and `cbp-gate` cross-check
- [x] Cosign keyless workflow defined with verify-before-tag
- [ ] `sign-release.yml` OIDC run PASS
- [ ] release assets verify after publication
- [ ] PyPI `cbe-review==0.2.0` digest verified
- [ ] old tags/assets unchanged

Release actions are executed only after the signing workflow PASS.

## 7. Artifacts / evidence

```text
wheel  cb4c07ea316836b63f8c9c9538417fb430ab82021d8a6ca10d713add79ab01bc
sdist  d04b60e0b0cf057370d23c042b6c48f8ac150d75a957c73d288ef69de3e77bdf
```

- CBE self-audit: `artifacts/self-audit/0.2.0.md`
- CBP v1.3.2 review: `artifacts/cbp-review/1.3.2.md`
- SBOM: `artifacts/sbom/cbe-0.2.0.cdx.json`
- Self-protection: `security/SELF_PROTECTION.sha256`
- CI: <https://github.com/JunxiangPan/cbe/actions/runs/42863397794>

## 8. Signing commands

Production verify:

```bash
cosign verify-blob \
  --bundle <file>.bundle \
  --certificate-identity-regexp \
    'https://github.com/JunxiangPan/cbe/.github/workflows/sign-release.yml@.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  <file>
```

`cosign attest-blob` SLSA v1 attestations are produced for wheel and sdist.
The Ed25519 signer/verifier is optional/legacy.

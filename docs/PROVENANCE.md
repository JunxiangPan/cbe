# CBE 0.2.0 provenance

Status: **SIGNING WORKFLOW DEFINED — release tag not created yet.**

- Source: CBE `main`, version `0.2.0`.
- CI: Ubuntu + Windows, coverage gate 80%, mutation recall gate.
- Actions: checkout/setup-python/PyPI/cosign-installer pinned to full commit SHAs.
- SBOM: `artifacts/sbom/cbe-0.2.0.cdx.json` (CycloneDX 1.5).
- Self-protection: `security/SELF_PROTECTION.sha256`.
- Production signature: **GitHub OIDC keyless Sigstore bundles** for wheel,
  sdist, `cbe-report.json`, `attestation.json`, `release-manifest.json`.
- Optional/legacy Ed25519 sidecar: retained, not production signing.
- Signing workflow: `.github/workflows/sign-release.yml`.
- Tag/release: created only after the workflow’s `cosign verify-blob` and CBE
  keyless verifier pass. A failed signature run must not tag.

The release provenance is recorded at runtime by the signed
`release-manifest.json` and `cbe-report.json`; do not pre-fill a tag hash.

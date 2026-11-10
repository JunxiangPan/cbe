# CBE 0.2.0 provenance (development)

Status: **NOT RELEASED.**

- Source: CBE `main`, version `0.2.0`.
- CI: Ubuntu + Windows, coverage gate 80%, mutation recall gate.
- Actions: checkout/setup-python/PyPI publish pinned to full commit SHAs.
- SBOM: `artifacts/sbom/cbe-0.2.0.cdx.json` (CycloneDX 1.5).
- Self-protection: `security/SELF_PROTECTION.sha256`.
- Signature/attestation: schemas + offline verifier delivered; production
  sidecar **BLOCKED_NO_SIGNING_IDENTITY**. No signature is claimed.
- Release: requires human approval; no v0.2.0 tag, GitHub Release, or PyPI
  upload exists yet.

The release provenance should be finalized with the source commit and CI run
only after the release is approved.

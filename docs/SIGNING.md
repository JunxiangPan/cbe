# CBE sidecar signing and attestation

Status: **BLOCKED_NO_SIGNING_IDENTITY**.

CBE 0.2.0 ships the sidecar schema and an offline verifier, but no production
signature or production attestation. No signing key or OIDC identity was
available, so no signature was fabricated.

## Sidecar files

- `manifest.sig` — JSON envelope, Ed25519 signature over canonical fields:
  `schema_version`, `alg`, `keyid`, `subject`, `manifest_sha256`,
  `report_sha256`, `attestation_sha256`.
- `attestation.json` — in-toto Statement v1 with the manifest/report subject
  digests and a CBE release predicate.
- The frozen CBE report schema is **not** changed; sidecars are external.

Schemas:

- `schemas/sidecar/manifest-signature.v1.schema.json`
- `schemas/sidecar/attestation.v1.schema.json`

## Sign (only with a real identity)

```bash
python tools/cbe_sign_sidecar.py \
  --manifest rules.json --report cbe-report.json \
  --attestation attestation.json \
  --private-key /secure/ed25519.pem --keyid release-2026 \
  --version v0.2.0 --out manifest.sig
```

The signer is a tool, not proof of identity. Keep the private key outside the
repository.

## Verify offline

```bash
python tools/cbe_verify_sidecar.py \
  --manifest rules.json --report cbe-report.json \
  --signature manifest.sig --attestation attestation.json \
  --public-key release-2026.pub
```

The verifier reads only these files and the public key. It checks schema,
manifest/report/attestation digests, subject binding, and the Ed25519
signature. It does not fetch or execute anything.

## Current delivery

- Schema: delivered.
- Signer: delivered for use with a real key.
- Verifier: delivered; tested with ephemeral keys.
- Production signature: **not produced** (`BLOCKED_NO_SIGNING_IDENTITY`).
- Production attestation: **not produced**.

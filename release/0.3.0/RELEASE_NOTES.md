# CBE 0.3.0 Release Notes (signed staging)

Status: **SIGNED STAGING — NOT RELEASED.**

## Highlights

- Multi-gate job integrity: `--gate-jobs cbp-gate mutation-gate ai-gate`.
- Per-gate bypass detection: `if:false`, commented gates, unreachable `needs`,
  `continue-on-error`, empty local reusable delegation.
- Optional `--cbp-report` records report/manifest hashes without importing CBP.
- Default `--gate-job` / 0.2.0 behavior unchanged.
- CBE report schema unchanged.
- Ed25519 sidecar is optional/legacy; production signing is Sigstore keyless.

## Verification

```text
tests:       272 passed
coverage:    81.91% (gate 80%)
mutation:    10/10
CBP:         v1.3.2 PASS
signatures:  keyless bundles verified (5 files)
```

No tag/release/PyPI until owner review.

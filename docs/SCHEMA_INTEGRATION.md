# CBS schema integration status

Status: **PENDING — no schema change made by CBE.**

The frozen CBE report schema remains:

```text
src/cbe/schemas/v1.7/cbe-report.schema.json
sha256 2b3e1c5a77a7f520b80d01fefa328c9353fffc5d65e87782ca90d193839c0e74
```

CBE 0.2.0 adds **sidecars only**:

- `manifest.sig` (signature envelope)
- `attestation.json` (in-toto Statement)

They are external files and are not fields in the CBE report. The report schema
still has `additionalProperties: false`; sidecar fields cannot be smuggled in.

## Pending integration test

`tests/contract/` pins the schema hash and asserts signature/attestation are
not report properties. When CBS publishes an amendment that changes the report
schema, this test must fail and the schema/consumer tests must be updated in a
separate, approved change.

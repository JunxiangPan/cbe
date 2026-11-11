# CBS schema integration status

Status: **PENDING CBS AMENDMENT — CBE-local additive `cbf` package_id.**

The CBE 0.3.1 report schema adds `cbf` to the existing `package_id` enum; no
field was added or removed. The CBS-side amendment is still pending.

```text
src/cbe/schemas/v1.7/cbe-report.schema.json
sha256 7824c18c639c9af8fc013739bdc75dba0d6e22c76f0a96ee91a372a581428fe5
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

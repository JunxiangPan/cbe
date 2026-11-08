# Proposed CONTRACT.md amendments (v1.7)

Status: **PROPOSED — NOT IN FORCE**
Target: `public-release/docs/v1.7/CONTRACT.md` @ `4a437df`
Target sha256: `a561f19e0a8e4dba92af82400b5696da18e000ba5362571cb0b40243b9a3afca`

Applicable patch: `CONTRACT_AMENDMENTS_PROPOSED.patch`
Patched preview: `CONTRACT_v1.7.1_PROPOSED.md`

`public-release` is read-only from CBE. CBE has not edited the contract and will
not apply this patch to `public-release`. The patch is a proposal for the CBS
thread to apply when it publishes **v1.7.1**. It was generated against
`4a437df` and checked with `git apply --check` against that exact blob.

The live contract has moved past `4a437df` (it added §11 Build-once Profiles).
CBS must rebase this proposal onto the current contract tip before applying,
and must confirm the three amendments do not conflict with §11. Do not apply
the patch blindly to the live working tree and do not hand-edit `4a437df`.

## Why this is a new version, not an in-place edit

CONTRACT.md §10 says changes require a new contract version, a
`docs/v1.7/CHANGELOG.md` entry, updates to affected E2E matrices, and no
retroactive change to published evidence. The F2 blocking set is a substantive
semantic change: any consumer that implemented the old “three structural
checks” reading will change behaviour. The CHANGELOG must mark this as a
breaking change for consumers, not a clarification.

The CBS v1.7.1 release must also update the E2E matrices:

- CBE-08 F2 denominator assertions (blocking rules are excluded; blocking
  exemption is exit 3; no blocking SKIP).
- CBE report identity tests (`package_id` = subject, `producer_id` = producer).
- Any CBP tests that parse the report identity or hash fields.

Do not silently patch `4a437df`; it is published historical evidence.

Recommended version: **v1.7.1**, with a breaking-change note. The preview file
is named `CONTRACT_v1.7.1_PROPOSED.md` for review only.

## Amendment 1 — F2 blocking set

Insert after “A SKIP over 20% exits `4`.” and before F3:

```text
F2 blocking set =
  the three structural checks (manifest validation, no-bypass enforcement,
  provider output missing/invalid)
  + any manifest rule with gate: "blocking".

advisory rules enter the SKIP denominator; blocking rules do not, and may not
be SKIPPED. A blocking rule's package_types must equal the manifest's top-level
package_types, so a blocking rule can never become non-applicable/SKIPPED.
```

Rationale: CBE must be able to block on real findings, not only on framework
errors. The original F2 parenthetical reads as an exhaustive list of three
checks; without this amendment, a manifest rule marked `gate: "blocking"` would
be an implementation extension that contradicts F2's literal text.

CBE-side enforcement:

- `CBE-SECRET-001` in `tests/e2e/fixtures/manifests/valid_full.json`.
- S06 (blocking implies `severity: error`), S07 (blocking package scope equals
  top-level).
- CBE-08 denominator tests.

## Amendment 2 — §5 hash representation

Insert after the CBE report JSON example and before the CBP quality manifest:

```text
### 5.2 Hash representation

The "sha256:..." forms in the examples are algorithm annotations, not part of
the value. Schema fields (rules_manifest_hash, evidence_sha256,
artifact_hashes.*) are bare 64-character lowercase hexadecimal strings. An
input carrying a sha256: prefix is an input error (exit 2); a tool must not
silently strip the prefix.
```

Also change the example values:

- `"rules_manifest_hash": "sha256:..."` → `"rules_manifest_hash": "<64 lowercase hex>"`
- `"evidence_sha256": "sha256:..."` → `"evidence_sha256": "<64 lowercase hex>"`
- `"release_body_hash": "sha256:..."` → `"release_body_hash": "<64 lowercase hex>"`
- `"artifact_hashes": {}` stays an object whose values are bare 64 hex.

Rationale: the frozen `schemas/v1.7/cbe-report.schema.json` and
`schemas/v1.7/quality-manifest.schema.json` only accept `^[a-fA-F0-9]{64}$`.
CBE cannot satisfy both the current example text and the schema.

Schema checklist for CBS:

- `schemas/v1.7/cbe-report.schema.json`: hash patterns remain bare 64 hex.
- `schemas/v1.7/quality-manifest.schema.json`: same.
- Any parser must reject a prefixed value with exit 2. Do not normalize it.

## Amendment 3 — §5.1 report identity

Insert after the CBE report JSON example:

```text
### 5.1 Report identity

- package_id is the subject package being verified (cbs, cbe, cbp, cbm, cbc,
  cbg).
- producer_id is the component that produced the report (cbe, cbp).
- version and tag are the subject package's version, not the producer's
  version.
- A consumer checks package_id against its own package name; producer_id is
  for traceability only.
```

Add `"producer_id": "cbe"` to the CBE report JSON example (after
`"package_id"`), and `"producer_id": "cbp"` to the CBP quality manifest example.

Rationale: CBE gating CBS must emit a report that says “I verified CBS”, while
still identifying CBE as the producer. With the old single `package_id`, a
consumer cannot tell whether `package_id: "cbe"` means “CBE verified itself” or
“CBE produced this report about CBE”. The CBE 0.1.0 self-report and the CBS
report are otherwise indistinguishable.

Schema checklist for CBS:

- `schemas/v1.7/cbe-report.schema.json`:
  - add `producer_id` to `required`;
  - `producer_id`: `{"enum": ["cbe"]}` or a shared producer enum;
  - `package_id`: enum of package types, not a free string;
  - keep `additionalProperties: false`.
- `schemas/v1.7/quality-manifest.schema.json`:
  - add `producer_id` to `required`;
  - `producer_id`: `{"enum": ["cbp"]}`;
  - `package_id`: enum of package types.
- Update the schema tests that currently use `"package_id": "cbe"` for a CBE
  report; a CBE report about CBS must use `"package_id": "cbs"` and
  `"producer_id": "cbe"`.

CBE-local proposal: `schemas/v1.7/cbe-report.schema.json` in this repository
already contains `producer_id` and the package enum. It is not contract-
conformant until CBS applies this amendment.

## Application procedure

1. CBS creates a contract branch from the **current** `public-release` contract
   tip, not from `4a437df`. `4a437df` remains the frozen input CBE was built
   against.
2. Rebase `CONTRACT_AMENDMENTS_PROPOSED.patch` onto that tip with `git apply -p1`
   (or `git apply --3way`), resolving only context drift.
3. Confirm the three amendments do not conflict with §11 Build-once Profiles.
4. Add the `docs/v1.7/CHANGELOG.md` entry and mark the F2 blocking-set change as
   breaking for consumers.
5. Update `schemas/v1.7/cbe-report.schema.json`,
   `schemas/v1.7/quality-manifest.schema.json`, and their tests: `producer_id`,
   package enum, bare 64-hex hashes.
6. Update CBE-08, CBE report identity tests, and CBP-01..CBP-15 where they parse
   the changed fields.
7. Publish **v1.7.1**; do not rewrite `4a437df`.

Until step 7, CBE reports must be marked with the contract ref they were built
against. The current CBE report schema has no `contract_ref` field; adding one
would be a fourth identity field and is intentionally out of scope for this
patch. CBE must not claim v1.7.1 contract conformance before step 7.

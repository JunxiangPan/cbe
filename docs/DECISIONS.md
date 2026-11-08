# CBE v1.7 decisions (frozen for P0)

Date: 2026-11-08
Contract source: `public-release/docs/v1.7/CONTRACT.md` @ `4a437df`
Contract sha256: `a561f19e0a8e4dba92af82400b5696da18e000ba5362571cb0b40243b9a3afca`

`public-release` is read-only from CBE. The contract amendments in
`CONTRACT_AMENDMENTS_PROPOSED.md` are **proposed**, not in force. CBE must not
claim contract conformance for the amended semantics until CBS applies them.

## D1. Repository

- Path: `D:\qq苏瑾言大肥鱼\cbe`, a sibling of `public-release` (CBS),
  `cbp-action-release` (CBP), and `cbm`.
- CBE is a peer project, not a CBS submodule.
- First commit: manifest schema, report/release-train/provider schemas, CLI
  skeleton, E2E fixtures, docs. No rule implementation.
- Bootstrap: until CBE 0.1.0 has a stable predecessor, self-check uses
  `--baseline <commit>`. After 0.1.0 is released, F4's previous-stable
  selection becomes active.

## D2. `gate` semantics

- Manifest rules may set `gate: "blocking"`.
- Blocking set = the three structural checks (manifest validation, no-bypass,
  provider output missing/invalid) + every manifest rule with
  `gate: "blocking"`.
- Advisory rules enter the F2 denominator; blocking rules do not and may not
  be SKIPPED.
- A blocking rule's `package_types` must equal the manifest's top-level
  `package_types` (S07), so a blocking rule cannot become non-applicable and
  then SKIPPED.
- Coherence: blocking requires `severity: error`; advisory requires
  `warning` or `note` (S06).
- This decision needs the F2 contract amendment. Without it, CBE-08 would test
  a self-consistent implementation that is not F2-conformant.

## D3. Hash format

- `rules_manifest_hash`, `evidence_sha256`, and `artifact_hashes.*` are bare
  64-character lowercase hex strings.
- The `sha256:` forms in CONTRACT examples are algorithm annotations, not part
  of the value.
- An input carrying a `sha256:` prefix is an input error (exit 2). CBE must not
  silently strip it.
- This needs the §5 contract amendment and the CBE/CBP report schema updates.

## D4. F6 placement

- CBE report `gate_status` remains `PASS | FAIL | SKIPPED_INFRA |
  PRECONDITION_FAIL`. It never carries `NOT_UPLOADED`.
- CBM/CBC status is carried in `schemas/v1.7/release-train.schema.json`:
  `components.{cbm,cbc}.{declared_attached,status}`.
- `status` enum: `PASS | NOT_UPLOADED | SKIPPED_INFRA | PRECONDITION_FAIL |
  EVIDENCE_ABSENT`.
- `NOT_UPLOADED` is not PASS, not SKIP, and is not counted in any denominator.
- `NOT_UPLOADED` does not block the CBS main package by itself. If
  `declared_attached=true` and the status is `NOT_UPLOADED`, the Release body
  must contain `declared as attached but not uploaded`; missing it is a P2-04
  failure recorded in the release-train artifact, not a CBE gate failure.

## D5. Report identity

- `package_id` = subject package being verified (`cbs`, `cbe`, `cbp`, `cbm`,
  `cbc`, `cbg`).
- `producer_id` = component that produced the report (`cbe` or `cbp`).
- `version` and `tag` = subject package's version, not the producer's version.
- Consumers check `package_id` against their own package name; `producer_id`
  is for traceability.
- CBE gating CBS: `package_id: "cbs"`, `producer_id: "cbe"`.
- CBE gating itself: `package_id: "cbe"`, `producer_id: "cbe"`.
- This needs the §5.1 contract amendment and the report schema update.

## Detail changes accepted from review

### D6. `blocking_applicable_count`

`validate-manifest` output includes both:

- `blocking_rule_count`: blocking rules in the manifest.
- `blocking_applicable_count`: blocking rules applicable to the current
  package context.

S07 makes them equal for a valid manifest. Keeping both makes CBE-03 able to
assert that S07 actually ran.

### D7. Workflow scan scope

`enforce-no-bypass --workflows` scans only the target repository's
`.github/workflows/`. It does not implicitly scan CBE's own gate workflow.
When CBE scans itself, the caller must pass:

```text
--exclude-workflow .github/workflows/cbe-e2e.yml
```

CBE-04 includes a control case asserting that CBE's own workflow is not
flagged when explicitly excluded.

## Commit sequence

1. **Commit 1 (this commit)**: schemas + `src/cbe/` CLI skeleton +
   `tests/e2e/fixtures/` + docs. No rule implementation; command bodies return
   `NOT_IMPLEMENTED` (exit 3).
2. **Commit 2**: framework implementation (manifest validator, no-bypass,
   provider runner, symbol index, SARIF emitter) + unit tests.
3. **Commit 3**: E2E tests CBE-01..CBE-11 + CI, then the first rule pack.

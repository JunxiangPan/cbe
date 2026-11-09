# CBE v1.7 boundary ledger (B-00..B-34)

Status values:

- **RESOLVED** — decision recorded and CBE-side artifact exists.
- **PENDING-CBS** — CBE cannot fix; CBS must apply a contract/schema change.
- **PENDING-IMPL** — decided; implementation lands in commit 2/3.
- **DEFERRED** — documented, not needed for P0.

| ID | Source | Boundary | Impact | Status / action |
|---|---|---|---|---|
| B-00 | v1.7 | CBE repository and previous stable CBE did not exist | F4/CBE-11 not executable literally | **RESOLVED**: repo created at `D:\qq苏瑾言大肥鱼\cbe`; bootstrap uses `--baseline <commit>` until 0.1.0 ships |
| B-01 | §8 | “CBE-01..11 as defined in the v1.7 execution contract” — no execution contract at 4a437df | No authoritative acceptance criteria | **RESOLVED CBE-side**: matrix frozen in `docs/E2E_MATRIX_V1.md`; CBE-01..04 implemented with `run_e2e.py`; CBE-05..11 fixtures-only; **PENDING-CBS** to reference it from the execution contract |
| B-02 | P0-03 / F2 | `gate` field undefined; F2 names three blocking checks | Blocking set ambiguity | **RESOLVED** by D2; **PENDING-CBS** F2 amendment |
| B-03 | §5 / schema | CONTRACT shows `sha256:...`; frozen schema accepts 64 hex only | Can’t satisfy both | **RESOLVED** by D3 (bare hex); **PENDING-CBS** §5 amendment + schema test update |
| B-04 | F6 / §5 | `NOT_UPLOADED` not in CBE report enum and `additionalProperties:false` | F6 cannot live in CBE report | **RESOLVED** by D4; `schemas/v1.7/release-train.schema.json` added; CBE gate unchanged |
| B-05 | §5 / release_body_v17.py | body generator reads `infrastructure_failures`/`not_uploaded`, absent from strict schemas | validated reports cannot feed body | **PENDING-CBS**: add fields or consume sibling evidence; CBE writes `cbe-evidence.json` in commit 2 |
| B-06 | F4 | “passed its release gates” + ERRATUM labels have no data source | Baseline selection nondeterministic | **PARTIAL**: `schemas/v1.7/releases.schema.json` + fixture added; **PENDING-IMPL** selector |
| B-07 | §8 | “empty output” vs zero findings undefined | Clean scan false fail / empty file false pass | **RESOLVED** by D3/B8 text: empty artifact = 3; `results:[]` = PASS |
| B-08 | §5 vs §7 | `package_id` was ambiguous | CBE gating CBS cannot identify subject | **RESOLVED** by D5; CBE-local report schema has `package_id` + `producer_id`; **PENDING-CBS** §5.1 amendment |
| B-09 | §1/F4/ORCH-01 | `PRECONDITION_FAIL` may be exit 2 or 3 | Parser misclassification | **RESOLVED** by precedence table in `docs/CLI_V1.md`; **PENDING-CBS** cause table confirmation |
| B-10 | §1 | exit 1 undefined | Crash handling ambiguous | **RESOLVED** CBE-side: catch-all → 3 `INTERNAL_ERROR`; parser treats unknown exit as 2 |
| B-11 | F2 | exact 20% and float precision | Boundary misclassification | **RESOLVED**: integer `skip_count*5 > applicable_count`; exactly 20% passes |
| B-12 | F2 | blocking set scope | F2 literal mismatch | **RESOLVED** by D2; awaiting amendment |
| B-13 | §5 | `warn_count`/`blocking_skip`/`skip_count` semantics undefined | Cross-repo accounting drift | **RESOLVED CBE-side** (advisory findings / any blocking skip / applicable advisory skips); document in CLI/report |
| B-14 | §6 | provider-native ids vs CBE namespace | Namespace violation or lost findings | **PENDING-IMPL**: map via `provider_rule_ids`; published SARIF only `CBE-*` |
| B-15 | §5 | hash canonicalization undefined | Cross-repo hash mismatch | **RESOLVED CBE-side**: JCS + SHA-256, bare hex; **PENDING-CBS** note |
| B-16 | P1-04 | “new rules must not false-positive” not defined | CBE-11 not objective | **RESOLVED** test design: current-version golden fixture expects 0 findings |
| B-17 | §5 | `sarif_paths` path format undefined | Code Scanning path failures | **RESOLVED CBE-side**: relative POSIX, no `..`, one per provider + merged |
| B-18 | §5 / schema | `version` allows optional `v`, `tag` requires `v` | Inconsistent pair | **RESOLVED CBE-side**: CBE emits `v` for both |
| B-19 | P0-04 | exemption location/grammar undefined | Inline exemptions hard to audit | **RESOLVED** by D6/D7 docs: dedicated file only; inline ignored |
| B-20 | §6/§8 | E2E ids share `CBE-` prefix with rule ids | Id collision confusion | **RESOLVED**: test ids are `CBE-01..11`; SARIF rule ids must be `CBE-<AREA>-NNN` |
| B-21 | §5/F1 | report `exit_code` vs process exit undefined | Parser ambiguity | **RESOLVED CBE-side**: must be equal; mismatch on input = 2 |
| B-22 | §3 vs §5 | `SKIPPED`/`NOT_UPLOADED` are gate statuses in §3 but not in CBE report | Confused per-rule vs gate status | **RESOLVED**: CBE report uses §5 subset; component statuses separate |
| B-23 | §1 | `PRECONDITION_FAIL` exit 2/3 cause table incomplete | Same as B-09 | **RESOLVED** CBE-side precedence; CBS confirmation pending |
| B-24 | §3/§5 | gate status vs component status are different enums | Enum reuse | **RESOLVED**: release-train schema has its own enum incl. `EVIDENCE_ABSENT` |
| B-25 | schema `$id` | local `cyber-butler.local` id | Cross-repo resolution | **DEFERRED**: local validation only for P0 |
| B-26 | release_body_v17.py | `## NOT_UPLOADED` lacks “declared as attached but not uploaded” | P2-04 failure | **PENDING-CBS**: body generator fix; CBE cannot edit public-release |
| B-27 | process | `public-release` HEAD moved past 4a437df (it added §11 Build-once Profiles) | Patch/contract drift; wrong revision may be consumed | **PENDING-CBS**: v1.7.1 applies a rebased patch to the current tip; CBE remains pinned to 4a437df and must not apply it directly |
| B-28 | F2 / P0-04 | Workflow scanner only detected `continue-on-error`/`|| true`, not a `cbe-gate` job skipped by `if: false`/`needs`/comment | Gate could be bypassed by never running it | **RESOLVED** in P0-04.5: job-graph parsing, exit 3 `reason=WORKFLOW_SKIPS_CBE_GATE`, CBE-04 subcases |
| B-29 | CBE-08 / v1.7.1 | CBS `contract/v1.7.1` is RC at `3de93ae`; declared and observed contract hash both `c1653c…`, and `vm-proof.yml` is clean, but the contract is still NOT FROZEN | Claiming CBE-08 passed would be a false PASS | **PENDING-CBS freeze**: CBE-08 remains DRAFT (`tools/cbe08_draft.py`, `docs/CBE-08_DRAFT.md`). `tools/cbe_contract_guard.py` pins `3de93ae` / `c1653c…` and fails on drift; `PINNED` is not PASS. If the frozen F2 set differs, rewrite fixtures/assertions |
| B-30 | P0-04.5 / static workflow analysis | Dynamic conditions (`inputs.*`, `vars.*`, `github.*`, functions) and dynamic `needs` chains cannot be evaluated before the run | A dynamic gate skip could be missed; claiming complete coverage would be false | **RESOLVED CBE-side as warning**: `UNVERIFIABLE_CONDITION` / `UNVERIFIABLE_NEEDS_CHAIN` warnings, never FAIL, never silent. The evaluator is a restricted literal parser, not Python `eval` |
| B-31 | CBE-07 / CBP interop | Old assumption “CBP preserves CBE-*” was wrong; CBP 1.1.0 and released 1.2.0 enforce namespace isolation | A test asserting CBE-* preservation would be wrong | **RESOLVED** against CBP 1.1.0 and released CBP 1.2.0 (`5ebd0eb`, PyPI wheel `188639bb…`): CBE-07b emits `CBE-SECRET-001`; CBP emits `CBP-EXT-SECRET-001` in `rule`, with `origin_rule: CBE-SECRET-001`. CBE-07b passes with the official 1.2.0 wheel |
| B-32 | §5 report / Release body | CBE-local report/body now carry `warn_count`, but CBS must consume the CBE body fragment | End-to-end Release body visibility is still not guaranteed | **RESOLVED CBE-side**: `tools/cbe_gate.py` writes `cbe-report.json` + `cbe-body-section.md` Section B with warn_count and warning codes. **PENDING-CBS**: the CBS Release body generator must consume the fragment before claiming end-to-end visibility |
| B-33 | CBP 1.2.0 vs CBS v1.7.1 RC | CBP 1.2.0 treats `artifact_repository` as an `owner/repo` string; the CBS RC contract sketches an object | A CBE private union would hide the mismatch | **PENDING-UPSTREAM**: CBE follows CBP 1.2.0's string shape and rejects the object; recorded, not hidden. No private variant |
| B-34 | CBE wheel | Schemas lived outside the package; an installed wheel failed with `SCHEMA_UNAVAILABLE` | CBE 0.1.0 RC would not be installable | **RESOLVED**: schemas bundled under `src/cbe/schemas` with package-data; installed-wheel smoke test passes |

**B-32 consequence:** CBE-local report/body visibility is implemented. Until the
CBS Release body generator consumes `cbe-body-section.md`, an auditor reading
the final CBS Release body may still see no CBE warning line. Do not claim
end-to-end “dynamic conditions are machine-visible” until CBS integration lands.

## P0 blockers at start of implementation

The five blockers named in review were B-00, B-01, B-03, B-04, B-08. Current
state:

- B-00 resolved by creating the repo; baseline bootstrap is explicit.
- B-01 resolved CBE-side; CBS must reference the frozen matrix.
- B-03 decided; CBS amendment/schema update pending.
- B-04 resolved; release-train schema added.
- B-08 decided; CBS amendment/schema update pending.
- B-28 resolved in P0-04.5; workflow gate-skip is now exit 3.
- B-29 remains pending CBS freeze; CBE-08 is DRAFT against `3de93ae`, with
  matching contract hash and clean `vm-proof.yml`, but no human freeze yet.
- B-30 is a documented static-analysis limit, surfaced as warnings; it is not
  complete coverage and must not be described as such.
- B-31 resolved against CBP 1.1.0 and released 1.2.0: CBE-07b is a real
  assertion of `CBP-EXT-*` namespace isolation with `origin_rule` traceability.
- B-33 is an upstream shape mismatch: CBE follows CBP 1.2.0's string
  `artifact_repository`; do not union it with the CBS RC object.
- B-34 resolved: schemas are bundled in the package; installed-wheel smoke test
  passes.

B-03/B-08 remain **PENDING-CBS** for contract conformance, but they no longer
block CBE-side implementation because the decisions are frozen and the local
schemas reflect them. CBE must not claim v1.7 contract conformance until CBS
applies the amendments.

## Remaining risks

- CBE 0.1.0 has no previous stable CBE; F4 self-check is bootstrap-only until a
  second CBE release exists.
- `public-release` is being modified concurrently; do not apply the patch to a
  later CONTRACT revision without rebasing.
- The CBE report schema is a local proposal with `producer_id`; CBS’s frozen
  schema still lacks it. A CBE report produced today will fail the CBS schema
  until Amendment 3 lands.
- The release body generator still expects `infrastructure_failures` and
  `not_uploaded` fields that the strict report schemas forbid. CBE will write
  sibling evidence; CBS must decide how the body consumes it.
- Workflow analysis is static. Dynamic `if`/`needs` conditions only produce
  warnings; they do not prove the gate ran. Do not describe the workflow scan
  as complete bypass coverage.
- CBE-07b is real against CBP 1.1.0: CBE-* is mapped to CBP-EXT-* with
  `origin_rule` retained; do not assert “CBP preserves CBE-*”.
- CBE-08 is draft-only until CBS v1.7.1. If the final F2 set differs from the
  draft, rewrite the case rather than adjusting assertions.
- B-32: CBE-local `cbe-report.json` / Section B now carry `warn_count`; CBS
  Release body integration is still pending. Do not claim end-to-end body
  visibility before CBS consumes the fragment.

# CBE v1.7 boundary ledger (B-00..B-32)

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
| B-29 | CBE-08 / v1.7.1 | F2 blocking-set amendment is not yet published; CBE-08 can only assert the v1.7.1 draft | Claiming CBE-08 passed would be a false PASS | **PENDING-CBS v1.7.1**; CBE-08 remains draft and must not be reported as passed. If v1.7.1's final F2 set differs from the draft, CBE-08 must be rewritten, not merely re-asserted |
| B-30 | P0-04.5 / static workflow analysis | Dynamic conditions (`inputs.*`, `vars.*`, `github.*`, functions) and dynamic `needs` chains cannot be evaluated before the run | A dynamic gate skip could be missed; claiming complete coverage would be false | **RESOLVED CBE-side as warning**: `UNVERIFIABLE_CONDITION` / `UNVERIFIABLE_NEEDS_CHAIN` warnings, never FAIL, never silent. The evaluator is a restricted literal parser (booleans, numbers, `==`/`!=`, `&&`/`\|\|`/`!`), not Python `eval`; attribute access, indexing, and function calls are unknown |
| B-31 | CBE-07 / CBP interop | CBP `report_aggregator.py:32/43` passes external rule IDs through; CBE-* can enter CBP SARIF | Cross-namespace violation; CBE-07 cannot test CBP consumption yet | **PENDING-CBP**: fix the aggregator to preserve `CBE-*` without rewriting. CBE-07 is split: 07a (CBE emits `CBE-*`) must PASS; 07b (CBP consumes and preserves) is explicit SKIP `CBP_REPORT_AGGREGATOR_NOT_FIXED`, non-blocking applicable, counted in `skip_count` and visible |
| B-32 | §5 report / Release body | `enforce-no-bypass` now emits `warn_count`, but `cbe-report.json` and Release body assembly are not implemented | Unverifiable conditions could be JSON-only and absent from the audited report/body | **PENDING-IMPL P0-05**: report assembly sums command `warn_count`; Section B lists the count and warning codes. Until then CBE must not claim report/body visibility |

**B-32 consequence:** until P0-05 report assembly lands,
`UNVERIFIABLE_CONDITION` / `UNVERIFIABLE_NEEDS_CHAIN` are visible only in
per-command JSON, not in `cbe-report.json` or Release body Section B. Auditors
reading the report/body cannot see workflow conditional-skip risk. Do not claim
“dynamic conditions are machine-visible” until B-32 is closed.

## P0 blockers at start of implementation

The five blockers named in review were B-00, B-01, B-03, B-04, B-08. Current
state:

- B-00 resolved by creating the repo; baseline bootstrap is explicit.
- B-01 resolved CBE-side; CBS must reference the frozen matrix.
- B-03 decided; CBS amendment/schema update pending.
- B-04 resolved; release-train schema added.
- B-08 decided; CBS amendment/schema update pending.
- B-28 resolved in P0-04.5; workflow gate-skip is now exit 3.
- B-29 remains pending CBS v1.7.1; CBE-08 is draft-only until then.
- B-30 is a documented static-analysis limit, surfaced as warnings; it is not
  complete coverage and must not be described as such.
- B-31 is pending CBP's `report_aggregator.py`; CBE-07 cannot test CBP
  consumption until that is fixed.

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
- CBE-07 can test only CBE's `CBE-*` output until CBP fixes
  `report_aggregator.py`; the consumed-view assertion is blocked.
- CBE-08 is draft-only until CBS v1.7.1. If the final F2 set differs from the
  draft, rewrite the case rather than adjusting assertions.
- B-32: `warn_count` is in command JSON but not yet in `cbe-report.json` or the
  Release body. P0-05 must wire it before anyone claims audit visibility.

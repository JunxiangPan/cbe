# CBE E2E matrix (CBE-01..CBE-11)

Status: CBE-01..CBE-07a are implemented. CBE-07b is an explicit counted SKIP
until CBP fixes `report_aggregator.py`. CBE-08..CBE-11 remain pending CBS
v1.7.1/upstream work. The matrix is the authoritative definition until CBS
references it from the v1.7 execution contract.

## CBE-01 — CLI contract

- File: `tests/e2e/test_cbe_01_cli_contract.py`
- Fixtures: `fixtures/cli/`
- Check: all five subcommands exist; each `--help` exits 0; unknown command,
  missing required option, and unknown flag exit 2 with a JSON error; no
  traceback; `--version` exits 0. A static guard asserts no command module
  still returns `NOT_IMPLEMENTED`.
- Expected: 0 for help/version; 2 for input errors. All five commands are
  implemented; the old “stub exits 3” negative sample is retired.

## CBE-02 — manifest valid

- File: `tests/e2e/test_cbe_02_manifest_valid.py`
- Fixtures: `manifests/valid_minimal.json`, `valid_full.json`,
  `valid_full_crlf.json`
- Check: schema passes; rule/provider counts; blocking/advisory counts;
  `blocking_rule_count == blocking_applicable_count`; LF and CRLF variants hash
  identically.
- Expected: 0 / `PASS`.

## CBE-03 — manifest invalid

- File: `tests/e2e/test_cbe_03_manifest_invalid.py`
- Fixtures: `manifests/invalid_*.json`, `duplicate_rule_id.json`,
  `blocking_warning.json`, `blocking_partial_scope.json`,
  `blocking_version_not_applicable.json`, `additional_property.json`
- Check: each missing/invalid required field (`rule_id`, `title`, `severity`,
  `gate`, `provider`, `version_constraint`, `schema_version`) exits 2 with a
  JSON path; CBP namespace, lowercase id, bad pack id, duplicate id,
  blocking+warning, blocking partial scope, unknown field; `zero_rules.json`
  exits 3 `NO_RULES`.
- Expected: 2 / `FAIL`; zero rules = 3.

## CBE-04 — no bypass

- File: `tests/e2e/test_cbe_04_no_bypass.py`
- Fixtures: `bypass/config/`, `bypass/comments/`, `bypass/env/`,
  `bypass/workflow-repo/`, `bypass/workflow-if-false-repo/`,
  `bypass/workflow-needs-repo/`, `bypass/workflow-commented-repo/`,
  `bypass/reachable-repo/`, `bypass/clean-repo/`, `exemptions/`,
  `manifests/five_advisory.json`
- Check: config, comment, env, and target-workflow disable attempts exit 3
  with `bypass_attempts[]`; clean control exits 0; CLI has no disable flags
  (unknown flag = 2); CBE's own `cbe-e2e.yml` is not scanned implicitly; a
  self-scan without `--exclude-workflow .github/workflows/cbe-e2e.yml` exits 2
  `SELF_WORKFLOW_EXCLUSION_REQUIRED`; blocking exemption exits 3; unknown
  exemption rule exits 2; 1/5 advisory skip passes, 2/5 exits 4.
- Gate-skip subcases: a `cbe-gate` job with literal `if: false`,
  `if: ${{ false }}` in its `needs` chain, an evaluable-false `!true`/`1 == 2`,
  or a commented-out `cbe-gate:` job exits 3 with
  `reason=WORKFLOW_SKIPS_CBE_GATE`; a reachable or statically true `cbe-gate`
  passes. Dynamic `if`/`needs` conditions, `env.FOO()`, and
  `inputs.foo == inputs.bar` exit 0 but emit `UNVERIFIABLE_CONDITION` /
  `UNVERIFIABLE_NEEDS_CHAIN` warnings; they are not silently treated as safe.
  `warn_count` equals `len(warnings)`.
- Expected: 3 / `FAIL`; clean/reachable = 0; unknown flag = 2; 1/5 = 0; 2/5 = 4.

## CBE-05 — exemptions

- File: `tests/e2e/test_cbe_05_exemptions.py`
- Fixtures: `exemptions/*.txt`, `exemptions/inline_comment.py`,
  `manifests/five_advisory.json`, `manifests/valid_blocking_zero.json`
- Check: exact `SKIPPED: <rule_id> reason=<...>`; advisory applicable exemption
  counts in denominator; blocking exemption exits 3 `blocking_skip=true`;
  unknown/duplicate/missing reason/bad format exit 2; non-applicable exemption
  is SKIPPED but not counted; inline source comment is not honored.
- Expected: 0 for valid advisory; 3 for blocking; 2 for malformed; 4 if the
  ratio crosses 20%.

## CBE-06 — provider output

- File: `tests/e2e/test_cbe_06_provider_output.py`
- Fixtures: `providers/sarif_ok.py`, `sarif_findings.py`, `empty.py`,
  `missing.py`, `invalid_sarif.py`, `timeout.py`, `crash.py`, `native_ids.py`;
  `manifests/valid_zero_findings.json`, `valid_native_ids.json`
- Check: every enabled provider has declared artifacts; valid zero-result SARIF
  is PASS; empty/missing/invalid artifact exits 3; provider exit 1 with valid
  artifact is a run; exit >= 2 fails; timeout is `SKIPPED_INFRA`; native id
  mapping works, unmapped id fails.
- Expected: 0 / `PASS`; 3 / `FAIL`; timeout 3 / `SKIPPED_INFRA`.

## CBE-07 — SARIF (split 07a / 07b)

- File: `tests/e2e/test_cbe_07_sarif.py`
- Fixtures: `sarif/valid.sarif`, `cbp_namespace.sarif`,
  `bad_rule_index.sarif`, `absolute_path.sarif`, `missing_rule.sarif`,
  `no_runs.sarif`, `cbp-consumer-skip.json`
- **CBE-07a — CBE output:** must PASS. SARIF 2.1.0 schema; only `CBE-*`;
  ruleIndex/level/message/location; relative POSIX paths; no runs is invalid;
  merged output is Code Scanning ingestible. Expected: 0 for valid; 3 for
  invalid/cross-namespace/absolute path.
- **CBE-07b — CBP consumption:** explicit `SKIP` while
  `report_aggregator.py:32/43` is unfixed. `skip_reason=CBP_REPORT_AGGREGATOR_NOT_FIXED`,
  `blocking=false`, `applicable=true`, `counted_in_skip_denominator=true`;
  it appears in `skip_count` and in the Release body. SKIP is not PASS and is
  not hidden. Once CBP fixes the aggregator, 07b becomes a real assertion:
  CBP consumes CBE SARIF and preserves `CBE-*`, never rewrites to `CBP-*`.
- Interop contract: CBE guarantees only `CBE-*` output; CBP's custom gate
  consumes the rules and does not re-emit SARIF. The consumed-view check belongs
  to CBP.
- **Report assembly (B-32):** `test_cbe_07a_gate_report.py` runs
  `tools/cbe_gate.py`, asserts `cbe-report.json` carries `warn_count`, and
  asserts `cbe-body-section.md` Section B lists `UNVERIFIABLE_CONDITION`.
  CBE-local visibility is implemented; CBS Release-body integration is pending.

## CBE-08 — F2 denominator

- File: `tests/e2e/test_cbe_08_skip_denominator.py`
- Fixtures: manifest combinations built in the test from
  `manifests/valid_full.json`; `exemptions/valid.txt`
- Check: denominator = non-blocking applicable checks only; non-applicable
  rules are SKIPPED but not counted; blocking rules are not counted and may not
  SKIP; a blocking rule excluded by version exits 3
  `BLOCKING_RULE_NOT_APPLICABLE`; 1/5 passes, 2/5 exits 4, 1/4 exits 4; zero
  applicable exits 3; exit 3 wins over 4.
- Expected: 0 / 4 / 3 per case.
- **Contract gate: blocked on CBS v1.7.1.** Until v1.7.1 is published with
  the F2 blocking-set amendment, these are draft assertions only. CBE must not
  report CBE-08 as passed, and must not claim F2 conformance. If v1.7.1's final
  F2 set differs from this draft, CBE-08 must be **rewritten** — fixtures and
  assertions — not merely re-asserted.

## CBE-09 — F4 baseline

- File: `tests/e2e/test_cbe_09_baseline.py`
- Fixtures: `releases/releases.json`, `releases/erratum_body.md`
- Check: highest eligible non-prerelease, no ERRATUM, both gates PASS, not
  current; v0.0.9 is selected for current v0.1.0; v0.0.7 body `ERRATUM:` and
  v0.0.8 label `erratum` are excluded; v0.0.6 CBP FAIL is excluded; v0.0.4
  missing CBP evidence is excluded; v0.1.0-rc.1 is excluded; no eligible and
  no `--baseline` exits 3 `PRECONDITION_FAIL`; explicit `--baseline` works;
  current version as baseline exits 2.
- Expected: 0 / 3 `PRECONDITION_FAIL` / 2.

## CBE-10 — F5/F6

- File: `tests/e2e/test_cbe_10_infra_not_uploaded.py`
- Fixtures: `providers/timeout.py`, `release-train/not-uploaded.json`,
  `release-train/declared-attached.json`,
  `release-train/evidence-absent.json`
- Check F5: infra exits 3 `SKIPPED_INFRA`, not counted in 20%, publish blocked,
  dedicated section, never PASS.
- Check F6: `NOT_UPLOADED` is not PASS/SKIP and not counted; does not block CBS
  by itself; `declared_attached=true` + `NOT_UPLOADED` without the exact phrase
  `declared as attached but not uploaded` is a P2-04 failure in the release-
  train artifact, not a CBE gate failure.
- Expected: 3 `SKIPPED_INFRA`; release-train status separate.

## CBE-11 — self-bootstrap

- File: `tests/e2e/test_cbe_11_self_bootstrap.py`
- Fixtures: `selfcheck/baseline-0.0.9/`, `current-manifest.json`,
  `current-output/expected-findings.json`, `baseline-2.json`,
  `baseline-3.json`, `baseline-4.json`
- Check: previous stable CBE validates current manifest/output and must exit 0;
  baseline 2/3/4 is an E2E failure; current new rules do not fire on the current
  version; no baseline and no `--baseline` exits 3 `PRECONDITION_FAIL`;
  isolated environment and hash-pinned baseline.
- Expected: 0 for compatible; 3 for baseline 2/3/4; 3 for no baseline.

## Fixture inventory

```text
tests/e2e/fixtures/
  manifests/        valid_*.json, invalid_*.json, zero_rules.json,
                    blocking_version_not_applicable.json,
                    valid_zero_findings.json, valid_native_ids.json,
                    valid_blocking_zero.json, five_advisory.json
  providers/        sarif_ok.py, sarif_findings.py, empty.py, missing.py,
                    invalid_sarif.py, timeout.py, crash.py, native_ids.py
  source-tree/      pkg/mod.py, scripts/tool.ps1, README.md, data.json, bad.py
  bypass/           config/, comments/, env/, workflow-repo/,
                    workflow-if-false-repo/, workflow-needs-repo/,
                    workflow-commented-repo/, reachable-repo/,
                    workflow-dynamic-if-repo/, workflow-dynamic-needs-repo/,
                    workflow-dynamic-comparison-repo/,
                    workflow-env-call-repo/,
                    workflow-negated-true-repo/, workflow-comparison-false-repo/,
                    workflow-static-true-repo/, clean-repo/
  exemptions/       valid.txt, missing_reason.txt, blocking.txt,
                    unknown_rule.txt, duplicate.txt, bad_format.txt,
                    inline_comment.py, not_applicable.txt
  releases/         releases.json, erratum_body.md
  sarif/            valid.sarif, cbp_namespace.sarif, bad_rule_index.sarif,
                    absolute_path.sarif, missing_rule.sarif, no_runs.sarif,
                    cbp-consumer-skip.json
  release-train/    not-uploaded.json, declared-attached.json,
                    evidence-absent.json
  selfcheck/        baseline-0.0.9/, current-manifest.json, current-output/,
                    baseline-2.json, baseline-3.json, baseline-4.json
  cli/              .keep
```

## Runner and CI

- `tests/e2e/run_e2e.py` runs the implemented CBE-01..07a tests and exits
  non-zero on any failure; JSON summary to stdout.
- `tools/cbe_gate.py` assembles `cbe-report.json` and `cbe-body-section.md` from
  the five command outputs; CBE-07a covers the warn_count report/body path.
- `.github/workflows/cbe-e2e.yml` runs it without `continue-on-error`, `|| true`,
  or `if: always()`.
- Fixtures are committed; no network. The baseline wheel is hash-pinned.
- `enforce-no-bypass --workflows` scans the target repo; when scanning CBE
  itself, pass `--exclude-workflow .github/workflows/cbe-e2e.yml`.

# CBE E2E matrix (CBE-01..CBE-11)

Status: CBE-01..CBE-11 are implemented; CBE-08 is PASS under the frozen
`contract-v1.7.1` / `c2b5e9` addendum `e318cbd`. CBE-07b runs against the
released CBP 1.2.2 (and historically 1.1.0/1.2.0/1.2.2 RC). The matrix is the
authoritative definition until CBS references it from the v1.7 execution
contract.

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
  `bypass/reachable-repo/`, `bypass/clean-repo/`,
  `bypass/renamed-gates-repo/`, `bypass/local-call-repo/`,
  `bypass/remote-call-repo/`, `exemptions/`, `manifests/five_advisory.json`
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
  `--strict` turns those warnings into exit 3.
- Renamed gate controls: `security-gate`, `enforce`, and `policy-check` are
  detected when passed via `--gate-job '^<name>$'`; without the option the
  default `^cbe[-_]gate$` reports `GATE_JOB_NOT_FOUND` (warning by default,
  exit 3 under `--strict`).
- Local/remote calls: job-level `uses: ./.github/workflows/*.yml` is followed
  recursively and a skipped delegated gate exits 3; a remote reusable workflow
  emits `UNVERIFIABLE_REMOTE_WORKFLOW`, never a silent PASS.
- `warn_count` equals `len(warnings)`.
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

- Files: `tests/e2e/test_cbe_07_sarif.py` (07a),
  `tests/e2e/test_cbe_07b_cbp_consumer.py` (07b)
- Fixtures: `sarif/valid.sarif`, `cbp_namespace.sarif`,
  `bad_rule_index.sarif`, `absolute_path.sarif`, `missing_rule.sarif`,
  `no_runs.sarif`, `cbp-consumer-expected.json`
- **CBE-07a — CBE output:** must PASS. SARIF 2.1.0 schema; only `CBE-*`;
  ruleIndex/level/message/location; relative POSIX paths; no runs is invalid;
  merged output is Code Scanning ingestible. Expected: 0 for valid; 3 for
  invalid/cross-namespace/absolute path.
- **CBE-07b — CBP consumption:** real assertion against the released CBP 1.2.0
  (and historically 1.1.0/1.2.0 RC). CBE emits `CBE-SECRET-001`; CBP
  `report_aggregator` consumes it and emits `CBP-EXT-SECRET-001` in `rule`,
  with `origin_rule: CBE-SECRET-001` retained for traceability. CBP's `rule`
  field must start with `CBP-`, never `CBE-`. This is namespace isolation, not
  “preserve CBE-*”.
- Interop contract: CBE guarantees only `CBE-*` output. CBP maps foreign IDs
  into `CBP-EXT-*` and keeps `origin_rule`; CBP output carries only `CBP-*`.
  The CBP-side test is `test_cbe_07b_cbp_consumer.py` with
  `cbp-action==1.2.0` installed via the `e2e` extra.
- **Report assembly (B-32):** `test_cbe_07a_gate_report.py` runs
  `tools/cbe_gate.py`, asserts `cbe-report.json` carries `warn_count`, and
  asserts `cbe-body-section.md` Section B lists `UNVERIFIABLE_CONDITION`.
  CBE-local visibility is implemented; CBS Release-body integration is pending.

## CBE-08 — F2 denominator (PASS)

- File: `tools/cbe08_draft.py` (F2 runner; it now emits PASS when all four
  frozen checks match)
- Guard: `tests/e2e/test_cbe_08_contract_guard.py`,
  `tools/cbe_contract_guard.py`,
  `tests/e2e/fixtures/contract/v1.7.1-pin.json`
- Guard check: pinned immutable tag `contract-v1.7.1`, commit `c2b5e9`,
  contract SHA256 `209d75b4…`, `vm-proof.yml` clean, and
  `FREEZE_NOTICE_ADDENDUM.md` at `e318cbd` / `51604f56…` authorizing PASS.
  Drift exits 3 `CONTRACT_CHANGED`; a successful guard says `PINNED`.
- Fixtures: manifest combinations from `manifests/five_advisory.json`,
  `valid_blocking_zero.json`, `zero_rules.json`; `exemptions/valid.txt`,
  `exemptions/blocking.txt`
- Check: denominator = non-blocking applicable checks only; blocking rules are
  not counted and may not SKIP; blocking exemption exits 3; zero rules exits 3;
  1/5 advisory skip passes; 2/5 would exit 4.
- **Status: PASS.** Frozen expectations and observed exits all match:
  `five_advisory_valid=0`, `non_blocking_1_of_5_skip=0`,
  `blocking_skip_exits_3=3`, `zero_rules_exits_3=3`.
- Evidence: `artifacts/rc-0.1.0/evidence/cbe-08-frozen.json`.
- **CBE report schema:** `test_cbe_report_rc2_schema.py` generates a real CBE
  report and validates it against the RC2 CBE report schema; the schema also
  accepts `gate_status=NOT_UPLOADED`.

## CBE-09 — F4 baseline

- File: `tests/e2e/test_cbe_09_baseline.py`
- Tool: `tools/cbe_baseline.py`
- Fixtures: `releases/releases.json`, `releases/releases_no_baseline.json`
- Check: highest eligible non-prerelease, no ERRATUM, CBE/CBP gates PASS, not
  current; v0.0.9 is selected for current v0.1.0; ERRATUM/prerelease/failed
  gates are excluded; no eligible and no `--baseline` exits 3
  `PRECONDITION_FAIL`; explicit tag is `explicit_tag`; explicit 40-hex commit is
  `explicit_commit` bootstrap; current version as baseline exits 2.
- Expected: 0 / 3 `PRECONDITION_FAIL` / 2. There is no stable CBE release yet,
  so RC evidence uses an explicit bootstrap, never a fake “stable” label.

## CBE-10 — F5/F6 + contract RC2 manifest

- File: `tests/e2e/test_cbe_10_f5_f6.py`
- Tool: `tools/cbe_train.py`
- Fixtures: `release-train/not-uploaded.json`, `declared-attached.json`,
  `evidence-absent.json`, `infra.json`; CBP quality manifest fixtures
  `cbp-quality-manifest-v12.json`, `cbp-quality-manifest-full.json`,
  `cbp-quality-manifest-object-repo.json`,
  `cbp-quality-manifest-string-repo.json`,
  `cbp-quality-manifest-schema-version-number.json`,
  `cbp-quality-manifest-cbc-event-field.json`
- Check F5: infra exits 3 `SKIPPED_INFRA`, not counted in 20%, dedicated body
  section, never PASS.
- Check F6: `NOT_UPLOADED` is not PASS/SKIP and not counted; does not block CBS
  by itself; `declared_attached=true` emits the exact phrase
  `declared as attached but not uploaded`; `EVIDENCE_ABSENT` is visible.
- Contract RC2 fields: `schema_version` must be the string `"1"`;
  `body_hash_scope` must be exactly `base`; `artifact_repository` must be the
  object `{repository, run_id, artifact_name}`. Bare strings and incomplete
  objects exit 2. The released CBP 1.2.2 `quality-manifest.json` is validated as
  a real manifest; CBE does not claim CBP's own gate PASS. `cbc_event` is an
  event stream, not a manifest field.
- Expected: 0 for NOT_UPLOADED/EVIDENCE_ABSENT; 3 `SKIPPED_INFRA`; 2 for
  invalid CBP manifest fields.

## CBE-11 — self-bootstrap

- File: `tests/e2e/test_cbe_11_self_bootstrap.py`
- Tool: `tools/cbe_selfcheck.py`
- Fixtures: `manifests/valid_minimal.json`, `manifests/invalid_missing_rule_id.json`,
  `bypass/clean-repo/`
- Check: baseline CBE `validate-manifest` and `run-provider` must both exit 0;
  missing baseline interpreter exits 3 `PRECONDITION_FAIL`; baseline exit 2/3/4
  makes self-check exit 3 FAIL; `--bootstrap` is recorded explicitly.
- Expected: 0 for compatible; 3 for missing/failing baseline. There is no
  previous stable CBE; RC evidence uses a wheel/source bootstrap of `70faad8`
  and records `bootstrap=true`, not a stable release claim.

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
  releases/         releases.json, releases_no_baseline.json, erratum_body.md
  sarif/            valid.sarif, cbp_namespace.sarif, bad_rule_index.sarif,
                    absolute_path.sarif, missing_rule.sarif, no_runs.sarif,
                    cbp-consumer-expected.json
  release-train/    not-uploaded.json, declared-attached.json,
                    evidence-absent.json, infra.json,
                    cbp-quality-manifest-v12.json,
                    cbp-quality-manifest-full.json,
                    cbp-quality-manifest-object-repo.json,
                    cbp-quality-manifest-string-repo.json,
                    cbp-quality-manifest-schema-version-number.json,
                    cbp-quality-manifest-cbc-event-field.json
  contract/         v1.7.1-pin.json
  cli/              .keep
```


## CBE 0.2.0 additions

- `tests/mutation/` runs 10 known bypass mutants and requires recall >= 0.95;
  every mutant must be non-PASS. Artifact:
  `artifacts/mutation/cbe-0.2.0.json`.
- Remote reusable workflows: default `UNVERIFIABLE_REMOTE_WORKFLOW`; optional
  `--fetch-remote` recursively scans fetched GitHub workflows. Network/auth/
  404/empty-shell/if:false/ghost-needs tests are in
  `tests/unit/test_enforce_no_bypass.py`; `--strict` exits 3 for unverifiable
  cases.
- Sidecar sign/verify tests use ephemeral Ed25519 keys; production signature is
  `BLOCKED_NO_SIGNING_IDENTITY`.
- Self-protection tamper tests cover workflow, gate script, and contract guard;
  CI runs `tools/cbe_self_protect.py --check`.
- Contract tests pin report schema, exit codes, object `artifact_repository`,
  body scope/hash shape, and the 20% threshold.
- Coverage gate is 80%; E2E subprocesses are excluded from coverage.

## Runner and CI

- `tests/e2e/run_e2e.py` runs CBE-01..07b, the CBE-08 contract guard, and
  CBE-09..11. The CBE-08 F2 draft tool (`tools/cbe08_draft.py`) is deliberately
  not counted as a passing E2E. Non-zero exit on any failure; JSON summary to
  stdout.
- Tools: `tools/cbe_gate.py` (report/body), `tools/cbe_baseline.py` (F4),
  `tools/cbe_train.py` (F5/F6 + CBP manifest), `tools/cbe_selfcheck.py`
  (CBE-11), `tools/cbe08_draft.py` (DRAFT only),
  `tools/cbe_contract_guard.py` (contract pin drift).
- `.github/workflows/cbe-e2e.yml` runs it without `continue-on-error`, `|| true`,
  or `if: always()`.
- Fixtures are committed; no network. The CBE baseline wheel/source used in the
  RC audit is recorded with its SHA-256 in the audit package.
- `enforce-no-bypass --workflows` scans the target repo; when scanning CBE
  itself, pass `--exclude-workflow .github/workflows/cbe-e2e.yml`.

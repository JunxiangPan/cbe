# CBE E2E matrix (CBE-01..CBE-11)

Status: fixtures frozen in commit 1; test files and runner land in commit 3.
The matrix is the authoritative definition until CBS references it from the
v1.7 execution contract.

## CBE-01 — CLI contract

- File: `tests/e2e/test_cbe_01_cli_contract.py`
- Fixtures: `fixtures/cli/`
- Check: all five subcommands exist; each `--help` exits 0; unknown command,
  missing required option, and unknown flag exit 2 with a JSON error; no
  traceback; `--version` exits 0.
- Expected: 0 for help/version; 2 for input errors.

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
  `additional_property.json`
- Check: each missing/invalid required field (`rule_id`, `title`, `severity`,
  `gate`, `provider`, `version_constraint`, `schema_version`) exits 2 with a
  JSON path; CBP namespace, lowercase id, bad pack id, duplicate id,
  blocking+warning, blocking partial scope, unknown field; `zero_rules.json`
  exits 3 `NO_RULES`.
- Expected: 2 / `FAIL`; zero rules = 3.

## CBE-04 — no bypass

- File: `tests/e2e/test_cbe_04_no_bypass.py`
- Fixtures: `bypass/config/`, `bypass/comments/`, `bypass/env/`,
  `bypass/workflow/`, `bypass/clean/`
- Check: config, comment, env, and target-workflow disable attempts exit 3
  with `bypass_attempts[]`; clean control exits 0; CLI has no disable flags
  (unknown flag = 2); CBE's own `cbe-e2e.yml` is not scanned when passed via
  `--exclude-workflow`.
- Expected: 3 / `FAIL`; clean = 0; unknown flag = 2.

## CBE-05 — exemptions

- File: `tests/e2e/test_cbe_05_exemptions.py`
- Fixtures: `exemptions/*.txt`, `exemptions/inline_comment.py`
- Check: exact `SKIPPED: <rule_id> reason=<...>`; advisory applicable exemption
  counts in denominator; blocking exemption exits 3 `blocking_skip=true`;
  unknown/duplicate/missing reason/bad format exit 2; non-applicable exemption
  is SKIPPED but not counted; inline source comment is not honored.
- Expected: 0 for valid advisory; 3 for blocking; 2 for malformed; 4 if the
  ratio crosses 20%.

## CBE-06 — provider output

- File: `tests/e2e/test_cbe_06_provider_output.py`
- Fixtures: `providers/sarif_ok.py`, `sarif_findings.py`, `empty.py`,
  `missing.py`, `invalid_sarif.py`, `timeout.py`, `crash.py`, `native_ids.py`
- Check: every enabled provider has declared artifacts; valid zero-result SARIF
  is PASS; empty/missing/invalid artifact exits 3; provider exit 1 with valid
  artifact is a run; exit >= 2 fails; timeout is `SKIPPED_INFRA`; native id
  mapping works, unmapped id fails.
- Expected: 0 / `PASS`; 3 / `FAIL`; timeout 3 / `SKIPPED_INFRA`.

## CBE-07 — SARIF

- File: `tests/e2e/test_cbe_07_sarif.py`
- Fixtures: `sarif/valid.sarif`, `cbp_namespace.sarif`,
  `bad_rule_index.sarif`, `absolute_path.sarif`, `missing_rule.sarif`,
  `no_runs.sarif`
- Check: SARIF 2.1.0 schema; only `CBE-*`; ruleIndex/level/message/location;
  relative POSIX paths; no runs is invalid; merged output is Code Scanning
  ingestible.
- Expected: 0 for valid; 3 for invalid/cross-namespace/absolute path.

## CBE-08 — F2 denominator

- File: `tests/e2e/test_cbe_08_skip_denominator.py`
- Fixtures: manifest combinations built in the test from
  `manifests/valid_full.json`; `exemptions/valid.txt`
- Check: denominator = non-blocking applicable checks only; non-applicable
  rules are SKIPPED but not counted; blocking rules are not counted and may not
  SKIP; 1/5 passes, 2/5 exits 4, 1/4 exits 4; zero applicable exits 3; exit 3
  wins over 4.
- Expected: 0 / 4 / 3 per case.

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
  manifests/        valid_*.json, invalid_*.json, zero_rules.json
  providers/        sarif_ok.py, sarif_findings.py, empty.py, missing.py,
                    invalid_sarif.py, timeout.py, crash.py, native_ids.py
  bypass/           config/, comments/, env/, workflow/, clean/
  exemptions/       valid.txt, missing_reason.txt, blocking.txt,
                    unknown_rule.txt, duplicate.txt, bad_format.txt,
                    inline_comment.py, not_applicable.txt
  releases/         releases.json, erratum_body.md
  sarif/            valid.sarif, cbp_namespace.sarif, bad_rule_index.sarif,
                    absolute_path.sarif, missing_rule.sarif, no_runs.sarif
  release-train/    not-uploaded.json, declared-attached.json,
                    evidence-absent.json
  selfcheck/        baseline-0.0.9/, current-manifest.json, current-output/,
                    baseline-2.json, baseline-3.json, baseline-4.json
  cli/              .keep
```

## Runner and CI

- `tests/e2e/run_e2e.py` runs CBE-01..11 in order and exits non-zero on any
  failure; JSON summary to stdout.
- `.github/workflows/cbe-e2e.yml` runs it without `continue-on-error`, `|| true`,
  or `if: always()`.
- Fixtures are committed; no network. The baseline wheel is hash-pinned.
- `enforce-no-bypass --workflows` scans the target repo; when scanning CBE
  itself, pass `--exclude-workflow .github/workflows/cbe-e2e.yml`.

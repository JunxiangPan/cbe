# CBE 0.1.0 Release Evidence

Distribution `cbe-review`; import package/CLI `cbe`. All evidence is copied
from the RC audit package and is read-only for this release staging directory.

| Evidence | File | Key fact |
|---|---|---|
| CBE-08 PASS | `evidence/cbe-08-frozen.json` | `status=PASS`, `not_pass=false`, failed_checks=[]; four F2 exits 0/0/3/3 |
| Contract guard | `evidence/contract-guard.json` | `PINNED`, frozen tag `contract-v1.7.1` / `c2b5e9`, contract `209d75b4…`, addendum `e318cbd` / `51604f56…` |
| CBE-07b on CBP 1.2.2 | `evidence/cbp-1.2.2-official.json` | `CBE-SECRET-001` → `CBP-EXT-SECRET-001`, `origin_rule=CBE-SECRET-001` |
| Real CBP 1.2.2 manifest | `evidence/cbp-1.2.2-quality-manifest.json` | sha256 `228594d0…`; object `artifact_repository` |
| CBE-08 F2 report schema | `evidence/cbe-report-rc2.report.json`, `evidence/cbe-report-rc2.validation.json` | real CBE report; RC2 schema; 0 errors |
| CBE-10 F5/F6 | `evidence/cbe-10-f5-f6.json` | `NOT_UPLOADED` not PASS/SKIP/counted; infra exit 3; object repository accepted; bare string rejected |
| CBE-09 | `evidence/cbe-09-baseline.json` | selector fixture; no stable CBE, explicit bootstrap only |
| CBE-11 | `evidence/cbe-11-selfcheck.json` | bootstrap PASS; not a stable-baseline claim |

Artifact hashes are in `RELEASE_MANIFEST.json` and `SHA256SUMS`.

## PyPI

Human approved `cbe-review==0.1.0`, but the upload is **BLOCKED**: no `twine`,
no `.pypirc`, no PyPI token, and no trusted-publisher workflow. No upload was
attempted; the old `cbe` name is never used.

# CBF adoption — CBE

Status: **PENDING_CBF_0.1.0**

- surfaces: `git` / `api` / `local-ai`
- planned gate: `cbf gate --surface git`
- planned CI job: `cbf-privacy-gate`
- evidence format: `cbf-evidence/v1`

CBE has **not** integrated CBF. There is **no CBF PASS**, and CBE does not
claim CBF compatibility. CBF is an independent project; CBE does not import
it and does not require it to be installed.

## Phase 0 (current)

- Adoption documented here.
- The `cbf-privacy-gate` CI job name is reserved in this document only; no
  workflow file is added in Phase 0.
- Existing CI does not fake a CBF result and does not use `continue-on-error`
  or `if: false` to bypass it.
- No GitHub Release, PyPI upload, or git push is claimed to have CBF evidence.

## Phase 1 (after CBF 0.1.0rc1)

- Add `cbf.policy.json` pinned to the CBF policy version/hash.
- Wire `cbf-privacy-gate` into the release/upload path and add the local
  pre-push `cbf gate --surface git`.
- Block upload/release on CBF failure; record `cbf-evidence/v1`.

## Boundary

CBE **does not implement CBF scanning** and does not judge CBF policy or
findings. CBE only verifies that a configured `cbf-privacy-gate` job is
reachable and not skipped. Future `--gate-jobs` includes `cbf-privacy-gate`;
CBE proves the job ran, nothing more. CBE does not import CBF or require it at
runtime.

CBE release/upload must be preceded by a real CBF PASS once CBF 0.1.0 is
available. CBE 0.3.0 was published during CBF Phase 0; it is **not** claimed to
have CBF evidence or a CBF PASS. No future CBE release may claim CBF compliance
without a real gate result.

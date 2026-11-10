# CBE 0.2.0 Release Notes

Status: **staged; no tag, no GitHub Release, no PyPI upload.**

CBE 0.2.0 is the gate-integrity release. Distribution remains `cbe-review`;
import package and CLI remain `cbe`.

## Highlights

- 10-mutant no-bypass recall: **1.0**; every mutant exits 3 / non-PASS.
- Remote reusable workflow closure: `--fetch-remote` opt-in, recursive local and
  remote scans; unverifiable/failed fetches exit 3 under `--strict`.
- Sidecar signing/attestation schemas + offline verifier; production identity
  unavailable, so status is **BLOCKED_NO_SIGNING_IDENTITY**.
- Self-protection manifest and CI tamper check.
- Contract red-line tests: frozen report schema, exit codes, object
  `artifact_repository`, body scope/hash, 20% threshold.
- Coverage gate 80% (current 82.93%; gate module 91%).
- 10%/15% skip-ratio warnings; 20% exit 4 unchanged.
- Actions pinned to commit SHAs; Windows path tests; no self-hosted runner.
- Threat model, package-name policy, schema-integration status, and SBOM.

## Compatibility

- Python >= 3.10.
- Runtime dependencies: `jsonschema>=4.20`, `pyyaml>=6.0`.
- Optional `sign` extra: `cryptography>=42`.
- Test-only `e2e` extra includes CBP 1.2.2 and cryptography.
- Never upload `cbe`; use `cbe-review`.

## Immutable prior releases

`v0.1.0` / `13f7ddc` and `v0.1.1` / `06f8f50`, their GitHub Releases, and their
PyPI artifacts are unchanged. CBE report schema is unchanged.

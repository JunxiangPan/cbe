# CBE 0.2.0 release staging

Status: **AWAITING HUMAN APPROVAL — no tag, no GitHub Release, no PyPI upload.**

Release readiness: [READINESS.md](READINESS.md).

Distribution: `cbe-review`; import package and CLI remain `cbe`.
This is a gate-integrity release, not a runtime security boundary.

## What is included

- **CBE-MUT-01**: 10 bypass mutants, recall **1.0**; no mutant is PASS.
- **CBE-REMOTE-01**: opt-in `--fetch-remote`; fetched GitHub reusable workflows
  are scanned recursively. Unfetched/network/auth/404 references remain
  `UNVERIFIABLE_REMOTE_WORKFLOW`; `--strict` exits 3.
- **CBE-TRUST-01**: Ed25519 sidecar schema, signer, and offline verifier.
  Production signing is **BLOCKED_NO_SIGNING_IDENTITY**; no signature is
  fabricated.
- **CBE-SELF-01**: `security/SELF_PROTECTION.sha256` and CI check for workflow,
  gate script, manifest core, and contract guard; tamper tests are red.
- **CBE-CONTRACT-01**: schema, exit codes, object `artifact_repository`, body
  scope, and 20% threshold pinned by tests.
- **CBE-COV-01**: unit coverage gate raised to 80%; current **83.00%**,
  `enforce_no_bypass.py` **91%**.
- **CBE-WIN-01**: Windows path/backslash test, SHA-pinned Actions, no
  self-hosted runner.
- **CBE-SKIP-01**: 10%/15% early warnings; 20% exit 4 is unchanged.
- **CBE-NAME-01**: `cbe` name collision documented; never upload `cbe`.
- **CBE-THREAT-01**: threat model documents what CBE does and does not defend.
- **CBE-SCHEMA-01**: report schema untouched; sidecars are external.
- **CBE-SBOM-01**: CycloneDX SBOM and SHA-pinned Actions.
- **CBE-CBP-01**: `--gate-job` can select `cbp-gate`; cross-gate test added.

## Artifacts

| File | SHA256 | Size |
|---|---|---|
| `cbe_review-0.2.0-py3-none-any.whl` | `cb4c07ea316836b63f8c9c9538417fb430ab82021d8a6ca10d713add79ab01bc` | 57,179 B |
| `cbe_review-0.2.0.tar.gz` | `d04b60e0b0cf057370d23c042b6c48f8ac150d75a957c73d288ef69de3e77bdf` | 47,966 B |

Wheel metadata:

```text
Name: cbe-review
Version: 0.2.0
License-Expression: Apache-2.0
License-File: LICENSE
sidecar schemas: present
```

## Boundaries

- `v0.1.0` and `v0.1.1` tags/assets are unchanged.
- CBE report schema unchanged (CBS amendment still required for any change).
- 20% skip threshold unchanged.
- Sidecar signing is blocked, not faked.
- Remote workflow fetch is opt-in; no remote workflow is called “verified”.
- CI: <https://github.com/JunxiangPan/cbe/actions/runs/42808359187>
  (Ubuntu + Windows success).
- Human approval is required before tag/release/PyPI.

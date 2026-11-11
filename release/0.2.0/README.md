# CBE 0.2.0 release staging

Status: **RELEASED — SIGNED via Sigstore keyless (GitHub OIDC); CBP v1.3.2 PASS.**

Release readiness: [READINESS.md](READINESS.md).

CBP v1.3.2 tag `63cc8f0` contains a real `cbp-gate`; CBE cross-check passes
with `--gate-job '^cbp-gate$' --exclude-workflow '.github/workflows/e2e-payload.yml' --strict`.
Production signing is the Sigstore keyless bundle from
`.github/workflows/sign-release.yml`; Ed25519 is optional/legacy only.

Distribution: `cbe-review`; import package and CLI remain `cbe`.
This is a gate-integrity release, not a runtime security boundary.

## What is included

- **CBE-MUT-01**: 10 bypass mutants, recall **1.0**; no mutant is PASS.
- **CBE-REMOTE-01**: opt-in `--fetch-remote`; fetched GitHub reusable workflows
  are scanned recursively. Unfetched/network/auth/404 references remain
  `UNVERIFIABLE_REMOTE_WORKFLOW`; `--strict` exits 3.
- **CBE-TRUST-01**: Sigstore keyless production signatures; Ed25519 sidecar
  schema/signer/verifier retained as optional/legacy. No fake signature is
  produced; no Ed25519 signature is claimed as production.
- **CBE-SELF-01**: `security/SELF_PROTECTION.sha256` and CI check for workflow,
  gate script, manifest core, and contract guard; tamper tests are red.
- **CBE-CONTRACT-01**: schema, exit codes, object `artifact_repository`, body
  scope, and 20% threshold pinned by tests.
- **CBE-COV-01**: unit coverage gate raised to 80%; current **82.93%** (latest observed 83.00%),
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
| `cbe_review-0.2.0-py3-none-any.whl` | `d9acbefaaf14172ce1d4fda50bf49007c13e443a1988de16bc125be3d1daac91` | 57,147 B |
| `cbe_review-0.2.0.tar.gz` | `e4c5cdb28ee91a0732cf1d43193c785e5c3feeff7b73924454d69690da61cf9f` | 47,221 B |

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

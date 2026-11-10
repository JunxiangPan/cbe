# CBE 0.2.0 Release Readiness

Status: **READY FOR OWNER FINAL CONFIRMATION — CBP v1.3.2 PASS; unsigned; branch/tag protection not configured.**

CBP v1.3.2 review: [artifacts/cbp-review/1.3.2.md](../../artifacts/cbp-review/1.3.2.md).

CBP v1.3.2 tag `63cc8f0` contains the real `cbp-gate`; CBE cross-check exits 0
with `--gate-job '^cbp-gate$' --exclude-workflow '.github/workflows/e2e-payload.yml' --strict`.
The post-tag docs HEAD `2708339` was not used as the release identity.

CBE is still **UNSIGNED**. Release is blocked only on branch/tag protection
configuration or an explicit owner waiver, plus final owner confirmation.

This page is the single readiness decision for the 0.2.0 staging package. No
v0.2.0 tag, GitHub Release, or PyPI upload exists.

---

## 1. Signed or unsigned

**UNSIGNED.**

```text
sidecar signing: BLOCKED_NO_SIGNING_IDENTITY
production manifest.sig: NOT PRODUCED
production attestation.json: NOT PRODUCED
```

Delivered:

- Ed25519 sidecar schemas (`schemas/sidecar/`)
- signer (`tools/cbe_sign_sidecar.py`)
- offline verifier (`tools/cbe_verify_sidecar.py`)
- ephemeral-key positive/negative tests

Not delivered: a production signing identity, a production public key, or a
real signature/attestation. Release notes must not use “signed”, “attested”,
“verified signature”, or equivalent wording unless that changes.

---

## 2. Branch protection

**NOT CONFIGURED.**

GitHub API check on 2026-11-10:

```text
GET /repos/JunxiangPan/cbe/branches/main/protection
-> 404 Branch not protected

GET /repos/JunxiangPan/cbe/rulesets
-> []
```

Consequences:

- `main` can be force-pushed/deleted by someone with permission.
- Required review is not enforced.
- Required checks are not enforced.
- The self-protection manifest can be changed in the same commit as a
  protected file; CI catches drift only when the check actually runs.

Owner must configure branch protection/rules **or** approve an explicit external-control waiver before release.

---

## 3. Required checks

**NOT ENFORCED.**

Intended contexts:

```text
e2e (ubuntu-latest)
e2e (windows-latest)
```

Actual state:

- Both checks are green at the candidate CI run:
  <https://github.com/JunxiangPan/cbe/actions/runs/42841108822>
- They are **not required checks** because `main` is unprotected.
- `pypi` environment has a required reviewer (`JunxiangPan`) and a branch
  policy; this is good but does not protect `main`.
- Tag protection API returned 404; `v0.1.0`, `v0.1.1`, and future `v0.2.0`
  are not protected by a GitHub tag rule.

Owner must configure required checks/tag protection **or** approve an explicit external-control waiver before release.

---

## 4. Remote parent-call reachability

**PARTIAL / EXPLICIT BOUNDARY.**

Implemented:

- local job-level `uses: ./.github/workflows/*.yml` recursive scan;
- opt-in `--fetch-remote` GitHub remote fetch;
- remote local references resolved inside the same repo/ref;
- unfetched/network/auth/404/parse failures are
  `UNVERIFIABLE_REMOTE_WORKFLOW` and `--strict` exits 3.

Not implemented:

- parent-call reachability is **not propagated into the child**. If a parent
  job that calls a reusable workflow is itself unreachable (`if: false`,
  skipped `needs`), CBE may scan the child standalone and not mark the parent
  call as unreachable.
- Therefore CBE 0.2.0 does not claim full remote reusable call-graph closure.
  A skipped parent call remains a known false-negative boundary unless the
  owner accepts it or the call graph is implemented in a later version.

This is not a “remote workflow verified” claim. Remote content is only scanned
when explicitly fetched; fetch success is not trust.

---

## 5. Owner approval

**CONDITIONAL — FINAL CONFIRMATION PENDING.**

```text
approval.required: true
approval.conditional: true
approval.approved: false
approver: human operator (conditional approval)
scope: GitHub Release + PyPI cbe-review 0.2.0
```

Release actions still prohibited until the owner confirms branch/tag protection
or an explicit waiver and gives final release approval:

- no `v0.2.0` tag;
- no GitHub Release;
- no PyPI upload;
- no old `cbe` upload;
- no movement of `v0.1.0` / `v0.1.1` or their assets.

---

## 6. Unsigned waiver template (NOT YET EXERCISED)

Only if the owner explicitly chooses unsigned release. The owner must fill and
approve this text; this template is not an approval.

```text
CBE 0.2.0 Unsigned Waiver

I, <owner>, approve releasing CBE 0.2.0 as UNSIGNED.

I understand:
- no production manifest.sig or attestation.json exists;
- the release is not signed or attested;
- the offline verifier/schema are tooling, not a signature;
- branch/tag protection and required checks are separate external controls;
- remote parent-call reachability is a known boundary.

Scope: <GitHub Release only | GitHub + PyPI cbe-review 0.2.0>
Date: <YYYY-MM-DD>
Signature/approval record: <link or text>
```

If this waiver is used, all release text must say **unsigned**.

---

## 7. Release gate

Release may proceed only after all are true:

- [ ] owner approval record completed;
- [ ] `main` branch protection configured **or** explicit external-control waiver;
- [ ] required checks configured (`e2e (ubuntu-latest)`, `e2e (windows-latest)`) **or** explicit waiver;
- [ ] tag protection configured for `v*` **or** explicit waiver;
- [ ] signed identity configured **or** unsigned waiver approved;
- [ ] remote parent-call boundary explicitly accepted;
- [ ] staging artifacts unchanged:
  - wheel `cb4c07ea316836b63f8c9c9538417fb430ab82021d8a6ca10d713add79ab01bc`
  - sdist `d04b60e0b0cf057370d23c042b6c48f8ac150d75a957c73d288ef69de3e77bdf`
- [ ] required CI green at the approved commit.

Current verdict: **READY — awaiting owner final confirmation / external-control waiver.**

## Evidence

- CI: <https://github.com/JunxiangPan/cbe/actions/runs/42841108822>
- Mutation recall: `artifacts/mutation/cbe-0.2.0.json` (10/10, 1.0)
- Self-protection: `security/SELF_PROTECTION.sha256`
- Signing status: `docs/SIGNING.md`
- Threat model: `docs/THREAT_MODEL.md`
- Schema status: `docs/SCHEMA_INTEGRATION.md`

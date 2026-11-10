# CBE 0.2.0 Release Readiness

Status: **HOLD — waiting for CBP v1.3.1 tag/release; unsigned; branch/tag protection not configured.**

CBP v1.3.0 review: [artifacts/cbp-review/1.3.0.md](../../artifacts/cbp-review/1.3.0.md).

CBP 1.3.1 release commit `c4b5471f4e5cd1485f759192046b8b5f6a90d777` exists,
but **no v1.3.1 tag or GitHub Release exists yet**. Tag-level review has not
started; v1.3.0 remains historical FAIL.

The real `cbp-gate` exists only in post-tag HEAD `3b900f5`; the released
`v1.3.0` tag peels to `4aba2ff` and has no `cbp-gate`.

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

Owner must configure branch protection/rules before release.

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
  <https://github.com/JunxiangPan/cbe/actions/runs/42808359187>
- They are **not required checks** because `main` is unprotected.
- `pypi` environment has a required reviewer (`JunxiangPan`) and a branch
  policy; this is good but does not protect `main`.
- Tag protection API returned 404; `v0.1.0`, `v0.1.1`, and future `v0.2.0`
  are not protected by a GitHub tag rule.

Owner must configure required checks and tag protection before release.

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

**NOT APPROVED.**

```text
approval.required: true
approval.approved: false
approver: null
approved_at: null
scope: null
```

Release actions still prohibited:

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
- [ ] `main` branch protection configured;
- [ ] required checks configured (`e2e (ubuntu-latest)`, `e2e (windows-latest)`);
- [ ] tag protection configured for `v*`;
- [ ] signed identity configured **or** unsigned waiver approved;
- [ ] remote parent-call boundary explicitly accepted;
- [ ] staging artifacts unchanged:
  - wheel `a55a14e5a730641afecb0d8dce4c06d2c4e564c0eb6e83aa2f37c436e49d8483`
  - sdist `219397728d677b7717b8f8b9395773cb333fd213540d6d268b59850436656c96`
- [ ] required CI green at the approved commit.

Current verdict: **HOLD.**

## Evidence

- CI: <https://github.com/JunxiangPan/cbe/actions/runs/42808359187>
- Mutation recall: `artifacts/mutation/cbe-0.2.0.json` (10/10, 1.0)
- Self-protection: `security/SELF_PROTECTION.sha256`
- Signing status: `docs/SIGNING.md`
- Threat model: `docs/THREAT_MODEL.md`
- Schema status: `docs/SCHEMA_INTEGRATION.md`

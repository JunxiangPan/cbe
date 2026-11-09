# CBE 0.1.0 Release Runbook

Status: **DRAFT — NOT EXECUTED. Human approval is mandatory.**
The release package is prepared; no tag, GitHub Release, or PyPI upload exists.
PyPI is separately blocked by the `cbe` name collision.

## 0. Approval record

Complete this before running any release command.

| Field | Value |
|---|---|
| Approver | _pending_ |
| Approval date | _pending_ |
| Scope approved | GitHub Release only; PyPI is blocked |
| Release source commit | `d820001ec1120408b4d76db323e9153465359805` |
| Wheel SHA256 | `966fabf110eb2909722670f23c4b22efdca773b1cd1381bd4fcc90e02266fa6e` |
| Sdist SHA256 | `bc474810fabce42397f75fa68dace3182f9308ab0681b53597c56220493daaff` |
| PyPI status | **BLOCKED — `cbe` owned by azizo-b/CBE** |

**Do not tag or publish until this table is filled by a human.**

## 1. Preconditions

Run from the CBE repository after approval:

```bash
git status --porcelain              # must be empty
git rev-parse HEAD                  # record the release-package commit
git rev-parse d820001ec1120408b4d76db323e9153465359805
git tag --list v0.1.0               # must be empty
gh release view v0.1.0              # must not exist
python -m pip index versions cbe    # 0.1.0 must not be published
```

Required evidence:

- `release/0.1.0/artifacts/cbe-0.1.0-py3-none-any.whl` hash matches the record.
- `release/0.1.0/artifacts/cbe-0.1.0.tar.gz` hash matches the record.
- `release/0.1.0/evidence/cbe-08-frozen.json` has `status=PASS`, `not_pass=false`,
  and all four F2 checks matching.
- `release/0.1.0/evidence/contract-guard.json` has `gate_status=PINNED`,
  `frozen=true`, and addendum `e318cbd` authorized.
- CI at the source commit is Ubuntu + Windows success.

Abort on any mismatch. Do not “fix” a tag or release in place.

## 2. Tag (only after approval)

Tag the recorded release source commit, not a moving branch and not a later
docs commit:

```bash
RELEASE_COMMIT=d820001ec1120408b4d76db323e9153465359805
git tag -a v0.1.0 "$RELEASE_COMMIT" -m "CBE 0.1.0"
git push origin refs/tags/v0.1.0
```

Verify:

```bash
git rev-parse v0.1.0^{}    # must equal RELEASE_COMMIT
git ls-remote --tags origin v0.1.0
```

Never force-update or move the tag. If the tag is wrong, stop and create a new
version/ERRATUM; do not rewrite it.

## 3. GitHub Release

Create the release from the annotated tag with the two artifacts:

```bash
gh release create v0.1.0 \
  release/0.1.0/artifacts/cbe-0.1.0-py3-none-any.whl \
  release/0.1.0/artifacts/cbe-0.1.0.tar.gz \
  --repo JunxiangPan/cbe \
  --title "CBE 0.1.0" \
  --notes-file release/0.1.0/RELEASE_NOTES.md
```

Verify release assets:

```bash
gh release view v0.1.0 --repo JunxiangPan/cbe \
  --json tagName,assets,url
```

The asset digests must equal the hashes above.

## 4. PyPI — BLOCKED; DO NOT RUN

`pip index versions cbe` reports the PyPI project `cbe` belongs to
`azizo-b/CBE` (Crossroads Bank for Enterprises), versions 0.1.7/0.1.8. It is a
different project. **Do not run `twine upload` for `cbe`.**

Unblocking requires a human decision on a new distribution name or PyPI
ownership, followed by rebuilding artifacts and re-auditing them. No PyPI
upload is approved by this runbook.

## 5. Post-release verification

Install from the GitHub Release asset or the staged wheel, not from PyPI:

```bash
python -m venv /tmp/cbe-release-check
/tmp/cbe-release-check/bin/pip install release/0.1.0/artifacts/cbe-0.1.0-py3-none-any.whl
/tmp/cbe-release-check/bin/cbe validate-manifest \
  --manifest tests/e2e/fixtures/manifests/valid_minimal.json
```

Expected: `PASS`, exit 0. Also verify `cbe --help` and the five subcommands.

## 6. Rollback

- Before any distribution: delete the GitHub Release and the local/remote tag
  only if the release was not distributed; record the reason.
- If PyPI is ever unblocked and a bad file is published: do not move the tag;
  yank the bad files, publish an ERRATUM, and bump the version.
- Never rewrite published evidence or move `contract-v1.7.1`.

## 7. Explicit non-actions

This runbook does **not** authorize:

- tagging without the approval record;
- any PyPI upload while the `cbe` name is owned by another project;
- changing CBE-08 PASS evidence after publication;
- editing CBS/CBP/CBM/CBC;
- moving `contract-v1.7.1`.

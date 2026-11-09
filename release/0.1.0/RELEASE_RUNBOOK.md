# CBE 0.1.0 Release Runbook

Status: **DRAFT — NOT EXECUTED. Human approval is mandatory.**
The release package is prepared; no tag, GitHub Release, or PyPI upload exists.

## 0. Approval record

Complete this before running any release command.

| Field | Value |
|---|---|
| Approver | _pending_ |
| Approval date | _pending_ |
| Scope approved | GitHub Release only / GitHub + PyPI |
| Release source commit | `d820001ec1120408b4d76db323e9153465359805` |
| Wheel SHA256 | `966fabf110eb2909722670f23c4b22efdca773b1cd1381bd4fcc90e02266fa6e` |
| Sdist SHA256 | `bc474810fabce42397f75fa68dace3182f9308ab0681b53597c56220493daaff` |

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

## 4. PyPI (optional; requires separate approval)

Only if the approval record explicitly includes PyPI:

```bash
python -m twine check release/0.1.0/artifacts/*
python -m twine upload \
  release/0.1.0/artifacts/cbe-0.1.0-py3-none-any.whl \
  release/0.1.0/artifacts/cbe-0.1.0.tar.gz
```

Then verify:

```bash
python -m pip download --no-deps --dest /tmp/cbe-pypi cbe==0.1.0
sha256sum /tmp/cbe-pypi/*
python -m pip index versions cbe
```

PyPI digests must match the recorded hashes. PyPI uploads cannot be deleted;
use yank + ERRATUM if necessary.

## 5. Post-release verification

```bash
python -m venv /tmp/cbe-release-check
/tmp/cbe-release-check/bin/pip install cbe==0.1.0
/tmp/cbe-release-check/bin/cbe validate-manifest \
  --manifest tests/e2e/fixtures/manifests/valid_minimal.json
```

Expected: `PASS`, exit 0. Also verify `cbe --help` and the five subcommands.

## 6. Rollback

- Before PyPI: delete the GitHub Release and the local/remote tag only if the
  release was not distributed; record the reason.
- After PyPI: do not move the tag. Yank the bad files, publish an ERRATUM, and
  bump the version.
- Never rewrite published evidence or move `contract-v1.7.1`.

## 7. Explicit non-actions

This runbook does **not** authorize:

- tagging without the approval record;
- publishing to PyPI without an explicit PyPI scope;
- changing CBE-08 PASS evidence after publication;
- editing CBS/CBP/CBM/CBC;
- moving `contract-v1.7.1`.

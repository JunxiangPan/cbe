# CBE 0.1.0 Release Runbook

Status: **DRAFT — NOT EXECUTED. Human approval is mandatory.**
The release package is prepared; no tag, GitHub Release, or PyPI upload exists.
Distribution name: `cbe-review`; import package and CLI remain `cbe`.
Tag choice: **B — tag `13f7ddc`, which includes the complete release package.**
Artifacts were built from `4561e83`; metadata corrections after `13f7ddc` are
docs-only and do not change the artifacts.

## 0. Approval record

Complete this before running any release command.

| Field | Value |
|---|---|
| Approver | human operator (chat approval) |
| Approval date | 2026-11-10T00:32:18+08:00 |
| Scope approved | GitHub Release; PyPI `cbe-review` conditional (not separately confirmed) |
| Release source commit | `4561e8338a09a7e681b08fc0c2b38fcff2d56e70` |
| Release package commit / tag target | `13f7ddc8af947a6bae10b4251beb2406e2d31f30` |
| Wheel SHA256 | `87f0ad40a6cffdf4f9c657e6cc972a0f93787259c52445a1c112a5c7753599a7` |
| Sdist SHA256 | `a77c653d178d5d0ab179da73c92184d9a54d5104ca5202f41574588979b68854` |
| PyPI distribution | `cbe-review` (available at preparation time; pending approval) |

**Do not tag or publish until this table is filled by a human.**

## 1. Preconditions

Run from the CBE repository after approval:

```bash
git status --porcelain              # must be empty
git rev-parse HEAD                  # must be the approved metadata commit
git rev-parse 13f7ddc8af947a6bae10b4251beb2406e2d31f30
git rev-parse 4561e8338a09a7e681b08fc0c2b38fcff2d56e70
git diff --stat 13f7ddc8af947a6bae10b4251beb2406e2d31f30..HEAD
# expected: only release/0.1.0 metadata files, no code or artifacts
git tag --list v0.1.0               # must be empty
gh release view v0.1.0              # must not exist
python -m pip index versions cbe-review   # must not exist yet
python -m pip index versions cbe          # owned by azizo-b/CBE; never upload here
```

Required evidence:

- `release/0.1.0/artifacts/cbe_review-0.1.0-py3-none-any.whl` hash matches.
- `release/0.1.0/artifacts/cbe_review-0.1.0.tar.gz` hash matches.
- `release/0.1.0/evidence/cbe-08-frozen.json` has `status=PASS`, `not_pass=false`,
  and all four F2 checks matching.
- `release/0.1.0/evidence/contract-guard.json` has `gate_status=PINNED`,
  `frozen=true`, and addendum `e318cbd` authorized.
- CI at the source commit is Ubuntu + Windows success.

Abort on any mismatch. Do not “fix” a tag or release in place.

## 2. Tag (only after approval)

Tag the release-package commit `13f7ddc`, which includes the complete release
package. Do not tag the artifact source commit `4561e83`; that commit does not
contain the release package.

```bash
RELEASE_COMMIT=13f7ddc8af947a6bae10b4251beb2406e2d31f30
SOURCE_COMMIT=4561e8338a09a7e681b08fc0c2b38fcff2d56e70
git tag -a v0.1.0 "$RELEASE_COMMIT" -m "CBE 0.1.0"
git push origin refs/tags/v0.1.0
```

Verify:

```bash
git rev-parse v0.1.0^{}    # must equal RELEASE_COMMIT (13f7ddc)
git merge-base --is-ancestor "$SOURCE_COMMIT" "$RELEASE_COMMIT"  # must be true
git ls-remote --tags origin v0.1.0
```

Never force-update or move the tag. If the tag is wrong, stop and create a new
version/ERRATUM; do not rewrite it.

## 3. GitHub Release

Create the release from the annotated tag with the two artifacts:

```bash
gh release create v0.1.0 \
  release/0.1.0/artifacts/cbe_review-0.1.0-py3-none-any.whl \
  release/0.1.0/artifacts/cbe_review-0.1.0.tar.gz \
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

Only if the approval record explicitly includes PyPI **and** `cbe-review` is
still unclaimed:

```bash
python -m twine check release/0.1.0/artifacts/*
python -m twine upload \
  release/0.1.0/artifacts/cbe_review-0.1.0-py3-none-any.whl \
  release/0.1.0/artifacts/cbe_review-0.1.0.tar.gz
```

Then verify:

```bash
python -m pip download --no-deps --dest /tmp/cbe-review-pypi cbe-review==0.1.0
sha256sum /tmp/cbe-review-pypi/*
python -m pip index versions cbe-review
```

PyPI digests must match the recorded hashes. Never upload the old `cbe` name.
PyPI uploads cannot be deleted; use yank + ERRATUM if necessary.

## 5. Post-release verification

If PyPI was approved and published:

```bash
python -m venv /tmp/cbe-release-check
/tmp/cbe-release-check/bin/pip install cbe-review==0.1.0
/tmp/cbe-release-check/bin/cbe validate-manifest \
  --manifest tests/e2e/fixtures/manifests/valid_minimal.json
```

If only the GitHub Release was approved, install the attached wheel instead:

```bash
/tmp/cbe-release-check/bin/pip install \
  release/0.1.0/artifacts/cbe_review-0.1.0-py3-none-any.whl
```

Expected: `PASS`, exit 0. Also verify `cbe --help` and the five subcommands.

## 6. Rollback

- Before any distribution: delete the GitHub Release and the local/remote tag
  only if the release was not distributed; record the reason.
- After PyPI: do not move the tag. Yank the bad files, publish an ERRATUM, and
  bump the version.
- Never rewrite published evidence or move `contract-v1.7.1`.

## 7. Explicit non-actions

This runbook does **not** authorize:

- tagging without the approval record;
- uploading the old `cbe` distribution name;
- publishing to PyPI without an explicit PyPI scope;
- changing CBE-08 PASS evidence after publication;
- editing CBS/CBP/CBM/CBC;
- moving `contract-v1.7.1`.

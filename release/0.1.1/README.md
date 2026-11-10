# CBE 0.1.1 — External-use package

Status: **APPROVED — release in progress (GitHub + PyPI cbe-review 0.1.1).**
This is a staging package for external use; `v0.1.0` and its artifacts are
unchanged.

## Distribution identity

```text
PyPI distribution: cbe-review
Import package:    cbe
CLI:               cbe
Version:           0.1.1
License:           Apache-2.0
```

> `pip install cbe` installs the unrelated Crossroads Bank for Enterprises
> package. Use `pip install cbe-review`.

## What changed

- Apache-2.0 `LICENSE` in the repository, wheel, and sdist.
- PyPI metadata: `License-Expression`, `License-File`, author/maintainer,
  classifiers, keywords, and project URLs.
- README rewritten for external users: audience, problem, install, quick start,
  and the `cbe` name warning.
- `enforce-no-bypass --strict`: unverifiable workflow conditions now exit 3.
- `enforce-no-bypass --gate-job REGEX`: default remains `^cbe[-_]gate$`;
  renamed gates can be selected explicitly.
- Local job-level `uses: ./.github/workflows/*.yml` workflows are followed
  recursively. Remote reusable workflows report `UNVERIFIABLE_REMOTE_WORKFLOW`
  and are never silently treated as PASS.

## Artifacts

| File | SHA256 | Size |
|---|---|---|
| `cbe_review-0.1.1-py3-none-any.whl` | `b838e4366196933e043119614d982f5bebdf3cc9a3d382ce7a302b96fd882f58` | 54,261 B |
| `cbe_review-0.1.1.tar.gz` | `768d2ea635e263b168871df2080537c0a6d84a316cfb34623240e54931bc4c96` | 45,387 B |

Wheel metadata verified:

```text
Name: cbe-review
Version: 0.1.1
License-Expression: Apache-2.0
License-File: LICENSE
```

Install from the wheel:

```bash
python -m pip install cbe_review-0.1.1-py3-none-any.whl
cbe --version
```

## Verification

- Full suite: **217 passed** (unit + E2E); CI run is authoritative for the
  committed tree.
- `enforce_no_bypass.py` unit coverage: **90%** (target 70%).
- Full unit coverage: **82.43%** (gate 60%).
- Ubuntu + Windows CI required before release.

## Boundaries

- `v0.1.0` tag remains at `13f7ddc`; its GitHub/PyPI artifacts are untouched.
- 0.1.0 PyPI metadata is immutable; these corrections take effect only in
  0.1.1.
- No 0.1.1 tag, GitHub Release, or PyPI upload exists.

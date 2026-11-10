# CBE 0.1.1 — External-use package

Status: **RELEASED on GitHub and PyPI.**
This is the external-use package; `v0.1.0` and its artifacts are unchanged.

- GitHub Release: <https://github.com/JunxiangPan/cbe/releases/tag/v0.1.1>
- PyPI: <https://pypi.org/project/cbe-review/0.1.1/>
- Tag: `v0.1.1` → `06f8f50`

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

- Full suite: **217 passed** (unit + E2E).
- `enforce_no_bypass.py` unit coverage: **90%** (target 70%).
- Full unit coverage: **82.43%** (gate 60%).
- Pre-release CI: <https://github.com/JunxiangPan/cbe/actions/runs/42738752814> — Ubuntu + Windows success.
- Post-release CI: <https://github.com/JunxiangPan/cbe/actions/runs/42740507273> — Ubuntu + Windows success.
- PyPI publish workflow: <https://github.com/JunxiangPan/cbe/actions/runs/42739625465> — success.

## Boundaries

- `v0.1.0` tag remains at `13f7ddc`; its GitHub/PyPI artifacts are untouched.
- `v0.1.1` tag / GitHub Release / PyPI upload exist.
- 0.1.0 PyPI metadata is immutable; corrections are in 0.1.1.
- Remote reusable workflows are reported only as `UNVERIFIABLE_REMOTE_WORKFLOW`; they are not claimed as verified.
- CBS/CBP/CBM/CBC were not modified.

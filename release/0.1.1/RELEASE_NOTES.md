# CBE 0.1.1 Release Notes

Status: **RELEASED on GitHub and PyPI.**

- GitHub Release: <https://github.com/JunxiangPan/cbe/releases/tag/v0.1.1>
- PyPI: <https://pypi.org/project/cbe-review/0.1.1/>
- Tag: `v0.1.1` → `06f8f50`

CBE 0.1.1 is the external-use hardening release. Distribution remains
`cbe-review`; the import package and CLI remain `cbe`.

## Highlights

- Apache-2.0 license, including wheel `License-Expression` / `License-File`.
- Complete PyPI metadata: author, maintainers, classifiers, keywords, project
  URLs, and homepage.
- README rewritten around audience, problem, and getting started.
- `enforce-no-bypass --strict` fails unverifiable workflow conditions.
- `--gate-job REGEX` for renamed gates (`security-gate`, `enforce`,
  `policy-check`); default is still `^cbe[-_]gate$`.
- Local reusable workflows are followed recursively; remote reusable
  workflows report `UNVERIFIABLE_REMOTE_WORKFLOW`.

## Compatibility

- Python >= 3.10.
- Runtime dependencies: `jsonschema>=4.20`, `pyyaml>=6.0`.
- Test-only `e2e` extra: `cbp-action==1.2.2`.
- `cbe-review` is the only PyPI distribution; do not install `cbe`.

## 0.1.0 metadata

The 0.1.0 wheel/sdist and tag `v0.1.0` are immutable. PyPI cannot edit 0.1.0
metadata; the license/classifier/URL corrections apply only to 0.1.1.

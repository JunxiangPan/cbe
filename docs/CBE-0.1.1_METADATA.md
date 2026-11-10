# CBE 0.1.1 metadata and licensing

Status: **released as 0.1.1; 0.1.0 remains immutable.**

- GitHub Release: <https://github.com/JunxiangPan/cbe/releases/tag/v0.1.1>
- PyPI: <https://pypi.org/project/cbe-review/0.1.1/>
- Tag: `v0.1.1` → `06f8f50`

## Distribution identity

```text
PyPI distribution: cbe-review
Import package:    cbe
Console command:   cbe
Version:           0.1.1
License:           Apache-2.0
```

`pip install cbe` installs the unrelated Crossroads Bank for Enterprises
package. Use `pip install cbe-review`; the import package and CLI remain
`cbe`.

## What changed in 0.1.1

- Added the Apache-2.0 `LICENSE`.
- Declared `license = "Apache-2.0"` and `license-files = ["LICENSE"]`.
- Added author/maintainer, classifiers, keywords, and project URLs.
- Rewrote the README entry point for external users.
- Added `--strict`, `--gate-job`, and local reusable-workflow recursion to
  `enforce-no-bypass`.

## 0.1.0 is immutable

PyPI does not allow metadata edits after upload. The 0.1.0 wheel and sdist
remain byte-identical to the published artifacts, and the `v0.1.0` tag remains
at `13f7ddc`. The corrected metadata applies only to 0.1.1 and later.

Published 0.1.0 identity:

```text
https://pypi.org/project/cbe-review/0.1.0/
wheel 87f0ad40a6cffdf4f9c657e6cc972a0f93787259c52445a1c112a5c7753599a7
sdist a77c653d178d5d0ab179da73c92184d9a54d5104ca5202f41574588979b68854
```

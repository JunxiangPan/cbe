# CBE 0.1.1 Release Smoke

Status: **PASS** — staged wheel installed into a clean venv before tagging.

## Wheel

```text
release/0.1.1/artifacts/cbe_review-0.1.1-py3-none-any.whl
sha256 b838e4366196933e043119614d982f5bebdf3cc9a3d382ce7a302b96fd882f58
```

## Install / metadata

```text
pip install <staged wheel>       PASS
cbe --version                    cbe 0.1.1
cbe --help                       PASS
validate-manifest --help         PASS
enforce-no-bypass --help         PASS
symbol-index --help              PASS
run-provider --help              PASS
emit-sarif --help                PASS
Name: cbe-review
Version: 0.1.1
License-Expression: Apache-2.0
License-File: LICENSE
```

`pip install cbe` remains the unrelated Crossroads Bank for Enterprises
package (PyPI author Aziz Baatout, version 0.1.8); the README warning is
correct.

## Functional checks

```text
--strict + dynamic if                  exit 3  UNVERIFIABLE_CONDITION
--gate-job '^security-gate$' + if:false exit 3 BYPASS_ATTEMPT
local uses ./.github/workflows/*.yml    exit 3  scans 2 workflows
remote uses + --strict                  exit 3  UNVERIFIABLE_REMOTE_WORKFLOW
```

No rebuild was performed for this smoke; the staged wheel was used.

# No-bypass mutation suite

Status: **P0 CBE-MUT-01**.

`run_mutations.py` runs the real `enforce-no-bypass` CLI against known bypass
shapes and records:

- expected reason
- expected exit code
- actual reason
- actual exit code
- PASS/non-PASS
- matched flag
- aggregate recall

The harness requires recall >= 0.95; the pytest wrapper asserts every mutant
is detected and none is reported as PASS.

Run:

```bash
python tests/mutation/run_mutations.py --output artifacts/mutation/cbe-0.2.0.json
pytest tests/mutation
```

Mutants:

1. `if: false` gate
2. commented-out gate job
3. ghost `needs`
4. `continue-on-error`
5. renamed gate via `--gate-job`
6. local reusable workflow shell
7. remote reusable workflow shell (`--strict`)
8. config disable
9. env disable
10. skip/disable comment

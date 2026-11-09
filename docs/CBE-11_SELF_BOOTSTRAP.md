# CBE-11 — self-bootstrap

Status: harness implemented; RC evidence uses an explicit bootstrap.

`tools/cbe_selfcheck.py` runs a baseline CBE interpreter against the current
manifest with:

```text
<baseline-python> -m cbe validate-manifest --manifest <current>
<baseline-python> -m cbe run-provider ... --all
```

- both commands must exit 0;
- a missing baseline interpreter exits 3 `PRECONDITION_FAIL`
  (`BASELINE_UNAVAILABLE`);
- baseline exit 2/3/4 makes the self-check exit 3 FAIL;
- `--bootstrap` is recorded in the result; it is not a stable-release claim.

## RC evidence

No previous stable CBE exists. The audit evidence uses two real baseline
executions:

1. a CBE 0.1.0 wheel built from an explicit source tree, installed in a temp
   venv, labeled `bootstrap=true`;
2. the committed CBE `70faad8` source tree added through
   `--baseline-pythonpath`, also labeled `bootstrap=true`.

Both exit 0. This proves the harness and packaging path, not F4 stable
compatibility. A future stable CBE release must be substituted before claiming
CBE-11 stable evidence.

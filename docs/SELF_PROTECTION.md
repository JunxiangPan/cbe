# CBE self-protection and external controls

Status: **CBE-side checks implemented; repository settings are external.**

## CBE-side self-protection

`security/SELF_PROTECTION.sha256` pins SHA256 for:

- `.github/workflows/cbe-e2e.yml`
- `.github/workflows/pypi-publish.yml`
- `src/cbe/commands/enforce_no_bypass.py`
- `src/cbe/manifest.py`
- `tools/cbe_contract_guard.py`

CI runs:

```bash
python tools/cbe_self_protect.py --check
```

A tampered file exits 3. Regenerate after an intentional protected-file change:

```bash
python tools/cbe_self_protect.py --write
```

The manifest is not self-protecting; it must be committed and reviewed with
the change.

## Required external settings

These cannot be enforced by CBE code and must be configured in GitHub:

1. Protect `main`:
   - require pull request review;
   - require status checks `e2e (ubuntu-latest)` and
     `e2e (windows-latest)`;
   - disallow force-push and deletion;
   - restrict who can push.
2. Protect tags `v*` (including `v0.1.0`, `v0.1.1`): disallow update/deletion.
3. Protect the `pypi` environment:
   - required reviewer;
   - only the release workflow may deploy;
   - trusted publisher limited to this repository/workflow.
4. Keep Actions allowlisted and pinned to full commit SHAs; do not allow
   arbitrary third-party actions by tag.
5. Use a scoped GitHub App/token for release automation; never a broad personal
   token.

## Actions pinning

`cbe-e2e.yml` and `pypi-publish.yml` use full commit SHAs for checkout,
setup-python, and PyPI publish. `tests/security/test_workflow_pins.py` fails if
a third-party `uses:` is a floating tag or a `self-hosted` runner appears.

## Limits

A repository administrator can change the workflow and the self-protection
manifest in the same commit. Branch protection, required review, and tag
protection are the controls that make that visible/blocked; CBE alone cannot
stop an admin with write access.

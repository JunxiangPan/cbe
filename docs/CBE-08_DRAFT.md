# CBE-08 DRAFT — F2 denominator against frozen CBS contract/v1.7.1

Status: **DRAFT — NOT PASS**

- Contract ref: CBS frozen tag `contract-v1.7.1` at commit
  `c2b5e9292552685cc40bd21b3ac2252847856715` (`c2b5e9`)
- Freeze baseline: `6835789`
- Contract SHA256:
  `209d75b4c900f9a2d1ad8f5c377ac1b8a868cf3e4cd449970e61e3ff380c18f1`
- `vm-proof.yml` has no conflict markers.
- **Blocking instruction:** `docs/v1.7/FREEZE_NOTICE.md` says
  **“CBE-08 remains DRAFT; do not report PASS.”** CBE therefore keeps DRAFT
  even though the contract is frozen. This is not a missing freeze.

## Draft assertions (not evidence of CBE-08 PASS)

`tools/cbe08_draft.py` records the current F2 behavior:

| Case | Observed | Contract expectation |
|---|---|---|
| 5 advisory rules, 1 exemption | applicable 5, skip 1, ratio 0.2, exit 0 | 20% passes |
| blocking rule + blocking exemption | exit 3, `blocking_skip=true` | blocking may not SKIP |
| zero rules | exit 3 `NO_RULES` | zero rules is a gate failure |

The script emits `"status": "DRAFT"`, `"not_pass": true`,
`"contract_status": "FROZEN_BY_TAG"`, and
`"cbe08_blocked_by": "CBS FREEZE_NOTICE says CBE-08 remains DRAFT; do not report PASS"`.
It is not included in the E2E pass count and must not be quoted as CBE-08 PASS.

## Contract guard

`tests/e2e/fixtures/contract/v1.7.1-pin.json` pins the immutable tag
`contract-v1.7.1`, not the moving branch:

```text
repo:              JunxiangPan/Cyber-Butler-Security
ref_type:          tag
tag:               contract-v1.7.1
commit:            c2b5e9292552685cc40bd21b3ac2252847856715
contract_sha256:   209d75b4c900f9a2d1ad8f5c377ac1b8a868cf3e4cd449970e61e3ff380c18f1
frozen:            true
```

`tools/cbe_contract_guard.py` resolves the annotated tag to its commit and
fetches the contract and `vm-proof.yml` from that commit. It exits 0 `PINNED`
only when the tag commit, contract hash, and vm-proof cleanliness all match;
otherwise it exits 3 `CONTRACT_CHANGED`.

## Flip rule

CBE-08 cannot become PASS while the frozen `FREEZE_NOTICE.md` says it must
remain DRAFT. A CBS correction to that notice is required first. If the
corrected notice allows the flip, rerun the F2 assertions against the frozen
hash and record the result; do not merely relabel this draft.

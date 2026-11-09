# CBE-08 PASS — F2 denominator against frozen CBS contract/v1.7.1

Status: **PASS**

- Contract: frozen tag `contract-v1.7.1` at commit
  `c2b5e9292552685cc40bd21b3ac2252847856715`
- Contract SHA256:
  `209d75b4c900f9a2d1ad8f5c377ac1b8a868cf3e4cd449970e61e3ff380c18f1`
- Addendum: `FREEZE_NOTICE_ADDENDUM.md` at commit
  `e318cbdac748a3a88057bd882e897f50c364bd97`
- Addendum SHA256:
  `51604f56b18cdd2fe388c9ca0e9977f703d32fb15c684f73a172b9380eb5faaf`
- The addendum authorizes CBE-08 evaluation against `contract-v1.7.1` /
  `209d75b4` and permits PASS when the four frozen F2 checks match.
- `CONTRACT.md` and the tag were unchanged; no CBE/CBP/CBM/CBC repository was
  modified by CBS.

## Frozen F2 checks

`tools/cbe08_draft.py` ran against the frozen contract:

| Check | Expected | Observed | Result |
|---|---|---|---|
| `five_advisory_valid` | 0 | 0 | PASS |
| `non_blocking_1_of_5_skip` | 0 | 0 | PASS |
| `blocking_skip_exits_3` | 3 | 3 | PASS |
| `zero_rules_exits_3` | 3 | 3 | PASS |

All four match; `failed_checks=[]`.

Evidence:
- `artifacts/rc-0.1.0/evidence/cbe-08-frozen.json`

## Guard

`tests/e2e/fixtures/contract/v1.7.1-pin.json` pins the immutable tag and the
addendum commit/hash. `tools/cbe_contract_guard.py` resolves the annotated tag,
verifies the addendum authorization phrase, and fails with `CONTRACT_CHANGED`
on tag, contract, vm-proof, addendum hash, or authorization drift.

`PINNED` is not CBE-08 PASS by itself; the PASS above additionally requires the
four frozen F2 checks to match. No other CBE-08 exemption is granted.

## Release boundary

CBE 0.1.0 remains an RC candidate: no tag, no GitHub release, no PyPI upload.

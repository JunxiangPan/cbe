# CBE-08 DRAFT — F2 denominator against CBS contract/v1.7.1 RC

Status: **DRAFT — NOT PASS**

- Contract ref: CBS `contract/v1.7.1` RC2 commit
  `683578964fb14518b2bd81d3fd49766b66feb851` (`6835789`)
- Declared candidate SHA256 in `docs/v1.7/RC_STATUS.md`:
  `209d75b4c900f9a2d1ad8f5c377ac1b8a868cf3e4cd449970e61e3ff380c18f1`
- Observed raw SHA256 of `docs/v1.7/CONTRACT.md` at `6835789`:
  `209d75b4c900f9a2d1ad8f5c377ac1b8a868cf3e4cd449970e61e3ff380c18f1`
- The hashes match, and `vm-proof.yml` has no conflict markers. The contract
  still says **RC2, NOT FROZEN**; human freeze has not happened. CBE-08 remains
  DRAFT.

## Draft assertions (not evidence of CBE-08 PASS)

`tools/cbe08_draft.py` records the current F2 behavior:

| Case | Observed | RC expectation |
|---|---|---|
| 5 advisory rules, 1 exemption | applicable 5, skip 1, ratio 0.2, exit 0 | 20% passes |
| blocking rule + blocking exemption | exit 3, `blocking_skip=true` | blocking may not SKIP |
| zero rules | exit 3 `NO_RULES` | zero rules is a gate failure |

The script always emits `"status": "DRAFT"`, `"not_pass": true`,
`"contract_hash_match": true`, and `"contract_status": "RC2_NOT_FROZEN"`. It is
not included in the E2E pass count and must not be quoted as CBE-08 PASS.

## Contract hash guard

`tests/e2e/fixtures/contract/v1.7.1-pin.json` pins:

```text
repo:              JunxiangPan/Cyber-Butler-Security
branch:            contract/v1.7.1
commit:            683578964fb14518b2bd81d3fd49766b66feb851
contract_sha256:   209d75b4c900f9a2d1ad8f5c377ac1b8a868cf3e4cd449970e61e3ff380c18f1
frozen:            false
```

`tools/cbe_contract_guard.py` fetches the current branch head, the contract
bytes at that head, and `vm-proof.yml`. It exits 0 `PINNED` only when the commit,
contract hash, and vm-proof cleanliness all match; otherwise it exits 3
`CONTRACT_CHANGED` with the pinned/observed values and an update action.

`tests/e2e/test_cbe_08_contract_guard.py` asserts the pinned case and simulates
a moved commit and a changed contract hash. A passing guard means the pin is
intact; it is **not** CBE-08 PASS.

## Freeze rule

CBE-08 becomes PASS only after CBS freezes the contract and a human audit
confirms the final F2 blocking set against these assertions. If the frozen set
differs, rewrite fixtures and assertions — do not relabel this draft.

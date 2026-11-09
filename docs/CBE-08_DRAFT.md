# CBE-08 DRAFT — F2 denominator against CBS contract/v1.7.1 RC

Status: **DRAFT — NOT PASS**

- Contract ref: CBS `contract/v1.7.1` commit
  `3de93aed99cf81c4408cb160dcf5846a8d2bacfe` (`3de93ae`)
- Declared candidate SHA256 in `docs/v1.7/RC_STATUS.md`:
  `c1653cfe1adbc74d2523d2fa12c965ab761fce978061c8e55443eb8b6db3a7e5`
- Observed raw SHA256 of `docs/v1.7/CONTRACT.md` at `3de93ae`:
  `c1653cfe1adbc74d2523d2fa12c965ab761fce978061c8e55443eb8b6db3a7e5`
- The hashes now match, and `vm-proof.yml` has no conflict markers. The contract
  still says **RC, NOT FROZEN**; human freeze has not happened. CBE-08 remains
  DRAFT.

## Draft assertions (not evidence of CBE-08 PASS)

`tools/cbe08_draft.py` records the current F2 behavior:

| Case | Observed | RC expectation |
|---|---|---|
| 5 advisory rules, 1 exemption | applicable 5, skip 1, ratio 0.2, exit 0 | 20% passes |
| blocking rule + blocking exemption | exit 3, `blocking_skip=true` | blocking may not SKIP |
| zero rules | exit 3 `NO_RULES` | zero rules is a gate failure |

The script always emits `"status": "DRAFT"`, `"not_pass": true`,
`"contract_hash_match": true`, and `"contract_status": "RC_NOT_FROZEN"`. It is
not included in the E2E pass count and must not be quoted as CBE-08 PASS.

## Freeze rule

CBE-08 becomes PASS only after CBS freezes the contract and a human audit
confirms the final F2 blocking set against these assertions. If the frozen set
differs, rewrite fixtures and assertions — do not relabel this draft.

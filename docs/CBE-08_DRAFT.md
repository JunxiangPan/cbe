# CBE-08 DRAFT — F2 denominator against CBS contract/v1.7.1 RC

Status: **DRAFT — NOT PASS**

- Contract ref: CBS `contract/v1.7.1` commit `04c9f8b`
- Declared candidate SHA256 in `docs/v1.7/RC_STATUS.md`:
  `19b37fd4f2def25a6945bd59affae3128fe466cc0bfd1809d522ba8291b3c12b`
- Observed raw SHA256 of `docs/v1.7/CONTRACT.md` at `04c9f8b`:
  `c1653cfe1adbc74d2523d2fa12c965ab761fce978061c8e55443eb8b6db3a7e5`
- The two hashes do not match. `vm-proof.yml` at the same commit still contains
  Git conflict markers. The contract is a candidate, not a frozen contract.

## Draft assertions (not evidence of CBE-08 PASS)

`tools/cbe08_draft.py` records the current F2 behavior:

| Case | Observed | RC expectation |
|---|---|---|
| 5 advisory rules, 1 exemption | applicable 5, skip 1, ratio 0.2, exit 0 | 20% passes |
| blocking rule + blocking exemption | exit 3, `blocking_skip=true` | blocking may not SKIP |
| zero rules | exit 3 `NO_RULES` | zero rules is a gate failure |

The script always emits `"status": "DRAFT"` and `"not_pass": true`. It is not
included in the E2E pass count and must not be quoted as CBE-08 PASS.

## Freeze rule

CBE-08 becomes PASS only after CBS freezes the contract, the declared and
observed hashes agree, the `vm-proof.yml` conflict is resolved, and the final F2
blocking set is checked against these assertions. If the frozen set differs,
rewrite fixtures and assertions — do not relabel this draft.

# Skip-ratio early-warning proposal

Status: **CBE-local warnings only; 20% contract threshold unchanged.**

The frozen F2 threshold remains:

```text
skip_ratio > 0.20  -> exit 4
skip_ratio == 0.20 -> not exit 4
```

CBE 0.2.0 adds non-blocking warnings at 10% and 15% so a release owner sees
risk before the hard threshold:

- `SKIP_RATIO_EARLY_WARNING_10`
- `SKIP_RATIO_EARLY_WARNING_15`

These warnings do not change `exit_code`, `gate_status`, the denominator, or
the 20% value. They are not a unilateral tightening.

## Suggested CBS amendment

If CBS wants early warning to be contract-visible, the amendment should define
whether the warning is report metadata, a non-blocking observation, or a
separate signal. CBE will not add report fields without that amendment, because
the CBE report schema is frozen.

# CBE-10 — F5/F6 release train and CBP 1.2.0 manifest fields

Status: implemented.

`tools/cbe_train.py` reads a `release-train.json` and produces JSON plus a
Markdown body fragment:

- `SKIPPED_INFRA` -> exit 3 `SKIPPED_INFRA`, dedicated Infrastructure failures
  section, never PASS, never counted in the 20% denominator.
- `NOT_UPLOADED` -> visible, not PASS, not SKIP, not counted; does not block
  CBS by itself. If `declared_attached=true`, the exact phrase
  `declared as attached but not uploaded` is emitted.
- `EVIDENCE_ABSENT` -> visible; not converted to `- none`.
- `skip_count=0`, `applicable_count=0`, `counted_in_skip_denominator=false` for
  the release-train section; CBM/CBC are not part of the CBE F2 denominator.

## CBP 1.2.0 RC fields

The optional `--cbp-manifest` check follows CBP 1.2.0 RC code `5da8b87`:

- `body_hash_scope` must be exactly `base`; `full` exits 2.
- `artifact_repository` is a non-empty `owner/repo` string. The CBS v1.7.1 RC
  contract currently sketches an object; CBE rejects the object against the
  CBP 1.2.0 shape and records the mismatch instead of inventing a union type.
- `cbc-event` is an event stream (`cbc-event-dir`, JSONL hash chain), not a
  manifest field. A private `cbc_event` manifest key is rejected as unexpected;
  CBE does not define a private variant.

This module is a CBE-side consumer/compatibility check, not a replacement for
CBP 1.2.0's own validator.

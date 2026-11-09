# CBE-10 — F5/F6 release train and contract RC2 manifest fields

Status: implemented; RC2 object shape fixture-tested, CBP 1.2.2 adoption pending.

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

## Contract RC2 fields

The optional `--cbp-manifest` check follows frozen contract RC2
(`contract-v1.7.1` / `c2b5e9`):

- `schema_version` must be the string `"1"`; numeric `1` is rejected.
- `body_hash_scope` must be exactly `base`; `full` exits 2.
- `artifact_repository` is the object
  `{repository, run_id, artifact_name}`. A bare `owner/repo` string, a missing
  `run_id`, or an unqualified artifact name is rejected.
- `cbc-event` is an event stream (`cbc-event-dir`, JSONL hash chain), not a
  manifest field. A private `cbc_event` manifest key is rejected as unexpected;
  CBE does not define a private variant.

CBP 1.2.2 is released. CBE validates its real `quality-manifest.json` (sha256
`228594d0…`) with the object `artifact_repository`; the `cbp-action==1.2.2`
pin is used. This is CBE's manifest-consumption check, not a claim that CBE
performed CBP's own gate PASS. This module is a CBE-side
consumer/compatibility check, not a replacement for CBP's own validator.

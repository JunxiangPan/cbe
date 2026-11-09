# CBE-09 — F4 baseline selection

Status: implemented; no stable CBE release exists yet.

`tools/cbe_baseline.py` selects a previous stable release from a
`releases.json` snapshot:

- stable `vX.Y.Z` only; prereleases are excluded;
- no machine-readable ERRATUM (`body` beginning `ERRATUM:` or `erratum` label);
- CBE gate PASS; CBP gate PASS when CBP evidence is present;
- not the current version;
- highest SemVer wins, then `published_at`.

If no candidate exists and `--baseline` is absent, the tool exits 3 with
`gate_status=PRECONDITION_FAIL` and `error.code=NO_ELIGIBLE_BASELINE`.
`--baseline vX.Y.Z` records `source=explicit_tag`; a 40-hex commit records
`source=explicit_commit` and says `bootstrap`, not stable. Using the current
version as the explicit baseline exits 2.

## RC evidence

There is no stable CBE release and no tag at the time of this RC. The audit
therefore records only:

- selector logic against committed fixtures (`v0.0.9` selected for `v0.1.0`);
- no-eligible case exits 3 `PRECONDITION_FAIL`;
- explicit commit bootstrap, explicitly labeled as bootstrap.

This is not a claim that CBE-09 has a real previous stable release. F4 stable
selection becomes real only after a CBE release is published and passes its
gates.

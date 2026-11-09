# CBM-scoped CBE report — CBM v0.1.0

Status: **REAL REPORT GENERATED; CBM identity accepted; B2 NOT CLAIMED AS PASS.**

This directory contains a CBM-scoped CBE report produced by the released
CBE 0.1.0 code against the real CBM source tree.

## Source and identity

```text
CBM source commit:   f605808a89d334b5458c38f92201583004b6fff0
CBM source tar sha256: e1d7f40fa483211b2f3ab882dd2fde575b9206826e2c90e74306c18fe28a0518
CBM version:         0.1.0
CBM tag:             none currently in the CBM repository
CBE version:         0.1.0 (release tag v0.1.0 -> 13f7ddc)
Report package_id:   cbm
Report producer_id:  cbe
Report version:      v0.1.0
Report tag:          v0.1.0
Report gate_status:  PASS
```

CBM currently has **no `v0.1.0` tag**; the report pins the real source commit
`f605808`. The `tag: v0.1.0` field is the target release identity required by
the CBM intake, not a claim that a CBM tag exists.

## How it was run

1. Exported the real CBM source tree at `f605808` with `git archive`.
2. Ran the real `gitleaks 8.30.1` scanner against that tree; no leaks found.
3. Ran `tools/cbe_gate.py` with a CBE-owned CBM scope manifest:
   - `CBE-SECRET-001` (blocking) → real gitleaks SARIF provider
   - `CBE-QUALITY-001` (advisory) → builtin manifest provider
4. Validated the resulting report with real CBM code
   (`cbm_attach.reports.load_report` + `identity_errors`).

CBM has no CBE rule-pack manifest of its own. The manifest
`cbe-rule-pack.json` is therefore a **CBE-owned CBM scope projection** using
CBE's real rule IDs; it is not represented as a CBM-provided upstream pack.
The report itself is generated output, not a hand-written fixture.

## Results

```text
CBE report sha256:       6b4dc1efd8433535efe70d4de9337910aa537fbcc982ebba3a014284f27fc76e
evidence_sha256:         1367f74cd3eadc3461d1f4805acb8c591003853eeb27fe63c9416ae439217cd3
rules_manifest_hash:     eeade50e538b418c74168d6b6019f82cddeab439c0765a970b24024a09abc076
applicable_count:        1
skip_count:              0
skip_ratio:              0.0
blocking_skip:           false
warn_count:              0
gitleaks findings:       0
CBM identity_errors:     []
```

CBM validation:

```text
CBE cbm cbe v0.1.0 v0.1.0 PASS
CBP cbm cbp v0.1.0
identity_errors []
```

## Artifacts

| File | SHA256 |
|---|---|
| `report/cbe-report.json` | `6b4dc1efd8433535efe70d4de9337910aa537fbcc982ebba3a014284f27fc76e` |
| `report/cbe.sarif` | `52caa776c054557d3992035dfbe6551128c7d90dd0d50576e299dbdce6673b05` |
| `report/cbe-body-section.md` | `beb972aece5bd84f6224b77a6649357b2a9315112ee80dd85c5f402c42c718af` |
| `cbe-rule-pack.json` | `450c27e87e770a887c12923a4ff93f56f085166ff976f86c037a28b008936470` |
| `validation.json` | generated CBM identity validation |

## Tools

```text
gitleaks:  8.30.1
binary:    D:/tmp/gitleaks-8.30.1/gitleaks.exe
binary sha256: 17157e2ee8b76fc8b1d8bee607a250e34b8a8023c8bc81822d4b5ee4d78fcb7c
zip sha256:    d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e
```

CBM CBP manifest used for identity validation:
`b41798f07be4dda35e2afa1a810381bcd6f5025fb5d33f5c5a1054834a390c82`
(`cbm-quality-manifest.json`, package `cbm`, producer `cbp`, v0.1.0).

## Boundaries

- No CBM repository files were modified.
- No CBM tag/release was created or moved.
- B2/B4 are **not** declared PASS; CBM must run its own RC gate.
- No PyPI upload; old `cbe` name is never used.
- CBE release tag `v0.1.0` was not moved.

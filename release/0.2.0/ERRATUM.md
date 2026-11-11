# CBE 0.2.0 — ERRATUM

Status: **ERRATUM — tag and published assets are intentionally left unchanged.**

CBE 0.2.0 has a staging/tag metadata inconsistency. This is a documentation
erratum, not a new release.

## Facts

```text
v0.2.0 tag:                 8c1452ed99c4a1010eba2ecd632c837007e22df1
tag staging wheel SHA256:   cb4c07ea316836b63f8c9c9538417fb430ab82021d8a6ca10d713add79ab01bc
tag staging sdist SHA256:   d04b60e0b0cf057370d23c042b6c48f8ac150d75a957c73d288ef69de3e77bdf

GitHub Release wheel SHA256: d9acbefaaf14172ce1d4fda50bf49007c13e443a1988de16bc125be3d1daac91
GitHub Release sdist SHA256: e4c5cdb28ee91a0732cf1d43193c785e5c3feeff7b73924454d69690da61cf9f
PyPI 0.2.0 wheel:            d9acbefaaf14172ce1d4fda50bf49007c13e443a1988de16bc125be3d1daac91
PyPI 0.2.0 sdist:            e4c5cdb28ee91a0732cf1d43193c785e5c3feeff7b73924454d69690da61cf9f
```

The `v0.2.0` tag's `release/0.2.0/RELEASE_MANIFEST.json` still records the
pre-release staging hashes (`cb4c...` / `d04b...`). The published GitHub
Release and PyPI artifacts use the signed build hashes (`d9ac...` / `e4c5...`).

## Decision

**Option B — mark 0.2.0 as ERRATUM. No 0.2.1 is created for this issue.**

- `v0.2.0` tag is **not moved**.
- Published 0.2.0 assets are **not rewritten**.
- No new tag/release/PyPI upload is made for this erratum.
- Consumers must verify the GitHub Release/PyPI artifacts and the signed
  `release-manifest.json`, not the tag's stale staging manifest.

The tag commit is immutable history. The post-tag `main` branch records the
actual released hashes, but that does not change the tag.

## Signed release assets

The GitHub/PyPI 0.2.0 artifacts are the signed ones. Sigstore keyless bundles
and SLSA attestations remain the production signatures; the tag staging
artifacts are not release artifacts and must not be treated as signed release
payloads.

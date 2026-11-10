# CBE threat model

Status: **CBE is a release-integrity gate, not a runtime security boundary.**

## What CBE is designed to catch

- Misconfigured or accidentally disabled rules.
- Low-level bypass attempts in config, comments, environment, and workflow
  files (`disable`, `skip`, `continue-on-error`, `|| true`).
- A gate job that is unreachable through `if: false`, a false literal, a
  missing `needs` target, or a commented-out job.
- A renamed gate when the caller supplies the correct `--gate-job` regex.
- A local reusable workflow whose delegated gate is skipped.
- A remote reusable workflow that cannot be fetched or verified, when
  `--strict` is used.
- Drift in the frozen CBE contract, schema, or self-protection manifest.

## What CBE does not defend against

- A malicious repository administrator with write access. They can change
  workflows, the rule pack, the gate wrapper, or this document.
- A stolen GitHub token or a compromised CI runner. CBE checks the workspace
  it is given; it cannot attest the runner's integrity.
- Runtime data exfiltration, malicious dependencies executing during install,
  or compromised provider binaries. CBE invokes providers; it does not sandbox
  them.
- A malicious upstream that controls both the artifact and the reports used to
  attest it.
- Remote reusable workflows that are unavailable, private, rate-limited, or
  authenticated differently. These are `UNVERIFIABLE_REMOTE_WORKFLOW`; they are
  never upgraded to “verified” by a warning.
- Branch-protection, required-check, environment-review, or PyPI trusted
  publisher configuration. Those are external controls (see
  `docs/SELF_PROTECTION.md`).

## Trust roots

- The repository’s protected branch and required CI check are the first trust
  root.
- The pinned CBS contract tag/hash and the CBE report schema are external
  contract roots.
- The sidecar public key, if used, is an external signing root. Without a
  production signing identity, CBE ships only the schema/verifier and reports
  `BLOCKED_NO_SIGNING_IDENTITY`; it does not fabricate signatures.
- GitHub Release/PyPI permissions are distribution roots, not proof that the
  code is safe.

## Remote workflow limitation

`--fetch-remote` is opt-in. Fetched remote workflows are scanned recursively,
but CBE does not claim that a remote workflow is trustworthy merely because it
was fetched. Unfetched, unauthenticated, or unreachable remote workflows remain
unverifiable; `--strict` turns them into exit 3.

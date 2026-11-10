# Package name and PyPI policy

Status: **`cbe-review` is the only distribution this project may upload.**

## Facts

- PyPI project `cbe` is owned by a different project:
  - author: Aziz Baatout
  - version: 0.1.8
  - purpose: Crossroads Bank for Enterprises (CBE/BCE/KBO/ZDU)
  - URL: <https://pypi.org/project/cbe/>
- `cbe-review` is this project:
  - import package / CLI: `cbe`
  - URL: <https://pypi.org/project/cbe-review/>
- `pip install cbe` installs the unrelated project. Every README and release
  warning says so.

## Policy

- Never upload the `cbe` distribution name.
- Never add a dependency, alias, or metadata field that redirects users to the
  other project.
- Keep the product identity as “CBE — Cyber-Butler Enforcement gate” while the
  distribution remains `cbe-review`.

## PyPI dispute/name options (research summary)

PyPI does not offer a general “reserve this name for later” mechanism. Name
disputes are handled under PEP 541; a transfer request normally requires a
concrete claim such as trademark/ownership or confusingly similar naming, not
mere inactivity. This project has no such claim and will not file a dispute.

If a different distribution name is ever required, choose a distinct name
(e.g. another `cbe-*` name), rebuild, and re-audit. Do not rename the existing
published artifacts.

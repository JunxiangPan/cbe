"""Deterministic, bounded source-tree walking for CBE commands."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Iterable, Iterator

from .errors import GateError, InputError

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".pytest-tmp",
    ".mypy_cache",
    "dist",
    "build",
    "out",
    "release-assets",
}

TEXT_EXTENSIONS = {
    ".py",
    ".pyi",
    ".ps1",
    ".psm1",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".cs",
    ".rb",
    ".sh",
    ".bash",
    ".zsh",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".ini",
    ".cfg",
    ".conf",
    ".txt",
}


def resolve_source_root(path: str | Path) -> Path:
    root = Path(path).resolve()
    if not root.is_dir():
        raise InputError("SOURCE_ROOT_NOT_FOUND", f"source root is not a directory: {path}")
    return root


def _relative_posix(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _matches_any(relative: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(relative, pattern) or fnmatch.fnmatch(Path(relative).name, pattern) for pattern in patterns)


def iter_source_files(
    root: str | Path,
    *,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
    max_bytes: int = 2_000_000,
) -> Iterator[Path]:
    """Yield text-like files under root in deterministic POSIX-path order.

    Symlinks that resolve outside root are a gate failure, not a silent skip.
    Directories are never followed through symlinks.
    """

    root_path = resolve_source_root(root)
    includes = list(include or ["*"])
    excludes = list(exclude or [])
    found: list[Path] = []

    for current, dirnames, filenames in os.walk(root_path, followlinks=False):
        current_path = Path(current)
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in DEFAULT_EXCLUDED_DIRS
            and not _matches_any(_relative_posix(root_path, current_path / name) + "/", excludes)
        )
        for name in sorted(filenames):
            path = current_path / name
            relative = _relative_posix(root_path, path)
            if _matches_any(relative, excludes):
                continue
            if not _matches_any(relative, includes):
                continue
            if path.is_symlink():
                try:
                    target = path.resolve(strict=True)
                except OSError as exc:
                    raise GateError("SYMLINK_BROKEN", f"broken symlink: {relative}: {exc}") from exc
                if not target.is_relative_to(root_path):
                    raise GateError("SYMLINK_ESCAPE", f"symlink escapes source root: {relative}")
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                if path.stat().st_size > max_bytes:
                    continue
            except OSError as exc:
                raise InputError("FILE_STAT_FAILED", f"cannot stat {relative}: {exc}") from exc
            found.append(path)

    for path in sorted(found, key=lambda item: _relative_posix(root_path, item)):
        yield path


def read_text(path: Path) -> str | None:
    """Read UTF-8 text; return None for binary or undecodable files."""

    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def workflow_files(root: str | Path) -> list[Path]:
    root_path = resolve_source_root(root)
    directory = root_path / ".github" / "workflows"
    if not directory.is_dir():
        return []
    files = [
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    ]
    return sorted(files, key=lambda item: item.name)


def is_cbe_repository(root: str | Path) -> bool:
    """Detect the CBE repository for the self-workflow guard.

    The check is intentionally narrow: a pyproject.toml naming the project
    `cbe` plus the CBE CLI package. A target repository that merely contains a
    `cbe` string is not treated as CBE.
    """

    root_path = Path(root).resolve()
    pyproject = root_path / "pyproject.toml"
    if not pyproject.is_file() or not (root_path / "src" / "cbe" / "cli.py").is_file():
        return False
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return False
    return any(line.strip().replace('"', "").replace("'", "") == "name = cbe" for line in text.splitlines())


def exclude_matches(relative: str, patterns: Iterable[str]) -> bool:
    return _matches_any(relative, patterns)

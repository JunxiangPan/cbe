"""Deterministic symbol index for CBE coverage evidence (P0-05)."""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from ..errors import GateError, InputError
from ..jsonio import sha256_json, write_json_atomic
from ..walk import iter_source_files, resolve_source_root

LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".pyi": "python",
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cs": "csharp",
    ".rb": "ruby",
    ".sh": "shell",
    ".bash": "shell",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".toml": "toml",
    ".json": "json",
    ".md": "markdown",
    ".txt": "text",
}

POWERSHELL_SYMBOL_RE = re.compile(r"^\s*(?:function|class|enum)\s+([A-Za-z_][A-Za-z0-9_-]*)", re.IGNORECASE)
JS_SYMBOL_RE = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][A-Za-z0-9_$]*)")


@dataclass
class Symbol:
    name: str
    qualified_name: str
    kind: str
    line: int
    column: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "qualified_name": self.qualified_name,
            "kind": self.kind,
            "line": self.line,
            "column": self.column,
        }


@dataclass
class FileIndex:
    path: str
    sha256: str
    language: str
    symbols: list[Symbol] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "language": self.language,
            "symbols": [symbol.as_dict() for symbol in self.symbols],
        }


def _language_for(path: Path) -> str:
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "unknown")


def _python_symbols(text: str, relative: str, warnings: list[dict[str, Any]]) -> list[Symbol]:
    try:
        tree = ast.parse(text, filename=relative)
    except SyntaxError as exc:
        warnings.append(
            {
                "code": "PYTHON_PARSE_FAILED",
                "path": relative,
                "line": exc.lineno or 0,
                "message": str(exc),
            }
        )
        return []

    symbols: list[Symbol] = []

    def visit(node: ast.AST, prefix: str) -> None:
        for child in getattr(node, "body", []):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = child.name
                symbols.append(
                    Symbol(
                        name=name,
                        qualified_name=f"{prefix}.{name}" if prefix else name,
                        kind="function",
                        line=child.lineno,
                        column=child.col_offset + 1,
                    )
                )
                visit(child, f"{prefix}.{name}" if prefix else name)
            elif isinstance(child, ast.ClassDef):
                name = child.name
                symbols.append(
                    Symbol(
                        name=name,
                        qualified_name=f"{prefix}.{name}" if prefix else name,
                        kind="class",
                        line=child.lineno,
                        column=child.col_offset + 1,
                    )
                )
                visit(child, f"{prefix}.{name}" if prefix else name)

    visit(tree, "")
    return sorted(symbols, key=lambda item: (item.line, item.column, item.qualified_name))


def _regex_symbols(text: str, pattern: re.Pattern[str], kind: str) -> list[Symbol]:
    symbols: list[Symbol] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = pattern.match(line)
        if match:
            name = match.group(1)
            symbols.append(
                Symbol(name=name, qualified_name=name, kind=kind, line=line_no, column=match.start(1) + 1)
            )
    return sorted(symbols, key=lambda item: (item.line, item.column, item.qualified_name))


def build_index(
    source_root: str | Path,
    *,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
    languages: Iterable[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = resolve_source_root(source_root)
    selected_languages = set(languages or [])
    warnings: list[dict[str, Any]] = []
    files: list[FileIndex] = []

    for path in iter_source_files(root, include=include, exclude=exclude):
        language = _language_for(path)
        if selected_languages and language not in selected_languages:
            continue
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise GateError("SOURCE_READ_FAILED", f"cannot read {path}: {exc}") from exc
        text = raw.decode("utf-8", errors="replace")
        relative = path.relative_to(root).as_posix()
        symbols: list[Symbol] = []
        if language == "python":
            symbols = _python_symbols(text, relative, warnings)
        elif language == "powershell":
            symbols = _regex_symbols(text, POWERSHELL_SYMBOL_RE, "function")
        elif language in {"javascript", "typescript"}:
            symbols = _regex_symbols(text, JS_SYMBOL_RE, "function")
        files.append(
            FileIndex(
                path=relative,
                sha256=hashlib.sha256(raw).hexdigest(),
                language=language,
                symbols=symbols,
            )
        )

    index = {
        "schema_version": "1",
        "source_root": ".",
        "files": [item.as_dict() for item in sorted(files, key=lambda item: item.path)],
    }
    if not index["files"]:
        raise GateError("NO_SOURCE_FILES", "symbol index found no source files")
    return index, warnings


def add_arguments(parser: argparse.ArgumentParser) -> None:
    return None


def run(args: argparse.Namespace) -> dict[str, Any]:
    index, warnings = build_index(
        args.source_root,
        include=args.include,
        exclude=args.exclude,
        languages=args.language,
    )
    output = Path(args.out)
    try:
        write_json_atomic(output, index)
    except OSError as exc:
        raise InputError("INDEX_WRITE_FAILED", f"cannot write {output}: {exc}") from exc

    file_count = len(index["files"])
    symbol_count = sum(len(item["symbols"]) for item in index["files"])
    languages: dict[str, int] = {}
    for item in index["files"]:
        languages[item["language"]] = languages.get(item["language"], 0) + 1

    return {
        "schema_version": "1",
        "command": "symbol-index",
        "ok": True,
        "exit_code": 0,
        "gate_status": "PASS",
        "source_root": str(args.source_root),
        "index_path": str(output),
        "index_sha256": sha256_json(index),
        "file_count": file_count,
        "symbol_count": symbol_count,
        "languages": dict(sorted(languages.items())),
        "excluded_count": 0,
        "symlink_skipped_count": 0,
        "warnings": warnings,
        "error": None,
    }

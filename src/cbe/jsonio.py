"""Bounded, deterministic JSON I/O for CBE."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from .errors import InputError


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: str | Path) -> Any:
    """Read strict UTF-8 JSON, rejecting BOM, duplicate keys, and trailing data."""

    try:
        if str(path) == "-":
            raw = sys.stdin.buffer.read()
            label = "<stdin>"
        else:
            raw = Path(path).read_bytes()
            label = str(path)
    except FileNotFoundError as exc:
        raise InputError("FILE_NOT_FOUND", f"input file not found: {path}") from exc
    except OSError as exc:
        raise InputError("FILE_READ_FAILED", f"cannot read {path}: {exc}") from exc

    if raw.startswith(b"\xef\xbb\xbf"):
        raise InputError("BOM_NOT_ALLOWED", f"{label} starts with a UTF-8 BOM")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError("UTF8_REQUIRED", f"{label} is not valid UTF-8: {exc}") from exc

    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except ValueError as exc:
        raise InputError("JSON_INVALID", f"{label} is not valid JSON: {exc}") from exc


def canonical_json(value: Any) -> str:
    """Canonical JSON for hashing.

    For the manifest subset (objects, arrays, strings, integers, booleans, null)
    this is equivalent to RFC 8785 ordering and separators. Floats are rejected
    so a manifest cannot acquire an implementation-specific number spelling.
    """

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise InputError("CANONICAL_JSON_FAILED", f"value cannot be canonicalized: {exc}") from exc


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_json(value: Any) -> str:
    return sha256_text(canonical_json(value))


def sha256_file(path: str | Path) -> str:
    try:
        return sha256_bytes(Path(path).read_bytes())
    except OSError as exc:
        raise InputError("FILE_READ_FAILED", f"cannot read {path}: {exc}") from exc


def write_json_atomic(path: str | Path, value: Any) -> None:
    """Write a JSON document atomically in the target directory."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, target)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def print_json(value: Any) -> None:
    sys.stdout.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.flush()


def apply_writer(writer: Callable[[Any], None], value: Any) -> None:
    writer(value)

"""Command skeleton helpers."""

from __future__ import annotations

from typing import Any

from ..errors import NotImplementedCommand


def not_implemented(command: str) -> dict[str, Any]:
    raise NotImplementedCommand(command)

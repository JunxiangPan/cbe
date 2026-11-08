"""emit-sarif command skeleton."""

from __future__ import annotations

import argparse
from typing import Any

from .common import not_implemented

COMMAND = "emit-sarif"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    return None


def run(args: argparse.Namespace) -> dict[str, Any]:
    return not_implemented(COMMAND)

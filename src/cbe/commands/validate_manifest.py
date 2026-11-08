"""validate-manifest command skeleton."""

from __future__ import annotations

import argparse
from typing import Any

from .common import not_implemented

COMMAND = "validate-manifest"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    # Arguments are added centrally by cbe.cli so the skeleton stays readable.
    return None


def run(args: argparse.Namespace) -> dict[str, Any]:
    return not_implemented(COMMAND)

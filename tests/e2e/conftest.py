"""Shared E2E fixtures."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture
def outside_tmp() -> Iterator[Path]:
    """A temp directory outside the repo, so --out-dir never sits in source root."""

    path = Path(tempfile.mkdtemp(prefix="cbe-e2e-"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)

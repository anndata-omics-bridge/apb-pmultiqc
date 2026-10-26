"""Canonical synthetic APB results; no downloaded corpus or sibling test imports."""

from __future__ import annotations

from pathlib import Path

import pytest
from apb2.api import ParsedLevels
from scripts.synthetic import parsed_result, stored_result


@pytest.fixture
def parsed(tmp_path: Path) -> ParsedLevels:
    """A known result with precursor and protein quantities."""
    return parsed_result(tmp_path)


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """A stored APB result ready for the public reader."""
    return stored_result(tmp_path)

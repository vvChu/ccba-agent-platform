"""Pytest configuration for ccba-diagram test suite."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure tests directory is importable
_tests_dir = str(Path(__file__).parent)
if _tests_dir not in sys.path:
    sys.path.insert(0, _tests_dir)

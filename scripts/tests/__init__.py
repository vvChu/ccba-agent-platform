"""CCBA scripts tests package."""

from pathlib import Path

_ROOT_TESTS = str(Path(__file__).resolve().parents[2] / "tests")
if _ROOT_TESTS not in __path__:
    __path__.append(_ROOT_TESTS)

"""CCBA Harness package — public re-export surface.

This file is intentionally a thin wrapper. All implementation lives in
the private sub-modules:

  _engine.py          — shared mutable state, monitors & hook engines
  _guard.py           — HarnessGuard class public interface

Only public symbols are re-exported here. Internal symbols (_prefixed)
remain private to the package. Tests that need internal access should
import directly from the sub-module (e.g. from ccba_harness._engine import _local).
"""

# ruff: noqa: F401
from __future__ import annotations

import subprocess  # needed as patch target for tests

# Public API re-exports
from ._engine import (
    HarnessEngine,
    HarnessLocal,
    HarnessState,
)
from ._guard import HarnessGuard
from ._mutex import FileMutexLock

__all__ = [
    "HarnessEngine",
    "HarnessGuard",
    "HarnessLocal",
    "HarnessState",
    "FileMutexLock",
]

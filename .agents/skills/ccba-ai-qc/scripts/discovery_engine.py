#!/usr/bin/env python3
"""Thin Adapter for DiscoveryEngine delegating to ccba_qc_core.discovery."""

from __future__ import annotations

import sys

from ccba_qc_core.discovery import (
    DiscoveryEngine,
    IDOPDiscovery,
    ProjectBackbone,
    SheetEntry,
)

__all__ = ["DiscoveryEngine", "IDOPDiscovery", "ProjectBackbone", "SheetEntry"]

if __name__ == "__main__":
    from ccba_qc_core.cli import app
    sys.exit(app(["discover", *sys.argv[1:]]))

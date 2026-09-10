#!/usr/bin/env python3
"""Thin Adapter for PcccMapReduceEngine delegating to ccba_qc_core.pccc."""

from __future__ import annotations

import sys

from ccba_qc_core.pccc import MapReduceEngine, PcccMapReduceEngine

__all__ = ["PcccMapReduceEngine", "MapReduceEngine"]

if __name__ == "__main__":
    from ccba_qc_core.cli import app
    sys.exit(app(["pccc", *sys.argv[1:]]))

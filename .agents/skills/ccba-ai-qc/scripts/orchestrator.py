#!/usr/bin/env python3
"""Thin Adapter for QCBatchOrchestrator delegating to ccba_qc_core.pipeline."""

from __future__ import annotations

import sys

from ccba_qc_core.pipeline import QCBatchOrchestrator

__all__ = ["QCBatchOrchestrator"]

if __name__ == "__main__":
    from ccba_qc_core.cli import app
    sys.exit(app(["batch", *sys.argv[1:]]))

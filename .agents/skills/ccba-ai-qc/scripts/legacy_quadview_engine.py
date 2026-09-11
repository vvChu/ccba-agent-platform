#!/usr/bin/env python3
"""Thin Adapter for QuadViewAuditEngine delegating to ccba_qc_core.quadview."""

from __future__ import annotations

import sys

from ccba_qc_core.quadview import IDOPAuditEngine, QuadViewAuditEngine

__all__ = ["QuadViewAuditEngine", "IDOPAuditEngine"]

if __name__ == "__main__":
    from ccba_qc_core.cli import app
    sys.exit(app(["audit", *sys.argv[1:]]))

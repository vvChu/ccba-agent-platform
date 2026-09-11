#!/usr/bin/env python3
"""Thin Adapter for ReporterEngine delegating to ccba_qc_core.reporter."""

from __future__ import annotations

from ccba_qc_core.reporter import IDOPReporter, ReporterEngine

__all__ = ["ReporterEngine", "IDOPReporter"]

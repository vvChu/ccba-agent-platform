#!/usr/bin/env python3
"""Legal Intelligence Pipeline CLI wrapper.

Thin adapter delegating to LegalIntelPipeline in `ccba_legal.coordinator`.
Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import sys

from ccba_legal import LegalIntelPipeline


def main() -> None:
    """Run the Legal Intelligence Pipeline CLI."""
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    pipeline = LegalIntelPipeline()
    sys.exit(pipeline.run_cli(sys.argv[1:]))


if __name__ == "__main__":
    main()

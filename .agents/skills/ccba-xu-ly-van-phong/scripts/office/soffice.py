#!/usr/bin/env python3
"""Thin CLI Adapter: ccba-xu-ly-van-phong soffice runner.

Delegates execution to Layer 1 Deep Seam: ccba_ooxml.run_soffice.
"""

from __future__ import annotations

import sys

from ccba_ooxml import find_soffice_bin, get_soffice_env, run_soffice

__all__ = ["find_soffice_bin", "get_soffice_env", "run_soffice"]


def main() -> int:
    try:
        res = run_soffice(sys.argv[1:])
        return res.returncode
    except Exception as exc:
        print(f"[ERROR] LibreOffice invocation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

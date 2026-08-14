"""Thin Backward-Compatible Facade for Repomix Packager.

Delegates execution to the deep ``RepomixPackager`` class in ``scripts.scaffolding.repomix``.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from scripts.scaffolding.repomix import RepomixPackager, main, run_repomix_pack
except (ImportError, ValueError):
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from scripts.scaffolding.repomix import RepomixPackager, main, run_repomix_pack

_packager = RepomixPackager()
check_npx_available = _packager.check_npx_available
run_repomix = _packager.pack

__all__ = [
    "RepomixPackager",
    "run_repomix_pack",
    "check_npx_available",
    "run_repomix",
    "main",
]

if __name__ == "__main__":
    main()

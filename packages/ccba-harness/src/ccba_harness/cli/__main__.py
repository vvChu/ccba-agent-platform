"""__main__.py - Entry point when invoked as `python -m ccba_harness.cli`."""

from __future__ import annotations

import sys

from .core import main

if __name__ == "__main__":
    sys.exit(main())

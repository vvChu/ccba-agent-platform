#!/usr/bin/env python3
"""update_arch_stats.py - Thin CLI Forwarding Shim for Architecture Stats Updater.

Delegates execution to scripts.scaffolding.arch_stats.
"""

import sys
from pathlib import Path

# Add project root to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.scaffolding.arch_stats import main

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""lint_construction_terminology.py - Thin CLI Adapter for Construction Terminology Linter.

Delegates execution to scripts.governance.lint_construction_terminology.
"""

import sys
from pathlib import Path

# Add project root to sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.governance.lint_construction_terminology import main

if __name__ == "__main__":
    main()

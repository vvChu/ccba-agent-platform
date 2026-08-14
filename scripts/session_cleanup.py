#!/usr/bin/env python3
"""
CLI entrypoint for CCBA Workspace Session Cleanup.
Delegates execution to the session_cleanup deep module in scripts/spoke/session_cleanup.py.
"""

import sys
from pathlib import Path

# Ensure sys.path contains platform root
PLATFORM_ROOT = Path(__file__).resolve().parents[1]
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

from scripts.spoke.session_cleanup import (
    main,
)

if __name__ == "__main__":
    main()

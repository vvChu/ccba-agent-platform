#!/usr/bin/env python3
"""
CLI entrypoint for ClaudeKit and Upstream Repository Update Checking.
Delegates execution to the UpstreamEvaluator deep module.
"""

import sys
from pathlib import Path

# Ensure sys.path contains platform root
PLATFORM_ROOT = Path(__file__).resolve().parents[2]
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

from scripts.spoke.upstream_evaluator import UpstreamEvaluator, main

if __name__ == "__main__":
    main()

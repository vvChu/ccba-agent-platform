#!/usr/bin/env python3
"""Legal Intelligence Pipeline CLI wrapper.

Thin adapter delegating to LegalIntelPipeline in `ccba_legal.coordinator`.
"""

import sys
from ccba_legal import LegalIntelPipeline

# Enforce UTF-8 output on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def main() -> None:
    """Run the Legal Intelligence Pipeline CLI."""
    pipeline = LegalIntelPipeline()
    sys.exit(pipeline.run_cli(sys.argv[1:]))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""CLI entrypoint for CCBA Brownfield Spoke Adoption.

Discovers existing project state, performs non-destructive additive merge,
installs security hooks, and syncs appropriate skill bundles.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure sys.path contains platform root
PLATFORM_ROOT = Path(__file__).resolve().parents[1]
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

from scripts.spoke.spoke_adopter import adopt_project


def main() -> None:
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="CCBA Brownfield Spoke Adoption")
    parser.add_argument(
        "--spoke",
        default=".",
        help="Path to the target existing spoke project folder (defaults to current directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform assessment and display discovery matrix without writing files.",
    )
    parser.add_argument(
        "--archetype",
        default=None,
        help="Explicit CCBA Spoke Archetype ('project_delivery', 'enterprise_governance', 'knowledge_corpus', 'specialized_extension').",
    )
    parser.add_argument(
        "--type",
        dest="project_type",
        default=None,
        help="Explicit CCBA project type ('Phần mềm', 'Thiết kế', 'Thẩm tra thiết kế', 'Kiểm định', 'Tác vụ Admin').",
    )
    parser.add_argument(
        "--mode",
        default=None,
        help="Execution mode ('software', 'delivery', 'hybrid').",
    )
    args = parser.parse_args()
    sys.exit(
        adopt_project(
            spoke_path=args.spoke,
            dry_run=args.dry_run,
            project_type=args.project_type,
            mode=args.mode,
            archetype=args.archetype,
        )
    )


if __name__ == "__main__":
    main()

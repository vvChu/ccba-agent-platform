"""Bootstrap script for setting up CCBA Spokes on an engineer's local machine.

Deprecated: Forwarding to SpokeBootstrapper (ADR-0044) in scripts.spoke.spoke_bootstrap.
"""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.spoke.spoke_bootstrap import SpokeBootstrapper


def bootstrap(spoke_path: str = ".") -> int:
    """Forward to modern SpokeBootstrapper."""
    print("=== CCBA AGENT PLATFORM — LOCAL DEV BOOTSTRAP (ADR-0044) ===")
    hub_root = Path(__file__).resolve().parents[2]
    bootstrapper = SpokeBootstrapper(spoke_path=spoke_path, hub_path=hub_root)
    return bootstrapper.bootstrap()


def main() -> None:
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass
        if hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8")
            except Exception:
                pass
    spoke_arg = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(bootstrap(spoke_arg))


if __name__ == "__main__":
    main()

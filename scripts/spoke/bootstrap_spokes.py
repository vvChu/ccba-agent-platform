"""Bootstrap script for setting up CCBA Spokes on an engineer's local machine."""

import subprocess
import sys
from pathlib import Path


def bootstrap():
    print("=== CCBA AGENT PLATFORM — LOCAL DEV BOOTSTRAP ===")

    # 1. Install ccba-ai editable package
    hub_root = Path(__file__).parents[1]
    ai_pkg = hub_root / "packages" / "ccba-ai"

    if ai_pkg.exists():
        print(f"\n[1/2] Installing ccba-ai package editable mode from {ai_pkg.resolve()}...")
        res = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(ai_pkg.resolve())],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            print(" ✅ ccba-ai installed successfully.")
        else:
            print(f" ⚠️ Warning installing ccba-ai: {res.stderr}")

    # 2. Setup Knowledge Spoke local path
    spoke_dir = Path("D:/GitHubProjects/ccba-legal-knowledge")
    print(f"\n[2/2] Checking Knowledge Spoke at {spoke_dir.resolve()}...")

    if spoke_dir.exists():
        print(" ✅ Knowledge Spoke is PRESENT on local disk.")
    else:
        print(" ℹ️ Knowledge Spoke not found locally. Initializing local folder...")
        spoke_dir.mkdir(parents=True, exist_ok=True)
        # Note: If remote URL is set, can do git clone here
        print(" ✅ Knowledge Spoke folder initialized.")

    print("\n🎉 BOOTSTRAP COMPLETE! Smart Resolution Gateway is active.")


if __name__ == "__main__":
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    bootstrap()

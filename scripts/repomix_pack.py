#!/usr/bin/env python3
"""
Python wrapper script for Node.js Repomix.
Generates temporary config, runs npx repomix, and packages source codebase into XML format.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Enforce UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def check_npx_available() -> bool:
    """Check if npx CLI is available in the current environment."""
    try:
        # Run npx --version
        subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            shell=True if sys.platform == "win32" else False
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def run_repomix(source_dir: Path, output_file: Path, exclude_patterns: list) -> bool:
    """Generate temporary config and execute repomix packaging."""
    config_file = source_dir / "repomix.config.json"

    # Standard ignore lists
    default_excludes = [
        "node_modules",
        ".venv",
        "venv",
        ".git",
        ".pytest_cache",
        "__pycache__",
        "*.pyc",
        "dist",
        "build",
        "uv.lock",
        "package-lock.json",
        ".chrome_profile",
        "claudekit-engineer"
    ]

    # Merge ignores
    final_excludes = list(set(default_excludes + exclude_patterns))

    # repomix config schema
    config_data = {
        "output": {
            "filePath": str(output_file.absolute()),
            "style": "xml",
            "parsable": True
        },
        "ignore": {
            "useGitignore": True,
            "customPatterns": final_excludes
        }
    }

    print(f"[Repomix Pack] Creating temporary config at: {config_file.name}")
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"[Repomix Pack] Running npx repomix on directory: {source_dir}")

        # Prepare command
        cmd = ["npx", "--yes", "repomix", str(source_dir.absolute()), "--config", str(config_file.absolute())]

        # Run process
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            shell=True if sys.platform == "win32" else False
        )

        if result.returncode == 0:
            print(f"[Repomix Pack] Successfully packaged codebase into: {output_file}")
            return True
        else:
            print(f"[Repomix Pack] Error executing repomix. Return code: {result.returncode}")
            print(f"Stdout:\n{result.stdout}")
            print(f"Stderr:\n{result.stderr}")
            return False

    except Exception as e:
        print(f"[Repomix Pack] Exception occurred: {e}")
        return False

    finally:
        # Cleanup temporary config file
        if config_file.exists():
            try:
                os.remove(config_file)
                print("[Repomix Pack] Cleaned up temporary config file.")
            except OSError as cleanup_err:
                print(f"[Repomix Pack] Warning: Could not clean up {config_file.name}: {cleanup_err}")


def main():
    parser = argparse.ArgumentParser(description="CCBA Repomix Packaging Wrapper")
    parser.add_argument("--source", default=".", help="Source directory to package (default: current)")
    parser.add_argument("--output", default=".md/scratch/source_pack.txt", help="Output pack file path")
    parser.add_argument("--exclude", nargs="*", default=[], help="Additional glob patterns to ignore")

    args = parser.parse_args()

    source_path = Path(args.source)
    output_path = Path(args.output)

    # Ensure output parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not check_npx_available():
        print("[Repomix Pack] Error: 'npx' is not installed or not found on PATH. Node.js is required.", file=sys.stderr)
        sys.exit(1)

    success = run_repomix(source_path, output_path, args.exclude)
    if not success:
        sys.exit(1)
    print("[Repomix Pack] Execution finished successfully.")


if __name__ == "__main__":
    main()

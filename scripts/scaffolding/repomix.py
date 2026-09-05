"""Repomix Codebase Packaging Engine.

Generates temporary config, executes Node.js npx repomix, and packages source codebase into XML format.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


class RepomixPackager:
    """Orchestrates codebase packaging into structured XML format using Repomix."""

    DEFAULT_EXCLUDES = [
        "node_modules",
        ".venv",
        "venv",
        ".git",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".coverage",
        "coverage.xml",
        "__pycache__",
        "*.pyc",
        "*.md.bak",
        "dist",
        "build",
        "uv.lock",
        "package-lock.json",
        ".chrome_profile",
        "claudekit-engineer",
    ]

    @staticmethod
    def check_npx_available() -> bool:
        """Check if npx CLI is available in the current environment."""
        try:
            subprocess.run(
                ["npx", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
                shell=True if sys.platform == "win32" else False,
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def build_config(
        self, output_file: Path, exclude_patterns: list[str] | None = None
    ) -> dict[str, Any]:
        """Generates repomix configuration data."""
        extra_excludes = exclude_patterns or []
        final_excludes = list(set(self.DEFAULT_EXCLUDES + extra_excludes))

        return {
            "output": {
                "filePath": str(output_file.resolve()),
                "style": "xml",
                "parsable": True,
            },
            "ignore": {"useGitignore": True, "customPatterns": final_excludes},
        }

    def pack(
        self,
        source_dir: Path,
        output_file: Path,
        exclude_patterns: list[str] | None = None,
    ) -> bool:
        """Generates temporary config, runs npx repomix, and cleans up afterwards."""
        config_file = source_dir / "repomix.config.json"
        config_data = self.build_config(output_file, exclude_patterns)

        print(f"[Repomix Pack] Creating temporary config at: {config_file.name}")
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            print(f"[Repomix Pack] Running npx repomix on directory: {source_dir}")
            cmd = [
                "npx",
                "--yes",
                "repomix",
                str(source_dir.resolve()),
                "--config",
                str(config_file.resolve()),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                shell=True if sys.platform == "win32" else False,
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
            if config_file.exists():
                try:
                    os.remove(config_file)
                    print("[Repomix Pack] Cleaned up temporary config file.")
                except OSError as cleanup_err:
                    print(
                        f"[Repomix Pack] Warning: Could not clean up {config_file.name}: {cleanup_err}"
                    )


def run_repomix_pack(
    source_dir: Path, output_file: Path, exclude_patterns: list[str] | None = None
) -> bool:
    """Convenience helper function to run repomix packaging."""
    packager = RepomixPackager()
    return packager.pack(source_dir, output_file, exclude_patterns)


def main() -> None:
    """CLI entry point for repomix packager."""
    if sys.platform == "win32":
        import io

        try:
            if isinstance(sys.stdout, io.TextIOWrapper):
                sys.stdout.reconfigure(encoding="utf-8")
            if isinstance(sys.stderr, io.TextIOWrapper):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="CCBA Repomix Packaging Wrapper")
    parser.add_argument(
        "--source", default=".", help="Source directory to package (default: current)"
    )
    parser.add_argument(
        "--output", default=".md/scratch/source_pack.txt", help="Output pack file path"
    )
    parser.add_argument(
        "--exclude", nargs="*", default=[], help="Additional glob patterns to ignore"
    )

    args = parser.parse_args()
    source_path = Path(args.source)
    output_path = Path(args.output)

    packager = RepomixPackager()
    if not packager.check_npx_available():
        print(
            "[Repomix Pack] Error: 'npx' is not installed or not found on PATH. Node.js is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    success = packager.pack(source_path, output_path, args.exclude)
    if not success:
        sys.exit(1)
    print("[Repomix Pack] Execution finished successfully.")


if __name__ == "__main__":
    main()

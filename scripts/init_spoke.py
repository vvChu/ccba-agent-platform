#!/usr/bin/env python3
"""CLI entrypoint for Deterministic CCBA Spoke Initialization.

Scaffolds directory structure, generates workspace_context.yaml, sets up .gitignore,
installs security guardrails, and sets up Virtual Hub Fallback.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure sys.path contains platform root
PLATFORM_ROOT = Path(__file__).resolve().parents[1]
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

from scripts.spoke.spoke_initializer import init_project


def main() -> None:
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Deterministic CCBA Spoke Initialization")
    parser.add_argument(
        "spoke_path",
        nargs="?",
        default=None,
        help="Path to target spoke directory (defaults to current directory).",
    )
    parser.add_argument(
        "-p",
        "--path",
        dest="path_opt",
        default=None,
        help="Alternative path to target spoke directory.",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Project name (defaults to target directory name).",
    )
    parser.add_argument(
        "--archetype",
        default=None,
        choices=[
            "project_delivery",
            "enterprise_governance",
            "knowledge_corpus",
            "specialized_extension",
        ],
        help="Explicit CCBA Spoke Archetype (default: project_delivery).",
    )
    parser.add_argument(
        "--type",
        dest="project_type",
        default=None,
        help="Explicit CCBA project type (e.g. 'Phần mềm', 'Thẩm tra thiết kế', 'Pháp điển', etc.).",
    )
    parser.add_argument(
        "--mode",
        default=None,
        help="Execution mode (e.g. 'software', 'delivery', 'admin', 'consulting', 'hybrid').",
    )
    parser.add_argument(
        "--sub-type",
        default=None,
        help="Sub-type for specialized_extension (defaults to personal_sandbox).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview initialization steps without writing files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass fail-safe gate to overwrite existing workspace_context.yaml.",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Synchronize skills immediately after initialization.",
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Bootstrap Python virtual environment and editable Hub packages.",
    )
    parser.add_argument(
        "--init-git",
        action="store_true",
        help="Initialize git repository if missing.",
    )
    args = parser.parse_args()

    if args.path_opt and args.spoke_path:
        if Path(args.path_opt).resolve() != Path(args.spoke_path).resolve():
            print(
                f"❌ Error: Conflicting spoke paths specified: '{args.spoke_path}' (positional) vs '{args.path_opt}' (-p/--path).\n"
                "   Please specify only one destination path.",
                file=sys.stderr,
            )
            sys.exit(1)

    target_path = args.path_opt or args.spoke_path or "."
    sys.exit(
        init_project(
            spoke_path=target_path,
            hub_path=PLATFORM_ROOT,
            name=args.name,
            archetype=args.archetype,
            project_type=args.project_type,
            mode=args.mode,
            sub_type=args.sub_type,
            dry_run=args.dry_run,
            force=args.force,
            sync=args.sync,
            bootstrap=args.bootstrap,
            init_git=args.init_git,
        )
    )


if __name__ == "__main__":
    main()

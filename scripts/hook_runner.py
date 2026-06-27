#!/usr/bin/env python3
"""
Unified Hook Runner CLI for ccba-agent-platform.
Orchestrates lifecycle hooks: session-init, pre-tool, post-tool.
"""

import sys
import os
import argparse
import importlib.util
from pathlib import Path

# Enforce UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

HOOKS_DIR = Path(__file__).parent / "hooks"


def run_hook_script(script_path: Path, event: str, payload: dict) -> int:
    """Dynamically load and run a hook script. Expects a `main(event, payload)` function."""
    if not script_path.exists():
        print(f"[Hook Runner] Warning: Script {script_path.name} not found.")
        return 0  # Fail-open by default
    
    try:
        spec = importlib.util.spec_from_file_location(script_path.stem, str(script_path))
        module = importlib.util.module_from_spec(spec)
        sys.modules[script_path.stem] = module
        spec.loader.exec_module(module)
        
        if hasattr(module, "main"):
            # Execute main function and return exit code
            return module.main(event, payload)
        else:
            print(f"[Hook Runner] Error: {script_path.name} does not define a 'main(event, payload)' function.")
            return 1
    except Exception as e:
        print(f"[Hook Runner] Error running hook {script_path.name}: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="CCBA Agent Lifecycle Hook Runner")
    parser.add_argument("event", choices=["session-init", "pre-tool", "post-tool"], help="Lifecycle event to trigger")
    parser.add_argument("--tool", help="Name of the tool being called (for pre/post tool use)")
    parser.add_argument("--path", help="Target path of the tool call (if applicable)")
    parser.add_argument("--args", help="JSON encoded arguments of the tool call")
    parser.add_argument("--status", help="Exit status or result description")

    args = parser.parse_args()

    payload = {
        "tool": args.tool,
        "path": args.path,
        "args": args.args,
        "status": args.status,
    }

    # Match event to hook scripts
    exit_code = 0
    if args.event == "session-init":
        exit_code = run_hook_script(HOOKS_DIR / "session_init.py", args.event, payload)
    elif args.event == "pre-tool":
        # Run privacy check and naming checks
        exit_code_privacy = run_hook_script(HOOKS_DIR / "privacy_block.py", args.event, payload)
        exit_code_naming = run_hook_script(HOOKS_DIR / "naming_convention.py", args.event, payload)
        exit_code = max(exit_code_privacy, exit_code_naming)
    elif args.event == "post-tool":
        # Run brand enforcement checks
        exit_code = run_hook_script(HOOKS_DIR / "brand_enforcement.py", args.event, payload)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

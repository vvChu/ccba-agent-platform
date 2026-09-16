"""CLI Entrypoint for ccba-ai package.

Supported subcommands:
    python -m ccba_ai eval-models --target <model_name>
    python -m ccba_ai mcp
"""

from __future__ import annotations

import sys


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("eval-models", "eval"):
        from ccba_ai.eval_runner import main as eval_main

        return eval_main(sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == "mcp":
        from ccba_ai.mcp_server import main as mcp_main

        mcp_main()
        return 0

    print("CCBA AI Gateway Client CLI")
    print("Available subcommands:")
    print("  eval-models    Run automated Golden Benchmarks on candidate models")
    print("  mcp            Run Model Context Protocol server")
    return 1


if __name__ == "__main__":
    sys.exit(main())

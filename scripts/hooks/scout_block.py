"""Hook script for pre-tool scout block checks.

Prevents Agent from reading, writing, searching, or exploring heavy/garbage
directories (like node_modules, .venv, .git) while allowing build commands.
"""

import json
import re
from pathlib import Path
from typing import Any

# Standard directory names to block
BLOCKED_DIRS: list[str] = [
    "node_modules",
    ".venv",
    "venv",
    ".git",
    ".pytest_cache",
    "__pycache__",
    "dist",
    "build",
    ".next",
    "target",
    "clones"
]

# Build and tool command patterns to allow execution (compiled)
BUILD_CMD_RE = re.compile(
    r"^(npm|pnpm|yarn|bun)\s+([^\s]+\s+)*(run\s+)?(build|test|lint|dev|start|install|ci|add|remove|update|publish|pack|init|create|exec)",
    re.IGNORECASE
)
TOOL_CMD_RE = re.compile(
    r"^(\./)?(npx|pnpx|bunx|tsc|esbuild|vite|webpack|rollup|turbo|nx|jest|vitest|pytest|mocha|eslint|prettier|go|cargo|make|mvn|mvnw|gradle|gradlew|dotnet|docker|podman|kubectl|helm|terraform|ansible|bazel|cmake|sbt|flutter|swift|ant|ninja|meson|python3?|pip|uv|deno|bundle|rake|gem|php|composer|ruby|mix|elixir)",
    re.IGNORECASE
)
VENV_EXEC_RE = re.compile(r"(^|[\/\\])\.?venv[\/\\](bin|Scripts)[\/\\]")
VENV_CREATE_RE = re.compile(r"^(python3?|py)\s+(-[\w.]+\s+)*-m\s+venv\s+|^uv\s+venv(\s|$)|^virtualenv\s+", re.IGNORECASE)


def is_allowed_command(cmd: str) -> bool:
    """Determine if execution command is a safe build/test command.

    Args:
        cmd: Raw command string.

    Returns:
        True if the command should bypass scout-block.
    """
    clean_cmd = cmd.strip()

    # Strip env var prefixes (e.g. "NODE_ENV=production npm run build")
    clean_cmd = re.sub(r"^(\w+=\S+\s+)+", "", clean_cmd)

    # Strip command wrappers (e.g. "sudo npm run build")
    clean_cmd = re.sub(r"^(sudo|env|nice|nohup|time|timeout)\s+", "", clean_cmd)
    clean_cmd = re.sub(r"^(\w+=\S+\s+)+", "", clean_cmd)  # double check env
    clean_cmd = clean_cmd.strip()

    if BUILD_CMD_RE.match(clean_cmd):
        return True
    if TOOL_CMD_RE.match(clean_cmd):
        return True
    if VENV_EXEC_RE.search(clean_cmd):
        return True
    if VENV_CREATE_RE.match(clean_cmd):
        return True

    return False


def is_path_blocked(path_str: str) -> bool:
    """Verify if a path target points to or resides inside blocked directories.

    Args:
        path_str: The target file path string.

    Returns:
        True if path belongs to a blocked directory.
    """
    try:
        # Resolve path components
        parts = Path(path_str).parts
        parts_lower = [p.lower() for p in parts]

        for blocked in BLOCKED_DIRS:
            if blocked.lower() in parts_lower:
                return True
        return False
    except (ValueError, TypeError):
        return False


def check_tool_arguments(args_dict: dict[str, Any], tool_name: str) -> tuple[bool, str]:
    """Scan tool arguments to find blocked paths or commands.

    Args:
        args_dict: JSON-parsed arguments dict.
        tool_name: Executed tool name.

    Returns:
        Tuple of (is_blocked, reason_string).
    """
    # 1. Check path-like fields
    path_keys = ["path", "file_path", "TargetFile", "AbsolutePath", "DirectoryPath", "SearchPath"]
    for key in path_keys:
        if path_val := args_dict.get(key):
            if is_path_blocked(str(path_val)):
                return True, f"accesses blocked directory: {path_val}"

    # 2. Check list fields (like multiple replace paths or excludes)
    if includes := args_dict.get("Includes"):
        if isinstance(includes, list):
            for pattern in includes:
                if any(blocked in pattern.lower() for blocked in BLOCKED_DIRS):
                    return True, f"contains blocked path glob: {pattern}"

    # 3. Check command string if tool runs process
    if tool_name == "run_command":
        if cmd_line := args_dict.get("CommandLine"):
            if not is_allowed_command(str(cmd_line)):
                # If command touches blocked dir and is not allowed command
                cmd_lower = str(cmd_line).lower()
                for blocked in BLOCKED_DIRS:
                    # Look for directory name inside command arguments
                    if re.search(r"\b" + re.escape(blocked.lower()) + r"\b", cmd_lower):
                        return True, f"executes arbitrary code on blocked directory: {cmd_line}"

    return False, ""


def main(event: str, payload: dict[str, Any]) -> int:
    """Pre-tool hook handler for scout directory blocks.

    Args:
        event: Life-cycle event name.
        payload: Metadata containing tool, path, and arguments.

    Returns:
        Exit code: 0 to allow, 2 to block.
    """
    path_arg = payload.get("path")
    args_str = payload.get("args") or "{}"
    tool_name = payload.get("tool") or ""

    # Check bypass
    is_approved = False
    if path_arg and path_arg.startswith("APPROVED:"):
        is_approved = True
    if not is_approved and "APPROVED:" in args_str:
        is_approved = True

    if is_approved:
        return 0

    # Parse arguments dict
    try:
        args_dict = json.loads(args_str)
    except (ValueError, TypeError, json.JSONDecodeError):
        args_dict = {}

    # Check if blocked
    blocked, reason = check_tool_arguments(args_dict, tool_name)
    if not blocked and path_arg:
        if is_path_blocked(path_arg):
            blocked = True
            reason = f"accesses blocked directory: {path_arg}"

    if blocked:
        print(f"""
\x1b[31m[SCOUT BLOCK]\x1b[0m: Access to heavy/garbage directory is blocked!

  \x1b[33mReason:\x1b[0m {reason}

  This directory (e.g. .venv, node_modules, .git) contains heavy files.
  Reading or searching it slows down the Agent and consumes excessive tokens.

  To bypass this block:
  1. Ask the user for explicit approval.
  2. Prefix your path or arguments with "APPROVED:".
""")
        return 2  # Block execution

    return 0

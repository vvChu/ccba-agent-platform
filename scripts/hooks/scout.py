"""Scout Block Hook for preventing exploration of heavy/garbage directories.

Prevents Agent from reading, writing, searching, or exploring heavy/garbage
directories (like node_modules, .venv, .git) while allowing build commands.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base import BaseHook, HookContext, HookResult


class ScoutBlockHook(BaseHook):
    """Blocks tools from traversing or modifying heavy build/garbage directories."""

    name = "scout_block"
    supported_events = ("pre-tool",)

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
        "clones",
    ]

    BUILD_CMD_RE = re.compile(
        r"^(npm|pnpm|yarn|bun)\s+([^\s]+\s+)*(run\s+)?(build|test|lint|dev|start|install|ci|add|remove|update|publish|pack|init|create|exec)",
        re.IGNORECASE,
    )
    TOOL_CMD_RE = re.compile(
        r"^(\./)?(npx|pnpx|bunx|tsc|esbuild|vite|webpack|rollup|turbo|nx|jest|vitest|pytest|mocha|eslint|prettier|go|cargo|make|mvn|mvnw|gradle|gradlew|dotnet|docker|podman|kubectl|helm|terraform|ansible|bazel|cmake|sbt|flutter|swift|ant|ninja|meson|python3?|pip|uv|deno|bundle|rake|gem|php|composer|ruby|mix|elixir)",
        re.IGNORECASE,
    )
    VENV_EXEC_RE = re.compile(r"(^|[\/\\])\.?venv[\/\\](bin|Scripts)[\/\\]")
    VENV_CREATE_RE = re.compile(
        r"^(python3?|py)\s+(-[\w.]+\s+)*-m\s+venv\s+|^uv\s+venv(\s|$)|^virtualenv\s+", re.IGNORECASE
    )

    @classmethod
    def is_allowed_command(cls, cmd: str) -> bool:
        clean_cmd = cmd.strip()
        clean_cmd = re.sub(r"^(\w+=\S+\s+)+", "", clean_cmd)
        clean_cmd = re.sub(r"^(sudo|env|nice|nohup|time|timeout)\s+", "", clean_cmd)
        clean_cmd = re.sub(r"^(\w+=\S+\s+)+", "", clean_cmd)
        clean_cmd = clean_cmd.strip()

        if cls.BUILD_CMD_RE.match(clean_cmd):
            return True
        if cls.TOOL_CMD_RE.match(clean_cmd):
            return True
        if cls.VENV_EXEC_RE.search(clean_cmd):
            return True
        if cls.VENV_CREATE_RE.match(clean_cmd):
            return True
        return False

    @classmethod
    def is_path_blocked(cls, path_str: str) -> bool:
        try:
            parts = Path(path_str).parts
            parts_lower = [p.lower() for p in parts]
            for blocked in cls.BLOCKED_DIRS:
                if blocked.lower() in parts_lower:
                    return True
            return False
        except (ValueError, TypeError):
            return False

    @classmethod
    def check_tool_arguments(cls, args_dict: dict[str, Any], tool_name: str) -> tuple[bool, str]:
        path_keys = [
            "path",
            "file_path",
            "TargetFile",
            "AbsolutePath",
            "DirectoryPath",
            "SearchPath",
        ]
        for key in path_keys:
            if path_val := args_dict.get(key):
                if cls.is_path_blocked(str(path_val)):
                    return True, f"accesses blocked directory: {path_val}"

        if includes := args_dict.get("Includes"):
            if isinstance(includes, list):
                for pattern in includes:
                    if any(blocked in pattern.lower() for blocked in cls.BLOCKED_DIRS):
                        return True, f"contains blocked path glob: {pattern}"

        if tool_name == "run_command":
            if cmd_line := args_dict.get("CommandLine"):
                if not cls.is_allowed_command(str(cmd_line)):
                    cmd_lower = str(cmd_line).lower()
                    for blocked in cls.BLOCKED_DIRS:
                        if re.search(r"\b" + re.escape(blocked.lower()) + r"\b", cmd_lower):
                            return True, f"executes arbitrary code on blocked directory: {cmd_line}"

        return False, ""

    def execute(self, context: HookContext) -> HookResult:
        if context.is_approved:
            return HookResult(name=self.name, exit_code=0, message="Scout block bypassed.")

        args_dict = context.parsed_args
        tool_name = context.tool
        path_arg = context.path

        blocked, reason = self.check_tool_arguments(args_dict, tool_name)
        if not blocked and path_arg:
            if self.is_path_blocked(path_arg):
                blocked = True
                reason = f"accesses blocked directory: {path_arg}"

        if blocked:
            msg = f"""
\x1b[31m[SCOUT BLOCK]\x1b[0m: Access to heavy/garbage directory is blocked!

  \x1b[33mReason:\x1b[0m {reason}

  This directory (e.g. .venv, node_modules, .git) contains heavy files.
  Reading or searching it slows down the Agent and consumes excessive tokens.

  To bypass this block:
  1. Ask the user for explicit approval.
  2. Prefix your path or arguments with "APPROVED:".
"""
            print(msg)
            return HookResult(
                name=self.name,
                exit_code=2,
                message=f"Access to blocked directory rejected: {reason}",
                details={"reason": reason},
            )

        return HookResult(
            name=self.name, exit_code=0, message="Target paths are clear of blocked directories."
        )

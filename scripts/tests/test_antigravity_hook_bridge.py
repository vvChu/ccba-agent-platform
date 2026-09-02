"""Tests for Antigravity Lifecycle Hook Bridge Adapter.

Validates schema translation (camelCase ↔ snake_case), decision mapping
(exit_code → decision), integration with HookCoordinator, and fail-safe behavior.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
ADR: 0054 — Antigravity Lifecycle Hooks & Security Bridge
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Ensure project root is importable
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.hooks.antigravity_hook_bridge import (
    _EXIT_CODE_TO_DECISION,
    _read_stdin,
    _result_to_stdout,
    _stdin_to_context,
    main,
)
from scripts.hooks.base import HookContext, HookResult


# ---------------------------------------------------------------------------
# Schema Translation Tests
# ---------------------------------------------------------------------------


class TestStdinToContext:
    """Tests for _stdin_to_context(): Antigravity camelCase → CCBA snake_case."""

    def test_run_command_translation(self) -> None:
        """Verify run_command stdin payload translates correctly."""
        payload: dict[str, Any] = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git push --force", "Cwd": "/workspace"},
            },
            "conversationId": "test-conv-123",
            "stepIdx": 5,
        }
        ctx = _stdin_to_context(payload)

        assert ctx.event == "pre-tool"
        assert ctx.tool == "run_command"
        assert ctx.path == ""  # run_command has no TargetFile
        assert "git push --force" in ctx.args
        assert ctx.raw_payload["conversationId"] == "test-conv-123"

    def test_write_to_file_extracts_path(self) -> None:
        """Verify TargetFile is extracted as path."""
        payload: dict[str, Any] = {
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": "/workspace/src/main.py",
                    "CodeContent": "print('hello')",
                },
            },
        }
        ctx = _stdin_to_context(payload)

        assert ctx.tool == "write_to_file"
        assert ctx.path == "/workspace/src/main.py"

    def test_view_file_extracts_absolute_path(self) -> None:
        """Verify AbsolutePath is extracted as path fallback."""
        payload: dict[str, Any] = {
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": "/workspace/.env"},
            },
        }
        ctx = _stdin_to_context(payload)

        assert ctx.path == "/workspace/.env"

    def test_empty_tool_call(self) -> None:
        """Verify graceful handling of empty toolCall."""
        ctx = _stdin_to_context({"toolCall": {}})

        assert ctx.tool == ""
        assert ctx.path == ""
        assert ctx.args == ""

    def test_missing_tool_call_key(self) -> None:
        """Verify graceful handling when toolCall key is absent."""
        ctx = _stdin_to_context({"conversationId": "test"})

        assert ctx.tool == ""
        assert ctx.path == ""

    def test_args_serialized_as_json_string(self) -> None:
        """Verify tool args (object) are serialized to JSON string for HookContext."""
        payload: dict[str, Any] = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "pytest", "Cwd": "/workspace"},
            },
        }
        ctx = _stdin_to_context(payload)

        # args should be valid JSON string, not dict
        parsed = json.loads(ctx.args)
        assert isinstance(parsed, dict)
        assert parsed["CommandLine"] == "pytest"


# ---------------------------------------------------------------------------
# Result Translation Tests
# ---------------------------------------------------------------------------


class TestResultToStdout:
    """Tests for _result_to_stdout(): CCBA exit_code → Antigravity decision."""

    def test_exit_code_0_maps_to_allow(self) -> None:
        results = [HookResult(name="test", exit_code=0, message="OK")]
        output = _result_to_stdout(0, results)

        assert output["decision"] == "allow"
        assert output["reason"] == ""  # Passed hooks have no reason

    def test_exit_code_1_maps_to_ask(self) -> None:
        results = [HookResult(name="test", exit_code=1, message="Needs review")]
        output = _result_to_stdout(1, results)

        assert output["decision"] == "ask"
        assert "Needs review" in output["reason"]

    def test_exit_code_2_maps_to_deny(self) -> None:
        results = [
            HookResult(name="privacy", exit_code=2, message="Secret detected"),
        ]
        output = _result_to_stdout(2, results)

        assert output["decision"] == "deny"
        assert "Secret detected" in output["reason"]

    def test_multiple_results_concatenate_reasons(self) -> None:
        results = [
            HookResult(name="hook_a", exit_code=1, message="Warning A"),
            HookResult(name="hook_b", exit_code=2, message="Block B"),
        ]
        output = _result_to_stdout(2, results)

        assert output["decision"] == "deny"
        assert "Warning A" in output["reason"]
        assert "Block B" in output["reason"]

    def test_unknown_exit_code_defaults_to_allow(self) -> None:
        results = [HookResult(name="test", exit_code=99, message="Unknown")]
        output = _result_to_stdout(99, results)

        assert output["decision"] == "allow"

    def test_empty_results_allow(self) -> None:
        output = _result_to_stdout(0, [])

        assert output["decision"] == "allow"
        assert output["reason"] == ""


# ---------------------------------------------------------------------------
# Decision Map Completeness
# ---------------------------------------------------------------------------


class TestDecisionMap:
    """Verify the decision mapping covers all CCBA exit codes."""

    def test_all_standard_codes_mapped(self) -> None:
        assert _EXIT_CODE_TO_DECISION[0] == "allow"
        assert _EXIT_CODE_TO_DECISION[1] == "ask"
        assert _EXIT_CODE_TO_DECISION[2] == "deny"


# ---------------------------------------------------------------------------
# Integration Tests (main entry point)
# ---------------------------------------------------------------------------


class TestMainIntegration:
    """Tests for main() — full stdin → coordinator → stdout pipeline."""

    def _run_main_with_stdin(self, stdin_data: str) -> str:
        """Helper: run main() with mocked stdin/stdout, return stdout content."""
        import io as _io

        mock_stdin = _io.StringIO(stdin_data)
        mock_stdout = _io.StringIO()

        with patch("sys.stdin", mock_stdin), patch("sys.stdout", mock_stdout):
            main()

        return mock_stdout.getvalue()

    def test_safe_command_allowed(self) -> None:
        """A safe command like 'pytest' should be allowed."""
        stdin_json = json.dumps({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "pytest -v"},
            },
            "conversationId": "test-safe",
        })
        stdout = self._run_main_with_stdin(stdin_json)
        result = json.loads(stdout)

        assert result["decision"] == "allow"

    def test_empty_stdin_failsafe(self) -> None:
        """Empty stdin should trigger fail-safe allow."""
        stdout = self._run_main_with_stdin("")
        result = json.loads(stdout)

        assert result["decision"] == "allow"

    def test_invalid_json_failsafe(self) -> None:
        """Malformed JSON stdin should trigger fail-safe allow."""
        stdout = self._run_main_with_stdin("{not valid json!!!")
        result = json.loads(stdout)

        assert result["decision"] == "allow"

    def test_output_is_valid_json(self) -> None:
        """Output must always be valid JSON."""
        stdin_json = json.dumps({
            "toolCall": {"name": "run_command", "args": {"CommandLine": "echo hi"}},
        })
        stdout = self._run_main_with_stdin(stdin_json)

        # Should not raise
        result = json.loads(stdout)
        assert "decision" in result

    def test_sensitive_file_access_blocked(self) -> None:
        """Accessing .env file should be blocked by PrivacyHook."""
        stdin_json = json.dumps({
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": "/workspace/.env"},
            },
        })
        stdout = self._run_main_with_stdin(stdin_json)
        result = json.loads(stdout)

        # PrivacyHook should block access to .env files
        assert result["decision"] in ("deny", "ask")

    def test_node_modules_path_blocked(self) -> None:
        """Accessing node_modules should be blocked by ScoutBlockHook."""
        stdin_json = json.dumps({
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": "/workspace/node_modules/pkg/index.js"},
            },
        })
        stdout = self._run_main_with_stdin(stdin_json)
        result = json.loads(stdout)

        assert result["decision"] in ("deny", "ask")

"""Unit Tests for CCBA Lifecycle Hooks Sub-Package (ADR-019).

Tests HookContext, HookResult, HookCoordinator, PrivacyHook, ScoutBlockHook,
SimplifyGateHook, BrandHook, NamingHook, SessionInitHook, and TestSpeedHook.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from scripts.eval.hook_runner import run_hooks
from scripts.hooks import (
    BaseHook,
    BrandHook,
    HookContext,
    HookCoordinator,
    HookResult,
    NamingHook,
    PrivacyHook,
    ScoutBlockHook,
    SessionInitHook,
    SimplifyGateHook,
    TestSpeedHook,
    get_default_coordinator,
)


class TestHookContextAndResult(unittest.TestCase):
    def test_hook_context_properties(self) -> None:
        ctx = HookContext(event="pre-tool", path="APPROVED:.env", args='{"key": "val"}')
        self.assertTrue(ctx.is_approved)
        self.assertEqual(ctx.clean_path, ".env")
        self.assertEqual(ctx.parsed_args, {"key": "val"})

        ctx_no_app = HookContext(event="pre-tool", path=".env", args="")
        self.assertFalse(ctx_no_app.is_approved)
        self.assertEqual(ctx_no_app.clean_path, ".env")
        self.assertEqual(ctx_no_app.parsed_args, {})

    def test_hook_result_helpers(self) -> None:
        pass_res = HookResult(name="test", exit_code=0)
        self.assertTrue(pass_res.is_passed)
        self.assertFalse(pass_res.is_blocked)
        self.assertFalse(pass_res.is_warning)

        warn_res = HookResult(name="test", exit_code=1)
        self.assertTrue(warn_res.is_warning)

        block_res = HookResult(name="test", exit_code=2)
        self.assertTrue(block_res.is_blocked)


class TestHookCoordinator(unittest.TestCase):
    def test_coordinator_dispatch_and_max_exit_code(self) -> None:
        coord = HookCoordinator()

        class PassHook(BaseHook):
            name = "pass_hook"

            def execute(self, context: HookContext) -> HookResult:
                return HookResult(name=self.name, exit_code=0)

        class BlockHook(BaseHook):
            name = "block_hook"

            def execute(self, context: HookContext) -> HookResult:
                return HookResult(name=self.name, exit_code=2)

        coord.register_hook("custom-event", PassHook())
        code, results = coord.run_event("custom-event", {})
        self.assertEqual(code, 0)
        self.assertEqual(len(results), 1)

        coord.register_hook("custom-event", BlockHook())
        code2, results2 = coord.run_event("custom-event", {})
        self.assertEqual(code2, 2)
        self.assertEqual(len(results2), 2)

    def test_coordinator_error_isolation(self) -> None:
        coord = HookCoordinator()

        class FaultyHook(BaseHook):
            name = "faulty_hook"

            def execute(self, context: HookContext) -> HookResult:
                raise RuntimeError("Simulated crash")

        coord.register_hook("crash-event", FaultyHook())
        code, results = coord.run_event("crash-event", {})
        self.assertEqual(code, 1)
        self.assertIn("Simulated crash", results[0].message)

    def test_default_coordinator_setup(self) -> None:
        coord = get_default_coordinator()
        self.assertTrue(len(coord.get_hooks("session-init")) >= 1)
        self.assertTrue(len(coord.get_hooks("pre-tool")) >= 3)
        self.assertTrue(len(coord.get_hooks("post-tool")) >= 1)
        self.assertTrue(len(coord.get_hooks("user-prompt-submit")) >= 1)


class TestPrivacyHook(unittest.TestCase):
    def setUp(self) -> None:
        self.hook = PrivacyHook()

    def test_block_sensitive_files(self) -> None:
        # Sensitive file blocked
        ctx = HookContext(event="pre-tool", path="config/.env")
        res = self.hook.execute(ctx)
        self.assertEqual(res.exit_code, 2)
        self.assertTrue(res.is_blocked)

        # Sensitive file with APPROVED allowed
        ctx_approved = HookContext(event="pre-tool", path="APPROVED:config/.env")
        res_approved = self.hook.execute(ctx_approved)
        self.assertEqual(res_approved.exit_code, 0)

        # Normal file passes
        ctx_normal = HookContext(event="pre-tool", path="src/main.py")
        res_normal = self.hook.execute(ctx_normal)
        self.assertEqual(res_normal.exit_code, 0)

    def test_secret_detection_in_args(self) -> None:
        raw_key = "AIzaSy" + "A" * 33
        ctx = HookContext(event="pre-tool", tool="write_file", args=f'{{"content": "{raw_key}"}}')
        res = self.hook.execute(ctx)
        self.assertEqual(res.exit_code, 2)


class TestScoutBlockHook(unittest.TestCase):
    def setUp(self) -> None:
        self.hook = ScoutBlockHook()

    def test_blocked_directory_paths(self) -> None:
        self.assertTrue(self.hook.is_path_blocked(".venv/bin/python"))
        self.assertTrue(self.hook.is_path_blocked("node_modules/express/index.js"))
        self.assertFalse(self.hook.is_path_blocked("src/main.py"))

    def test_blocked_and_allowed_commands(self) -> None:
        self.assertTrue(self.hook.is_allowed_command("pytest tests/test_unit.py"))
        self.assertTrue(self.hook.is_allowed_command("npm run build"))
        self.assertTrue(self.hook.is_allowed_command("uv venv"))
        self.assertFalse(self.hook.is_allowed_command("ls node_modules"))

    def test_execute_blocking(self) -> None:
        ctx = HookContext(
            event="pre-tool",
            tool="run_command",
            args=json.dumps({"CommandLine": "cat .venv/pyvenv.cfg"}),
        )
        res = self.hook.execute(ctx)
        self.assertEqual(res.exit_code, 2)


class TestSimplifyGateHook(unittest.TestCase):
    def setUp(self) -> None:
        self.hook = SimplifyGateHook()

    def test_verb_detection(self) -> None:
        sev, v = self.hook.matched_severity("please ship changes")
        self.assertEqual(sev, "hard")
        self.assertEqual(v.lower(), "ship")

        sev, v = self.hook.matched_severity("ready to commit the code")
        self.assertEqual(sev, "soft")
        self.assertEqual(v.lower(), "commit")

        sev, v = self.hook.matched_severity("do not ship right now")
        self.assertEqual(sev, "")

    def test_bypass_mechanisms(self) -> None:
        ctx_approved = HookContext(
            event="user-prompt-submit", status="APPROVED: please ship this release"
        )
        self.assertEqual(self.hook.execute(ctx_approved).exit_code, 0)

        os.environ["CK_SIMPLIFY_DISABLED"] = "1"
        try:
            ctx_env = HookContext(event="user-prompt-submit", status="please ship this release")
            self.assertEqual(self.hook.execute(ctx_env).exit_code, 0)
        finally:
            del os.environ["CK_SIMPLIFY_DISABLED"]


class TestBrandAndNamingHooks(unittest.TestCase):
    def test_brand_spelling_and_prohibited_words(self) -> None:
        hook = BrandHook()
        # Mock file check
        mock_file = MagicMock(spec=Path)
        mock_file.read_text.return_value = "Using claudekit and lorem ipsum text."
        mock_file.name = "sample.md"

        findings = hook.check_file(mock_file)
        self.assertTrue(any("ClaudeKit" in f for f in findings))
        self.assertTrue(any("lorem ipsum" in f for f in findings))

    def test_naming_conventions(self) -> None:
        hook = NamingHook()
        # Generic name warning
        ctx_generic = HookContext(event="pre-tool", path="scripts/temp.py")
        res_generic = hook.execute(ctx_generic)
        self.assertEqual(res_generic.exit_code, 0)
        self.assertTrue(any("generic name" in w for w in res_generic.details.get("warnings", [])))

        # Python non-snake_case warning
        ctx_bad_py = HookContext(event="pre-tool", path="src/BadFileName.py")
        res_bad_py = hook.execute(ctx_bad_py)
        self.assertTrue(any("snake_case" in w for w in res_bad_py.details.get("warnings", [])))


class TestSpeedAndSessionHooks(unittest.TestCase):
    def test_test_speed_hook_marker_detection(self) -> None:
        mock_file = MagicMock(spec=Path)
        mock_file.read_text.return_value = (
            "import pytest\n@pytest.mark.slow\ndef test_heavy(): pass"
        )
        self.assertTrue(TestSpeedHook.has_slow_marker(mock_file))

    def test_session_init_execution(self) -> None:
        hook = SessionInitHook()
        ctx = HookContext(event="session-init")
        res = hook.execute(ctx)
        self.assertEqual(res.exit_code, 0)


class TestHookRunnerCLI(unittest.TestCase):
    def test_run_hooks_pre_tool_allow_and_block(self) -> None:
        # Allowed file
        code_allow = run_hooks("pre-tool", {"tool": "view_file", "path": "src/app.py"})
        self.assertEqual(code_allow, 0)

        # Blocked file (.env)
        code_block = run_hooks("pre-tool", {"tool": "view_file", "path": ".env"})
        self.assertEqual(code_block, 2)

        # Blocked file with APPROVED
        code_bypass = run_hooks("pre-tool", {"tool": "view_file", "path": "APPROVED:.env"})
        self.assertEqual(code_bypass, 0)


if __name__ == "__main__":
    unittest.main()

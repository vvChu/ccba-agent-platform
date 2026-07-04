import json
import unittest

from scripts.hooks.scout_block import (
    check_tool_arguments,
    is_allowed_command,
    is_path_blocked,
    main,
)


class TestScoutBlock(unittest.TestCase):
    def test_is_path_blocked(self):
        self.assertTrue(is_path_blocked(".venv/bin/python"))
        self.assertTrue(is_path_blocked("node_modules/express/index.js"))
        self.assertTrue(is_path_blocked("packages/web/node_modules/react"))
        self.assertTrue(is_path_blocked(".git/config"))
        self.assertTrue(
            is_path_blocked(".md/extracted_docs/references/clones/claudekit-engineer/README.md")
        )
        self.assertFalse(is_path_blocked("src/main.py"))
        self.assertFalse(is_path_blocked("docs/setup.md"))

    def test_is_allowed_command(self):
        self.assertTrue(is_allowed_command("npm run build"))
        self.assertTrue(is_allowed_command("pnpm install"))
        self.assertTrue(is_allowed_command("python3 -m venv .venv"))
        self.assertTrue(is_allowed_command("uv venv"))
        self.assertTrue(is_allowed_command("pytest"))
        self.assertTrue(is_allowed_command("NODE_ENV=production npm run build"))

        self.assertFalse(is_allowed_command("cd .venv"))
        self.assertFalse(is_allowed_command("cat .venv/pyvenv.cfg"))
        self.assertFalse(is_allowed_command("ls node_modules"))

    def test_check_tool_arguments(self):
        # 1. Blocked path argument
        args = {"AbsolutePath": "d:/project/node_modules/react/index.js"}
        blocked, reason = check_tool_arguments(args, "view_file")
        self.assertTrue(blocked)
        self.assertIn("node_modules", reason)

        # 2. Blocked command argument
        args = {"CommandLine": "ls node_modules"}
        blocked, reason = check_tool_arguments(args, "run_command")
        self.assertTrue(blocked)

        # 3. Allowed command argument
        args = {"CommandLine": "npm run build"}
        blocked, reason = check_tool_arguments(args, "run_command")
        self.assertFalse(blocked)

    def test_hook_main_blocking(self):
        # Mock payload that accesses node_modules
        payload = {
            "tool": "view_file",
            "path": "d:/project/node_modules/react/index.js",
            "args": json.dumps({"AbsolutePath": "d:/project/node_modules/react/index.js"}),
        }
        exit_code = main("pre-tool", payload)
        self.assertEqual(exit_code, 2)

        # Mock payload with APPROVED bypass
        payload["path"] = "APPROVED:d:/project/node_modules/react/index.js"
        exit_code = main("pre-tool", payload)
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()

"""test_orchestrator.py - Unit tests for EvalOrchestrator deep module in ccba_harness."""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
HARNESS_SRC = PROJECT_ROOT / "packages" / "ccba-harness" / "src"
if str(HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(HARNESS_SRC))

from ccba_harness.orchestrator import EvalOrchestrator


class TestEvalOrchestrator(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = EvalOrchestrator(project_root=PROJECT_ROOT)

    def test_extract_failed_gate(self) -> None:
        output = "- Gate 1 Architecture: ❌ FAILED\n- Gate 2 Tests: ✅ PASSED"
        gate = self.orchestrator.extract_failed_gate(output)
        self.assertEqual(gate, "Gate 1 Architecture")

    def test_extract_culprit_file(self) -> None:
        output = 'Traceback (most recent call last):\n  File "packages/ccba-ai/src/ccba_ai/client.py", line 42, in <module>'
        culprit = self.orchestrator.extract_culprit_file(output)
        self.assertEqual(culprit, "packages/ccba-ai/src/ccba_ai/client.py")

    def test_extract_summary_traceback(self) -> None:
        output = "Line 1\nLine 2\nValueError: Invalid setting\nLine 4"
        lines = self.orchestrator.extract_summary_traceback(output)
        self.assertTrue(any("ValueError: Invalid setting" in line for line in lines))

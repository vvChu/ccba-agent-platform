"""Unit tests for Docker Sandbox Runner and DockerSandboxScorer (TICKET-007)."""

from __future__ import annotations

import pytest

from ccba_harness.evals.models import EvalItem
from ccba_harness.evals.sandbox import (
    DockerSandboxRunner,
    DockerSandboxScorer,
    SandboxConfig,
    extract_code_blocks,
)


def test_sandbox_config_defaults() -> None:
    """Verify SandboxConfig default parameters."""
    cfg = SandboxConfig()
    assert cfg.image == "python:3.11-alpine"
    assert cfg.timeout_seconds == 15.0
    assert cfg.memory_limit == "256m"
    assert cfg.network_disabled is True
    assert cfg.allow_fallback is True


def test_extract_code_blocks() -> None:
    """Test extracting Python code from fenced markdown text."""
    text = (
        "Dưới đây là hàm giải pháp:\n\n"
        "```python\n"
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n"
        "```\n\n"
        "Và hàm nhân:\n\n"
        "```py\n"
        "def multiply(a: int, b: int) -> int:\n"
        "    return a * b\n"
        "```"
    )
    blocks = extract_code_blocks(text)
    assert len(blocks) == 2
    assert "def add" in blocks[0]
    assert "def multiply" in blocks[1]


def test_extract_code_blocks_raw_python() -> None:
    """Test extracting raw python code without fences."""
    raw = "def greet(name: str) -> str:\n    return f'Hello {name}'"
    blocks = extract_code_blocks(raw)
    assert len(blocks) == 1
    assert "def greet" in blocks[0]


def test_docker_sandbox_runner_execution() -> None:
    """Test executing a clean test suite in the Docker runner."""
    runner = DockerSandboxRunner()
    code = "def calculate_total(items: list[float]) -> float:\n    return sum(items)\n"
    test_code = (
        "import unittest\n"
        "from solution import calculate_total\n\n"
        "class TestCalculateTotal(unittest.TestCase):\n"
        "    def test_sum(self):\n"
        "        self.assertEqual(calculate_total([10.0, 20.0, 5.5]), 35.5)\n"
        "        self.assertEqual(calculate_total([]), 0.0)\n\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n"
    )
    result = runner.execute(code, test_code)
    assert result.passed
    assert result.exit_code == 0
    assert result.duration_ms > 0.0


def test_docker_sandbox_runner_failing_test() -> None:
    """Test that an incorrect solution triggers a failing result."""
    runner = DockerSandboxRunner()
    bad_code = (
        "def calculate_total(items: list[float]) -> float:\n"
        "    return 0.0\n"  # Wrong answer
    )
    test_code = (
        "import unittest\n"
        "from solution import calculate_total\n\n"
        "class TestCalculateTotal(unittest.TestCase):\n"
        "    def test_sum(self):\n"
        "        self.assertEqual(calculate_total([10.0, 20.0]), 30.0)\n\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n"
    )
    result = runner.execute(bad_code, test_code)
    assert not result.passed
    assert result.exit_code != 0
    assert "AssertionError" in (result.stderr + result.stdout)


def test_docker_sandbox_runner_fallback() -> None:
    """Test localized fallback execution directly."""
    runner = DockerSandboxRunner(config=SandboxConfig(allow_fallback=True))
    code = "def is_even(n: int) -> bool:\n    return n % 2 == 0\n"
    test_code = (
        "import unittest\n"
        "from solution import is_even\n\n"
        "class TestEven(unittest.TestCase):\n"
        "    def test_even(self):\n"
        "        self.assertTrue(is_even(4))\n"
        "        self.assertFalse(is_even(5))\n\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n"
    )
    result = runner._execute_fallback(code, test_code)
    assert result.passed
    assert result.is_fallback is True
    assert result.exit_code == 0


@pytest.mark.asyncio
async def test_docker_sandbox_scorer_success() -> None:
    """Test DockerSandboxScorer with correct code."""
    scorer = DockerSandboxScorer()
    item = EvalItem(
        id="test_sandbox_01",
        input_prompt="Viết hàm tính giai thừa bằng đệ quy",
        metadata={
            "test_code": (
                "import unittest\n"
                "from solution import factorial\n\n"
                "class TestFactorial(unittest.TestCase):\n"
                "    def test_factorial(self):\n"
                "        self.assertEqual(factorial(0), 1)\n"
                "        self.assertEqual(factorial(5), 120)\n\n"
                "if __name__ == '__main__':\n"
                "    unittest.main()\n"
            )
        },
    )
    output = (
        "Dưới đây là hàm giải pháp theo yêu cầu:\n\n"
        "```python\n"
        "def factorial(n: int) -> int:\n"
        "    if n <= 1:\n"
        "        return 1\n"
        "    return n * factorial(n - 1)\n"
        "```\n"
    )
    result = await scorer.score(output, item)
    assert result.score == 1.0
    assert not result.is_critical_fail
    assert "PASS" in result.reasoning


@pytest.mark.asyncio
async def test_docker_sandbox_scorer_failure_triggers_critical() -> None:
    """Test DockerSandboxScorer with failing test triggers critical fail."""
    scorer = DockerSandboxScorer(is_critical=True)
    item = EvalItem(
        id="test_sandbox_fail",
        input_prompt="Viết hàm tính giai thừa",
        metadata={
            "test_code": (
                "import unittest\n"
                "from solution import factorial\n\n"
                "class TestFactorial(unittest.TestCase):\n"
                "    def test_factorial(self):\n"
                "        self.assertEqual(factorial(5), 120)\n\n"
                "if __name__ == '__main__':\n"
                "    unittest.main()\n"
            )
        },
    )
    output = "```python\ndef factorial(n: int) -> int:\n    return 42\n```\n"
    result = await scorer.score(output, item)
    assert result.score == 0.0
    assert result.is_critical_fail is True
    assert "FAIL" in result.reasoning


@pytest.mark.asyncio
async def test_docker_sandbox_scorer_missing_code() -> None:
    """Test DockerSandboxScorer when output contains no python code."""
    scorer = DockerSandboxScorer(is_critical=True)
    item = EvalItem(
        id="test_sandbox_no_code",
        input_prompt="Viết hàm tính tổng",
        metadata={"test_code": "import unittest..."},
    )
    output = "Tôi không thể viết mã này."
    result = await scorer.score(output, item)
    assert result.score == 0.0
    assert result.is_critical_fail is True


@pytest.mark.asyncio
async def test_docker_sandbox_scorer_skipped_when_no_tests() -> None:
    """Test DockerSandboxScorer gracefully skips when item has no test suite."""
    scorer = DockerSandboxScorer()
    item = EvalItem(
        id="test_sandbox_no_test",
        input_prompt="Viết hàm tổng",
        metadata={},
    )
    output = "```python\ndef foo(): pass\n```"
    result = await scorer.score(output, item)
    assert result.score == 1.0
    assert not result.is_critical_fail
    assert "Skipped" in result.reasoning

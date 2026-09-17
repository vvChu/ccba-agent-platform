"""Unit tests for Dynamic Model Discovery & Heuristic Succession Resolution."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ccba_ai.antigravity_provider import (
    AntigravityCLIProvider,
    canonicalize_model_name,
    extract_available_models_from_stderr,
    is_unrecognized_model_error,
    resolve_latest_compatible_model,
)
from ccba_ai.eval_runner import run_eval_benchmark, validate_case_output

SAMPLE_AGY_STDERR = """error: invalid model selection (--model "gemini-3.7-flash-medium" --effort ""): model gemini-3.7-flash-medium is not recognized as a known model or custom model in settings
Available models:
  Gemini 3.8 Flash (High)
  Gemini 3.8 Flash (Medium)
  Gemini 3.8 Flash (Low)
  Gemini 3.7 Flash (High)
  Gemini 3.6 Flash (High)
  Gemini 3.6 Flash (Medium)
  Gemini 3.1 Pro (High)
  Claude Sonnet 4.6 (Thinking)
  Claude Opus 4.6 (Thinking)
  GPT-OSS 120B (Medium)
"""


class TestCanonicalizeModelName:
    """Test converting human-readable model names to canonical slugs."""

    def test_gemini_names(self) -> None:
        assert canonicalize_model_name("Gemini 3.8 Flash (High)") == "gemini-3.8-flash-high"
        assert canonicalize_model_name("Gemini 3.8 Flash (Medium)") == "gemini-3.8-flash-medium"
        assert canonicalize_model_name("Gemini 3.1 Pro (Low)") == "gemini-3.1-pro-low"

    def test_already_canonical(self) -> None:
        assert canonicalize_model_name("gemini-3.7-flash-medium") == "gemini-3.7-flash-medium"

    def test_empty(self) -> None:
        assert canonicalize_model_name("") == ""
        assert canonicalize_model_name("   ") == ""


class TestExtractAvailableModels:
    """Test parsing available model list from agy stderr output."""

    def test_parse_real_stderr(self) -> None:
        models = extract_available_models_from_stderr(SAMPLE_AGY_STDERR)
        assert len(models) == 10
        assert models[0] == "gemini-3.8-flash-high"
        assert models[1] == "gemini-3.8-flash-medium"
        assert "claude-sonnet-4.6-thinking" in models or "claude-sonnet-4.6" in models

    def test_no_marker(self) -> None:
        models = extract_available_models_from_stderr("Some other error without marker")
        assert models == []

    def test_is_unrecognized_model_error(self) -> None:
        assert is_unrecognized_model_error(SAMPLE_AGY_STDERR) is True
        assert is_unrecognized_model_error("error: invalid model selection") is True
        assert is_unrecognized_model_error("fatal error: disk full") is False


class TestResolveLatestCompatibleModel:
    """Test heuristic successor resolution logic."""

    def test_upgrade_version_same_tier_and_effort(self) -> None:
        available = [
            "gemini-3.8-flash-high",
            "gemini-3.8-flash-medium",
            "gemini-3.8-flash-low",
            "gemini-3.6-flash-medium",
        ]
        # Requesting 3.7 medium -> should pick 3.8 medium
        resolved = resolve_latest_compatible_model("gemini-3.7-flash-medium", available)
        assert resolved == "gemini-3.8-flash-medium"

    def test_upgrade_version_high_effort(self) -> None:
        available = [
            "gemini-3.8-flash-high",
            "gemini-3.8-flash-medium",
            "gemini-3.6-flash-high",
        ]
        # Requesting 3.7 high -> should pick 3.8 high
        resolved = resolve_latest_compatible_model("gemini-3.7-flash-high", available)
        assert resolved == "gemini-3.8-flash-high"

    def test_already_supported_returns_original(self) -> None:
        available = ["gemini-3.7-flash-medium", "gemini-3.8-flash-medium"]
        resolved = resolve_latest_compatible_model("gemini-3.7-flash-medium", available)
        assert resolved == "gemini-3.7-flash-medium"

    def test_empty_available_returns_original(self) -> None:
        resolved = resolve_latest_compatible_model("gemini-3.7-flash-medium", [])
        assert resolved == "gemini-3.7-flash-medium"

    def test_fallback_to_same_tier_when_effort_missing(self) -> None:
        # Only high effort is available in 3.8
        available = ["gemini-3.8-flash-high", "gemini-3.6-flash-medium"]
        resolved = resolve_latest_compatible_model("gemini-3.7-flash-medium", available)
        # Should pick same tier (flash) with medium if possible, or 3.8
        assert "flash" in resolved


class TestAntigravitySelfHealingRetry:
    """Test automatic retry on unrecognized model in AntigravityCLIProvider."""

    @patch("shutil.which", return_value="/usr/bin/agy")
    @patch("subprocess.run")
    def test_chat_self_healing_retry(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        provider = AntigravityCLIProvider(default_model="gemini-3.7-flash-medium")

        # 1st call fails with unrecognized model
        fail_res = MagicMock()
        fail_res.returncode = 1
        fail_res.stderr = SAMPLE_AGY_STDERR
        fail_res.stdout = ""

        # 2nd call (retry) succeeds with gemini-3.8-flash-medium
        success_res = MagicMock()
        success_res.returncode = 0
        success_res.stderr = ""
        success_res.stdout = json.dumps(
            {"event": "result", "result": {"response": "Hello from Gemini 3.8"}}
        )

        mock_run.side_effect = [fail_res, success_res]

        response_text, usage = provider.chat("Hello")
        assert response_text == "Hello from Gemini 3.8"
        assert mock_run.call_count == 2

        # Verify retry command used the resolved model
        retry_cmd = mock_run.call_args_list[1][0][0]
        assert "--model" in retry_cmd
        model_idx = retry_cmd.index("--model") + 1
        assert retry_cmd[model_idx] == "gemini-3.8-flash-medium"

    @pytest.mark.asyncio
    @patch("shutil.which", return_value="/usr/bin/agy")
    @patch("asyncio.create_subprocess_exec")
    async def test_chat_async_self_healing_retry(
        self, mock_exec: MagicMock, mock_which: MagicMock
    ) -> None:
        provider = AntigravityCLIProvider(default_model="gemini-3.7-flash-medium")

        # 1st proc fails
        proc1 = AsyncMock()
        proc1.returncode = 1
        proc1.communicate.return_value = (b"", SAMPLE_AGY_STDERR.encode("utf-8"))

        # 2nd proc succeeds
        proc2 = AsyncMock()
        proc2.returncode = 0
        success_stdout = json.dumps(
            {"event": "result", "result": {"response": "Hello from async 3.8"}}
        ).encode("utf-8")
        proc2.communicate.return_value = (success_stdout, b"")

        mock_exec.side_effect = [proc1, proc2]

        response_text, usage = await provider.chat_async("Hello")
        assert response_text == "Hello from async 3.8"
        assert mock_exec.call_count == 2


class TestEvalRunnerValidation:
    """Test benchmark validation types in eval_runner."""

    def test_validate_json_keys(self) -> None:
        case = {
            "validation_type": "json_keys",
            "expected_keys": ["name", "age"],
        }
        passed, err = validate_case_output(case, '{"name": "Alice", "age": 30}')
        assert passed is True

        passed, err = validate_case_output(case, '{"name": "Alice"}')
        assert passed is False
        assert "Missing required JSON keys" in (err or "")

    def test_validate_verbatim_keywords(self) -> None:
        case = {
            "validation_type": "verbatim_keywords",
            "expected_keywords": ["Ủy ban nhân dân", "Sở Xây dựng"],
        }
        passed, _ = validate_case_output(
            case, "Theo quy định, Ủy ban nhân dân và Sở Xây dựng phối hợp."
        )
        assert passed is True

        passed, err = validate_case_output(case, "Không có cơ quan liên quan.")
        assert passed is False

    def test_validate_code_ast(self) -> None:
        case = {
            "validation_type": "code_ast",
            "expected_keywords": ["def test_func", "return"],
        }
        valid_code = "```python\ndef test_func(x: int) -> int:\n    return x * 2\n```"
        passed, _ = validate_case_output(case, valid_code)
        assert passed is True

        invalid_code = "def syntax error: return"
        passed, err = validate_case_output(case, invalid_code)
        assert passed is False

    def test_mock_eval_benchmark_execution(self) -> None:
        # Test benchmark execution with mock provider
        ret = run_eval_benchmark(
            target_model="mock-gemini-3.8",
            mock=True,
        )
        assert ret == 0

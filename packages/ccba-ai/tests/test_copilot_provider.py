"""Unit tests for CopilotCLIProvider and Copilot response parsing (Tier 3 Fallback)."""

from __future__ import annotations

import subprocess
from unittest.mock import AsyncMock, patch

import pytest

from ccba_ai.copilot_provider import (
    CopilotChatCompletion,
    CopilotCLIProvider,
    CopilotUsage,
    parse_copilot_json_response,
)


class TestParseCopilotJsonResponse:
    """Tests for Copilot CLI NDJSON output parsing."""

    def test_parse_jsonl_events(self) -> None:
        """Should extract text from assistant.message and usage from checkpoint & result."""
        ndjson = "\n".join(
            [
                '{"type":"session.start","data":{"sessionId":"sess-123"}}',
                '{"type":"assistant.message","data":{"content":"Hello from "}}',
                '{"type":"assistant.message","data":{"content":"Copilot CLI!"}}',
                '{"type":"session.usage_checkpoint","data":{"promptCacheBreakState":[{"models":{"gpt-5.4-mini":{"prompt_tokens":120}}}]}}',
                '{"type":"result","usage":{"totalApiDurationMs":2540.5}}',
            ]
        )
        text, usage = parse_copilot_json_response(ndjson)
        assert text == "Hello from Copilot CLI!"
        assert usage.prompt_tokens == 120
        assert usage.completion_tokens == 4  # 4 words
        assert usage.total_tokens == 124
        assert usage.duration_ms == 2540.5

    def test_parse_plain_text_fallback(self) -> None:
        """Should fall back to plain text if output is not NDJSON."""
        raw_text = "This is a plain text response without JSON wrapper."
        text, usage = parse_copilot_json_response(raw_text)
        assert text == raw_text
        assert usage.prompt_tokens == 9
        assert usage.completion_tokens == 9

    def test_empty_output_raises_runtime_error(self) -> None:
        """Should raise RuntimeError when output is completely empty."""
        with pytest.raises(RuntimeError, match="No valid response"):
            parse_copilot_json_response("")

    def test_malformed_json_lines_skipped(self) -> None:
        """Should skip malformed JSON lines gracefully if valid message exists."""
        raw = "\n".join(
            [
                "{invalid json",
                '{"type":"assistant.message","data":{"content":"Recovered!"}}',
            ]
        )
        text, usage = parse_copilot_json_response(raw)
        assert text == "Recovered!"


class TestCopilotCLIProvider:
    """Tests for CopilotCLIProvider client interface and duck-typing."""

    def test_is_available_returns_bool(self) -> None:
        provider = CopilotCLIProvider(binary_path="copilot", enable_daemon=False)
        with patch("shutil.which", return_value="/usr/bin/copilot"):
            assert provider.is_available() is True
        with patch("shutil.which", return_value=None):
            with patch("os.path.isfile", return_value=False):
                assert provider.is_available() is False

    def test_sync_chat_oneshot_success(self) -> None:
        provider = CopilotCLIProvider(binary_path="copilot", enable_daemon=False)
        mock_stdout = "\n".join(
            [
                '{"type":"assistant.message","data":{"content":"42"}}',
                '{"type":"result","usage":{"totalApiDurationMs":1500.0}}',
            ]
        )
        mock_res = subprocess.CompletedProcess(args=["copilot"], returncode=0, stdout=mock_stdout, stderr="")

        with patch("subprocess.run", return_value=mock_res) as mock_run:
            text, usage = provider.chat("What is the answer?", model="gpt-5.4-mini")
            assert text == "42"
            assert usage.duration_ms == 1500.0
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "-p" in cmd
            assert "--output-format" in cmd
            assert "json" in cmd
            assert "--no-custom-instructions" in cmd

    def test_sync_chat_timeout(self) -> None:
        provider = CopilotCLIProvider(binary_path="copilot", enable_daemon=False)
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="copilot", timeout=10)):
            with pytest.raises(subprocess.TimeoutExpired):
                provider.chat("Test prompt", timeout=10)

    def test_sync_chat_nonzero_exit_raises(self) -> None:
        provider = CopilotCLIProvider(binary_path="copilot", enable_daemon=False)
        mock_res = subprocess.CompletedProcess(args=["copilot"], returncode=1, stdout="", stderr="Authorization error")
        with patch("subprocess.run", return_value=mock_res):
            with pytest.raises(RuntimeError, match="Copilot CLI failed"):
                provider.chat("Test prompt")

    def test_duck_typed_sync_client(self) -> None:
        """Verify provider.sync_client mimics openai.chat.completions.create."""
        provider = CopilotCLIProvider(binary_path="copilot", enable_daemon=False)
        with patch.object(provider, "chat", return_value=("Mock answer", CopilotUsage(prompt_tokens=10, completion_tokens=2))):
            resp = provider.sync_client.chat.completions.create(
                model="gpt-5.4-mini",
                messages=[{"role": "user", "content": "Hello"}],
            )
            assert isinstance(resp, CopilotChatCompletion)
            assert resp.choices[0].message.content == "Mock answer"
            assert resp.usage.prompt_tokens == 10

    @pytest.mark.asyncio
    async def test_duck_typed_async_client(self) -> None:
        """Verify provider.async_client mimics async openai client."""
        provider = CopilotCLIProvider(binary_path="copilot", enable_daemon=False)
        with patch.object(
            provider,
            "chat_async",
            new_callable=AsyncMock,
            return_value=("Async answer", CopilotUsage(prompt_tokens=5, completion_tokens=2)),
        ):
            resp = await provider.async_client.chat.completions.create(
                model="gpt-5.4-mini",
                messages=[{"role": "user", "content": "Async Hello"}],
            )
            assert isinstance(resp, CopilotChatCompletion)
            assert resp.choices[0].message.content == "Async answer"

"""Unit tests for AntigravityCLIProvider (Tier 3 Fallback)."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from ccba_ai.antigravity_provider import (
    AgyChatCompletion,
    AntigravityCLIProvider,
    parse_ndjson_response,
    serialize_messages,
)

# ---------------------------------------------------------------------------
# Test serialize_messages
# ---------------------------------------------------------------------------


class TestSerializeMessages:
    """Tests for OpenAI messages → prompt string conversion."""

    def test_user_only(self) -> None:
        messages = [{"role": "user", "content": "Hello world"}]
        result = serialize_messages(messages)
        assert result == "Hello world"

    def test_system_and_user(self) -> None:
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "What is 1+1?"},
        ]
        result = serialize_messages(messages)
        assert "[System Instruction]" in result
        assert "You are helpful." in result
        assert "What is 1+1?" in result

    def test_multi_turn(self) -> None:
        messages = [
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"},
        ]
        result = serialize_messages(messages)
        assert "[System Instruction]" in result
        assert "[Previous Assistant Response]" in result
        assert "How are you?" in result

    def test_empty_messages(self) -> None:
        result = serialize_messages([])
        assert result == ""


# ---------------------------------------------------------------------------
# Test parse_ndjson_response
# ---------------------------------------------------------------------------


class TestParseNdjsonResponse:
    """Tests for NDJSON stream-json output parsing."""

    def test_parse_result_event(self) -> None:
        """Should extract response from 'result' event."""
        ndjson = "\n".join(
            [
                '{"event":"init","conversation_id":"abc123"}',
                '{"event":"step_update","step_update":{"step_index":0,"state":"DONE","step_type":"user_input"}}',
                '{"event":"step_update","step_update":{"step_index":1,"state":"DONE","step_type":"agent_response","text_delta":"1 + 1 = 2\\n"}}',
                '{"event":"result","result":{"response":"1 + 1 = 2\\n","duration_seconds":34.22,"usage":{"input_tokens":26507,"output_tokens":91,"total_tokens":26598}}}',
            ]
        )
        text, usage = parse_ndjson_response(ndjson)
        assert text == "1 + 1 = 2"
        assert usage.prompt_tokens == 26507
        assert usage.completion_tokens == 91
        assert usage.total_tokens == 26598

    def test_fallback_to_text_delta(self) -> None:
        """Should concatenate text_delta if no result event found."""
        ndjson = "\n".join(
            [
                '{"event":"init","conversation_id":"abc"}',
                '{"event":"step_update","step_update":{"step_type":"agent_response","text_delta":"Hello "}}',
                '{"event":"step_update","step_update":{"step_type":"agent_response","text_delta":"world"}}',
            ]
        )
        text, usage = parse_ndjson_response(ndjson)
        assert text == "Hello world"
        assert usage.prompt_tokens == 0  # No usage data available

    def test_no_valid_response_raises(self) -> None:
        """Should raise RuntimeError if no response can be extracted."""
        ndjson = '{"event":"init","conversation_id":"abc"}\n'
        with pytest.raises(RuntimeError, match="No valid response"):
            parse_ndjson_response(ndjson)

    def test_malformed_json_lines_skipped(self) -> None:
        """Should skip malformed JSON lines and still extract valid response."""
        ndjson = "\n".join(
            [
                "not-json-at-all",
                '{"event":"result","result":{"response":"OK","usage":{}}}',
            ]
        )
        text, usage = parse_ndjson_response(ndjson)
        assert text == "OK"


# ---------------------------------------------------------------------------
# Test AntigravityCLIProvider
# ---------------------------------------------------------------------------


class TestAntigravityCLIProvider:
    """Tests for AntigravityCLIProvider core functionality."""

    def test_is_available_found(self) -> None:
        """Should return True when agy is on PATH."""
        with patch("ccba_ai.antigravity_provider.shutil.which", return_value="/usr/bin/agy"):
            provider = AntigravityCLIProvider()
            assert provider.is_available() is True

    def test_is_available_not_found(self) -> None:
        """Should return False when agy is not on PATH and path doesn't exist."""
        with patch("ccba_ai.antigravity_provider.shutil.which", return_value=None):
            with patch("ccba_ai.antigravity_provider.os.path.isfile", return_value=False):
                provider = AntigravityCLIProvider(binary_path="/nonexistent/agy")
                assert provider.is_available() is False

    def test_build_command(self) -> None:
        """Should build correct command with all required flags."""
        provider = AntigravityCLIProvider(binary_path="/usr/bin/agy")
        cmd = provider._build_command("Hello", "gemini-3.7-flash-high")
        assert cmd[0] == "/usr/bin/agy"
        assert "-p" in cmd
        assert "Hello" in cmd
        assert "--model" in cmd
        assert "gemini-3.7-flash-high" in cmd
        assert "--output-format" in cmd
        assert "stream-json" in cmd
        assert "--disable-slash-commands" in cmd
        assert "--sandbox" in cmd

    def test_chat_success(self) -> None:
        """Should parse subprocess output and return response text."""
        ndjson_output = json.dumps(
            {
                "event": "result",
                "result": {
                    "response": "The answer is 42.\n",
                    "usage": {"input_tokens": 100, "output_tokens": 10, "total_tokens": 110},
                },
            }
        )

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ndjson_output
        mock_result.stderr = ""

        with patch("ccba_ai.antigravity_provider.subprocess.run", return_value=mock_result):
            provider = AntigravityCLIProvider(binary_path="agy")
            text, usage = provider.chat("What is the meaning of life?")
            assert text == "The answer is 42."
            assert usage.prompt_tokens == 100

    def test_chat_nonzero_exit_raises(self) -> None:
        """Should raise RuntimeError on non-zero exit code."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Authentication failed"

        with patch("ccba_ai.antigravity_provider.subprocess.run", return_value=mock_result):
            provider = AntigravityCLIProvider(binary_path="agy")
            with pytest.raises(RuntimeError, match="Antigravity CLI failed"):
                provider.chat("test")

    def test_chat_timeout_propagates(self) -> None:
        """Should propagate subprocess.TimeoutExpired."""
        with patch(
            "ccba_ai.antigravity_provider.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["agy"], timeout=120),
        ):
            provider = AntigravityCLIProvider(binary_path="agy")
            with pytest.raises(subprocess.TimeoutExpired):
                provider.chat("test", timeout=120)

    def test_default_model(self) -> None:
        """Should use default model when none specified."""
        provider = AntigravityCLIProvider(default_model="claude-sonnet-4-6")
        assert provider.default_model == "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Test OpenAI-Compatible Adapter
# ---------------------------------------------------------------------------


class TestAgySyncAdapter:
    """Tests for the OpenAI-compatible sync adapter interface."""

    def test_adapter_interface_chain(self) -> None:
        """Should support client.chat.completions.create() chain."""
        ndjson_output = json.dumps(
            {
                "event": "result",
                "result": {
                    "response": "Mocked response",
                    "usage": {"input_tokens": 50, "output_tokens": 5, "total_tokens": 55},
                },
            }
        )

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ndjson_output
        mock_result.stderr = ""

        with patch("ccba_ai.antigravity_provider.subprocess.run", return_value=mock_result):
            provider = AntigravityCLIProvider(binary_path="agy")
            client = provider.sync_client

            # This mimics how fallback_fn_builder calls the client
            response = client.chat.completions.create(
                model="gemini-3.7-flash-medium",
                messages=[
                    {"role": "system", "content": "Be concise."},
                    {"role": "user", "content": "Say hello"},
                ],
                max_tokens=1024,  # Should be silently ignored
                temperature=0.7,  # Should be silently ignored
            )

            assert isinstance(response, AgyChatCompletion)
            assert response.choices[0].message.content == "Mocked response"
            assert response.model == "gemini-3.7-flash-medium"
            assert response.usage.prompt_tokens == 50


# ---------------------------------------------------------------------------
# Test Async Provider
# ---------------------------------------------------------------------------


class TestAgyAsyncProvider:
    """Tests for async AntigravityCLIProvider."""

    @pytest.mark.asyncio
    async def test_chat_async_success(self) -> None:
        """Should parse async subprocess output."""
        ndjson_output = json.dumps(
            {
                "event": "result",
                "result": {
                    "response": "Async answer\n",
                    "usage": {"input_tokens": 200, "output_tokens": 20, "total_tokens": 220},
                },
            }
        )

        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.returncode = 0
        mock_proc.communicate = MagicMock(return_value=(ndjson_output.encode("utf-8"), b""))

        # Make communicate awaitable

        async def mock_communicate():
            return ndjson_output.encode("utf-8"), b""

        mock_proc.communicate = mock_communicate

        with patch(
            "ccba_ai.antigravity_provider.asyncio.create_subprocess_exec",
            return_value=mock_proc,
        ):
            provider = AntigravityCLIProvider(binary_path="agy")
            text, usage = await provider.chat_async("Async test")
            assert text == "Async answer"
            assert usage.total_tokens == 220

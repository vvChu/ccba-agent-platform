"""Antigravity CLI Bridge Provider for CCBA AI Fallback Matrix.

Zero-config LLM fallback via Antigravity CLI (agy) subprocess.

WARNING: ~30-40s latency per call [measured]. The overhead comes from agy loading
full agent context (rules, skills, MCP schemas, system prompt ~26K tokens) on
every invocation. Use ONLY as interactive fallback, NOT for batch pipelines.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("ccba_ai.antigravity")

# Default model for Antigravity CLI
DEFAULT_AGY_MODEL = "gemini-3.7-flash-medium"

# Default timeout: 2 minutes to account for ~30-40s agent context loading
DEFAULT_AGY_TIMEOUT = 120.0


# ---------------------------------------------------------------------------
# Response dataclasses (minimal OpenAI ChatCompletion interface)
# ---------------------------------------------------------------------------


@dataclass
class AgyMessage:
    """Minimal message mimicking OpenAI ChatCompletionMessage."""

    content: str | None = None
    role: str = "assistant"


@dataclass
class AgyChoice:
    """Minimal choice mimicking OpenAI ChatCompletionChoice."""

    message: AgyMessage = field(default_factory=AgyMessage)
    finish_reason: str = "stop"
    index: int = 0


@dataclass
class AgyUsage:
    """Token usage statistics from agy stream-json output."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class AgyChatCompletion:
    """Minimal response mimicking OpenAI ChatCompletion.

    Supports ``response.choices[0].message.content`` access pattern
    required by ``fallback_fn_builder`` in ``client.py``.
    """

    choices: list[AgyChoice] = field(default_factory=lambda: [AgyChoice()])
    id: str = "agy-fallback"
    model: str = "agy-model"
    usage: AgyUsage = field(default_factory=AgyUsage)


# ---------------------------------------------------------------------------
# OpenAI-compatible adapter namespaces
# ---------------------------------------------------------------------------


class AgyCompletions:
    """Sync mock of ``client.chat.completions`` namespace."""

    def __init__(self, provider: AntigravityCLIProvider) -> None:
        self._provider = provider

    def create(self, **kwargs: Any) -> AgyChatCompletion:
        """Sync create — mimics ``OpenAI().chat.completions.create()``.

        Accepts ``model``, ``messages``, and silently ignores unsupported
        kwargs (``max_tokens``, ``temperature``) since agy doesn't support them.
        """
        model = str(kwargs.get("model", self._provider.default_model))
        messages: list[dict[str, str]] = kwargs.get("messages", [])

        prompt = serialize_messages(messages)
        text, usage = self._provider.chat(prompt, model=model)

        return AgyChatCompletion(
            choices=[AgyChoice(message=AgyMessage(content=text))],
            model=model,
            usage=usage,
        )


class AsyncAgyCompletions:
    """Async mock of ``client.chat.completions`` namespace."""

    def __init__(self, provider: AntigravityCLIProvider) -> None:
        self._provider = provider

    async def create(self, **kwargs: Any) -> AgyChatCompletion:
        """Async create — mimics ``AsyncOpenAI().chat.completions.create()``."""
        model = str(kwargs.get("model", self._provider.default_model))
        messages: list[dict[str, str]] = kwargs.get("messages", [])

        prompt = serialize_messages(messages)
        text, usage = await self._provider.chat_async(prompt, model=model)

        return AgyChatCompletion(
            choices=[AgyChoice(message=AgyMessage(content=text))],
            model=model,
            usage=usage,
        )


class AgyChatResource:
    """Sync mock of ``client.chat`` namespace."""

    def __init__(self, provider: AntigravityCLIProvider) -> None:
        self.completions = AgyCompletions(provider)


class AsyncAgyChatResource:
    """Async mock of ``client.chat`` namespace."""

    def __init__(self, provider: AntigravityCLIProvider) -> None:
        self.completions = AsyncAgyCompletions(provider)


class AgySyncClient:
    """OpenAI-compatible sync adapter for ``fallback_fn_builder``.

    Supports: ``client.chat.completions.create(model=..., messages=..., **kwargs)``
    """

    def __init__(self, provider: AntigravityCLIProvider) -> None:
        self.chat = AgyChatResource(provider)


class AgyAsyncClient:
    """OpenAI-compatible async adapter for ``fallback_coro_builder``.

    Supports: ``await client.chat.completions.create(model=..., messages=..., **kwargs)``
    """

    def __init__(self, provider: AntigravityCLIProvider) -> None:
        self.chat = AsyncAgyChatResource(provider)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def serialize_messages(messages: list[dict[str, str]]) -> str:
    """Convert OpenAI messages array to single prompt string.

    Tradeoff: Loses semantic role boundaries (system vs user vs assistant),
    but sufficient for fallback scenario. ``max_tokens`` and ``temperature``
    are NOT supported by ``agy -p`` and are silently ignored.

    Args:
        messages: OpenAI-format messages list.

    Returns:
        Single prompt string suitable for ``agy -p``.
    """
    parts: list[str] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            parts.append(f"[System Instruction]\n{content}")
        elif role == "user":
            parts.append(content)
        elif role == "assistant":
            parts.append(f"[Previous Assistant Response]\n{content}")
    return "\n\n".join(parts)


def parse_ndjson_response(raw_output: str) -> tuple[str, AgyUsage]:
    """Extract response text and usage from NDJSON stream-json output.

    Expected NDJSON events from ``agy -p --output-format stream-json``::

        {"event":"init", ...}
        {"event":"step_update", "step_update":{"step_type":"agent_response", "text_delta":"..."}}
        {"event":"result", "result":{"response":"...", "usage":{...}}}

    Args:
        raw_output: Raw stdout from agy subprocess.

    Returns:
        Tuple of (response_text, usage).

    Raises:
        RuntimeError: If no valid response found in output.
    """
    usage = AgyUsage()

    # Primary: look for "result" event
    for line in raw_output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if obj.get("event") == "result":
                result_data = obj.get("result", {})
                response_text = result_data.get("response", "")
                usage_data = result_data.get("usage", {})
                if usage_data:
                    usage = AgyUsage(
                        prompt_tokens=usage_data.get("input_tokens", 0),
                        completion_tokens=usage_data.get("output_tokens", 0),
                        total_tokens=usage_data.get("total_tokens", 0),
                    )
                if response_text:
                    return response_text.strip(), usage
        except (json.JSONDecodeError, KeyError):
            continue

    # Fallback: concatenate text_delta from step_update events
    text_parts: list[str] = []
    for line in raw_output.strip().splitlines():
        try:
            obj = json.loads(line)
            step = obj.get("step_update", {})
            if step.get("step_type") == "agent_response" and "text_delta" in step:
                text_parts.append(step["text_delta"])
        except (json.JSONDecodeError, KeyError):
            continue

    if text_parts:
        return "".join(text_parts).strip(), usage

    raise RuntimeError(
        f"No valid response in agy stream-json output. "
        f"Raw output ({len(raw_output)} bytes): {raw_output[:300]}"
    )


# ---------------------------------------------------------------------------
# Main Provider
# ---------------------------------------------------------------------------


class AntigravityCLIProvider:
    """Zero-config LLM fallback via Antigravity CLI subprocess.

    Wraps ``agy -p --output-format stream-json`` calls behind an
    OpenAI-compatible interface for use in ``TieredFallbackRouter``.

    WARNING: ~30-40s latency per call [measured]. Use ONLY as interactive
    fallback on developer workstations, NOT for batch pipelines (> 10 calls).

    Args:
        binary_path: Path to agy executable. Auto-detected via ``shutil.which``.
        default_model: Default model name for ``agy --model`` flag.
        timeout: Subprocess timeout in seconds. Default 120s accounts for
            ~30-40s agent context loading overhead.
    """

    def __init__(
        self,
        binary_path: str | None = None,
        default_model: str = DEFAULT_AGY_MODEL,
        timeout: float = DEFAULT_AGY_TIMEOUT,
    ) -> None:
        self._binary_path = binary_path or shutil.which("agy") or "agy"
        self.default_model = default_model
        self.timeout = timeout
        self.sync_client = AgySyncClient(self)
        self.async_client = AgyAsyncClient(self)

    def is_available(self) -> bool:
        """Check if agy binary exists on the system.

        Returns:
            True if agy is found via ``shutil.which`` or at the configured path.
        """
        found = shutil.which(self._binary_path)
        if found:
            return True
        return os.path.isfile(self._binary_path)

    def chat(
        self,
        prompt: str,
        *,
        model: str | None = None,
        timeout: float | None = None,
    ) -> tuple[str, AgyUsage]:
        """Execute single prompt via ``agy -p`` (sync subprocess).

        Args:
            prompt: The prompt text (already serialized from messages).
            model: Model name for ``agy --model`` flag.
            timeout: Subprocess timeout override in seconds.

        Returns:
            Tuple of (response_text, usage).

        Raises:
            RuntimeError: If agy fails or returns no valid response.
            subprocess.TimeoutExpired: If execution exceeds timeout.
        """
        effective_model = model or self.default_model
        effective_timeout = timeout or self.timeout

        cmd = self._build_command(prompt, effective_model)

        logger.info(
            f"[ccba-ai] Antigravity CLI call: model={effective_model}, timeout={effective_timeout}s"
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                encoding="utf-8",
                # shell=False (default) — NO shell injection risk
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"[ccba-ai] Antigravity CLI timed out after {effective_timeout}s")
            raise

        if result.returncode != 0:
            logger.warning(
                f"[ccba-ai] Antigravity CLI exited with code {result.returncode}: "
                f"{result.stderr[:500]}"
            )
            raise RuntimeError(
                f"Antigravity CLI failed (exit {result.returncode}): {result.stderr[:200]}"
            )

        return parse_ndjson_response(result.stdout)

    async def chat_async(
        self,
        prompt: str,
        *,
        model: str | None = None,
        timeout: float | None = None,
    ) -> tuple[str, AgyUsage]:
        """Execute single prompt via ``agy -p`` (async subprocess).

        Args:
            prompt: The prompt text.
            model: Model name for ``agy --model`` flag.
            timeout: Subprocess timeout override in seconds.

        Returns:
            Tuple of (response_text, usage).

        Raises:
            RuntimeError: If agy fails or times out.
        """
        effective_model = model or self.default_model
        effective_timeout = timeout or self.timeout

        cmd = self._build_command(prompt, effective_model)

        logger.info(f"[ccba-ai] Antigravity CLI async call: model={effective_model}")

        kwargs: dict[str, Any] = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **kwargs,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=effective_timeout
            )
        except asyncio.TimeoutError:
            await self._kill_process_tree(proc)
            raise RuntimeError(
                f"Antigravity CLI async timed out after {effective_timeout}s"
            ) from None

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            raise RuntimeError(f"Antigravity CLI failed (exit {proc.returncode}): {stderr[:200]}")

        return parse_ndjson_response(stdout)

    def _build_command(self, prompt: str, model: str) -> list[str]:
        """Build agy CLI command with optimal flags for automation.

        Flags used:
        - ``-p``: Single-turn non-interactive (headless)
        - ``--output-format stream-json``: NDJSON output for reliable parsing
        - ``--disable-slash-commands``: No slash command expansion
        - ``--sandbox``: Restrict terminal/filesystem access
        - ``--model``: Force specific model
        """
        return [
            self._binary_path,
            "-p",
            prompt,
            "--model",
            model,
            "--output-format",
            "stream-json",
            "--disable-slash-commands",
            "--sandbox",
        ]

    @staticmethod
    async def _kill_process_tree(proc: asyncio.subprocess.Process) -> None:
        """Kill process tree on all platforms.

        On Windows, ``proc.kill()`` only kills the parent process, leaving
        child processes (agy.exe workers) running as zombies. Must use
        ``taskkill /F /T /PID`` for full tree cleanup.
        """
        pid = proc.pid
        if pid is None:
            return

        if sys.platform == "win32":
            # taskkill /F (force) /T (tree) kills all child processes
            os.system(f"taskkill /F /T /PID {pid} >nul 2>&1")  # noqa: S605
        else:
            try:
                import signal

                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass

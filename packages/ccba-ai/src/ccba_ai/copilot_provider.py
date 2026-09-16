"""GitHub Copilot CLI Bridge Provider for CCBA AI Fallback Matrix.

Zero-config LLM fallback via GitHub Copilot CLI (copilot.exe) subprocess.
Provides access to OpenAI GPT-5.4 / GPT-5.4-mini and Claude models via developer's
existing GitHub Copilot subscription.

Supports both:
1. One-Shot Subprocess Bridge (headless non-interactive with -p).
2. Persistent Stdio Daemon Bridge (low latency ~2.6s via daemon_bridge).
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

from ccba_ai.antigravity_provider import serialize_messages
from ccba_ai.daemon_bridge import PersistentStdioDaemon

logger = logging.getLogger("ccba_ai.copilot")

# Default model for Copilot CLI
DEFAULT_COPILOT_MODEL = "gpt-5.4-mini"
DEFAULT_COPILOT_TIMEOUT = 120.0


# ---------------------------------------------------------------------------
# Response dataclasses (minimal OpenAI ChatCompletion interface)
# ---------------------------------------------------------------------------


@dataclass
class CopilotMessage:
    """Minimal message mimicking OpenAI ChatCompletionMessage."""

    content: str | None = None
    role: str = "assistant"


@dataclass
class CopilotChoice:
    """Minimal choice mimicking OpenAI ChatCompletionChoice."""

    message: CopilotMessage = field(default_factory=CopilotMessage)
    finish_reason: str = "stop"
    index: int = 0


@dataclass
class CopilotUsage:
    """Token usage statistics from copilot json output."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: float = 0.0


@dataclass
class CopilotChatCompletion:
    """Minimal response mimicking OpenAI ChatCompletion.

    Supports ``response.choices[0].message.content`` access pattern.
    """

    choices: list[CopilotChoice] = field(default_factory=lambda: [CopilotChoice()])
    model: str = DEFAULT_COPILOT_MODEL
    usage: CopilotUsage = field(default_factory=CopilotUsage)


# ---------------------------------------------------------------------------
# Duck-typed OpenAI Client Adapters
# ---------------------------------------------------------------------------


class CopilotSyncCompletions:
    """Duck-typed completions resource for sync OpenAI interface."""

    def __init__(self, provider: CopilotCLIProvider) -> None:
        self._provider = provider

    def create(self, **kwargs: Any) -> CopilotChatCompletion:
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", self._provider.default_model)
        timeout = kwargs.get("timeout")

        prompt = serialize_messages(messages)
        text, usage = self._provider.chat(prompt, model=model, timeout=timeout)

        choice = CopilotChoice(message=CopilotMessage(content=text))
        return CopilotChatCompletion(choices=[choice], model=model, usage=usage)


class CopilotSyncChat:
    """Duck-typed chat resource for sync OpenAI interface."""

    def __init__(self, provider: CopilotCLIProvider) -> None:
        self.completions = CopilotSyncCompletions(provider)


class CopilotSyncClient:
    """Duck-typed sync client compatible with OpenAI SDK."""

    def __init__(self, provider: CopilotCLIProvider) -> None:
        self.chat = CopilotSyncChat(provider)


class CopilotAsyncCompletions:
    """Duck-typed completions resource for async OpenAI interface."""

    def __init__(self, provider: CopilotCLIProvider) -> None:
        self._provider = provider

    async def create(self, **kwargs: Any) -> CopilotChatCompletion:
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", self._provider.default_model)
        timeout = kwargs.get("timeout")

        prompt = serialize_messages(messages)
        text, usage = await self._provider.chat_async(prompt, model=model, timeout=timeout)

        choice = CopilotChoice(message=CopilotMessage(content=text))
        return CopilotChatCompletion(choices=[choice], model=model, usage=usage)


class CopilotAsyncChat:
    """Duck-typed chat resource for async OpenAI interface."""

    def __init__(self, provider: CopilotCLIProvider) -> None:
        self.completions = CopilotAsyncCompletions(provider)


class CopilotAsyncClient:
    """Duck-typed async client compatible with AsyncOpenAI SDK."""

    def __init__(self, provider: CopilotCLIProvider) -> None:
        self.chat = CopilotAsyncChat(provider)


# ---------------------------------------------------------------------------
# Output Parsing Helpers
# ---------------------------------------------------------------------------


def parse_copilot_json_response(raw_output: str) -> tuple[str, CopilotUsage]:
    """Parse output from copilot CLI (--output-format json or plain text).

    Args:
        raw_output: Stdout string from copilot subprocess.

    Returns:
        Tuple of (response_text, usage).
    """
    text_pieces: list[str] = []
    p_tokens = 0
    c_tokens = 0
    api_duration_ms = 0.0

    lines = raw_output.strip().splitlines()
    is_jsonl = False

    for line in lines:
        line_s = line.strip()
        if not line_s or not line_s.startswith("{"):
            continue

        try:
            obj = json.loads(line_s)
            is_jsonl = True
            event_type = obj.get("type")

            if event_type == "assistant.message":
                content = obj.get("data", {}).get("content", "")
                if content:
                    text_pieces.append(content)

            elif event_type == "session.usage_checkpoint":
                # Extract prompt tokens if available
                checkpoint_data = obj.get("data", {})
                for break_state in checkpoint_data.get("promptCacheBreakState", []):
                    for _, mdata in break_state.get("models", {}).items():
                        if "prompt_tokens" in mdata:
                            p_tokens = max(p_tokens, int(mdata["prompt_tokens"]))

            elif event_type == "result":
                usage_meta = obj.get("usage", {})
                api_duration_ms = float(usage_meta.get("totalApiDurationMs", 0.0))

        except (json.JSONDecodeError, KeyError):
            continue

    if is_jsonl and text_pieces:
        full_text = "".join(text_pieces).strip()
        c_tokens = max(1, len(full_text.split()))
        usage = CopilotUsage(
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=p_tokens + c_tokens,
            duration_ms=api_duration_ms,
        )
        return full_text, usage

    # Plain text fallback (from -s or unstructured stdout)
    plain_text = raw_output.strip()
    if plain_text:
        words = len(plain_text.split())
        usage = CopilotUsage(
            prompt_tokens=max(1, words),
            completion_tokens=max(1, words),
            total_tokens=max(2, words * 2),
            duration_ms=0.0,
        )
        return plain_text, usage

    raise RuntimeError(f"No valid response in copilot CLI output ({len(raw_output)} bytes).")


# ---------------------------------------------------------------------------
# Main Provider
# ---------------------------------------------------------------------------


class CopilotCLIProvider:
    """Zero-config LLM fallback via GitHub Copilot CLI (copilot.exe).

    Args:
        binary_path: Path to copilot executable. Auto-detected via ``shutil.which``.
        default_model: Default model name for ``copilot --model`` flag.
        timeout: Subprocess timeout in seconds (default: 120s).
        enable_daemon: Whether to use persistent Stdio daemon for low latency.
    """

    def __init__(
        self,
        binary_path: str | None = None,
        default_model: str = DEFAULT_COPILOT_MODEL,
        timeout: float = DEFAULT_COPILOT_TIMEOUT,
        enable_daemon: bool = True,
    ) -> None:
        self._binary_path = binary_path or shutil.which("copilot") or "copilot"
        self.default_model = default_model
        self.timeout = timeout
        self.enable_daemon = enable_daemon

        self.sync_client = CopilotSyncClient(self)
        self.async_client = CopilotAsyncClient(self)

        # Persistent daemon bridge
        self._daemon: PersistentStdioDaemon | None = None
        if self.enable_daemon:
            self._daemon = PersistentStdioDaemon(
                build_command=lambda: self._build_command("", self.default_model),
                idle_timeout=900.0,
            )

    def is_available(self) -> bool:
        """Check if copilot executable is installed on the system."""
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
    ) -> tuple[str, CopilotUsage]:
        """Execute prompt via copilot CLI (sync).

        Attempts low-latency daemon first; falls back to one-shot subprocess.
        """
        effective_model = model or self.default_model
        effective_timeout = timeout or self.timeout

        # If daemon is enabled and target model matches default, attempt daemon turn
        if self._daemon is not None and effective_model == self.default_model:
            return self._daemon.send_turn_sync(
                prompt=prompt,
                parse_response_fn=parse_copilot_json_response,
                fallback_oneshot_fn=lambda p: self._chat_oneshot(p, effective_model, effective_timeout),
                timeout=effective_timeout,
            )

        return self._chat_oneshot(prompt, effective_model, effective_timeout)

    def _chat_oneshot(
        self, prompt: str, model: str, timeout: float
    ) -> tuple[str, CopilotUsage]:
        """Run single prompt as an isolated one-shot subprocess."""
        cmd = self._build_command(prompt, model)
        logger.info(f"[ccba-ai] Copilot CLI one-shot call: model={model}, timeout={timeout}s")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"[ccba-ai] Copilot CLI timed out after {timeout}s")
            raise

        if result.returncode != 0:
            logger.warning(
                f"[ccba-ai] Copilot CLI exited with code {result.returncode}: {result.stderr[:400]}"
            )
            raise RuntimeError(f"Copilot CLI failed (exit {result.returncode}): {result.stderr[:200]}")

        return parse_copilot_json_response(result.stdout)

    async def chat_async(
        self,
        prompt: str,
        *,
        model: str | None = None,
        timeout: float | None = None,
    ) -> tuple[str, CopilotUsage]:
        """Execute prompt via copilot CLI (async)."""
        effective_model = model or self.default_model
        effective_timeout = timeout or self.timeout

        if self._daemon is not None and effective_model == self.default_model:
            return await self._daemon.send_turn_async(
                prompt=prompt,
                parse_response_fn=parse_copilot_json_response,
                fallback_oneshot_fn=lambda p: self._chat_oneshot_async(p, effective_model, effective_timeout),
                timeout=effective_timeout,
            )

        return await self._chat_oneshot_async(prompt, effective_model, effective_timeout)

    async def _chat_oneshot_async(
        self, prompt: str, model: str, timeout: float
    ) -> tuple[str, CopilotUsage]:
        """Run single prompt as an async one-shot subprocess."""
        cmd = self._build_command(prompt, model)
        logger.info(f"[ccba-ai] Copilot CLI async one-shot call: model={model}")

        kwargs: dict[str, Any] = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **kwargs,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            raise RuntimeError(f"Copilot CLI async timed out after {timeout}s") from None

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            raise RuntimeError(f"Copilot CLI failed (exit {proc.returncode}): {stderr[:200]}")

        return parse_copilot_json_response(stdout)

    def _build_command(self, prompt: str, model: str) -> list[str]:
        """Build copilot CLI command with optimal flags for automated execution."""
        cmd = [
            self._binary_path,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--no-custom-instructions",
            "--model",
            model,
        ]
        return cmd

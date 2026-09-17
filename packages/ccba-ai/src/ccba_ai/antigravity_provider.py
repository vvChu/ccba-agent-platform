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
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

from ccba_ai.daemon_bridge import kill_process_tree

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
# Dynamic Model Discovery & Heuristic Succession Resolution
# ---------------------------------------------------------------------------


def is_unrecognized_model_error(stderr: str) -> bool:
    """Check if agy error output indicates an invalid or unsupported model selection."""
    lower = stderr.lower()
    return (
        "is not recognized as a known model" in lower
        or "invalid model selection" in lower
        or "unknown model" in lower
    )


def canonicalize_model_name(name: str) -> str:
    """Normalize human-readable model name to canonical CLI model slug.

    Examples:
        'Gemini 3.8 Flash (High)' -> 'gemini-3.8-flash-high'
        'Gemini 3.7 Flash (Medium)' -> 'gemini-3.7-flash-medium'
        'gemini-3.7-flash-medium' -> 'gemini-3.7-flash-medium'
    """
    raw = name.strip()
    if not raw:
        return ""
    # Strip parens
    cleaned = raw.replace("(", "").replace(")", "").strip()
    # Replace spaces and underscores with dashes
    slug = re.sub(r"[\s_]+", "-", cleaned).lower()
    return slug


def extract_available_models_from_stderr(stderr: str) -> list[str]:
    """Extract and normalize model names from agy stderr output.

    When agy fails with 'model ... is not recognized', it prints:
        Available models:
          Gemini 3.8 Flash (High)
          Gemini 3.8 Flash (Medium)
          ...
    """
    lines = stderr.splitlines()
    found_marker = False
    models: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if "Available models:" in line:
            found_marker = True
            continue
        if found_marker:
            # Model names are indented lines after the marker
            if line.startswith("  ") or line.startswith("\t"):
                canonical = canonicalize_model_name(stripped)
                if canonical and canonical not in models:
                    models.append(canonical)
            else:
                break
    return models


def resolve_latest_compatible_model(requested_model: str, available_models: list[str]) -> str:
    """Resolve the best compatible successor model if requested_model is not available.

    Preserves:
    1. Provider / Family (e.g. gemini)
    2. Tier (e.g. flash vs pro)
    3. Effort / Variant (e.g. medium vs high vs low)
    And selects the highest version available.
    """
    if not available_models:
        return requested_model
    if requested_model in available_models:
        return requested_model

    req_slug = canonicalize_model_name(requested_model)
    if req_slug in available_models:
        return req_slug

    # Parse requested model: e.g. gemini-3.7-flash-medium
    # match (family)-(version)-(variant)
    match = re.match(r"^([a-zA-Z]+)-([\d\.]+)-(.*)$", req_slug)
    if not match:
        return available_models[0]

    family, version_str, variant = match.groups()

    def parse_version(model_name: str) -> tuple[int, ...]:
        v_match = re.search(r"-(\d+(?:\.\d+)*)-", model_name)
        if v_match:
            try:
                return tuple(int(p) for p in v_match.group(1).split("."))
            except ValueError:
                return (0,)
        return (0,)

    # 1. Exact variant match (same family & same variant, e.g. flash-medium)
    exact_variant_candidates = [
        m for m in available_models if m.startswith(f"{family}-") and m.endswith(f"-{variant}")
    ]
    if exact_variant_candidates:
        exact_variant_candidates.sort(key=parse_version, reverse=True)
        return exact_variant_candidates[0]

    # 2. Same tier match (e.g. flash)
    tier = variant.split("-")[0] if "-" in variant else variant
    same_tier_candidates = [
        m for m in available_models if m.startswith(f"{family}-") and f"-{tier}-" in m
    ]
    if same_tier_candidates:
        # Prefer medium effort if original was medium, else highest version
        same_tier_candidates.sort(
            key=lambda m: (parse_version(m), "medium" in m),
            reverse=True,
        )
        return same_tier_candidates[0]

    # 3. Same family match
    same_family_candidates = [m for m in available_models if m.startswith(f"{family}-")]
    if same_family_candidates:
        same_family_candidates.sort(key=parse_version, reverse=True)
        return same_family_candidates[0]

    return available_models[0]


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
            resolved_model = self._resolve_fallback_model_on_error(effective_model, result.stderr)
            if resolved_model:
                logger.warning(
                    f"[ccba-ai] Model '{effective_model}' not recognized by agy. "
                    f"Auto-redirecting to '{resolved_model}' (retry 1/1)..."
                )
                retry_cmd = self._build_command(prompt, resolved_model)
                try:
                    retry_res = subprocess.run(
                        retry_cmd,
                        capture_output=True,
                        text=True,
                        timeout=effective_timeout,
                        encoding="utf-8",
                    )
                    if retry_res.returncode == 0:
                        return parse_ndjson_response(retry_res.stdout)
                    logger.warning(
                        f"[ccba-ai] Retry with '{resolved_model}' failed (exit {retry_res.returncode}): "
                        f"{retry_res.stderr[:200]}"
                    )
                except Exception as retry_exc:
                    logger.warning(f"[ccba-ai] Retry with '{resolved_model}' failed: {retry_exc}")

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
            resolved_model = self._resolve_fallback_model_on_error(effective_model, stderr)
            if resolved_model:
                logger.warning(
                    f"[ccba-ai] Model '{effective_model}' not recognized by agy. "
                    f"Auto-redirecting to '{resolved_model}' (async retry 1/1)..."
                )
                retry_cmd = self._build_command(prompt, resolved_model)
                try:
                    retry_proc = await asyncio.create_subprocess_exec(
                        *retry_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        **kwargs,
                    )
                    retry_stdout_bytes, retry_stderr_bytes = await asyncio.wait_for(
                        retry_proc.communicate(), timeout=effective_timeout
                    )
                    if retry_proc.returncode == 0:
                        retry_stdout = retry_stdout_bytes.decode("utf-8", errors="replace")
                        return parse_ndjson_response(retry_stdout)
                    retry_stderr = retry_stderr_bytes.decode("utf-8", errors="replace")
                    logger.warning(
                        f"[ccba-ai] Async retry with '{resolved_model}' failed (exit {retry_proc.returncode}): "
                        f"{retry_stderr[:200]}"
                    )
                except Exception as retry_exc:
                    logger.warning(
                        f"[ccba-ai] Async retry with '{resolved_model}' failed: {retry_exc}"
                    )

            raise RuntimeError(f"Antigravity CLI failed (exit {proc.returncode}): {stderr[:200]}")

        return parse_ndjson_response(stdout)

    def _resolve_fallback_model_on_error(self, requested_model: str, stderr: str) -> str | None:
        """Attempt to extract available models from error and resolve successor."""
        if not is_unrecognized_model_error(stderr):
            return None

        available = extract_available_models_from_stderr(stderr)
        if not available:
            available = self.list_available_models()

        resolved = resolve_latest_compatible_model(requested_model, available)
        if resolved and resolved != requested_model:
            return resolved
        return None

    def list_available_models(self, timeout: float = 10.0) -> list[str]:
        """Query available models from ``agy models`` CLI command."""
        try:
            res = subprocess.run(
                [self._binary_path, "models"],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
            )
            if res.returncode == 0:
                models: list[str] = []
                for line in res.stdout.splitlines():
                    line = line.strip()
                    if not line or line.startswith("Fetching"):
                        continue
                    parts = line.split()
                    if parts:
                        slug = canonicalize_model_name(parts[0])
                        if slug and slug not in models:
                            models.append(slug)
                return models
        except Exception as e:
            logger.debug(f"[ccba-ai] Failed to query agy models: {e}")
        return []

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
        """Kill process tree on all platforms using unified safe kill_process_tree."""
        pid = getattr(proc, "pid", None)
        kill_process_tree(pid)

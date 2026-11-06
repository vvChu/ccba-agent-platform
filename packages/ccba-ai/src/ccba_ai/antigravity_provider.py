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
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from ccba_ai.daemon_bridge import kill_process_tree
from ccba_ai.routing import ModelArchetype

logger = logging.getLogger("ccba_ai.antigravity")

# Default model for Antigravity CLI
DEFAULT_AGY_MODEL = ModelArchetype.STANDARD_MEDIUM

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


@runtime_checkable
class CLIProviderPort(Protocol):
    """Port protocol for CLI-backed LLM failover providers (Antigravity & Copilot)."""

    default_model: str

    def is_available(self) -> bool: ...

    def chat(
        self, prompt: str, *, model: str | None = None, timeout: float | None = None
    ) -> tuple[str, Any]: ...

    async def chat_async(
        self, prompt: str, *, model: str | None = None, timeout: float | None = None
    ) -> tuple[str, Any]: ...


def _default_agy_completion(text: str, model: str, usage: Any) -> AgyChatCompletion:
    """Construct default AgyChatCompletion from CLI output."""
    return AgyChatCompletion(
        choices=[AgyChoice(message=AgyMessage(content=text))],
        model=model,
        usage=usage,
    )


class CLISyncCompletions:
    """Shared sync adapter of ``client.chat.completions`` namespace for CLI providers."""

    def __init__(
        self,
        provider: CLIProviderPort,
        completion_factory: Callable[[str, str, Any], Any] = _default_agy_completion,
    ) -> None:
        self._provider = provider
        self._completion_factory = completion_factory

    def create(self, **kwargs: Any) -> Any:
        """Sync create — mimics ``OpenAI().chat.completions.create()``."""
        model = str(kwargs.get("model", self._provider.default_model))
        messages: list[dict[str, str]] = kwargs.get("messages", [])
        timeout: float | None = kwargs.get("timeout")

        prompt = serialize_messages(messages)
        text, usage = self._provider.chat(prompt, model=model, timeout=timeout)
        return self._completion_factory(text, model, usage)


class CLIAsyncCompletions:
    """Shared async adapter of ``client.chat.completions`` namespace for CLI providers."""

    def __init__(
        self,
        provider: CLIProviderPort,
        completion_factory: Callable[[str, str, Any], Any] = _default_agy_completion,
    ) -> None:
        self._provider = provider
        self._completion_factory = completion_factory

    async def create(self, **kwargs: Any) -> Any:
        """Async create — mimics ``AsyncOpenAI().chat.completions.create()``."""
        model = str(kwargs.get("model", self._provider.default_model))
        messages: list[dict[str, str]] = kwargs.get("messages", [])
        timeout: float | None = kwargs.get("timeout")

        prompt = serialize_messages(messages)
        text, usage = await self._provider.chat_async(prompt, model=model, timeout=timeout)
        return self._completion_factory(text, model, usage)


class CLISyncChatResource:
    """Sync mock of ``client.chat`` namespace."""

    def __init__(
        self,
        provider: CLIProviderPort,
        completion_factory: Callable[[str, str, Any], Any] = _default_agy_completion,
    ) -> None:
        self.completions = CLISyncCompletions(provider, completion_factory)


class CLIAsyncChatResource:
    """Async mock of ``client.chat`` namespace."""

    def __init__(
        self,
        provider: CLIProviderPort,
        completion_factory: Callable[[str, str, Any], Any] = _default_agy_completion,
    ) -> None:
        self.completions = CLIAsyncCompletions(provider, completion_factory)


class CLISyncClient:
    """OpenAI-compatible sync adapter for ``fallback_fn_builder``."""

    def __init__(
        self,
        provider: CLIProviderPort,
        completion_factory: Callable[[str, str, Any], Any] = _default_agy_completion,
    ) -> None:
        self.chat = CLISyncChatResource(provider, completion_factory)


class CLIAsyncClient:
    """OpenAI-compatible async adapter for ``fallback_coro_builder``."""

    def __init__(
        self,
        provider: CLIProviderPort,
        completion_factory: Callable[[str, str, Any], Any] = _default_agy_completion,
    ) -> None:
        self.chat = CLIAsyncChatResource(provider, completion_factory)


# Backward-compatible aliases for Antigravity CLI adapter classes
AgyCompletions = CLISyncCompletions
AsyncAgyCompletions = CLIAsyncCompletions
AgyChatResource = CLISyncChatResource
AsyncAgyChatResource = CLIAsyncChatResource
AgySyncClient = CLISyncClient
AgyAsyncClient = CLIAsyncClient


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


def _extract_ndjson_result_event(lines: list[str]) -> tuple[str | None, AgyUsage]:
    """Scan NDJSON lines for a 'result' event and return (response_text, usage)."""
    usage = AgyUsage()
    for raw_line in lines:
        line = raw_line.strip()
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
    return None, usage


def parse_ndjson_response(raw_output: str) -> tuple[str, AgyUsage]:
    """Extract response text and usage from NDJSON stream-json output."""
    lines = raw_output.strip().splitlines()
    primary_text, usage = _extract_ndjson_result_event(lines)
    if primary_text is not None:
        return primary_text, usage

    text_parts: list[str] = []
    for line in lines:
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


_BARE_GEMINI_CLI_PATTERN = re.compile(r"^gemini-\d+(?:\.\d+)*-(?:flash|argon)$", re.IGNORECASE)


def normalize_gemini_cli_model(model: str, default_effort: str = "high") -> str:
    """Normalize bare Gemini Flash/Argon CLI model names by appending default effort suffix.

    Passing bare 'gemini-3.8-flash' or 'gemini-4-argon' to ``agy --model`` causes
    the CLI subprocess to hang until TimeoutExpired.

    Args:
        model: Raw or canonical model name.
        default_effort: Effort suffix to append when missing ('high', 'medium', 'low').

    Returns:
        Model slug safe for ``agy --model``.
    """
    slug = canonicalize_model_name(model) if " " in model or "(" in model else model.strip()
    if _BARE_GEMINI_CLI_PATTERN.match(slug):
        return f"{slug.lower()}-{default_effort}"
    return slug


def canonicalize_model_name(name: str) -> str:
    """Normalize human-readable model name to canonical CLI model slug.

    Examples:
        'Gemini 3.8 Flash (High)' -> 'gemini-3.8-flash-high'
        'Claude Opus 5.5 (High)' -> 'claude-opus-5-5-high'
        'gemini-3.7-flash-medium' -> 'gemini-3.7-flash-medium'
    """
    raw = name.strip()
    if not raw:
        return ""
    # Strip parens
    cleaned = raw.replace("(", "").replace(")", "").strip()
    # Replace spaces and underscores with dashes
    slug = re.sub(r"[\s_]+", "-", cleaned).lower()
    slug = re.sub(r"\b(claude-(?:opus|sonnet)-)(\d+)\.(\d+)", r"\1\2-\3", slug)
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


def _parse_model_version_tuple(model_name: str) -> tuple[int, ...]:
    """Extract numeric version tuple from a canonical model slug."""
    v_match = re.search(r"-(\d+(?:\.\d+)*)-", model_name)
    if v_match:
        try:
            return tuple(int(p) for p in v_match.group(1).split("."))
        except ValueError:
            return (0,)
    return (0,)


def _resolve_claude_successor(req_slug: str, available_models: list[str]) -> str | None:
    """Resolve compatible Claude model successor if req_slug is a Claude slug."""
    claude_match = re.match(r"^(claude-(?:opus|sonnet))-(\d+(?:[-.]\d+)*)(?:-(.*))?$", req_slug)
    if not claude_match:
        return None
    c_family, _, c_effort = claude_match.groups()
    target_effort = "high" if c_effort in (None, "", "thinking") else c_effort
    c_candidates = [m for m in available_models if m.startswith(f"{c_family}-")]
    if not c_candidates:
        return None
    exact_c = [m for m in c_candidates if m.endswith(f"-{target_effort}")]
    pool = exact_c or c_candidates
    pool.sort(
        key=lambda m: tuple(int(p) for p in re.findall(r"\d+", m[len(c_family) :])),
        reverse=True,
    )
    return pool[0]


def resolve_latest_compatible_model(requested_model: str, available_models: list[str]) -> str:
    """Resolve the best compatible successor model if requested_model is not available."""
    if not available_models or requested_model in available_models:
        return requested_model

    req_slug = canonicalize_model_name(requested_model)
    if req_slug in available_models:
        return req_slug

    claude_res = _resolve_claude_successor(req_slug, available_models)
    if claude_res:
        return claude_res

    match = re.match(r"^([a-zA-Z]+)-([\d\.]+)-(.*)$", req_slug)
    if not match:
        return available_models[0]

    family, _, variant = match.groups()
    exact_variant_candidates = [
        m for m in available_models if m.startswith(f"{family}-") and m.endswith(f"-{variant}")
    ]
    if exact_variant_candidates:
        exact_variant_candidates.sort(key=_parse_model_version_tuple, reverse=True)
        return exact_variant_candidates[0]

    tier = variant.split("-")[0] if "-" in variant else variant
    same_tier_candidates = [
        m for m in available_models if m.startswith(f"{family}-") and f"-{tier}-" in m
    ]
    if same_tier_candidates:
        same_tier_candidates.sort(
            key=lambda m: (_parse_model_version_tuple(m), "medium" in m),
            reverse=True,
        )
        return same_tier_candidates[0]

    same_family_candidates = [m for m in available_models if m.startswith(f"{family}-")]
    if same_family_candidates:
        same_family_candidates.sort(key=_parse_model_version_tuple, reverse=True)
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

    def _retry_sync_with_resolved_model(
        self, prompt: str, effective_model: str, stderr: str, effective_timeout: float
    ) -> tuple[str, AgyUsage] | None:
        """Attempt 1-shot sync retry if stderr indicates an unrecognized model."""
        resolved_model = self._resolve_fallback_model_on_error(effective_model, stderr)
        if not resolved_model:
            return None
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
        return None

    def chat(
        self,
        prompt: str,
        *,
        model: str | None = None,
        timeout: float | None = None,
    ) -> tuple[str, AgyUsage]:
        """Execute single prompt via ``agy -p`` (sync subprocess)."""
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
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"[ccba-ai] Antigravity CLI timed out after {effective_timeout}s")
            raise

        if result.returncode != 0:
            retried = self._retry_sync_with_resolved_model(
                prompt, effective_model, result.stderr, effective_timeout
            )
            if retried is not None:
                return retried
            logger.warning(
                f"[ccba-ai] Antigravity CLI exited with code {result.returncode}: "
                f"{result.stderr[:500]}"
            )
            raise RuntimeError(
                f"Antigravity CLI failed (exit {result.returncode}): {result.stderr[:200]}"
            )

        return parse_ndjson_response(result.stdout)

    async def _run_async_subprocess(
        self, cmd: list[str], effective_timeout: float
    ) -> tuple[int, str, str]:
        """Spawn async agy subprocess and return (returncode, stdout, stderr)."""
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

        return (
            proc.returncode or 0,
            stdout_bytes.decode("utf-8", errors="replace"),
            stderr_bytes.decode("utf-8", errors="replace"),
        )

    async def chat_async(
        self,
        prompt: str,
        *,
        model: str | None = None,
        timeout: float | None = None,
    ) -> tuple[str, AgyUsage]:
        """Execute single prompt via ``agy -p`` (async subprocess)."""
        effective_model = model or self.default_model
        effective_timeout = timeout or self.timeout
        cmd = self._build_command(prompt, effective_model)
        logger.info(f"[ccba-ai] Antigravity CLI async call: model={effective_model}")

        rc, stdout, stderr = await self._run_async_subprocess(cmd, effective_timeout)
        if rc != 0:
            resolved_model = self._resolve_fallback_model_on_error(effective_model, stderr)
            if resolved_model:
                logger.warning(
                    f"[ccba-ai] Model '{effective_model}' not recognized by agy. "
                    f"Auto-redirecting to '{resolved_model}' (async retry 1/1)..."
                )
                try:
                    r_rc, r_out, r_err = await self._run_async_subprocess(
                        self._build_command(prompt, resolved_model), effective_timeout
                    )
                    if r_rc == 0:
                        return parse_ndjson_response(r_out)
                    logger.warning(
                        f"[ccba-ai] Async retry with '{resolved_model}' failed (exit {r_rc}): {r_err[:200]}"
                    )
                except Exception as retry_exc:
                    logger.warning(
                        f"[ccba-ai] Async retry with '{resolved_model}' failed: {retry_exc}"
                    )
            raise RuntimeError(f"Antigravity CLI failed (exit {rc}): {stderr[:200]}")

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
        - ``--model``: Force specific model (normalized against bare suffix hang)
        """
        safe_model = normalize_gemini_cli_model(model)
        return [
            self._binary_path,
            "-p",
            prompt,
            "--model",
            safe_model,
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

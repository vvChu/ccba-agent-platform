"""Unit tests for ModelArchetype and choose_model in ccba_ai.routing."""

from ccba_ai.routing import ModelArchetype, choose_model


def test_model_archetype_constants() -> None:
    """Verify all archetype constants are non-empty valid strings."""
    assert ModelArchetype.OCR == "ocr-primary"
    assert ModelArchetype.OCR_FALLBACK == "ocr-fallback"
    assert ModelArchetype.OCR_TIER4 == "ocr-tier4"
    assert ModelArchetype.STANDARD == "gemini-3.7-flash"
    assert ModelArchetype.STANDARD_MEDIUM == "gemini-3.7-flash-medium"
    assert ModelArchetype.REASONING == "gemini-3.7-flash-high"
    assert ModelArchetype.REASONING_ALT == "claude-sonnet-4-6-thinking"
    assert ModelArchetype.LOCAL == "qwen-local-primary"
    assert ModelArchetype.RAG == "rag-core"
    assert ModelArchetype.CLAUDE_OPUS_46 == "claude-opus-4-6"


def test_choose_model_routing() -> None:
    """Verify choose_model maps task types to correct model aliases."""
    assert choose_model("ocr") == ModelArchetype.OCR
    assert choose_model("coding") == ModelArchetype.STANDARD
    assert choose_model("reasoning") == ModelArchetype.REASONING
    assert choose_model("audit") == ModelArchetype.REASONING
    assert choose_model("legal") == ModelArchetype.REASONING
    assert choose_model("private") == ModelArchetype.LOCAL
    assert choose_model("rag") == ModelArchetype.RAG
    assert choose_model("synthesis") == ModelArchetype.CLAUDE_OPUS_46
    assert choose_model("deep_reasoning") == ModelArchetype.CLAUDE_OPUS_46


def test_choose_model_fallback() -> None:
    """Verify unknown task type falls back to standard general model."""
    assert choose_model("unknown-task-type") == ModelArchetype.STANDARD
    assert choose_model("") == ModelArchetype.STANDARD


def test_is_reasoning_model() -> None:
    """Verify is_reasoning_model correctly identifies reasoning models."""
    from ccba_ai.routing import is_reasoning_model

    assert is_reasoning_model("gemini-3.7-flash-high") is True
    assert is_reasoning_model("claude-sonnet-4-6-thinking") is True
    assert is_reasoning_model("claude-opus-4-6") is True
    assert is_reasoning_model("claude-opus-4.6") is True
    assert is_reasoning_model("opus-4.6") is True
    assert is_reasoning_model("claude-opus-4-6-thinking") is True
    assert is_reasoning_model("custom-opus-4-6") is True
    assert is_reasoning_model("custom-opus-4.6") is True
    assert is_reasoning_model("reasoning-gemma") is True
    assert is_reasoning_model("o1-preview") is True
    assert is_reasoning_model("o3-mini") is True
    assert is_reasoning_model("custom-high") is True

    assert is_reasoning_model("gemini-3.7-flash") is False
    assert is_reasoning_model("qwen-local-primary") is False
    assert is_reasoning_model("ocr-primary") is False
    assert is_reasoning_model("") is False


def test_resolve_max_tokens_auto_elevation() -> None:
    """Verify resolve_max_tokens elevates reasoning models from default to 16384."""
    from ccba_ai.routing import resolve_max_tokens

    # Default 1024 on reasoning model -> elevated to 16384
    assert resolve_max_tokens("gemini-3.7-flash-high", 1024, baseline_default=1024) == 16384
    assert resolve_max_tokens("claude-sonnet-4-6-thinking", 1024, baseline_default=1024) == 16384

    # Default 2048 on reasoning model (multi-turn) -> elevated to 16384
    assert resolve_max_tokens("gemini-3.7-flash-high", 2048, baseline_default=2048) == 16384

    # Non-reasoning model keeps default
    assert resolve_max_tokens("gemini-3.7-flash", 1024, baseline_default=1024) == 1024

    # Explicit custom max_tokens is preserved even on reasoning models
    assert resolve_max_tokens("gemini-3.7-flash-high", 500, baseline_default=1024) == 500
    assert resolve_max_tokens("gemini-3.7-flash-high", 32768, baseline_default=1024) == 32768
    assert resolve_max_tokens("gemini-3.7-flash-high", 65536, baseline_default=1024) == 65536

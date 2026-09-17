"""Model Archetypes & Routing Module for CCBA AI Gateway.

Provides standardized model constants and routing helpers according to the
AI Gateway Client Integration Contract.
"""

from __future__ import annotations


class ModelArchetype:
    """Standard Model Archetypes for CCBA AI Gateway on Server Spark."""

    # Archetype 1: OCR & Vision Ingestion (Google AI Studio Direct 10 keys)
    OCR = "ocr-primary"
    OCR_FALLBACK = "ocr-fallback"
    OCR_TIER4 = "ocr-tier4"

    # Archetype 2: Standard General / Coding (Google API + Centralized Proxy)
    STANDARD = "gemini-3.7-flash"
    STANDARD_MEDIUM = "gemini-3.7-flash-medium"
    STANDARD_TEXT_GEMMA = "text-gemma"
    GEMINI_38_FLASH = "gemini-3.8-flash"

    # Archetype 3: Deep Reasoning / Complex Audit (Google API + Centralized Proxy)
    REASONING = "gemini-3.7-flash-high"
    REASONING_ALT = "claude-sonnet-4-6-thinking"
    REASONING_GEMMA = "reasoning-gemma"
    GEMINI_31_PRO_HIGH = "gemini-3.1-pro-high"
    CLAUDE_OPUS_46 = "claude-opus-4-6"

    # Archetype 4: Local Private / Zero-Cost (vLLM Qwen 35B Local GPU DGX)
    LOCAL = "qwen-local-primary"
    RAG = "rag-core"

    # Archetype 5: Embeddings
    EMBEDDING = "gemini-embedding-2"


def choose_model(task_type: str) -> str:
    """Route a given task type to its recommended model archetype alias.

    Args:
        task_type: Descriptive task string (e.g. 'ocr', 'coding', 'reasoning',
            'research', 'fast', 'private', 'vietnamese', 'embedding').

    Returns:
        The target model name alias on AI Gateway.
    """
    routing = {
        "ocr": ModelArchetype.OCR,
        "vision": ModelArchetype.STANDARD,
        "coding": ModelArchetype.STANDARD,
        "general": ModelArchetype.STANDARD,
        "fast": ModelArchetype.STANDARD,
        "reasoning": ModelArchetype.REASONING,
        "audit": ModelArchetype.REASONING,
        "research": ModelArchetype.REASONING,
        "legal": ModelArchetype.REASONING,
        "private": ModelArchetype.LOCAL,
        "local": ModelArchetype.LOCAL,
        "rag": ModelArchetype.RAG,
        "vietnamese": ModelArchetype.LOCAL,
        "embedding": ModelArchetype.EMBEDDING,
    }
    return routing.get(task_type.lower().strip(), ModelArchetype.STANDARD)


def is_reasoning_model(model_name: str) -> bool:
    """Check if model name denotes a deep reasoning model with internal thinking.

    Args:
        model_name: Name or alias of the AI model.

    Returns:
        True if the model uses deep reasoning (Archetype 3 or contains thinking indicators).
    """
    if not model_name:
        return False
    name = model_name.lower().strip()
    return any(
        kw in name
        for kw in (
            "-high",
            "-thinking",
            "reasoning",
            "o1",
            "o3",
            ModelArchetype.REASONING.lower(),
            ModelArchetype.REASONING_ALT.lower(),
            ModelArchetype.REASONING_GEMMA.lower(),
        )
    )


def resolve_max_tokens(
    model_name: str,
    requested_max_tokens: int,
    baseline_default: int = 1024,
    reasoning_allocation: int = 16384,
) -> int:
    """Auto-allocate tokens for reasoning models if requested_max_tokens is at baseline default.

    If the caller explicitly passed a custom max_tokens (e.g. 500 or 32768),
    their custom value is respected and preserved.

    Args:
        model_name: Target model name.
        requested_max_tokens: The max_tokens value passed by caller.
        baseline_default: The default value used by caller (e.g. 1024 or 2048).
        reasoning_allocation: Target allocation for reasoning models (default 16384).

    Returns:
        The effective max_tokens to use for the API call.
    """
    if requested_max_tokens == baseline_default and is_reasoning_model(model_name):
        return reasoning_allocation
    return requested_max_tokens

"""prompting.py - Prompt Engineering Helpers and Iterative Evaluator-Optimizer Loops for CCBA AI SDK.

Provides XML envelope wrapping, tag extraction utilities, and Evaluator-Optimizer feedback loops
(Technique 15: Generator <-> Evaluator with feedback refinement).
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OptimizationStep:
    """Represents a single iteration step in an Evaluator-Optimizer loop."""

    iteration: int
    draft: str
    score: float
    feedback: str


@dataclass
class OptimizationResult:
    """Result of an Evaluator-Optimizer loop."""

    final_output: str
    iterations: int
    score: float
    passed: bool
    history: list[OptimizationStep] = field(default_factory=list)


def xml_envelope(
    tags: dict[str, Any] | list[tuple[str, Any]],
    indent: int = 0,
) -> str:
    """Wraps context, instructions, documents, and rules into well-structured XML envelopes.

    Args:
        tags: Dictionary or list of (tag_name, content) tuples.
        indent: Indentation level.

    Returns:
        Formatted XML string.

    Example:
        >>> xml_envelope({"instructions": "Summarize", "context": {"topic": "BIM"}})
        '<instructions>\\nSummarize\\n</instructions>\\n<context>\\n{"topic": "BIM"}\\n</context>'
    """
    items = tags.items() if isinstance(tags, dict) else tags
    blocks: list[str] = []
    pad = " " * indent

    for tag_name, content in items:
        clean_tag = tag_name.strip().replace(" ", "_")
        if isinstance(content, (dict, list)):
            body = json.dumps(content, ensure_ascii=False, indent=2)
        elif content is None:
            body = ""
        else:
            body = str(content).strip()

        block = f"{pad}<{clean_tag}>\n{body}\n{pad}</{clean_tag}>"
        blocks.append(block)

    return "\n\n".join(blocks)


def parse_xml_tags(text: str, tags: list[str] | None = None) -> dict[str, str]:
    """Extracts content between specified XML tags from a model response.

    Args:
        text: Raw text containing XML tags.
        tags: Optional list of tag names to extract. If None, extracts all found top-level tags.

    Returns:
        Dictionary mapping tag names to their inner text contents.
    """
    if not text:
        return {}

    extracted: dict[str, str] = {}

    if tags:
        for tag in tags:
            pattern = re.compile(rf"<{tag}>(.*?)</{tag}>", re.DOTALL | re.IGNORECASE)
            match = pattern.search(text)
            if match:
                extracted[tag] = match.group(1).strip()
    else:
        pattern = re.compile(r"<([a-zA-Z0-9_\-]+)>(.*?)</\1>", re.DOTALL)
        for match in pattern.finditer(text):
            tag_name = match.group(1)
            inner_text = match.group(2).strip()
            extracted[tag_name] = inner_text

    return extracted


async def _run_optimization_step(
    iteration: int,
    current_feedback: str | None,
    generator_fn: Callable[[str | None], Awaitable[str] | str],
    evaluator_fn: Callable[[str], Awaitable[tuple[float, str]] | tuple[float, str]],
) -> OptimizationStep:
    """Execute one generate-and-evaluate iteration and return an OptimizationStep."""
    raw_draft = generator_fn(current_feedback)
    draft = await raw_draft if isinstance(raw_draft, Awaitable) else str(raw_draft)

    raw_eval = evaluator_fn(draft)
    score, feedback = await raw_eval if isinstance(raw_eval, Awaitable) else raw_eval
    return OptimizationStep(iteration=iteration, draft=draft, score=score, feedback=feedback)


async def evaluator_optimizer_loop_async(
    generator_fn: Callable[[str | None], Awaitable[str] | str],
    evaluator_fn: Callable[[str], Awaitable[tuple[float, str]] | tuple[float, str]],
    max_iterations: int = 3,
    pass_score: float = 85.0,
) -> OptimizationResult:
    """Executes an asynchronous Evaluator-Optimizer refinement loop."""
    history: list[OptimizationStep] = []
    current_feedback: str | None = None
    best_draft = ""
    best_score = -1.0

    for iteration in range(1, max_iterations + 1):
        step = await _run_optimization_step(iteration, current_feedback, generator_fn, evaluator_fn)
        history.append(step)

        if step.score > best_score:
            best_score = step.score
            best_draft = step.draft

        if step.score >= pass_score:
            return OptimizationResult(
                final_output=step.draft,
                iterations=iteration,
                score=step.score,
                passed=True,
                history=history,
            )
        current_feedback = step.feedback

    return OptimizationResult(
        final_output=best_draft if best_draft else (history[-1].draft if history else ""),
        iterations=len(history),
        score=best_score if best_score >= 0 else 0.0,
        passed=False,
        history=history,
    )


def evaluator_optimizer_loop(
    generator_fn: Callable[[str | None], str],
    evaluator_fn: Callable[[str], tuple[float, str]],
    max_iterations: int = 3,
    pass_score: float = 85.0,
) -> OptimizationResult:
    """Synchronous convenience wrapper for evaluator_optimizer_loop_async."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        raise RuntimeError(
            "evaluator_optimizer_loop() cannot be called from within a running event loop. "
            "Please use 'await evaluator_optimizer_loop_async()' directly."
        )

    return asyncio.run(
        evaluator_optimizer_loop_async(
            generator_fn=generator_fn,
            evaluator_fn=evaluator_fn,
            max_iterations=max_iterations,
            pass_score=pass_score,
        )
    )

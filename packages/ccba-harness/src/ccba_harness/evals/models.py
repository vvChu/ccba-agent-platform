"""models.py - Data Transfer Objects for CCBA Evals Framework.

Provides structured dataclasses for evaluation items, score results, and summary reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalItem:
    """Represents an individual evaluation test case item."""

    id: str
    input_prompt: str | dict[str, Any]
    golden_answer: str | dict[str, Any] | None = None
    rubric: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoreResult:
    """Result of a single scorer evaluating an output."""

    scorer_name: str
    score: float  # Normalized score between 0.0 and 1.0
    raw_output: Any = None
    reasoning: str | None = None
    is_critical_fail: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalItemResult:
    """Comprehensive evaluation result for a single item across all scorers."""

    item_id: str
    task_output: Any
    scores: list[ScoreResult]
    composite_score: float  # Percentage score between 0.0 and 100.0
    passed: bool
    critical_failed: bool = False
    error: str | None = None
    exception: Exception | None = None


@dataclass
class EvalReport:
    """Summary report for an evaluation run across a dataset."""

    total_items: int
    passed_items: int
    failed_items: int
    overall_score: float  # Percentage score 0.0 - 100.0
    pass_rate: float  # Percentage of items passed 0.0 - 100.0
    item_results: list[EvalItemResult] = field(default_factory=list)
    summary_by_scorer: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

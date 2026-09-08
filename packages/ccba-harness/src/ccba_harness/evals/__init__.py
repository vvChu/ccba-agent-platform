"""CCBA Evals Framework — Public Interface for Evaluation Benchmarks & Scorers.

Provides local-first evaluation runners, code-based scorers, and model-based rubric judges.
"""

from __future__ import annotations

from .models import EvalItem, EvalItemResult, EvalReport, ScoreResult
from .runner import AutoItemScorer, EvalRunner, load_eval_dataset, run_eval_pipeline
from .scorers import (
    BaseScorer,
    ExactMatchScorer,
    JsonSchemaScorer,
    LengthBoundsScorer,
    LLMRubricScorer,
    RegexScorer,
)

__all__ = [
    "EvalItem",
    "ScoreResult",
    "EvalItemResult",
    "EvalReport",
    "BaseScorer",
    "ExactMatchScorer",
    "RegexScorer",
    "LengthBoundsScorer",
    "JsonSchemaScorer",
    "LLMRubricScorer",
    "EvalRunner",
    "AutoItemScorer",
    "load_eval_dataset",
    "run_eval_pipeline",
]

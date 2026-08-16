"""scorers.py - Scoring implementations for CCBA Evals Framework.

Provides Code-based scorers (ExactMatch, Regex, JsonSchema, Length) and Model-based scorers (LLMRubricScorer).
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from .models import EvalItem, ScoreResult


class BaseScorer(ABC):
    """Abstract base class for all evaluation scorers."""

    def __init__(
        self,
        name: str,
        weight: float = 1.0,
        is_critical: bool = False,
    ) -> None:
        self.name = name
        self.weight = weight
        self.is_critical = is_critical

    @abstractmethod
    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        """Evaluate task output against item and return a ScoreResult."""
        pass


class ExactMatchScorer(BaseScorer):
    """Deterministic exact match code-based scorer."""

    def __init__(
        self,
        name: str = "exact_match",
        weight: float = 1.0,
        is_critical: bool = False,
        case_sensitive: bool = False,
        strip_whitespace: bool = True,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.case_sensitive = case_sensitive
        self.strip_whitespace = strip_whitespace

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        golden_str = str(item.golden_answer) if item.golden_answer is not None else ""

        if self.strip_whitespace:
            out_str = out_str.strip()
            golden_str = golden_str.strip()

        if not self.case_sensitive:
            matched = out_str.lower() == golden_str.lower()
        else:
            matched = out_str == golden_str

        score = 1.0 if matched else 0.0
        is_crit_fail = self.is_critical and not matched

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=matched,
            reasoning="Exact match passed" if matched else "Exact match mismatch",
            is_critical_fail=is_crit_fail,
        )


class RegexScorer(BaseScorer):
    """Regex pattern matching code-based scorer."""

    def __init__(
        self,
        pattern: str,
        name: str = "regex_match",
        weight: float = 1.0,
        is_critical: bool = False,
        flags: int = re.IGNORECASE | re.DOTALL,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.pattern = pattern
        self.flags = flags
        self._compiled = re.compile(pattern, flags=flags)

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        matched = bool(self._compiled.search(out_str))
        score = 1.0 if matched else 0.0
        is_crit_fail = self.is_critical and not matched

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=matched,
            reasoning=f"Regex pattern '{self.pattern}' {'found' if matched else 'not found'}",
            is_critical_fail=is_crit_fail,
        )


class LengthBoundsScorer(BaseScorer):
    """Character/token length bounds validation scorer."""

    def __init__(
        self,
        name: str = "length_bounds",
        min_length: int = 0,
        max_length: int = 100_000,
        weight: float = 1.0,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.min_length = min_length
        self.max_length = max_length

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        length = len(str(output)) if output is not None else 0
        valid = self.min_length <= length <= self.max_length
        score = 1.0 if valid else 0.0
        is_crit_fail = self.is_critical and not valid

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=length,
            reasoning=f"Length {length} within [{self.min_length}, {self.max_length}]"
            if valid
            else f"Length {length} out of bounds [{self.min_length}, {self.max_length}]",
            is_critical_fail=is_crit_fail,
        )


class JsonSchemaScorer(BaseScorer):
    """Validates JSON structure and required keys."""

    def __init__(
        self,
        required_keys: list[str] | None = None,
        name: str = "json_schema",
        weight: float = 1.0,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.required_keys = required_keys or []

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        if isinstance(output, dict):
            parsed = output
        else:
            try:
                # Extract potential JSON block
                out_str = str(output).strip()
                if "```json" in out_str:
                    out_str = out_str.split("```json", 1)[1].split("```", 1)[0].strip()
                elif "```" in out_str:
                    out_str = out_str.split("```", 1)[1].split("```", 1)[0].strip()
                parsed = json.loads(out_str)
            except Exception as e:
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    raw_output=None,
                    reasoning=f"JSON parsing failed: {e}",
                    is_critical_fail=self.is_critical,
                )

        if not isinstance(parsed, dict):
            return ScoreResult(
                scorer_name=self.name,
                score=0.0,
                raw_output=parsed,
                reasoning="Parsed JSON is not an object/dict",
                is_critical_fail=self.is_critical,
            )

        missing = [k for k in self.required_keys if k not in parsed]
        if missing:
            return ScoreResult(
                scorer_name=self.name,
                score=0.0,
                raw_output=parsed,
                reasoning=f"Missing required keys: {missing}",
                is_critical_fail=self.is_critical,
            )

        return ScoreResult(
            scorer_name=self.name,
            score=1.0,
            raw_output=parsed,
            reasoning="Valid JSON with all required keys",
            is_critical_fail=False,
        )


class LLMRubricScorer(BaseScorer):
    """Model-based LLM-as-a-Judge Scorer with Chain-of-Thought Rubric."""

    def __init__(
        self,
        rubric: str | None = None,
        name: str = "llm_judge",
        weight: float = 1.0,
        is_critical: bool = False,
        model: str = "gemini-3.7-flash",
        ai_client: Any = None,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.default_rubric = rubric
        self.model = model
        self.ai_client = ai_client

    def _build_judge_prompt(self, output: Any, item: EvalItem) -> str:
        rubric_text = item.rubric or self.default_rubric or "Grade the correctness of the answer."
        input_text = (
            item.input_prompt
            if isinstance(item.input_prompt, str)
            else json.dumps(item.input_prompt, ensure_ascii=False)
        )
        output_text = str(output)
        golden_text = str(item.golden_answer) if item.golden_answer else "N/A"

        return f"""You are an expert impartial evaluation judge. You will evaluate an AI assistant's response against a specific rubric and reference.

<input_task>
{input_text}
</input_task>

<golden_reference>
{golden_text}
</golden_reference>

<assistant_response>
{output_text}
</assistant_response>

<rubric>
{rubric_text}
</rubric>

Evaluation Instructions:
1. Think step-by-step inside <thinking></thinking> tags to analyze whether the assistant response satisfies the rubric.
2. Provide a score inside <score></score> tags using a Likert scale integer from 1 to 5:
   - 1 = Completely incorrect / dangerous hallucination / severe rule violation
   - 2 = Poor / major issues or inaccuracies
   - 3 = Acceptable / minor flaws but captures the essence
   - 4 = Good / high quality and mostly accurate
   - 5 = Excellent / perfectly satisfies all rubric criteria

Also output either 'correct' (if score >= 3) or 'incorrect' (if score < 3) inside <correctness></correctness> tags."""

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        prompt = self._build_judge_prompt(output, item)

        client = self.ai_client
        if client is None:
            try:
                from ccba_ai import async_ai

                client = async_ai
            except ImportError:
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    reasoning="ccba_ai client not available and no custom ai_client provided",
                    is_critical_fail=self.is_critical,
                )

        try:
            # Execute chat completion
            if hasattr(client, "chat") and callable(client.chat):
                # Check if async or sync
                import asyncio

                if asyncio.iscoroutinefunction(client.chat):
                    raw_reply = await client.chat(prompt, model=self.model)
                else:
                    raw_reply = client.chat(prompt, model=self.model)
            else:
                raw_reply = str(client(prompt))

            reply_str = str(raw_reply)

            # Extract thinking
            thinking_match = re.search(r"<thinking>(.*?)</thinking>", reply_str, re.DOTALL)
            reasoning = thinking_match.group(1).strip() if thinking_match else reply_str

            # Extract score
            score_match = re.search(r"<score>([1-5])</score>", reply_str)
            if score_match:
                likert = int(score_match.group(1))
            else:
                # Fallback to correctness
                corr_match = re.search(
                    r"<correctness>(.*?)</correctness>", reply_str, re.IGNORECASE
                )
                if corr_match and "correct" in corr_match.group(1).lower():
                    likert = 4
                else:
                    likert = 1

            # Normalize Likert 1-5 -> 0.0 - 1.0
            norm_score = max(0.0, min(1.0, (likert - 1) / 4.0))
            is_crit_fail = self.is_critical and (likert == 1)

            return ScoreResult(
                scorer_name=self.name,
                score=norm_score,
                raw_output=likert,
                reasoning=reasoning,
                is_critical_fail=is_crit_fail,
                metadata={"likert_scale": likert},
            )

        except Exception as e:
            return ScoreResult(
                scorer_name=self.name,
                score=0.0,
                raw_output=None,
                reasoning=f"LLM judge evaluation failed: {e}",
                is_critical_fail=self.is_critical,
            )

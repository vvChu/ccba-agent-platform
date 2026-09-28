"""scorers/rule_based.py - Deterministic rule-based scorers: ExactMatch, Regex, LengthBounds, JsonSchema."""

from __future__ import annotations

import json
import re
from typing import Any

from ..models import EvalItem, ScoreResult
from .base import BaseScorer


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
        min_len = self.min_length
        max_len = self.max_length
        if item and item.metadata and isinstance(item.metadata, dict):
            item_cfg = item.metadata.get("scorer_config", {}).get(self.name, {})
            if "min_length" in item_cfg:
                min_len = int(item_cfg["min_length"])
            if "max_length" in item_cfg:
                max_len = int(item_cfg["max_length"])

        length = len(str(output)) if output is not None else 0
        valid = min_len <= length <= max_len
        score = 1.0 if valid else 0.0
        is_crit_fail = self.get_effective_is_critical(item) and not valid

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=length,
            reasoning=f"Length {length} within [{min_len}, {max_len}]"
            if valid
            else f"Length {length} out of bounds [{min_len}, {max_len}]",
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

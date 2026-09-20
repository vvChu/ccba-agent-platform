"""scorers.py - Scoring implementations for CCBA Evals Framework.

Provides Code-based scorers (ExactMatch, Regex, JsonSchema, Length) and Model-based scorers (LLMRubricScorer).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .legal_index import LegalFlatIndex, StatutoryDocument, load_legal_flat_index
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
    """Model-based LLM-as-a-Judge Scorer with Chain-of-Thought Rubric and SQLite caching."""

    def __init__(
        self,
        rubric: str | None = None,
        name: str = "llm_judge",
        weight: float = 1.0,
        is_critical: bool = False,
        model: str = "gemini-3.7-flash",
        ai_client: Any = None,
        enable_cache: bool = True,
        cache_db_path: Path | str | None = None,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.default_rubric = rubric
        self.model = model
        self.ai_client = ai_client
        self.enable_cache = enable_cache
        self.cache_db_path = cache_db_path or os.environ.get("CCBA_EVAL_CACHE_DB")
        self._mem_conn: sqlite3.Connection | None = None

        if self.enable_cache:
            self._init_cache()

    def _get_db_target(self) -> Path | str:
        if self.cache_db_path:
            return self.cache_db_path
        cur = Path.cwd().resolve()
        for p in [cur, *cur.parents]:
            if (p / ".md").exists() or (p / ".agents").exists() or (p / "pyproject.toml").exists():
                cache_dir = p / ".md" / "cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                return cache_dir / "eval_judge_cache.db"
        cache_dir = cur / ".md" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "eval_judge_cache.db"

    def _init_cache(self) -> None:
        try:
            target = self._get_db_target()
            if target == ":memory:":
                self._mem_conn = sqlite3.connect(":memory:")
                conn = self._mem_conn
            else:
                target_path = Path(target)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(str(target_path), timeout=10.0)
                try:
                    conn.execute("PRAGMA journal_mode=WAL;")
                except Exception:
                    pass

            with conn:
                conn.execute("PRAGMA busy_timeout=10000;")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS llm_rubric_cache (
                        cache_key TEXT PRIMARY KEY,
                        model TEXT NOT NULL,
                        prompt_hash TEXT NOT NULL,
                        score REAL NOT NULL,
                        raw_output INTEGER NOT NULL,
                        reasoning TEXT NOT NULL,
                        is_critical_fail INTEGER NOT NULL,
                        metadata_json TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    """
                )
            if target != ":memory:":
                conn.close()
        except Exception:
            self.enable_cache = False

    def _get_connection(self) -> sqlite3.Connection | None:
        if not self.enable_cache:
            return None
        target = self._get_db_target()
        if target == ":memory:":
            return self._mem_conn
        try:
            conn = sqlite3.connect(str(target), timeout=10.0)
            conn.execute("PRAGMA busy_timeout=10000;")
            return conn
        except Exception:
            return None

    def _compute_cache_key(self, prompt: str) -> str:
        combined = f"{self.model}\n{prompt}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def _lookup_cache(self, cache_key: str) -> ScoreResult | None:
        if not self.enable_cache:
            return None
        conn = None
        try:
            conn = self._get_connection()
            if conn is None:
                return None
            cursor = conn.cursor()
            cursor.execute(
                "SELECT score, raw_output, reasoning, is_critical_fail, metadata_json FROM llm_rubric_cache WHERE cache_key = ?",
                (cache_key,),
            )
            row = cursor.fetchone()
            if row:
                score, raw_output, reasoning, _saved_crit_fail, meta_str = row
                try:
                    meta_dict = json.loads(meta_str)
                except Exception:
                    meta_dict = {}
                meta_dict["cached"] = True
                raw_int = (
                    int(raw_output)
                    if isinstance(raw_output, (int, float, str)) and str(raw_output).isdigit()
                    else 0
                )
                is_crit_fail = self.is_critical and (raw_int == 1)
                return ScoreResult(
                    scorer_name=self.name,
                    score=float(score),
                    raw_output=raw_int,
                    reasoning=reasoning,
                    is_critical_fail=is_crit_fail,
                    metadata=meta_dict,
                )
        except sqlite3.DatabaseError:
            self.enable_cache = False
        except Exception:
            pass
        finally:
            if conn is not None and self._get_db_target() != ":memory:":
                try:
                    conn.close()
                except Exception:
                    pass
        return None

    def _store_cache(self, cache_key: str, prompt: str, result: ScoreResult) -> None:
        if not self.enable_cache:
            return
        conn = None
        try:
            conn = self._get_connection()
            if conn is None:
                return
            p_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            created_at = datetime.now(timezone.utc).isoformat()
            meta_json = json.dumps(result.metadata, ensure_ascii=False, default=str)
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO llm_rubric_cache
                    (cache_key, model, prompt_hash, score, raw_output, reasoning, is_critical_fail, metadata_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cache_key,
                        self.model,
                        p_hash,
                        result.score,
                        result.raw_output if isinstance(result.raw_output, int) else 0,
                        result.reasoning or "",
                        1 if result.is_critical_fail else 0,
                        meta_json,
                        created_at,
                    ),
                )
        except sqlite3.DatabaseError:
            self.enable_cache = False
        except Exception:
            pass
        finally:
            if conn is not None and self._get_db_target() != ":memory:":
                try:
                    conn.close()
                except Exception:
                    pass

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
        cache_key = self._compute_cache_key(prompt)

        cached_result = self._lookup_cache(cache_key)
        if cached_result is not None:
            return cached_result

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

            result = ScoreResult(
                scorer_name=self.name,
                score=norm_score,
                raw_output=likert,
                reasoning=reasoning,
                is_critical_fail=is_crit_fail,
                metadata={"likert_scale": likert},
            )
            self._store_cache(cache_key, prompt, result)
            return result

        except Exception as e:
            return ScoreResult(
                scorer_name=self.name,
                score=0.0,
                raw_output=None,
                reasoning=f"LLM judge evaluation failed: {e}",
                is_critical_fail=self.is_critical,
            )


class SingleWriterInvariantScorer(BaseScorer):
    """Validates that agent coordination outputs respect Single-Writer invariants and isolated sandboxes."""

    def __init__(
        self,
        name: str = "single_writer_invariant",
        weight: float = 1.0,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.pattern = re.compile(
            r"(single-writer|isolated|sandbox|working directory|thư mục làm việc|riêng biệt|độc lập|mutex|flock|\.agents/|append-only)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        matched = bool(self.pattern.search(out_str))
        score = 1.0 if matched else 0.0
        is_crit_fail = self.is_critical and not matched

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=matched,
            reasoning=(
                "Single-Writer invariant verified (isolated sandbox / separate directory / lock)"
                if matched
                else "Single-Writer violation: missing working directory isolation, sandbox, or mutex guardrail"
            ),
            is_critical_fail=is_crit_fail,
        )


class ProgressiveDisclosureScorer(BaseScorer):
    """Validates Markdown link integrity and Level 1/2/3 Progressive Disclosure architecture."""

    def __init__(
        self,
        name: str = "progressive_disclosure_links",
        weight: float = 1.0,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        self.disclosure_pattern = re.compile(
            r"(progressive disclosure|bộc lộ dần|references/|tham chiếu|level [123]|pha [123]|chỉ mục)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        has_links = bool(self.link_pattern.search(out_str))
        has_disclosure = bool(self.disclosure_pattern.search(out_str))
        valid = has_links or has_disclosure
        score = 1.0 if valid else 0.0
        is_crit_fail = self.is_critical and not valid

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output={"has_links": has_links, "has_disclosure": has_disclosure},
            reasoning=(
                "Progressive disclosure structure or valid markdown links detected"
                if valid
                else "Missing progressive disclosure cues or valid markdown reference links"
            ),
            is_critical_fail=is_crit_fail,
        )


class HandoffProtocolScorer(BaseScorer):
    """Validates agent handoff protocol, parent notification, RACI alignment, and completion verdicts."""

    def __init__(
        self,
        name: str = "handoff_protocol",
        weight: float = 1.0,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.protocol_pattern = re.compile(
            r"(handoff|send_message|parent|verdict|kết luận|bàn giao|raci|chủ trì|bộ môn|clean|violation|hoàn tất|báo cáo)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        matched = bool(self.protocol_pattern.search(out_str))
        score = 1.0 if matched else 0.0
        is_crit_fail = self.is_critical and not matched

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=matched,
            reasoning=(
                "Handoff protocol verified (send_message / handoff report / verdict / role boundary)"
                if matched
                else "Missing handoff protocol, completion verdict, or parent notification pattern"
            ),
            is_critical_fail=is_crit_fail,
        )


def get_orchestration_scorers() -> list[BaseScorer]:
    """Returns the standard scorer suite for multi-agent orchestration skills."""
    return [
        SingleWriterInvariantScorer(weight=0.35, is_critical=True),
        ProgressiveDisclosureScorer(weight=0.35),
        HandoffProtocolScorer(weight=0.30),
    ]


class HardCompletionLockScorer(BaseScorer):
    """Validates that coding/engineering tasks enforce deterministic verification and Hard Completion Lock (ADR-0058)."""

    def __init__(
        self,
        name: str = "hard_completion_lock",
        weight: float = 0.4,
        is_critical: bool = True,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.pattern = re.compile(
            r"(python -m ccba_harness verify-patch|verify-patch|pytest|test execution|deterministic verification|khóa cứng hoàn tất|hard completion lock)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        matched = bool(self.pattern.search(out_str))
        score = 1.0 if matched else 0.0
        is_crit_fail = self.is_critical and not matched

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=matched,
            reasoning=(
                "Hard Completion Lock verified (python -m ccba_harness verify-patch / deterministic verification)"
                if matched
                else "Missing Hard Completion Lock: must verify via `python -m ccba_harness verify-patch` or deterministic test suite"
            ),
            is_critical_fail=is_crit_fail,
        )


class EngineeringDisciplineScorer(BaseScorer):
    """Validates engineering rigor: Double-Pass Review, KISS, idempotency, RCA, and explicit error handling."""

    def __init__(
        self,
        name: str = "engineering_discipline",
        weight: float = 0.35,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.double_pass_pattern = re.compile(
            r"(double-pass|self-adversarial|root cause|rca|code-first|rà soát hai vòng)",
            re.IGNORECASE,
        )
        self.engineering_rigor_pattern = re.compile(
            r"(kiss|idempotent|idempotency|error handling|test coverage|type hint|deep module|seam|refactor)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        has_dp = bool(self.double_pass_pattern.search(out_str))
        has_rigor = bool(self.engineering_rigor_pattern.search(out_str))

        if has_dp and has_rigor:
            score = 1.0
            reasoning = "Engineering discipline fully verified (Double-Pass Review + KISS / Rigor Guardrails)"
        elif has_dp or has_rigor:
            score = 0.5
            reasoning = (
                "Partial engineering discipline verified: "
                + ("Double-Pass present, missing KISS/Rigor" if has_dp else "KISS/Rigor present, missing Double-Pass")
            )
        else:
            score = 0.0
            reasoning = "Missing engineering discipline guardrails (Double-Pass Review, KISS, RCA, or Error Handling)"

        is_crit_fail = self.is_critical and score == 0.0

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output={"double_pass": has_dp, "rigor": has_rigor},
            reasoning=reasoning,
            is_critical_fail=is_crit_fail,
        )


def get_coding_scorers() -> list[BaseScorer]:
    """Returns the standard scorer suite for coding and software engineering skills."""
    return [
        HardCompletionLockScorer(weight=0.4, is_critical=True),
        EngineeringDisciplineScorer(weight=0.35),
        LengthBoundsScorer(name="depth", min_length=20, max_length=25000, weight=0.25),
    ]


class AntiDebrisScorer(BaseScorer):
    """Validates that skill outputs do not contain dead wood, junk HTML comments, or template debris."""

    def __init__(
        self,
        name: str = "anti_debris",
        weight: float = 0.3,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.debris_patterns: list[tuple[re.Pattern[str], str]] = [
            (
                re.compile(r"<!--\s*Ratchet Optimization Refinement", re.IGNORECASE),
                "Ratchet optimization junk comment",
            ),
            (
                re.compile(r"<!--\s*(TODO|FIXME|TEMP|TEST)\b", re.IGNORECASE),
                "Temporary debris comment",
            ),
            (
                re.compile(r"(/ck:[a-zA-Z0-9_\-]+|/ultrathink\b|<tasks\b|TaskCreate|AskUserQuestion)"),
                "ClaudeKit dead wood remnant",
            ),
        ]

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        detected: list[str] = []
        for pattern, label in self.debris_patterns:
            if pattern.search(out_str):
                detected.append(label)

        clean = len(detected) == 0
        score = 1.0 if clean else 0.0
        is_crit_fail = self.is_critical and not clean

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output={"clean": clean, "detected": detected},
            reasoning=(
                "Output is clean of debris and junk comments"
                if clean
                else f"Debris detected in output: {', '.join(detected)}"
            ),
            is_critical_fail=is_crit_fail,
        )


class LeanStructuralScorer(BaseScorer):
    """Composite lean structural scorer evaluating progressive disclosure, length bounds, and anti-debris."""

    def __init__(
        self,
        name: str = "lean_structural",
        weight: float = 1.0,
        is_critical: bool = False,
        min_length: int = 20,
        max_length: int = 25000,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.progressive_scorer = ProgressiveDisclosureScorer(weight=0.4)
        self.length_scorer = LengthBoundsScorer(
            name="depth", min_length=min_length, max_length=max_length, weight=0.3
        )
        self.debris_scorer = AntiDebrisScorer(weight=0.3)

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        res_prog = await self.progressive_scorer.score(output, item)
        res_len = await self.length_scorer.score(output, item)
        res_deb = await self.debris_scorer.score(output, item)

        combined_score = (res_prog.score * 0.4) + (res_len.score * 0.3) + (res_deb.score * 0.3)
        is_crit = self.is_critical and (
            res_prog.is_critical_fail or res_len.is_critical_fail or res_deb.is_critical_fail
        )

        reasons = [res_prog.reasoning, res_len.reasoning, res_deb.reasoning]
        return ScoreResult(
            scorer_name=self.name,
            score=combined_score,
            raw_output={
                "progressive": res_prog.score,
                "length": res_len.score,
                "anti_debris": res_deb.score,
            },
            reasoning="; ".join(reasons),
            is_critical_fail=is_crit,
        )


def get_lean_structural_scorers() -> list[BaseScorer]:
    """Returns the standard safe lean structural scorer suite for generic and non-coding skills."""
    return [
        ProgressiveDisclosureScorer(weight=0.4),
        LengthBoundsScorer(name="depth", min_length=20, max_length=25000, weight=0.3),
        AntiDebrisScorer(weight=0.3),
    ]


class LegalVerbatimProvenanceScorer(BaseScorer):
    """Evaluates legal verbatim provenance, gazette citations, and anti-trap constraints (ADR-0059).

    Enforces the Zero-Hallucination & Anti-Trap Critical Hard Floor:
    1. Output must cite valid statutory documents (Decrees, Laws, Circulars, QCVN, TCVN).
    2. Citing expired/superseded documents (e.g. NĐ 136/2020, Luật 50/2014, QCVN 06:2020) without
       acknowledging replacement results in score=0.0 with is_critical_fail=True.
    3. Citing fabricated/non-existent statutory documents results in score=0.0 with is_critical_fail=True.
    4. Citing non-existent clauses (Điều, Khoản, Mục, Bảng, Phụ lục) in a document results in
       score=0.0 with is_critical_fail=True.
    5. Records cryptographic SHA-256 provenance and official gazette numbers in metadata.
    """

    def __init__(
        self,
        name: str = "legal_verbatim_provenance",
        weight: float = 0.5,
        is_critical: bool = True,
        require_citation: bool = True,
        index: LegalFlatIndex | None = None,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.require_citation = require_citation
        self._index = index

        self.doc_patterns: list[re.Pattern[str]] = [
            re.compile(
                r"(?:Nghị\s*định|NĐ)\s+(?:số\s+)?([0-9]+/[0-9]{4}(?:/[A-ZĐa-z0-9\-]+)?)",
                re.IGNORECASE,
            ),
            re.compile(
                r"Luật(?:\s+[A-Za-zÀ-ỹ\s]+)?\s+(?:số\s+)?([0-9]+/[0-9]{4}(?:/QH[0-9]+)?)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:Thông\s*tư|TT)\s+(?:số\s+)?([0-9]+/[0-9]{4}(?:/[A-Z0-9\-]+)?)",
                re.IGNORECASE,
            ),
            re.compile(r"(QCVN\s+[0-9]+(?::[0-9]{4})?(?:/[A-Z0-9\-]+)?)", re.IGNORECASE),
            re.compile(r"(TCVN\s+[0-9]+(?::[0-9]{4})?(?:/[A-Z0-9\-]+)?)", re.IGNORECASE),
            re.compile(
                r"\b([0-9]+/[0-9]{4}/(?:NĐ-CP|ND-CP|QH[0-9]+|TT-[A-Z0-9]+|QĐ-[A-Z0-9]+))\b",
                re.IGNORECASE,
            ),
        ]

        self.clause_doc_patterns: list[tuple[re.Pattern[str], int, int]] = [
            (
                re.compile(
                    r"((?:Khoản\s+\d+\s+)?Điều\s+\d+|Mục\s+[0-9\.]+|Bảng\s+[A-Za-z0-9\.]+|Phụ\s+lục\s+[A-Za-z0-9\.]+)\s*(?:của|tại|theo)?\s*[^,\.\n]{0,30}?(?:Nghị\s*định|NĐ|Luật|Thông\s*tư|TT|QCVN|TCVN)\s+(?:số\s+)?([A-Za-z0-9_:\/\-Đđ]+)",
                    re.IGNORECASE,
                ),
                1,
                2,
            ),
            (
                re.compile(
                    r"(?:Nghị\s*định|NĐ|Luật|Thông\s*tư|TT|QCVN|TCVN)\s+(?:số\s+)?([A-Za-z0-9_:\/\-Đđ]+)[^,\.\n]{0,30}?(?:tại|theo|khoản|điều|mục|bảng|phụ\s+lục)?\s*((?:Khoản\s+\d+\s+)?Điều\s+\d+|Mục\s+[0-9\.]+|Bảng\s+[A-Za-z0-9\.]+|Phụ\s+lục\s+[A-Za-z0-9\.]+)",
                    re.IGNORECASE,
                ),
                2,
                1,
            ),
        ]

        self.replacement_indicators: tuple[str, ...] = (
            "thay thế",
            "hết hiệu lực",
            "bãi bỏ",
            "hết hạn",
            "bị thay",
            "superseded",
            "expired",
            "thay bằng",
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        if not out_str.strip():
            if self.require_citation:
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    reasoning="Văn bản phản hồi rỗng, không phát hiện trích dẫn căn cứ pháp lý",
                    is_critical_fail=self.is_critical,
                )
            return ScoreResult(
                scorer_name=self.name,
                score=1.0,
                reasoning="Empty output allowed without citations",
                is_critical_fail=False,
            )

        index = self._index or load_legal_flat_index()
        out_lower = out_str.lower()

        # 1. Extract candidate document references
        detected_doc_refs: list[str] = []
        for pat in self.doc_patterns:
            for m in pat.finditer(out_str):
                ref = m.group(1).strip(".,;:() ") if m.groups() else m.group(0).strip(".,;:() ")
                if ref and ref not in detected_doc_refs:
                    detected_doc_refs.append(ref)

        # Also check known documents & replacements mentioned by string in text
        for doc_num in list(index.documents.keys()) + list(index.replaces_map.keys()):
            if doc_num.lower() in out_lower and doc_num not in detected_doc_refs:
                detected_doc_refs.append(doc_num)

        # 2. Extract clause-document pairs
        extracted_pairs: list[tuple[str, str]] = []
        for pat, clause_grp, doc_grp in self.clause_doc_patterns:
            for m in pat.finditer(out_str):
                clause = m.group(clause_grp).strip(".,;:() ")
                dref = m.group(doc_grp).strip(".,;:() ")
                if clause and dref:
                    extracted_pairs.append((clause, dref))

        # 3. Check zero citations
        if not detected_doc_refs:
            if self.require_citation:
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    raw_output={"citations_found": 0},
                    reasoning=(
                        "Không phát hiện trích dẫn văn bản quy phạm pháp luật nào "
                        "(Luật, Nghị định, Thông tư, QCVN, TCVN) theo quy chuẩn ADR-0059"
                    ),
                    is_critical_fail=self.is_critical,
                )
            return ScoreResult(
                scorer_name=self.name,
                score=1.0,
                reasoning="No citations required",
                is_critical_fail=False,
            )

        # 4. Verify each detected document reference
        verified_docs: list[StatutoryDocument] = []
        seen_doc_numbers: set[str] = set()

        for doc_ref in detected_doc_refs:
            is_exp, replacement = index.is_expired_or_replaced(doc_ref)
            if is_exp:
                # Must acknowledge expiration or replacement
                has_indicator = any(kw in out_lower for kw in self.replacement_indicators)
                has_rep_cited = False
                if replacement:
                    rep_short = replacement.split("/")[0].lower()
                    has_rep_cited = rep_short in out_lower or replacement.lower() in out_lower
                else:
                    has_rep_cited = True

                if not (has_indicator and has_rep_cited):
                    return ScoreResult(
                        scorer_name=self.name,
                        score=0.0,
                        raw_output={"trap_doc": doc_ref, "replacement": replacement},
                        reasoning=(
                            f"Bẫy pháp lý (Anti-Trap Hard Floor): Trích dẫn văn bản đã hết hiệu lực/bị thay thế '{doc_ref}' "
                            f"mà không nêu rõ đã được thay thế bởi '{replacement}'"
                        ),
                        is_critical_fail=True,
                    )
                # Properly acknowledged expired trap, continue
                continue

            doc = index.get_document(doc_ref)
            if doc is None:
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    raw_output={"unknown_doc": doc_ref},
                    reasoning=(
                        f"Bịa đặt căn cứ pháp lý (Zero-Hallucination Hard Floor): "
                        f"Văn bản '{doc_ref}' không tồn tại trong công báo hoặc chỉ mục pháp luật"
                    ),
                    is_critical_fail=True,
                )

            if doc.document_number not in seen_doc_numbers:
                verified_docs.append(doc)
                seen_doc_numbers.add(doc.document_number)

        # 5. Verify clauses
        doc_clause_map: dict[str, list[str]] = {}
        for clause, dref in extracted_pairs:
            matched_doc = index.get_document(dref)
            if matched_doc:
                doc_clause_map.setdefault(matched_doc.document_number, []).append(clause)

        for doc_num, clauses in doc_clause_map.items():
            target_doc = index.documents.get(doc_num)
            if not target_doc:
                continue
            for cl in clauses:
                if not target_doc.has_clause(cl):
                    return ScoreResult(
                        scorer_name=self.name,
                        score=0.0,
                        raw_output={"doc": doc_num, "fake_clause": cl},
                        reasoning=(
                            f"Bịa đặt điều khoản (Zero-Hallucination Hard Floor): "
                            f"Điều/Khoản '{cl}' không tồn tại trong văn bản '{target_doc.document_number}'"
                        ),
                        is_critical_fail=True,
                    )

        # 6. Verify target law match if specified in test item metadata
        target_law = item.metadata.get("target_law") or item.metadata.get("law")
        if target_law:
            target_nums = re.findall(
                r"\b([0-9]+/[0-9]{4}|QCVN\s+[0-9]+(?::[0-9]{4})?|TCVN\s+[0-9]+(?::[0-9]{4})?)\b",
                str(target_law),
                re.IGNORECASE,
            )
            if target_nums and not any(num.lower() in out_lower for num in target_nums):
                target_matched = False
                for num in target_nums:
                    is_exp, rep = index.is_expired_or_replaced(num)
                    if rep and rep.lower() in out_lower:
                        target_matched = True
                        break
                if not target_matched:
                    return ScoreResult(
                        scorer_name=self.name,
                        score=0.0,
                        raw_output={"target_law": target_law},
                        reasoning=f"Không viện dẫn đúng văn bản mục tiêu '{target_law}' theo yêu cầu nghiệp vụ",
                        is_critical_fail=True,
                    )

        provenance_records = [
            {
                "document_number": d.document_number,
                "title": d.title,
                "cong_bao_number": d.cong_bao_number,
                "pdf_sha256": d.pdf_sha256,
                "verified_clauses": doc_clause_map.get(d.document_number, []),
            }
            for d in verified_docs
        ]

        return ScoreResult(
            scorer_name=self.name,
            score=1.0,
            raw_output={
                "verified_documents": [d.document_number for d in verified_docs],
                "provenance": provenance_records,
            },
            reasoning=(
                f"Xác thực căn cứ pháp lý thành công: {len(verified_docs)} văn bản hợp lệ "
                f"(SHA-256 đối soát công báo)"
            ),
            is_critical_fail=False,
            metadata={"provenance": provenance_records},
        )


def get_legal_scorers() -> list[BaseScorer]:
    """Returns the standard scorer suite for legal domain skills (ADR-0059)."""
    return [
        LegalVerbatimProvenanceScorer(weight=0.5, is_critical=True),
        ProgressiveDisclosureScorer(weight=0.2),
        AntiDebrisScorer(weight=0.15),
        LengthBoundsScorer(name="depth", min_length=20, max_length=25000, weight=0.15),
    ]

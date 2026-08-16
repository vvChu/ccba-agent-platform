"""test_evals_engine.py - Scoped Fast Unit Tests for CCBA Evals Framework.

Tests Code-based scorers, Model-based LLM rubric scoring, composite weighted calculations,
and critical fail guardrails.
"""

from __future__ import annotations

import asyncio

import pytest

from ccba_harness.evals import (
    EvalItem,
    EvalRunner,
    ExactMatchScorer,
    JsonSchemaScorer,
    LengthBoundsScorer,
    LLMRubricScorer,
    RegexScorer,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_exact_match_scorer():
    scorer = ExactMatchScorer(case_sensitive=False)
    item = EvalItem(id="t1", input_prompt="Hello", golden_answer="World")

    # Match
    res_pass = asyncio.run(scorer.score("world ", item))
    assert res_pass.score == 1.0
    assert not res_pass.is_critical_fail

    # Mismatch
    res_fail = asyncio.run(scorer.score("Earth", item))
    assert res_fail.score == 0.0


def test_regex_scorer():
    scorer = RegexScorer(pattern=r"QCVN\s*06:2022", is_critical=True)
    item = EvalItem(id="t2", input_prompt="Căn cứ pháp lý")

    res_pass = asyncio.run(scorer.score("Theo QCVN 06:2022/BXD quy định...", item))
    assert res_pass.score == 1.0
    assert not res_pass.is_critical_fail

    res_fail = asyncio.run(scorer.score("Theo TCVN 3890:2023...", item))
    assert res_fail.score == 0.0
    assert res_fail.is_critical_fail  # Critical rule triggered


def test_length_bounds_scorer():
    scorer = LengthBoundsScorer(min_length=10, max_length=50)
    item = EvalItem(id="t3", input_prompt="Write brief summary")

    res_ok = asyncio.run(scorer.score("This is a valid length output text.", item))
    assert res_ok.score == 1.0

    res_short = asyncio.run(scorer.score("Short", item))
    assert res_short.score == 0.0


def test_json_schema_scorer():
    scorer = JsonSchemaScorer(required_keys=["clause", "status", "finding"])
    item = EvalItem(id="t4", input_prompt="Audit PCCC")

    # Valid dict
    valid_dict = {"clause": "3.2.1", "status": "PASS", "finding": "Lối thoát nạn chuẩn"}
    res_dict = asyncio.run(scorer.score(valid_dict, item))
    assert res_dict.score == 1.0

    # Valid json string in markdown block
    json_md = (
        '```json\n{"clause": "3.2.1", "status": "PASS", "finding": "Lối thoát nạn chuẩn"}\n```'
    )
    res_md = asyncio.run(scorer.score(json_md, item))
    assert res_md.score == 1.0

    # Missing keys
    missing_dict = {"clause": "3.2.1"}
    res_missing = asyncio.run(scorer.score(missing_dict, item))
    assert res_missing.score == 0.0


def test_llm_rubric_scorer_with_mock():
    class MockAIClient:
        async def chat(self, prompt: str, model: str = "") -> str:
            return """<thinking>
The assistant correctly identified the fire resistance rating and cited QCVN 06:2022.
It fully satisfies all criteria in the rubric without flaws.
</thinking>
<score>5</score>
<correctness>correct</correctness>"""

    scorer = LLMRubricScorer(
        rubric="Must verify fire rating correctly.",
        ai_client=MockAIClient(),
        is_critical=True,
    )
    item = EvalItem(
        id="t5",
        input_prompt="Kiểm tra bậc chịu lửa",
        golden_answer="Bậc I",
    )

    res = asyncio.run(scorer.score("Công trình đạt Bậc I chịu lửa theo QCVN 06:2022.", item))
    assert res.score == 1.0  # (5 - 1) / 4 = 1.0
    assert "fire resistance rating" in (res.reasoning or "")
    assert not res.is_critical_fail


def test_llm_rubric_scorer_critical_fail():
    class MockFailingAIClient:
        async def chat(self, prompt: str, model: str = "") -> str:
            return """<thinking>
Severe error: The assistant cited an expired decree and fabricated test data.
</thinking>
<score>1</score>
<correctness>incorrect</correctness>"""

    scorer = LLMRubricScorer(
        rubric="Must not cite expired decree.",
        ai_client=MockFailingAIClient(),
        is_critical=True,
    )
    item = EvalItem(id="t6", input_prompt="Tra cứu pháp luật")

    res = asyncio.run(scorer.score("Áp dụng Nghị định 136/2020...", item))
    assert res.score == 0.0  # (1 - 1) / 4 = 0.0
    assert res.is_critical_fail  # Critical fail flagged


def test_eval_runner_async_execution():
    dataset = [
        EvalItem(id="case_1", input_prompt="Echo A", golden_answer="A"),
        EvalItem(id="case_2", input_prompt="Echo B", golden_answer="B"),
    ]

    async def mock_task(item: EvalItem) -> str:
        return item.golden_answer if item.golden_answer else ""

    scorers = [
        ExactMatchScorer(name="exact", weight=2.0),
        LengthBoundsScorer(name="length", min_length=1, max_length=10, weight=1.0),
    ]

    runner = EvalRunner(default_pass_threshold=85.0)
    report = asyncio.run(runner.run(dataset, mock_task, scorers))

    assert report.total_items == 2
    assert report.passed_items == 2
    assert report.failed_items == 0
    assert report.overall_score == 100.0
    assert report.pass_rate == 100.0
    assert "exact" in report.summary_by_scorer
    assert report.summary_by_scorer["exact"] == 100.0


def test_eval_runner_critical_fail_blocks_pass():
    dataset = [
        EvalItem(id="case_crit", input_prompt="Test crit", golden_answer="A"),
    ]

    # Task returns output that passes length (weight 10) but fails critical exact match (weight 1)
    async def mock_task(item: EvalItem) -> str:
        return "Long text that is not A"

    scorers = [
        ExactMatchScorer(name="exact_crit", weight=1.0, is_critical=True),
        LengthBoundsScorer(name="length_heavy", min_length=1, max_length=100, weight=10.0),
    ]

    runner = EvalRunner(default_pass_threshold=80.0)
    report = asyncio.run(runner.run(dataset, mock_task, scorers))

    # Composite score would be (10*1.0 + 1*0) / 11 * 100 = 90.91%
    # But because exact_crit is critical and failed, the item MUST fail!
    item_res = report.item_results[0]
    assert item_res.composite_score > 80.0
    assert item_res.critical_failed
    assert not item_res.passed
    assert report.passed_items == 0
    assert report.failed_items == 1


def test_eval_runner_sync_execution():
    dataset = [
        EvalItem(id="sync_case", input_prompt="Sync task", golden_answer="OK"),
    ]

    def sync_task(item: EvalItem) -> str:
        return "OK"

    scorers = [ExactMatchScorer(name="sync_exact")]
    runner = EvalRunner()
    report = runner.run_sync(dataset, sync_task, scorers)

    assert report.total_items == 1
    assert report.passed_items == 1
    assert report.overall_score == 100.0

"""test_evals_engine.py - Scoped Fast Unit Tests for CCBA Evals Framework.

Tests Code-based scorers, Model-based LLM rubric scoring, composite weighted calculations,
and critical fail guardrails.
"""

from __future__ import annotations

import asyncio
import json

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
from ccba_harness.evals.runner import load_eval_dataset

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


def test_llm_rubric_scorer_sqlite_cache(tmp_path):
    """Verify that LLMRubricScorer uses SQLite cache to avoid duplicate LLM calls."""

    class CountingMockAIClient:
        def __init__(self):
            self.call_count = 0

        async def chat(self, prompt: str, model: str = "") -> str:
            self.call_count += 1
            return """<thinking>Correct</thinking>
<score>4</score>
<correctness>correct</correctness>"""

    client = CountingMockAIClient()
    db_path = tmp_path / "cache.db"
    scorer = LLMRubricScorer(
        rubric="Must be accurate.",
        ai_client=client,
        enable_cache=True,
        cache_db_path=db_path,
    )
    item = EvalItem(id="cache_test_1", input_prompt="Question 1", golden_answer="Answer 1")

    # First invocation: cache miss -> calls LLM
    res1 = asyncio.run(scorer.score("Answer 1 output", item))
    assert res1.score == 0.75  # (4 - 1) / 4 = 0.75
    assert client.call_count == 1
    assert not res1.metadata.get("cached")

    # Second invocation: cache hit -> does NOT call LLM
    res2 = asyncio.run(scorer.score("Answer 1 output", item))
    assert res2.score == 0.75
    assert client.call_count == 1  # Still 1!
    assert res2.metadata.get("cached") is True

    # Different output: cache miss -> calls LLM
    res3 = asyncio.run(scorer.score("Different output", item))
    assert res3.score == 0.75
    assert client.call_count == 2
    assert not res3.metadata.get("cached")

    # When enable_cache is False, always calls LLM
    no_cache_scorer = LLMRubricScorer(
        rubric="Must be accurate.",
        ai_client=client,
        enable_cache=False,
    )
    res4 = asyncio.run(no_cache_scorer.score("Answer 1 output", item))
    assert client.call_count == 3
    assert not res4.metadata.get("cached")


def test_load_eval_dataset_difficulty_and_limit(tmp_path):
    """Verify that dataset loading respects difficulty and limit filters."""
    data = [
        {"id": "d1", "input_prompt": "P1", "metadata": {"difficulty": "easy"}},
        {"id": "d2", "input_prompt": "P2", "metadata": {"difficulty": "medium"}},
        {"id": "d3", "input_prompt": "P3", "metadata": {"difficulty": "hard"}},
        {"id": "d4", "input_prompt": "P4", "difficulty": "hard"},  # direct attribute
        {"id": "d5", "input_prompt": "P5", "metadata": {"difficulty": "easy"}},
    ]
    ds_file = tmp_path / "dataset.json"
    ds_file.write_text(json.dumps(data), encoding="utf-8")

    # Filter by difficulty
    hard_items = load_eval_dataset(dataset_path=ds_file, difficulty="hard")
    assert len(hard_items) == 2
    assert {it.id for it in hard_items} == {"d3", "d4"}

    # Filter by limit
    limited_items = load_eval_dataset(dataset_path=ds_file, limit=3)
    assert len(limited_items) == 3
    assert [it.id for it in limited_items] == ["d1", "d2", "d3"]

    # Filter by both difficulty and limit
    both_items = load_eval_dataset(dataset_path=ds_file, difficulty="hard", limit=1)
    assert len(both_items) == 1
    assert both_items[0].id == "d3"


def test_load_eval_dataset_zero_and_negative_limit(tmp_path):
    """Verify limit=0 and negative limits correctly return empty list."""
    data = [
        {"id": "d1", "input_prompt": "P1"},
        {"id": "d2", "input_prompt": "P2"},
    ]
    ds_file = tmp_path / "ds.json"
    ds_file.write_text(json.dumps(data), encoding="utf-8")

    assert len(load_eval_dataset(dataset_path=ds_file, limit=0)) == 0
    assert len(load_eval_dataset(dataset_path=ds_file, limit=-1)) == 0


def test_llm_rubric_scorer_critical_fail_cache_independence(tmp_path):
    """Verify is_critical_fail is dynamically evaluated per scorer instance, not blindly loaded from cache row."""

    class FailingMockAIClient:
        async def chat(self, prompt: str, model: str = "") -> str:
            return "<thinking>Total fail</thinking>\n<score>1</score>\n<correctness>incorrect</correctness>"

    client = FailingMockAIClient()
    db_path = tmp_path / "crit_cache.db"
    item = EvalItem(id="crit_test_1", input_prompt="Q", golden_answer="A")

    # Scorer A has is_critical=False -> Likert 1 is NOT critical fail
    scorer_non_crit = LLMRubricScorer(
        rubric="Test",
        ai_client=client,
        is_critical=False,
        cache_db_path=db_path,
    )
    res_a = asyncio.run(scorer_non_crit.score("output", item))
    assert res_a.score == 0.0
    assert res_a.is_critical_fail is False

    # Scorer B has is_critical=True -> Same item hits cache, MUST evaluate to is_critical_fail=True
    scorer_crit = LLMRubricScorer(
        rubric="Test",
        ai_client=client,
        is_critical=True,
        cache_db_path=db_path,
    )
    res_b = asyncio.run(scorer_crit.score("output", item))
    assert res_b.score == 0.0
    assert res_b.metadata.get("cached") is True
    assert res_b.is_critical_fail is True


def test_llm_rubric_scorer_corrupted_db_fallback(tmp_path):
    """Verify corrupted database gracefully disables cache and falls back to direct LLM call."""

    class MockAIClient:
        def __init__(self):
            self.calls = 0

        async def chat(self, prompt: str, model: str = "") -> str:
            self.calls += 1
            return "<score>5</score>"

    corrupted_db = tmp_path / "corrupted.db"
    corrupted_db.write_bytes(b"NOT A VALID SQLITE DB FILE HEADER CONTENT")

    client = MockAIClient()
    scorer = LLMRubricScorer(
        rubric="Test",
        ai_client=client,
        enable_cache=True,
        cache_db_path=corrupted_db,
    )
    assert scorer.enable_cache is False
    res = asyncio.run(scorer.score("Response text", EvalItem(id="test", input_prompt="Prompt")))
    assert client.calls == 1
    assert res.score == 1.0
    assert res.raw_output == 5


def test_orchestration_scorers():
    """Verify OrchestrationScorers evaluate single-writer, progressive disclosure, and handoff protocols."""
    from ccba_harness.evals.scorers import (
        HandoffProtocolScorer,
        ProgressiveDisclosureScorer,
        SingleWriterInvariantScorer,
        get_orchestration_scorers,
    )

    item = EvalItem(id="orch1", input_prompt="Teamwork preview task")

    # 1. SingleWriterInvariantScorer
    sw_scorer = SingleWriterInvariantScorer(is_critical=True)
    res_sw_pass = asyncio.run(
        sw_scorer.score(
            "Working in isolated sandbox directory .agents/worker_1 with append-only log",
            item,
        )
    )
    assert res_sw_pass.score == 1.0
    assert not res_sw_pass.is_critical_fail

    res_sw_fail = asyncio.run(
        sw_scorer.score("Writing directly to shared repo root files concurrently", item)
    )
    assert res_sw_fail.score == 0.0
    assert res_sw_fail.is_critical_fail

    # 2. ProgressiveDisclosureScorer
    pd_scorer = ProgressiveDisclosureScorer()
    res_pd_pass = asyncio.run(
        pd_scorer.score(
            "Refer to [references/discovery.md](references/discovery.md) for Level 2 instructions.",
            item,
        )
    )
    assert res_pd_pass.score == 1.0

    res_pd_fail = asyncio.run(
        pd_scorer.score("Plain flat text without any links or references.", item)
    )
    assert res_pd_fail.score == 0.0

    # 3. HandoffProtocolScorer
    hp_scorer = HandoffProtocolScorer()
    res_hp_pass = asyncio.run(
        hp_scorer.score(
            "Audit report saved to handoff.md. Verdict: CLEAN. send_message sent to parent.",
            item,
        )
    )
    assert res_hp_pass.score == 1.0

    res_hp_fail = asyncio.run(hp_scorer.score("Task finished without notifying anyone.", item))
    assert res_hp_fail.score == 0.0

    # 4. get_orchestration_scorers factory
    suite = get_orchestration_scorers()
    assert len(suite) == 3
    assert any(s.name == "single_writer_invariant" for s in suite)
    assert any(s.name == "progressive_disclosure_links" for s in suite)
    assert any(s.name == "handoff_protocol" for s in suite)

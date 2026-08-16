"""test_prompting.py - Scoped Fast Unit Tests for ccba_ai.prompting.

Tests XML envelope formatting, XML tag extraction, and Evaluator-Optimizer refinement loops.
"""

from __future__ import annotations

import asyncio

import pytest

from ccba_ai.prompting import (
    OptimizationResult,
    evaluator_optimizer_loop,
    evaluator_optimizer_loop_async,
    parse_xml_tags,
    xml_envelope,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_xml_envelope_dict_and_list():
    """Test wrapping dictionaries and lists in XML envelopes."""
    payload = {
        "instructions": "Hãy tóm tắt văn bản",
        "context": {"topic": "QCVN 06:2022/BXD", "scope": "PCCC"},
        "documents": ["Doc 1", "Doc 2"],
    }
    result = xml_envelope(payload)

    assert "<instructions>\nHãy tóm tắt văn bản\n</instructions>" in result
    assert "<context>\n{\n" in result
    assert '"topic": "QCVN 06:2022/BXD"' in result
    assert "<documents>\n[\n" in result


def test_xml_envelope_list_of_tuples():
    """Test wrapping list of key-value tuples with indentation."""
    items = [
        ("task", "Kiểm tra giới hạn chịu lửa"),
        ("rubric", "Bậc II chịu lửa tối thiểu RE 60"),
    ]
    result = xml_envelope(items, indent=2)

    assert "  <task>\nKiểm tra giới hạn chịu lửa\n  </task>" in result
    assert "  <rubric>\nBậc II chịu lửa tối thiểu RE 60\n  </rubric>" in result


def test_parse_xml_tags_all_and_specific():
    """Test extracting all tags vs specific tags from model response."""
    response_text = """
    <thinking>
    Phân tích yêu cầu bậc chịu lửa theo Bảng 4 QCVN 06:2022.
    </thinking>
    <score>4</score>
    <answer>
    Công trình yêu cầu Bậc II chịu lửa.
    </answer>
    """
    # Extract all
    extracted_all = parse_xml_tags(response_text)
    assert extracted_all["thinking"].startswith("Phân tích yêu cầu")
    assert extracted_all["score"] == "4"
    assert "Bậc II" in extracted_all["answer"]

    # Extract specific tags
    extracted_spec = parse_xml_tags(response_text, tags=["score", "answer"])
    assert "thinking" not in extracted_spec
    assert extracted_spec["score"] == "4"
    assert "Bậc II" in extracted_spec["answer"]


def test_evaluator_optimizer_loop_pass_first_iteration():
    """Test loop completing immediately when first draft meets pass_score."""

    async def run_test():
        async def mock_generator(feedback: str | None) -> str:
            return "Bản thảo hoàn hảo ngay từ đầu"

        async def mock_evaluator(draft: str) -> tuple[float, str]:
            return 95.0, "Xuất sắc"

        res: OptimizationResult = await evaluator_optimizer_loop_async(
            generator_fn=mock_generator,
            evaluator_fn=mock_evaluator,
            max_iterations=3,
            pass_score=85.0,
        )

        assert res.passed is True
        assert res.iterations == 1
        assert res.score == 95.0
        assert res.final_output == "Bản thảo hoàn hảo ngay từ đầu"
        assert len(res.history) == 1

    asyncio.run(run_test())


def test_evaluator_optimizer_loop_refinement_success():
    """Test loop improving draft iteratively using feedback."""

    async def run_test():
        generation_calls = []

        async def mock_generator(feedback: str | None) -> str:
            generation_calls.append(feedback)
            if feedback is None:
                return "Bản thảo sơ sài v1"
            return f"Bản thảo đã sửa theo: {feedback}"

        async def mock_evaluator(draft: str) -> tuple[float, str]:
            if "sơ sài" in draft:
                return 60.0, "Cần bổ sung viện dẫn QCVN 06:2022/BXD"
            return 90.0, "Đã đạt yêu cầu"

        res: OptimizationResult = await evaluator_optimizer_loop_async(
            generator_fn=mock_generator,
            evaluator_fn=mock_evaluator,
            max_iterations=3,
            pass_score=85.0,
        )

        assert res.passed is True
        assert res.iterations == 2
        assert res.score == 90.0
        assert "QCVN 06:2022/BXD" in res.final_output
        assert len(res.history) == 2
        assert generation_calls[0] is None
        assert generation_calls[1] == "Cần bổ sung viện dẫn QCVN 06:2022/BXD"

    asyncio.run(run_test())


def test_evaluator_optimizer_loop_max_iterations_exceeded():
    """Test loop respecting max_iterations limit when draft never meets threshold."""

    async def run_test():
        async def mock_generator(feedback: str | None) -> str:
            return "Bản thảo không đạt"

        async def mock_evaluator(draft: str) -> tuple[float, str]:
            return 50.0, "Chưa đạt"

        res: OptimizationResult = await evaluator_optimizer_loop_async(
            generator_fn=mock_generator,
            evaluator_fn=mock_evaluator,
            max_iterations=3,
            pass_score=85.0,
        )

        assert res.passed is False
        assert res.iterations == 3
        assert res.score == 50.0
        assert len(res.history) == 3

    asyncio.run(run_test())


def test_evaluator_optimizer_loop_sync_execution():
    """Test synchronous execution wrapper."""

    def mock_generator(feedback: str | None) -> str:
        return "Sync Draft"

    def mock_evaluator(draft: str) -> tuple[float, str]:
        return 92.0, "Good"

    res = evaluator_optimizer_loop(
        generator_fn=mock_generator,
        evaluator_fn=mock_evaluator,
        max_iterations=3,
        pass_score=85.0,
    )

    assert res.passed is True
    assert res.iterations == 1
    assert res.score == 92.0

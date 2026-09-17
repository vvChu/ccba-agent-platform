"""Automated Benchmark Evaluation Suite for CCBA AI Models.

Evaluates candidate models against Golden Benchmarks across 5 criteria:
1. JSON Structured Output Adherence
2. Legal Verbatim Grounding (ADR-0059)
3. Python Code Syntax & PEP 8 Completeness
4. Multi-Step Reasoning Conflict Audit
5. Latency Probe & Token Overhead
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ccba_ai.client import AIClient
from ccba_ai.llm_utils import parse_llm_json
from ccba_ai.routing import ModelArchetype

logger = logging.getLogger("ccba_ai.eval")

DEFAULT_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "eval_benchmarks.json"
)


@dataclass
class TestCaseResult:
    """Evaluation result for a single benchmark test case."""

    case_id: str
    category: str
    title: str
    passed: bool
    latency_s: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    error_message: str | None = None
    output_preview: str = ""


@dataclass
class ModelEvalSummary:
    """Aggregated evaluation metrics for a specific model."""

    model_name: str
    total_cases: int
    passed_cases: int
    avg_latency_s: float
    p95_latency_s: float
    total_tokens: int
    case_results: list[TestCaseResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return (self.passed_cases / self.total_cases * 100.0) if self.total_cases else 0.0


def validate_case_output(case: dict[str, Any], raw_output: str) -> tuple[bool, str | None]:
    """Validate model output against case validation rules."""
    val_type = case.get("validation_type", "")
    text = raw_output.strip()

    if val_type == "json_keys":
        try:
            data = parse_llm_json(text)
            if not isinstance(data, dict):
                return False, f"Expected JSON dict, got {type(data).__name__}"
            expected = case.get("expected_keys", [])
            missing = [k for k in expected if k not in data]
            if missing:
                return False, f"Missing required JSON keys: {missing}"
            return True, None
        except Exception as e:
            return False, f"JSON parse error: {e}"

    elif val_type == "verbatim_keywords":
        expected = case.get("expected_keywords", [])
        missing = [kw for kw in expected if kw.lower() not in text.lower()]
        if missing:
            return False, f"Missing expected legal entities/keywords: {missing}"
        return True, None

    elif val_type == "code_ast":
        # Extract code block if wrapped in markdown
        code = text
        if "```python" in code:
            code = code.split("```python", 1)[1].split("```", 1)[0]
        elif "```" in code:
            code = code.split("```", 1)[1].split("```", 1)[0]
        try:
            ast.parse(code)
        except SyntaxError as se:
            return False, f"Python SyntaxError: {se}"
        expected = case.get("expected_keywords", [])
        missing = [kw for kw in expected if kw not in code]
        if missing:
            return False, f"Missing expected code tokens: {missing}"
        return True, None

    elif val_type == "decision_match":
        expected = case.get("expected_keywords", [])
        missing = [kw for kw in expected if kw.lower() not in text.lower()]
        if missing:
            return False, f"Audit reasoning missing conclusion keywords: {missing}"
        return True, None

    elif val_type == "exact_or_prefix":
        expected = case.get("expected_keywords", [])
        for kw in expected:
            if kw.lower() in text.lower():
                return True, None
        return False, f"Output did not match expected probe token: {expected}"

    return True, None


def setup_mock_benchmark_responses(provider: Any) -> None:
    """Register deterministic benchmark responses in MockProvider for offline testing."""
    if not hasattr(provider, "register_pattern"):
        return
    provider.register_pattern(
        "ccba tower",
        json.dumps(
            {
                "project_name": "CCBA Tower",
                "location": "Số 1 Hoàng Đạo Thúy, Cầu Giấy, Hà Nội",
                "building_area_m2": 1200,
                "height_m": 45,
                "floors_above": 15,
                "basements": 2,
            },
            ensure_ascii=False,
        ),
    )
    provider.register_pattern(
        "38/2026/qđ-ubnd",
        "Quyết định số 38/2026/QĐ-UBND áp dụng đối với Ủy ban nhân dân các cấp, Sở và Ủy ban nhân dân cấp xã.",
    )
    provider.register_pattern(
        "calculate_gross_floor_area",
        '```python\ndef calculate_gross_floor_area(floor_areas: list[float]) -> float:\n    """Calculate gross floor area."""\n    for a in floor_areas:\n        if a < 0:\n            raise ValueError(\'Area must be non-negative\')\n    return float(sum(floor_areas))\n```',
    )
    provider.register_pattern(
        "tổng mặt bằng 1/500",
        "UBND cấp xã không có thẩm quyền phê duyệt quy hoạch tổng mặt bằng 1/500 theo quy định. Kết luận: Không hợp lệ.",
    )
    provider.register_pattern(
        "phản hồi đúng 1 từ duy nhất",
        "OK",
    )


def evaluate_model_on_cases(
    client: AIClient,
    model: str,
    cases: list[dict[str, Any]],
) -> ModelEvalSummary:
    """Run all benchmark cases against target model and collect telemetry."""
    if client.mock_mode and hasattr(client, "mock_provider"):
        setup_mock_benchmark_responses(client.mock_provider)

    results: list[TestCaseResult] = []
    latencies: list[float] = []
    total_tokens = 0

    for case in cases:
        cid = case["id"]
        cat = case.get("category", "general")
        title = case.get("title", cid)
        prompt = case["prompt"]

        t0 = time.perf_counter()
        passed = False
        err_msg = None
        output_preview = ""
        p_tok = c_tok = r_tok = 0

        try:
            res = client.chat_with_metadata(prompt, model=model, temperature=0.0)
            latency = time.perf_counter() - t0
            latencies.append(latency)
            output_text = res.content
            output_preview = (output_text[:120] + "...") if len(output_text) > 120 else output_text

            if res.usage:
                p_tok = res.usage.prompt_tokens
                c_tok = res.usage.completion_tokens
                total_tokens += res.usage.total_tokens
                r_tok = getattr(res.usage, "reasoning_tokens", 0)

            passed, err_msg = validate_case_output(case, output_text)
        except Exception as exc:
            latency = time.perf_counter() - t0
            latencies.append(latency)
            passed = False
            err_msg = str(exc)

        results.append(
            TestCaseResult(
                case_id=cid,
                category=cat,
                title=title,
                passed=passed,
                latency_s=latency,
                prompt_tokens=p_tok,
                completion_tokens=c_tok,
                reasoning_tokens=r_tok,
                error_message=err_msg,
                output_preview=output_preview,
            )
        )

    latencies_sorted = sorted(latencies)
    avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
    p95_idx = int(len(latencies_sorted) * 0.95)
    p95_lat = latencies_sorted[p95_idx] if latencies_sorted else 0.0
    passed_count = sum(1 for r in results if r.passed)

    return ModelEvalSummary(
        model_name=model,
        total_cases=len(cases),
        passed_cases=passed_count,
        avg_latency_s=avg_lat,
        p95_latency_s=p95_lat,
        total_tokens=total_tokens,
        case_results=results,
    )


def generate_markdown_report(
    target_summary: ModelEvalSummary,
    baseline_summary: ModelEvalSummary | None = None,
) -> str:
    """Generate professional Markdown comparison report."""
    lines: list[str] = []
    lines.append("# CCBA Model Benchmark Evaluation Report")
    lines.append("")
    lines.append(f"- **Target Candidate**: `{target_summary.model_name}`")
    if baseline_summary:
        lines.append(f"- **Baseline Reference**: `{baseline_summary.model_name}`")
    lines.append(f"- **Total Benchmark Cases**: {target_summary.total_cases}")
    lines.append("")

    # Summary table
    lines.append("## 1. Overall Performance Matrix")
    lines.append("")
    lines.append("| Metric | Target Candidate | Baseline | Status |")
    lines.append("| :--- | :---: | :---: | :---: |")
    target_pr = f"{target_summary.pass_rate:.1f}% ({target_summary.passed_cases}/{target_summary.total_cases})"
    base_pr = (
        f"{baseline_summary.pass_rate:.1f}% ({baseline_summary.passed_cases}/{baseline_summary.total_cases})"
        if baseline_summary
        else "N/A"
    )
    pr_status = "[PASSED]" if target_summary.pass_rate >= 80.0 else "[FAILED]"
    lines.append(f"| **Pass Rate** | {target_pr} | {base_pr} | {pr_status} |")

    target_lat = f"{target_summary.avg_latency_s:.2f}s (P95: {target_summary.p95_latency_s:.2f}s)"
    base_lat = (
        f"{baseline_summary.avg_latency_s:.2f}s (P95: {baseline_summary.p95_latency_s:.2f}s)"
        if baseline_summary
        else "N/A"
    )
    lines.append(f"| **Latency (Avg / P95)** | {target_lat} | {base_lat} | [MEASURED] |")
    base_tokens = f"{baseline_summary.total_tokens:,}" if baseline_summary else "N/A"
    lines.append(
        f"| **Total Tokens** | {target_summary.total_tokens:,} | {base_tokens} | [MEASURED] |"
    )
    lines.append("")

    # Detail breakdown
    lines.append("## 2. Test Case Breakdown")
    lines.append("")
    lines.append("| Case ID | Category | Status | Latency | Tokens | Details |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :--- |")
    for r in target_summary.case_results:
        status_icon = "[Pass]" if r.passed else "[Fail]"
        tok_info = f"{r.prompt_tokens} in / {r.completion_tokens} out"
        detail = r.error_message if not r.passed else "Valid response"
        lines.append(
            f"| `{r.case_id}` | {r.category} | {status_icon} | {r.latency_s:.2f}s | {tok_info} | {detail} |"
        )
    lines.append("")

    # Upgrade Recommendation
    lines.append("## 3. Platform Upgrade Recommendation")
    lines.append("")
    if target_summary.pass_rate >= 80.0:
        lines.append(
            f"[RECOMMEND APPROVAL]: Candidate `{target_summary.model_name}` achieved "
            f"{target_summary.pass_rate:.1f}% pass rate on Golden Benchmarks.\n"
            f"It is safe to promote this model to `ModelArchetype.STANDARD` in `packages/ccba-ai/src/ccba_ai/routing.py`."
        )
    else:
        lines.append(
            f"[HOLD / REJECT]: Candidate `{target_summary.model_name}` pass rate ({target_summary.pass_rate:.1f}%) "
            f"is below the 80% threshold. Do not promote."
        )
    lines.append("")

    return "\n".join(lines)


def run_eval_benchmark(
    target_model: str,
    baseline_model: str | None = None,
    mock: bool = False,
    fixtures_path: Path | None = None,
) -> int:
    """Execute complete benchmark evaluation suite."""
    fpath = fixtures_path or DEFAULT_FIXTURE_PATH
    if not fpath.is_file():
        logger.error(f"Benchmark fixtures not found: {fpath}")
        return 1

    with open(fpath, encoding="utf-8") as f:
        cases = json.load(f)

    if mock:
        os.environ["CCBA_AI_MOCK"] = "1"

    client = AIClient()

    print(f"[*] Running Golden Benchmarks ({len(cases)} cases) on target: {target_model}...")
    target_summary = evaluate_model_on_cases(client, target_model, cases)

    baseline_summary = None
    if baseline_model:
        print(f"[*] Running Golden Benchmarks on baseline: {baseline_model}...")
        baseline_summary = evaluate_model_on_cases(client, baseline_model, cases)

    report = generate_markdown_report(target_summary, baseline_summary)
    print("\n" + report)

    return 0 if target_summary.pass_rate >= 80.0 else 1


def main(argv: list[str] | None = None) -> int:
    """CLI parser for ccba_ai eval-models."""
    parser = argparse.ArgumentParser(
        prog="python -m ccba_ai eval-models",
        description="Run automated Golden Benchmarks on candidate LLM models.",
    )
    parser.add_argument(
        "--target",
        "-t",
        required=True,
        help="Target model identifier to evaluate (e.g. gemini-3.8-flash-medium).",
    )
    parser.add_argument(
        "--baseline",
        "-b",
        default=ModelArchetype.STANDARD_MEDIUM,
        help="Baseline model identifier for A/B comparison (default: current standard medium).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode without live LLM calls (for CI / testing).",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=None,
        help="Path to custom benchmark fixtures JSON file.",
    )

    args = parser.parse_args(argv)
    return run_eval_benchmark(
        target_model=args.target,
        baseline_model=args.baseline,
        mock=args.mock,
        fixtures_path=args.fixtures,
    )


if __name__ == "__main__":
    sys.exit(main())

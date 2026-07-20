#!/usr/bin/env python3
"""eval_runner.py - Core Evaluation Runner for CCBA AI Agent Skills.
Chạy cô lập các test cases cho từng skill, hỗ trợ Regex Asserts và LLM-as-a-Judge.
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

# Console UTF-8 compatibility for Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Add project root and ccba-ai package to sys.path to enable imports
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "ccba-ai" / "src"))

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ccba.eval.runner")


def load_skill_prompt(skill_name: str) -> str:
    """Đọc tệp SKILL.md của skill tương ứng làm System Prompt."""
    skill_path = project_root / ".agents" / "skills" / skill_name / "SKILL.md"
    if not skill_path.exists():
        logger.warning(f"Không tìm thấy file SKILL.md tại {skill_path}. Chạy ở chế độ không có System Prompt.")
        return ""
    try:
        content = skill_path.read_text(encoding="utf-8")
        return content
    except Exception as e:
        logger.error(f"Lỗi khi đọc file SKILL.md cho {skill_name}: {e}")
        return ""


def run_llm_judge(prompt: str, output: str, rubric: str, judge_model: str = "gemini-3.1-pro-high") -> tuple[bool, str]:
    """Sử dụng LLM đóng vai trò Judge để chấm điểm đầu ra dựa trên Rubric."""
    from ccba_ai import ai

    judge_prompt = (
        "Bạn là kiểm định viên chất lượng AI Agent (QC Evaluator) tại CCBA.\n"
        "Nhiệm vụ của bạn là đánh giá xem kết quả thực thi của Agent có đạt yêu cầu hay không dựa trên Rubric dưới đây.\n\n"
        f"YÊU CẦU GỐC CỦA NGƯỜI DÙNG:\n---\n{prompt}\n---\n\n"
        f"KẾT QUẢ ĐẦU RA CỦA AGENT:\n---\n{output}\n---\n\n"
        f"TIÊU CHÍ CHẤM ĐIỂM (RUBRIC):\n---\n{rubric}\n---\n\n"
        "YÊU CẦU ĐẦU RA:\n"
        "Trả về duy nhất một chuỗi JSON hợp lệ với cấu trúc sau (không bọc trong markdown code block):\n"
        "{\n"
        '  "passed": true,\n'
        '  "reason": "Giải thích ngắn gọn lý do tại sao đạt hoặc không đạt"\n'
        "}"
    )

    try:
        res = ai.chat(judge_prompt, model=judge_model, max_tokens=1024, temperature=0.1)
        # Clean markdown code blocks if model output them
        cleaned_res = res.strip()
        if cleaned_res.startswith("```json"):
            cleaned_res = cleaned_res[7:]
        if cleaned_res.endswith("```"):
            cleaned_res = cleaned_res[:-3]
        cleaned_res = cleaned_res.strip()

        data = json.loads(cleaned_res)
        return bool(data.get("passed", False)), str(data.get("reason", "No reason provided."))
    except Exception as e:
        logger.error(f"Lỗi khi chạy LLM Judge: {e}")
        return False, f"LLM Judge gặp lỗi hệ thống: {e}"


def evaluate_case(case: dict[str, Any], system_prompt: str, model_id: str, trials: int) -> dict[str, Any]:
    """Chạy đánh giá một test case qua N lần thử."""
    from ccba_ai import ai

    case_id = case.get("id", "unknown")
    prompt = case.get("prompt", "")
    assertions = case.get("assertions", [])
    
    logger.info(f"👉 Bắt đầu kiểm thử Case [{case_id}] (Số lần thử: {trials})")
    
    success_count = 0
    trial_details = []

    for t in range(1, trials + 1):
        logger.info(f"   Lần thử {t}/{trials}...")
        
        # 1. Gọi LLM sinh kết quả (Isolated call)
        try:
            output = ai.chat(prompt, system=system_prompt, model=model_id, temperature=0.3)
        except Exception as e:
            logger.error(f"   [Thất bại] Lỗi kết nối API LLM ở lần thử {t}: {e}")
            trial_details.append({"trial": t, "passed": False, "error": str(e)})
            continue

        # 2. Thực hiện các Assertions
        passed_all_asserts = True
        assert_failures = []

        for assertion in assertions:
            assert_type = assertion.get("type", "regex")
            
            if assert_type == "regex":
                pattern = assertion.get("pattern", "")
                if not re.search(pattern, output, re.IGNORECASE | re.DOTALL):
                    passed_all_asserts = False
                    msg = f"Regex mismatch: Pattern '{pattern}' không tồn tại trong kết quả."
                    assert_failures.append(msg)
                    logger.warning(f"      ❌ {msg}")
            
            elif assert_type == "negative_regex":
                pattern = assertion.get("pattern", "")
                if re.search(pattern, output, re.IGNORECASE | re.DOTALL):
                    passed_all_asserts = False
                    msg = f"Negative Regex failure: Pattern '{pattern}' xuất hiện trong kết quả (lẽ ra không được có)."
                    assert_failures.append(msg)
                    logger.warning(f"      ❌ {msg}")
            
            elif assert_type == "llm_judge":
                rubric = assertion.get("rubric", "")
                judge_model = assertion.get("model", "gemini-3.1-pro-high")
                passed_judge, reason_judge = run_llm_judge(prompt, output, rubric, judge_model)
                if not passed_judge:
                    passed_all_asserts = False
                    msg = f"LLM Judge FAILED: {reason_judge}"
                    assert_failures.append(msg)
                    logger.warning(f"      ❌ {msg}")
                else:
                    logger.info(f"      ✅ LLM Judge PASSED: {reason_judge}")

        if passed_all_asserts:
            success_count += 1
            trial_details.append({"trial": t, "passed": True, "output_snippet": output[:100] + "..."})
            logger.info("      ✅ Đạt tất cả các Assertions.")
        else:
            trial_details.append({"trial": t, "passed": False, "failures": assert_failures, "output": output})

    reliability = success_count / trials
    passed_case = success_count == trials  # Phải đạt 100% các lần thử mới tính là Pass hoàn toàn

    logger.info(f"📊 Kết quả Case [{case_id}]: {'PASS' if passed_case else 'FAILED'} (Reliability: {reliability:.1%})")
    
    return {
        "id": case_id,
        "passed": passed_case,
        "reliability": reliability,
        "details": trial_details
    }


def run_eval_for_skill(skill_name: str, test_cases_path: Path, model_id: str, trials: int) -> bool:
    """Chạy toàn bộ kiểm định cho một skill cụ thể. Trả về True nếu PASS 100%."""
    if not test_cases_path.exists():
        logger.error(f"Không tìm thấy file cấu hình test cases tại {test_cases_path}")
        return False

    logger.info(f"==================================================")
    logger.info(f"🎬 Khởi chạy Evals cho Skill: {skill_name}")
    logger.info(f"📄 Test Cases: {test_cases_path}")
    logger.info(f"🤖 Model: {model_id} | Số lần thử: {trials}")
    logger.info(f"==================================================")

    # 1. Đọc test cases
    try:
        with open(test_cases_path, "r", encoding="utf-8") as f:
            cases = json.load(f)
    except Exception as e:
        logger.error(f"Lỗi khi đọc tệp test cases JSON: {e}")
        return False

    system_prompt = load_skill_prompt(skill_name)

    # 2. Chạy từng case
    results = []
    failed_cases = 0

    for case in cases:
        result = evaluate_case(case, system_prompt, model_id, trials)
        results.append(result)
        if not result["passed"]:
            failed_cases += 1

    # 3. Xuất báo cáo tổng kết
    logger.info(f"==================================================")
    logger.info(f"🏁 BÁO CÁO KẾT QUẢ KIỂM THỬ SKILL: {skill_name}")
    logger.info(f"Tổng số Cases: {len(cases)} | Đạt (Pass): {len(cases) - failed_cases} | Lỗi (Failed): {failed_cases}")
    logger.info(f"==================================================")

    for res in results:
        status_str = "🟢 PASS" if res["passed"] else "🔴 FAILED"
        logger.info(f"- [{res['id']}] Status: {status_str} | Reliability: {res['reliability']:.1%}")

    return failed_cases == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="CCBA AI Skills Evaluation Harness Runner.")
    parser.add_argument("--skill", type=str, default=None, help="Tên skill cần kiểm định (ví dụ: copywriting). Mặc định là 'all'.")
    parser.add_argument("--test-cases", type=str, default=None, help="Đường dẫn file JSON test cases. Mặc định tự tìm trong eval-gate/test_cases.")
    parser.add_argument("--model", type=str, default="gemini-3.1-pro-high", help="Model ID của Agent cần test (mặc định: gemini-3.1-pro-high).")
    parser.add_argument("--trials", type=int, default=3, help="Số lần chạy thử cho mỗi test case (mặc định: 3).")
    args = parser.parse_args()

    test_cases_dir = project_root / ".agents" / "skills" / "eval-gate" / "test_cases"

    # Chạy cho một skill cụ thể
    if args.skill and args.skill.lower() != "all":
        if args.test_cases:
            test_cases_path = Path(args.test_cases).absolute()
        else:
            test_cases_path = test_cases_dir / f"eval_{args.skill}.json"

        success = run_eval_for_skill(args.skill, test_cases_path, args.model, args.trials)
        if not success:
            sys.exit(1)
        sys.exit(0)

    # Chạy cho tất cả các skills được phát hiện trong thư mục test_cases
    else:
        logger.info("🔍 Phát hiện chế độ chạy Evals cho TẤT CẢ các kỹ năng...")
        if not test_cases_dir.exists():
            logger.error(f"Không tìm thấy thư mục cấu hình test cases tại {test_cases_dir}")
            sys.exit(1)

        test_files = list(test_cases_dir.glob("eval_*.json"))
        if not test_files:
            logger.warning("Không tìm thấy tệp test case 'eval_*.json' nào.")
            sys.exit(0)

        logger.info(f"📂 Tìm thấy {len(test_files)} file cấu hình kiểm thử.")
        
        all_success = True
        summary_results = []

        for tf in test_files:
            # Trích xuất skill name từ file name 'eval_<skill_name>.json'
            skill_name = tf.stem[5:]
            success = run_eval_for_skill(skill_name, tf, args.model, args.trials)
            summary_results.append((skill_name, success))
            if not success:
                all_success = False

        # In báo cáo tổng hợp cuối cùng
        logger.info("==================================================")
        logger.info("🏁 TỔNG HỢP KIỂM THỬ TOÀN BỘ AI SKILLS")
        logger.info("==================================================")
        for skill_name, success in summary_results:
            status_str = "🟢 PASS" if success else "🔴 FAILED"
            logger.info(f"- Skill [{skill_name}]: {status_str}")
        logger.info("==================================================")

        if not all_success:
            logger.error("❌ Một hoặc nhiều kỹ năng kiểm thử FAILED. Vui lòng rà soát lại.")
            sys.exit(1)
        else:
            logger.info("🎉 Tất cả các kỹ năng đều PASS kiểm thử tự động!")
            sys.exit(0)


if __name__ == "__main__":
    main()

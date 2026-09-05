#!/usr/bin/env python3
"""eval_runner.py - Core Evaluation Runner for CCBA AI Agent Skills.
Chạy cô lập các test cases cho từng skill, hỗ trợ Regex Asserts và LLM-as-a-Judge.
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml

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


def get_skill_path(skill_name: str) -> Path:
    """Xác định đường dẫn file SKILL.md từ catalog.yaml hoặc thư mục mặc định."""
    default_path = project_root / ".agents" / "skills" / skill_name / "SKILL.md"
    if default_path.exists():
        return default_path

    # Fallback to ccba- prefix if not provided
    if not skill_name.startswith("ccba-"):
        ccba_path = project_root / ".agents" / "skills" / f"ccba-{skill_name}" / "SKILL.md"
        if ccba_path.exists():
            return ccba_path

    catalog_file = project_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    if catalog_file.exists():
        try:
            with open(catalog_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                skills_list = data.get("skills", [])
                for item in skills_list:
                    name = item.get("name", "")
                    if (name == skill_name or name == f"ccba-{skill_name}") and "skill_path" in item:
                        candidate = project_root / item["skill_path"]
                        if candidate.exists():
                            return candidate
        except Exception:
            pass
    return default_path


def load_skill_prompt(skill_name: str) -> str:
    """Đọc tệp SKILL.md của skill tương ứng làm System Prompt."""
    skill_path = get_skill_path(skill_name)
    if not skill_path.exists():
        logger.warning(f"Không tìm thấy file SKILL.md tại {skill_path}. Chạy ở chế độ không có System Prompt.")
        return ""
    try:
        content = skill_path.read_text(encoding="utf-8")
        return content
    except Exception as e:
        logger.error(f"Lỗi khi đọc file SKILL.md cho {skill_name}: {e}")
        return ""


def preserve_yaml_frontmatter(original_prompt: str, edited_prompt: str) -> str:
    """Bảo tồn phần YAML Frontmatter gốc của file SKILL.md khi LLM Optimizer chỉnh sửa nội dung."""
    if not original_prompt.startswith("---"):
        return edited_prompt

    parts = original_prompt.split("---", 2)
    if len(parts) < 3:
        return edited_prompt

    original_frontmatter = f"---{parts[1]}---"

    cleaned_body = edited_prompt
    if edited_prompt.startswith("---"):
        edited_parts = edited_prompt.split("---", 2)
        if len(edited_parts) >= 3:
            cleaned_body = edited_parts[2]

    cleaned_body = cleaned_body.lstrip("\r\n")
    return f"{original_frontmatter}\n\n{cleaned_body}"


def optimizer_edit_prompt(
    original_prompt: str,
    failure_details: list[dict[str, Any]],
    model_id: str = "gemini-3.1-pro-high",
) -> str:
    """Gọi LLM Optimizer đóng vai trò Prompt Engineer đề xuất chỉnh sửa văn bản SKILL.md."""
    from ccba_ai import ai

    failures_summary = json.dumps(failure_details, ensure_ascii=False, indent=2)

    optimizer_instruction = (
        "Bạn là một chuyên gia Prompt Optimizer tối ưu hóa tài liệu kỹ năng AI Agent (SKILL.md) tại CCBA.\n"
        "Dựa trên các lỗi kiểm thử vừa xảy ra ở giai đoạn Rollout, nhiệm vụ của bạn là chỉnh sửa văn bản nội dung hướng dẫn trong SKILL.md để khắc phục các sai sót này.\n\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. Chỉ điều chỉnh hoặc bổ sung câu từ, quy định rào chắn, hoặc ví dụ minh họa trong phần nội dung markdown.\n"
        "2. Không thay đổi ý nghĩa cốt lõi của kỹ năng.\n"
        "3. Trả về toàn bộ nội dung markdown mới đã được tối ưu hóa (không cần bao gồm YAML frontmatter header).\n\n"
        f"CHI TIẾT LỖI KIỂM THỬ GẦN NHẤT:\n---\n{failures_summary}\n---\n\n"
        f"NỘI DUNG SKILL.MD HIỆN TẠI:\n---\n{original_prompt}\n---\n\n"
        "NỘI DUNG SKILL.MD MỚI ĐÃ TỐI ƯU:"
    )

    try:
        raw_edited = ai.chat(optimizer_instruction, model=model_id, max_tokens=4096, temperature=0.2)
        final_prompt = preserve_yaml_frontmatter(original_prompt, raw_edited)
        return final_prompt
    except Exception as e:
        logger.error(f"Lỗi khi chạy Optimizer Prompt: {e}")
        return original_prompt



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
        cleaned_res = res.strip()
        if "```" in cleaned_res:
            cleaned_res = re.sub(r"```(?:json)?", "", cleaned_res).strip()

        json_match = re.search(r"\{.*\}", cleaned_res, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            data = json.loads(cleaned_res)

        return bool(data.get("passed", False)), str(data.get("reason", "No reason provided."))
    except Exception as e:
        logger.error(f"Lỗi khi chạy LLM Judge: {e}")
        return False, f"LLM Judge gặp lỗi hệ thống: {e}"


def evaluate_case(case: dict[str, Any], system_prompt: str, model_id: str, trials: int) -> dict[str, Any]:
    """Chạy đánh giá một test case qua N lần thử."""
    from ccba_ai import ai

    case_id = case.get("id", "unknown")
    prompt = case.get("prompt") or case.get("input_prompt", "")
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

    logger.info("==================================================")
    logger.info(f"🎬 Khởi chạy Evals cho Skill: {skill_name}")
    logger.info(f"📄 Test Cases: {test_cases_path}")
    logger.info(f"🤖 Model: {model_id} | Số lần thử: {trials}")
    logger.info("==================================================")

    # 1. Đọc test cases
    try:
        with open(test_cases_path, encoding="utf-8") as f:
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
    logger.info("==================================================")
    logger.info(f"🏁 BÁO CÁO KẾT QUẢ KIỂM THỬ SKILL: {skill_name}")
    logger.info(f"Tổng số Cases: {len(cases)} | Đạt (Pass): {len(cases) - failed_cases} | Lỗi (Failed): {failed_cases}")
    logger.info("==================================================")

    for res in results:
        status_str = "🟢 PASS" if res["passed"] else "🔴 FAILED"
        logger.info(f"- [{res['id']}] Status: {status_str} | Reliability: {res['reliability']:.1%}")

    return failed_cases == 0


def auto_tune_skill(
    skill_name: str,
    test_cases_path: Path,
    model_id: str,
    trials: int,
    max_iterations: int = 3,
) -> bool:
    """Chạy quy trình Skill Auto-Tuning 4 bước (Rollout -> Reflect -> Edit -> Validate)."""
    skill_path = project_root / ".agents" / "skills" / skill_name / "SKILL.md"
    if not skill_path.exists():
        logger.error(f"Không tìm thấy file SKILL.md cho skill [{skill_name}] tại {skill_path}")
        return False

    logger.info("==================================================")
    logger.info(f"🚀 BẮT ĐẦU CHU TRÌNH AUTO-TUNE CHO SKILL: {skill_name}")
    logger.info(f"🔄 Số vòng lặp tối đa: {max_iterations}")
    logger.info("==================================================")

    current_prompt = load_skill_prompt(skill_name)
    best_prompt = current_prompt
    best_pass_rate = 0.0

    for iteration in range(1, max_iterations + 1):
        logger.info(f"\n--- 🔄 AUTO-TUNE ITERATION {iteration}/{max_iterations} ---")

        # 1. Rollout: Evaluate current prompt
        try:
            with open(test_cases_path, encoding="utf-8") as f:
                cases = json.load(f)
        except Exception as e:
            logger.error(f"Lỗi đọc test cases: {e}")
            return False

        results = []
        failure_details = []
        passed_cases = 0

        for case in cases:
            res = evaluate_case(case, current_prompt, model_id, trials)
            results.append(res)
            if res["passed"]:
                passed_cases += 1
            else:
                failure_details.append({"id": res["id"], "failures": res["details"]})

        current_pass_rate = passed_cases / len(cases) if cases else 0.0
        logger.info(f"📊 Iteration {iteration} Pass Rate: {current_pass_rate:.1%}")

        if current_pass_rate > best_pass_rate:
            best_pass_rate = current_pass_rate
            best_prompt = current_prompt

        # Nếu đạt 100% Pass Rate -> Dừng sớm thành công
        if current_pass_rate == 1.0:
            logger.info("🎉 SKILL ĐÃ ĐẠT 100% PASS RATE! Không cần tối ưu thêm.")
            break

        if iteration == max_iterations:
            logger.info("⚠️ Đã đạt số vòng lặp tối đa.")
            break

        # 2. Reflect & 3. Edit: Call LLM Optimizer
        logger.info("💡 Phát hiện lỗi. Đang kích hoạt LLM Optimizer đề xuất chỉnh sửa prompt...")
        candidate_prompt = optimizer_edit_prompt(current_prompt, failure_details, model_id)

        # 4. Validate Gate: Test candidate prompt
        logger.info("🛡️ Đang chạy Validation Gate kiểm thử candidate prompt mới...")
        candidate_passed = 0
        for case in cases:
            res = evaluate_case(case, candidate_prompt, model_id, trials)
            if res["passed"]:
                candidate_passed += 1

        candidate_pass_rate = candidate_passed / len(cases) if cases else 0.0
        logger.info(f"📊 Candidate Pass Rate: {candidate_pass_rate:.1%} (Best so far: {best_pass_rate:.1%})")

        if candidate_pass_rate >= best_pass_rate:
            logger.info("✅ Validation Gate PASSED: Candidate prompt đạt kết quả tốt hơn hoặc bằng. Chấp nhận candidate!")
            current_prompt = candidate_prompt
            best_pass_rate = candidate_pass_rate
            best_prompt = candidate_prompt
        else:
            logger.warning("❌ Validation Gate REJECTED: Prompt Drift phát hiện! Candidate giảm điểm số. Từ chối candidate.")

    # Ghi nhận best_prompt vào file SKILL.md nếu đạt kết quả tốt hơn ban đầu
    if best_pass_rate > 0:
        try:
            skill_path.write_text(best_prompt, encoding="utf-8")
            logger.info(f"💾 Đã cập nhật file SKILL.md tại {skill_path} với Pass Rate tốt nhất: {best_pass_rate:.1%}")
        except Exception as e:
            logger.error(f"Không thể ghi đè file SKILL.md: {e}")

    return best_pass_rate == 1.0


def dry_run_validate(test_files: list[Path]) -> bool:
    """Validates JSON structure and regex assertions in all test_files without calling LLM APIs."""
    logger.info("🧪 Bắt đầu chế độ DRY-RUN (Validate syntax & regex)...")
    valid_count = 0
    total_cases = 0
    errors = []

    for tf in sorted(test_files):
        skill_name = tf.stem[5:]
        try:
            with open(tf, encoding="utf-8") as f:
                cases = json.load(f)
        except Exception as e:
            msg = f"File {tf.name} lỗi JSON syntax: {e}"
            errors.append(msg)
            logger.error(f"❌ {msg}")
            continue

        NOISE_PROMPT_PATTERNS = [
            r"\bquicksort\b",
            r"\bfibonacci\b",
            r"\bbubble\s*sort\b",
            r"\bsick\s*leave\b",
            r"\bbinary\s*search\b",
        ]

        file_ok = True
        for case in cases:
            total_cases += 1
            cid = case.get("id", "")
            prompt_text = case.get("prompt") or case.get("input_prompt", "")
            if not cid or not prompt_text:
                msg = f"File {tf.name}: case thiếu 'id' hoặc 'prompt'"
                errors.append(msg)
                file_ok = False
                continue

            # Kiểm tra noise prompt ngoại lai không sát nghiệp vụ
            if skill_name not in ("tdd", "implement", "code-review"):
                for noise_pat in NOISE_PROMPT_PATTERNS:
                    if re.search(noise_pat, prompt_text, re.IGNORECASE):
                        msg = f"File {tf.name} case [{cid}]: Phát hiện Noise Prompt không sát nghiệp vụ (pattern: '{noise_pat}'). Vui lòng thay bằng negative prompt chuyên môn sát thực tế."
                        errors.append(msg)
                        file_ok = False

            for assertion in case.get("assertions", []):
                atype = assertion.get("type")
                if atype in ("regex", "negative_regex"):
                    pattern = assertion.get("pattern", "")
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        msg = f"File {tf.name} case [{cid}]: Regex '{pattern}' không hợp lệ ({e})"
                        errors.append(msg)
                        file_ok = False
        if file_ok:
            valid_count += 1
            logger.info(f"  - [{skill_name}] ({len(cases)} cases): Syntax, Regex & Noise-free OK")

    logger.info("==================================================")
    logger.info(f"🧪 BÁO CÁO DRY-RUN: Validated {len(test_files)} files ({total_cases} test cases).")
    if errors:
        logger.error(f"❌ Phát hiện {len(errors)} lỗi syntax/regex:")
        for err in errors:
            logger.error(f"  - {err}")
        return False
    logger.info("🎉 Tất cả test cases JSON & Regex patterns đều HỢP LỆ 100%!")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="CCBA AI Skills Evaluation Harness Runner.")
    parser.add_argument("--skill", type=str, default=None, help="Tên skill cần kiểm định (ví dụ: copywriting). Mặc định là 'all'.")
    parser.add_argument("--test-cases", type=str, default=None, help="Đường dẫn file JSON test cases. Mặc định tự tìm trong eval-gate/test_cases.")
    parser.add_argument("--model", type=str, default="gemini-3.1-pro-high", help="Model ID của Agent cần test (mặc định: gemini-3.1-pro-high).")
    parser.add_argument("--trials", type=int, default=3, help="Số lần chạy thử cho mỗi test case (mặc định: 3).")
    parser.add_argument("--auto-tune", action="store_true", help="Bật chế độ tự động tối ưu hóa SKILL.md (SkillOpt loop).")
    parser.add_argument("--max-iterations", type=int, default=3, help="Số vòng lặp auto-tune tối đa (mặc định: 3).")
    parser.add_argument("--dry-run", action="store_true", help="Kiểm tra cú pháp file JSON và regex pattern mà không gọi LLM API.")
    parser.add_argument("--mine-logs", action="store_true", help="Tự động bóc tách user prompts từ transcript logs để auto-tune test cases trước khi chạy evals.")
    args = parser.parse_args()

    test_cases_dir = project_root / ".agents" / "skills" / "ccba-eval-gate" / "test_cases"
    if not test_cases_dir.exists():
        test_cases_dir = project_root / ".agents" / "skills" / "eval-gate" / "test_cases"

    if args.mine_logs:
        logger.info("⛏️ Kích hoạt Production Log Mining trước khi chạy Evals...")
        try:
            from scripts.eval.log_eval_miner import mine_logs_and_export
            mine_logs_and_export(project_root / ".system_generated" / "logs", test_cases_dir, args.skill)
        except Exception as e:
            logger.warning(f"⚠️ Không thể mine logs: {e}")

    def _resolve_test_file(skill_name: str) -> Path:
        clean = skill_name.replace("ccba-", "").replace("ccba_", "").replace("-", "_")
        clean_no_qc = clean.replace("ai_qc_", "").replace("ai_qc-", "")
        candidates = [
            test_cases_dir / f"eval_{skill_name}.json",
            test_cases_dir / f"eval_{skill_name.replace('-', '_')}.json",
            test_cases_dir / f"eval_{clean}.json",
            test_cases_dir / f"eval_{clean_no_qc}.json",
        ]
        for cand in candidates:
            if cand.exists():
                return cand
        return candidates[0]

    if args.dry_run:
        if args.skill and args.skill.lower() != "all":
            tf = _resolve_test_file(args.skill)
            success = dry_run_validate([tf]) if tf.exists() else False
        else:
            test_files = list(test_cases_dir.glob("eval_*.json"))
            success = dry_run_validate(test_files)
        sys.exit(0 if success else 1)

    # Chạy cho một skill cụ thể
    if args.skill and args.skill.lower() != "all":
        if args.test_cases:
            test_cases_path = Path(args.test_cases).absolute()
        else:
            test_cases_path = _resolve_test_file(args.skill)

        if args.auto_tune:
            success = auto_tune_skill(args.skill, test_cases_path, args.model, args.trials, args.max_iterations)
        else:
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
            skill_name = tf.stem[5:]
            if args.auto_tune:
                success = auto_tune_skill(skill_name, tf, args.model, args.trials, args.max_iterations)
            else:
                success = run_eval_for_skill(skill_name, tf, args.model, args.trials)
            summary_results.append((skill_name, success))
            if not success:
                all_success = False

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


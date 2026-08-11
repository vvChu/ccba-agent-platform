#!/usr/bin/env python3
"""log_eval_miner.py - Production Log Mining & Failure-Driven Auto-Tuning Tool for CCBA Skills Evals.

Parses user interactions from transcript.jsonl logs, applies privacy redaction (maskara-privacy patterns),
detects router failures / disclaimer mismatches, and generates 4-layer compliant synthetic test cases.
"""

import argparse
import json
import logging
import re
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ccba.eval.miner")

# Sensitive Data Redaction Patterns (Maskara Privacy Standard)
SENSITIVE_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL_REDACTED]"),
    (r"\b(?:0\d{9,10}|\+84\d{9,10})\b", "[PHONE_REDACTED]"),
    (
        r"\b(?:sk-[A-Za-z0-9]{20,}|AIzaSy[A-Za-z0-9_-]{33}|ghp_[A-Za-z0-9]{36})\b",
        "[API_KEY_REDACTED]",
    ),
    (
        r"\b(?:100\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b",
        "[IP_REDACTED]",
    ),
]


def redact_sensitive_info(text: str) -> str:
    """Redacts sensitive user data (emails, phone numbers, API keys, IPs) using Maskara Privacy patterns.

    Args:
        text: Raw text string from user input.

    Returns:
        Redacted text string.
    """
    if not text:
        return ""
    cleaned = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned)
    return cleaned.strip()


def parse_transcript_logs(log_dir: Path) -> list[dict]:
    """Scans log_dir recursively for transcript.jsonl files and extracts user prompts.

    Args:
        log_dir: Path to directory containing transcript log files.

    Returns:
        List of parsed interaction dictionaries containing user_input, response, and step_index.
    """
    interactions = []
    if not log_dir.exists():
        logger.warning(f"⚠️ Thư mục log '{log_dir}' không tồn tại.")
        return interactions

    log_files = list(log_dir.rglob("transcript*.jsonl"))
    logger.info(f"📂 Tìm thấy {len(log_files)} file transcript log trong {log_dir}")

    for log_file in log_files:
        try:
            with open(log_file, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"❌ Lỗi đọc file {log_file.name}: {e}")
            continue

        last_user_prompt = None

        for line in lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue

            stype = data.get("type", "")
            content = data.get("content", "")

            if stype == "USER_INPUT":
                last_user_prompt = redact_sensitive_info(content)
            elif stype == "PLANNER_RESPONSE" and last_user_prompt:
                interactions.append(
                    {
                        "source_file": log_file.name,
                        "step_index": data.get("step_index", 0),
                        "user_prompt": last_user_prompt,
                        "planner_response": content,
                    }
                )
                last_user_prompt = None

    logger.info(f"📊 Đã bóc tách được {len(interactions)} lượt tương tác người dùng.")
    return interactions


def identify_router_failures(interactions: list[dict]) -> list[dict]:
    """Identifies interaction logs where Agent issued disclaimers or failed skill routing.

    Args:
        interactions: List of parsed interaction dicts.

    Returns:
        List of flagged failure cases suitable for synthetic test cases.
    """
    flagged_cases = []
    disclaimer_keywords = [
        "không thuộc phạm vi",
        "không hỗ trợ",
        "tôi là agent",
        "tôi là trợ lý",
        "chỉ hỗ trợ",
        "không phải tư vấn pháp lý",
    ]

    for item in interactions:
        response_text = item.get("planner_response", "").lower()
        user_prompt = item.get("user_prompt", "")

        if not user_prompt or len(user_prompt) < 10:
            continue

        is_disclaimer = any(kw in response_text for kw in disclaimer_keywords)
        if is_disclaimer:
            flagged_cases.append(
                {
                    "user_prompt": user_prompt,
                    "reason": "disclaimer_or_router_mismatch",
                    "raw_response_snippet": response_text[:150],
                }
            )

    logger.info(
        f"🔍 Phát hiện {len(flagged_cases)} cases nghi vấn Router Failure / Disclaimer Mismatch."
    )
    return flagged_cases


def generate_synthetic_test_case(prompt: str, skill_name: str, case_index: int) -> dict:
    """Generates a 4-layer compliant test case dictionary.

    Args:
        prompt: Redacted user prompt.
        skill_name: Target skill name.
        case_index: Index number for unique ID.

    Returns:
        Test case dict ready for eval JSON.
    """
    cid = f"test_{skill_name.replace('-', '_')}_mined_{case_index:02d}"
    return {
        "id": cid,
        "prompt": prompt,
        "assertions": [
            {"type": "regex", "pattern": f"({skill_name}|xử lý|hướng dẫn|thực hiện|quy định)"}
        ],
    }


def mine_logs_and_export(log_dir: Path, output_dir: Path, skill_filter: str = None) -> int:
    """Main execution pipeline to mine logs, redact data, and update test cases files.

    Args:
        log_dir: Path to directory containing logs.
        output_dir: Path to test_cases directory.
        skill_filter: Optional skill name filter.

    Returns:
        Total number of synthetic test cases generated.
    """
    interactions = parse_transcript_logs(log_dir)
    failures = identify_router_failures(interactions)

    if not failures:
        logger.info("🎉 Không phát hiện router failures nào cần auto-tune.")
        return 0

    exported_count = 0
    output_dir.mkdir(parents=True, exist_ok=True)

    target_skill = skill_filter or "academic_writing"
    target_json = output_dir / f"eval_{target_skill}.json"

    existing_cases = []
    if target_json.exists():
        try:
            with open(target_json, encoding="utf-8") as f:
                existing_cases = json.load(f)
        except Exception:
            existing_cases = []

    existing_prompts = {c.get("prompt") for c in existing_cases if "prompt" in c}

    for _idx, fcase in enumerate(failures, 1):
        p_text = fcase["user_prompt"]
        if p_text in existing_prompts:
            continue

        syn_case = generate_synthetic_test_case(p_text, target_skill, len(existing_cases) + 1)
        existing_cases.append(syn_case)
        existing_prompts.add(p_text)
        exported_count += 1

    if exported_count > 0:
        with open(target_json, "w", encoding="utf-8") as f:
            json.dump(existing_cases, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Đã xuất {exported_count} test cases thực chiến mới vào {target_json.name}")

    return exported_count


def main():
    parser = argparse.ArgumentParser(
        description="CCBA Production Log Mining & Eval Auto-Tuning Tool"
    )
    parser.add_argument(
        "--log-dir", default=".system_generated/logs", help="Thư mục chứa transcript logs"
    )
    parser.add_argument(
        "--output-dir",
        default=".agents/skills/eval-gate/test_cases",
        help="Thư mục xuất test_cases JSON",
    )
    parser.add_argument("--skill", help="Tên skill cụ thể cần nạp test cases mined")

    args = parser.parse_args()
    log_dir = Path(args.log_dir)
    output_dir = Path(args.output_dir)

    count = mine_logs_and_export(log_dir, output_dir, args.skill)
    print(f"Mining hoàn tất: {count} cases được cập nhật.")


if __name__ == "__main__":
    main()

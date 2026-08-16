#!/usr/bin/env python3
"""log_eval_miner.py - Production Log Mining & Failure-Driven Auto-Tuning Tool for CCBA Skills Evals.

Parses user interactions from transcript.jsonl logs, applies privacy redaction (Maskara Privacy Standard),
detects multi-type failure patterns (Router Disclaimer, Tool Exception, Outdated Citation),
and generates EvalItem specs compatible with ccba_harness.evals framework.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

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
        r"\b(?:100\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3})\b",
        "[IP_REDACTED]",
    ),
]

# Failure Taxonomy Detection Patterns
DISCLAIMER_KEYWORDS = [
    "không thuộc phạm vi",
    "không hỗ trợ",
    "tôi là agent",
    "tôi là trợ lý",
    "chỉ hỗ trợ",
    "không thể thực hiện",
    "tôi không có khả năng",
    "không phải tư vấn pháp lý",
]

EXCEPTION_KEYWORDS = [
    "traceback (most recent call last)",
    "toolexecutionerror",
    "invalid tool call",
    "syntaxerror:",
    "typeerror:",
    "valueerror:",
    "runtimeerror:",
    '"status": "error"',
]

OUTDATED_LEGAL_CITATIONS = [
    (r"136/2020/NĐ-CP", "Nghị định 136/2020 đã được thay thế/sửa đổi bởi Nghị định 105/2025"),
    (r"QCVN\s*06:2020", "QCVN 06:2020 đã được thay thế bởi QCVN 06:2022/BXD & Sửa đổi 1:2023"),
    (r"149/2020/TT-BCA", "Thông tư 149/2020 đã được cập nhật"),
]

IGNORABLE_CONTROL_COMMANDS = {
    "proceed",
    "approve",
    "yes",
    "y",
    "ok",
    "tiếp tục",
    "đồng ý",
    "1",
    "2",
    "3",
    "continue",
    "/proceed",
    "/approve",
}


def redact_sensitive_info(text: str) -> str:
    """Redacts sensitive user data (emails, phone numbers, API keys, IPs) using Maskara patterns."""
    if not text:
        return ""
    cleaned = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned)
    return cleaned.strip()


def extract_clean_user_prompt(raw_text: str) -> str:
    """Extracts clean user prompt, stripping XML enclosing tags and system metadata."""
    if not raw_text:
        return ""
    # Extract <USER_REQUEST>...</USER_REQUEST> if present
    match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", raw_text, re.DOTALL)
    if match:
        raw_text = match.group(1)
    raw_text = re.sub(
        r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", raw_text, flags=re.DOTALL
    )
    raw_text = re.sub(
        r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", raw_text, flags=re.DOTALL
    )
    raw_text = re.sub(r"<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>", "", raw_text, flags=re.DOTALL)
    return redact_sensitive_info(raw_text.strip())


def resolve_log_dir(configured_dir: Path | str | None) -> Path:
    """Resolves log directory with fallback to ~/.gemini/antigravity/brain."""
    if configured_dir:
        p = Path(configured_dir)
        if p.exists():
            return p

    # Fallback 1: Local workspace .system_generated/logs
    local_logs = Path(".system_generated/logs")
    if local_logs.exists():
        return local_logs

    # Fallback 2: ~/.gemini/antigravity/brain
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        return brain_dir

    return Path(configured_dir or ".system_generated/logs")


def find_transcript_files(log_dir: Path) -> list[Path]:
    """Safely traverses directory tree to find all transcript.jsonl files, skipping broken symlinks/junctions."""
    if not log_dir.exists():
        return []
    if log_dir.is_file() and log_dir.name.endswith(".jsonl"):
        return [log_dir]

    log_files: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(log_dir, followlinks=False):
        if "transcript.jsonl" in filenames:
            log_files.append(Path(dirpath) / "transcript.jsonl")
        elif any(f.startswith("transcript") and f.endswith(".jsonl") for f in filenames):
            for f in filenames:
                if (
                    f.startswith("transcript")
                    and f.endswith(".jsonl")
                    and not f.endswith("_full.jsonl")
                ):
                    log_files.append(Path(dirpath) / f)
    return log_files


def classify_target_skill(user_prompt: str) -> str:
    """Classifies user prompt to appropriate skill domain based on keywords."""
    prompt_lower = user_prompt.lower()

    if prompt_lower.startswith("you are teamwork_preview_") or prompt_lower.startswith(
        "you are forensic auditor"
    ):
        return "agent_orchestration"

    if any(
        k in prompt_lower
        for k in ["pccc", "thẩm tra", "mep", "qcvn 06", "chịu lửa", "bản vẽ", "dwg", "cad", "khói"]
    ):
        return "pccc_audit"

    if any(
        k in prompt_lower
        for k in [
            "luật",
            "nghị định",
            "thông tư",
            "vbpl",
            "pháp lý",
            "pháp điển",
            "vbhn",
            "tvpl",
            "nghị định 105",
            "nghị định 136",
        ]
    ):
        return "legal_intel"
    if any(
        k in prompt_lower
        for k in ["bài báo", "khoa học", "imrad", "nghiên cứu", "học thuật", "trích dẫn"]
    ):
        return "academic_writing"
    if any(
        k in prompt_lower
        for k in ["công văn", "tờ trình", "hợp đồng", "biên bản", "soạn thảo", "copywriting"]
    ):
        return "copywriting"
    if any(k in prompt_lower for k in ["bim", "ifc", "uniclass", "rase", "revit"]):
        return "bigbim_classification"
    return "general_domain"


def parse_transcript_logs(log_dir: Path) -> list[dict[str, Any]]:
    """Scans log_dir safely for transcript.jsonl files and extracts user prompts and assistant outputs."""
    target_dir = resolve_log_dir(log_dir)
    interactions: list[dict[str, Any]] = []
    if not target_dir.exists():
        logger.warning(f"⚠️ Thư mục log '{target_dir}' không tồn tại.")
        return interactions

    log_files = find_transcript_files(target_dir)
    logger.info(f"📂 Tìm thấy {len(log_files)} file transcript log trong {target_dir}")

    for log_file in log_files:
        try:
            with open(log_file, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"❌ Lỗi đọc file {log_file.name}: {e}")
            continue

        last_user_prompt = None
        conv_id = log_file.parents[2].name if len(log_file.parents) >= 3 else log_file.parent.name

        for line in lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue

            stype = data.get("type", "")
            content = data.get("content", "")
            status = data.get("status", "")

            if stype == "USER_INPUT":
                clean_p = extract_clean_user_prompt(content)
                if len(clean_p) >= 5 and clean_p.lower() not in IGNORABLE_CONTROL_COMMANDS:
                    last_user_prompt = clean_p
            elif last_user_prompt:
                has_error = False
                response_snippet = ""

                if stype == "PLANNER_RESPONSE" and content:
                    response_snippet = content
                elif stype in ("TOOL_EXECUTION", "RUN_COMMAND") and (
                    status == "ERROR" or "Traceback" in content
                ):
                    response_snippet = content
                    has_error = True
                elif stype == "SYSTEM_MESSAGE" and (
                    "Traceback" in content or "error" in content.lower()
                ):
                    response_snippet = content
                    has_error = True

                if response_snippet:
                    interactions.append(
                        {
                            "conversation_id": conv_id,
                            "source_file": log_file.name,
                            "step_index": data.get("step_index", 0),
                            "user_prompt": last_user_prompt,
                            "planner_response": response_snippet,
                            "is_error": has_error,
                        }
                    )
                    if stype == "PLANNER_RESPONSE" and content:
                        last_user_prompt = None

    logger.info(f"📊 Đã bóc tách được {len(interactions)} lượt tương tác người dùng.")
    return interactions


def identify_failures(
    interactions: list[dict[str, Any]], taxonomy_filter: str | None = None
) -> list[dict[str, Any]]:
    """Identifies and classifies interaction failures into a 3-category taxonomy."""
    flagged_cases: list[dict[str, Any]] = []

    for item in interactions:
        response_text = str(item.get("planner_response", ""))
        response_lower = response_text.lower()
        user_prompt = str(item.get("user_prompt", ""))

        if not user_prompt or len(user_prompt) < 10:
            continue

        detected_type = None
        reason = ""

        # 1. Check Outdated Legal Citation
        for pattern, explanation in OUTDATED_LEGAL_CITATIONS:
            if re.search(pattern, response_text, re.IGNORECASE):
                detected_type = "OUTDATED_CITATION"
                reason = f"Detected citation of outdated decree: {explanation}"
                break

        # 2. Check Router Disclaimer
        if not detected_type:
            if any(kw in response_lower for kw in DISCLAIMER_KEYWORDS):
                detected_type = "ROUTER_DISCLAIMER"
                reason = "Agent issued a refusal disclaimer on potentially valid domain prompt."

        # 3. Check Tool Exception / Crash
        if not detected_type:
            if item.get("is_error") or any(exc in response_lower for exc in EXCEPTION_KEYWORDS):
                detected_type = "TOOL_EXCEPTION"
                reason = "Tool execution crashed or encountered an unhandled exception."

        if detected_type:
            if taxonomy_filter and taxonomy_filter.upper() != detected_type:
                continue

            flagged_cases.append(
                {
                    "conversation_id": item.get("conversation_id", ""),
                    "user_prompt": user_prompt,
                    "failure_type": detected_type,
                    "reason": reason,
                    "source_file": item.get("source_file", ""),
                    "step_index": item.get("step_index", 0),
                    "raw_response_snippet": response_text[:200],
                }
            )

    logger.info(f"🔍 Phát hiện {len(flagged_cases)} ca lỗi cần chuyển hóa thành Evals.")
    return flagged_cases


def generate_eval_spec_item(
    failure_case: dict[str, Any],
    skill_name: str,
    case_index: int,
    format_type: str = "harness",
) -> dict[str, Any]:
    """Generates an evaluation test case dictionary formatted for ccba_harness.evals."""
    cid = f"test_{skill_name.replace('-', '_')}_mined_{case_index:02d}"
    prompt = failure_case["user_prompt"]
    ftype = failure_case.get("failure_type", "UNKNOWN")
    reason = failure_case.get("reason", "")

    if format_type == "legacy":
        return {
            "id": cid,
            "prompt": prompt,
            "failure_type": ftype,
            "assertions": [
                {
                    "type": "regex",
                    "pattern": f"({skill_name}|xử lý|hướng dẫn|thực hiện|quy định)",
                }
            ],
        }

    # 'harness' format compatible with ccba_harness.evals.EvalItem
    rubric = (
        f"Must properly process prompt without issuing disclaimer or crashing. "
        f"Specific constraint: {reason}"
    )

    return {
        "id": cid,
        "input_prompt": prompt,
        "golden_answer": None,
        "rubric": rubric,
        "metadata": {
            "failure_type": ftype,
            "source_file": failure_case.get("source_file", ""),
            "conversation_id": failure_case.get("conversation_id", ""),
            "step_index": failure_case.get("step_index", 0),
            "mined_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_skill": skill_name,
        },
    }


def mine_logs_and_export(
    log_dir: Path,
    output_dir: Path,
    skill_filter: str | None = None,
    taxonomy: str | None = None,
    format_type: str = "harness",
    auto_inject: bool = False,
) -> int:
    """Main execution pipeline to mine logs, redact data, and export EvalItem test cases."""
    interactions = parse_transcript_logs(log_dir)
    failures = identify_failures(interactions, taxonomy_filter=taxonomy)

    if not failures:
        logger.info("🎉 Không phát hiện failures nào cần auto-tune.")
        return 0

    exported_count = 0
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group failures by skill
    grouped_failures: dict[str, list[dict[str, Any]]] = {}
    for fcase in failures:
        skill = skill_filter or classify_target_skill(fcase["user_prompt"])
        grouped_failures.setdefault(skill, []).append(fcase)

    for target_skill, skill_cases in grouped_failures.items():
        target_json = output_dir / f"eval_{target_skill}.json"

        existing_cases: list[dict[str, Any]] = []
        if target_json.exists():
            try:
                with open(target_json, encoding="utf-8") as f:
                    existing_cases = json.load(f)
            except Exception:
                existing_cases = []

        existing_prompts = {
            c.get("input_prompt") or c.get("prompt") for c in existing_cases if isinstance(c, dict)
        }

        skill_exported = 0
        for fcase in skill_cases:
            p_text = fcase["user_prompt"]
            if p_text in existing_prompts:
                continue

            eval_spec = generate_eval_spec_item(
                fcase,
                target_skill,
                len(existing_cases) + 1,
                format_type=format_type,
            )
            existing_cases.append(eval_spec)
            existing_prompts.add(p_text)
            skill_exported += 1
            exported_count += 1

        if skill_exported > 0 or auto_inject:
            with open(target_json, "w", encoding="utf-8") as f:
                json.dump(existing_cases, f, ensure_ascii=False, indent=2)
            logger.info(
                f"✅ Đã xuất {skill_exported} test cases thực chiến mới vào {target_json.name}"
            )

    return exported_count


def main() -> int:
    """CLI Entrypoint for Log Eval Miner."""
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="CCBA Production Log Mining & Eval Auto-Tuning Tool"
    )
    parser.add_argument(
        "--log-dir",
        default=None,
        help="Thư mục chứa transcript logs (mặc định tự động tìm ~/.gemini/antigravity/brain)",
    )
    parser.add_argument(
        "--output-dir",
        default=".agents/skills/eval-gate/test_cases",
        help="Thư mục xuất test_cases JSON",
    )
    parser.add_argument("--skill", help="Tên skill cụ thể cần nạp test cases mined")
    parser.add_argument(
        "--taxonomy",
        choices=["ROUTER_DISCLAIMER", "TOOL_EXCEPTION", "OUTDATED_CITATION"],
        help="Lọc loại lỗi cụ thể",
    )
    parser.add_argument(
        "--format",
        choices=["harness", "legacy"],
        default="harness",
        help="Định dạng xuất (harness cho ccba_harness.evals, legacy cho 4-layer assertions)",
    )
    parser.add_argument(
        "--auto-inject",
        action="store_true",
        help="Tự động ghi đè/bổ sung vào file eval test cases của skill",
    )

    args = parser.parse_args()
    log_dir = Path(args.log_dir) if args.log_dir else resolve_log_dir(None)
    output_dir = Path(args.output_dir)

    count = mine_logs_and_export(
        log_dir=log_dir,
        output_dir=output_dir,
        skill_filter=args.skill,
        taxonomy=args.taxonomy,
        format_type=args.format,
        auto_inject=args.auto_inject,
    )
    print(f"Mining hoàn tất: {count} cases được cập nhật.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

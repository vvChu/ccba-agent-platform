# packages/ccba-harness/src/ccba_harness/evals/miner.py
"""log_eval_miner - Production Log Mining & Failure-Driven Auto-Tuning Tool for CCBA Skills Evals.

Deep Seam module providing transcript parsing, privacy redaction (Maskara Privacy Standard),
failure taxonomy identification, domain classification, and EvalItem spec formatting.
"""

from __future__ import annotations

import datetime
import json
import logging
import re
from pathlib import Path
from typing import Any

from ._miner_catalog import (
    _CATALOG_CACHE,
    CANONICAL_TO_LEGACY_MAP,
    DEFAULT_CATALOG_RELATIVE_PATH,
    DEFAULT_SCRATCH_DIR,
    DISCLAIMER_KEYWORDS,
    EXCEPTION_KEYWORDS,
    FIRE_SAFETY_KEYWORDS,
    IGNORABLE_CONTROL_COMMANDS,
    LEGACY_SKILL_FILE_MAP,
    LEGACY_TO_CANONICAL_MAP,
    MASKARA_REGEX_PATTERNS,
    OUTDATED_LEGAL_CITATIONS,
    PII_PATTERNS,
    SENSITIVE_PATTERNS,
    SKILL_DOMAIN_EXTENSIONS,
    _find_project_root,
    classify_target_skill,
    clear_catalog_cache,
    extract_clean_user_prompt,
    load_catalog,
    redact_sensitive_info,
    resolve_catalog_path,
    resolve_output_test_file,
    score_skill_match,
    strip_accents,
    to_canonical_skill_name,
    to_legacy_skill_name,
)

logger = logging.getLogger("ccba.eval.miner")

__all__ = [
    "CANONICAL_TO_LEGACY_MAP",
    "DEFAULT_CATALOG_RELATIVE_PATH",
    "DEFAULT_SCRATCH_DIR",
    "DISCLAIMER_KEYWORDS",
    "EXCEPTION_KEYWORDS",
    "FIRE_SAFETY_KEYWORDS",
    "IGNORABLE_CONTROL_COMMANDS",
    "LEGACY_SKILL_FILE_MAP",
    "LEGACY_TO_CANONICAL_MAP",
    "MASKARA_REGEX_PATTERNS",
    "OUTDATED_LEGAL_CITATIONS",
    "PII_PATTERNS",
    "SENSITIVE_PATTERNS",
    "SKILL_DOMAIN_EXTENSIONS",
    "_CATALOG_CACHE",
    "_find_project_root",
    "classify_target_skill",
    "clear_catalog_cache",
    "extract_clean_user_prompt",
    "find_transcript_files",
    "generate_eval_spec_item",
    "identify_failures",
    "load_catalog",
    "mine_logs_and_export",
    "parse_transcript_logs",
    "redact_sensitive_info",
    "resolve_catalog_path",
    "resolve_log_dir",
    "resolve_output_test_file",
    "score_skill_match",
    "strip_accents",
    "to_canonical_skill_name",
    "to_legacy_skill_name",
]


def resolve_log_dir(configured_dir: Path | str | None) -> Path:
    """Resolves log directory, checking configured dir, local logs, workspace chats, and brain."""
    if configured_dir:
        p = Path(configured_dir)
        if p.exists():
            return p

    local_logs = Path(".system_generated/logs")
    if local_logs.exists():
        return local_logs

    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        return brain_dir

    gemini_tmp = Path.home() / ".gemini" / "tmp"
    if gemini_tmp.exists():
        return gemini_tmp

    return Path(configured_dir or ".system_generated/logs")


def _is_candidate_transcript_file(f: Path) -> bool:
    """Check whether a file path matches transcript or session log naming rules."""
    if not f.is_file():
        return False
    if f.name == "transcript.jsonl":
        return True
    if (
        f.name.startswith("transcript")
        and f.name.endswith(".jsonl")
        and not f.name.endswith("_full.jsonl")
    ):
        return True
    return f.name.startswith("session-") and (f.name.endswith(".json") or f.name.endswith(".jsonl"))


def _scan_sub_transcript_dir(sub: Path, log_files: list[Path]) -> None:
    """Scan a single subdirectory for system_generated transcripts or chat sessions."""
    sys_logs = sub / ".system_generated" / "logs"
    if sys_logs.is_dir():
        t_file = sys_logs / "transcript.jsonl"
        if t_file.is_file():
            log_files.append(t_file)

    chats_dir = (
        sub / "chats" if (sub / "chats").is_dir() else (sub if sub.name == "chats" else None)
    )
    if chats_dir and chats_dir.is_dir():
        try:
            for cf in chats_dir.iterdir():
                if (
                    cf.is_file()
                    and cf.name.startswith("session-")
                    and (cf.name.endswith(".json") or cf.name.endswith(".jsonl"))
                ):
                    log_files.append(cf)
        except (OSError, PermissionError):
            pass
        return

    try:
        for sf in sub.iterdir():
            if _is_candidate_transcript_file(sf):
                log_files.append(sf)
    except (OSError, PermissionError):
        pass


def find_transcript_files(log_dir: Path) -> list[Path]:
    """Finds all transcript.jsonl and session-*.json/jsonl files using targeted shallow scanning."""
    if not log_dir.exists():
        return []
    if log_dir.is_file():
        if (
            log_dir.name.endswith(".jsonl") or log_dir.name.endswith(".json")
        ) and not log_dir.name.endswith("_full.jsonl"):
            return [log_dir]
        return []

    log_files: list[Path] = []
    try:
        entries = list(log_dir.iterdir())
    except (OSError, PermissionError):
        return []

    for f in entries:
        if _is_candidate_transcript_file(f):
            log_files.append(f)

    for sub in entries:
        if sub.is_dir():
            _scan_sub_transcript_dir(sub, log_files)

    return sorted(set(log_files))


def _extract_message_text(mcontent: Any) -> str:
    """Extract string text from a session message content payload (list or string)."""
    if isinstance(mcontent, list):
        return "".join(
            part["text"] + "\n" for part in mcontent if isinstance(part, dict) and "text" in part
        )
    if isinstance(mcontent, str):
        return mcontent
    return str(mcontent)


def _parse_json_session_file(
    log_file: Path, content_text: str, conv_id: str, interactions: list[dict[str, Any]]
) -> None:
    """Parse a standard JSON session document (e.g. Gemini CLI session-*.json)."""
    try:
        doc = json.loads(content_text)
    except Exception:
        return
    if not (isinstance(doc, dict) and isinstance(doc.get("messages"), list)):
        return
    session_id = doc.get("sessionId", conv_id)
    last_user_prompt: str | None = None
    for msg in doc["messages"]:
        if not isinstance(msg, dict):
            continue
        mtype = str(msg.get("type", "")).lower()
        mcontent = msg.get("content", "")
        if mtype in ("user", "human"):
            user_text = _extract_message_text(mcontent) if isinstance(mcontent, (list, str)) else ""
            clean_p = extract_clean_user_prompt(user_text)
            if len(clean_p) >= 5 and clean_p.lower() not in IGNORABLE_CONTROL_COMMANDS:
                last_user_prompt = clean_p
        elif last_user_prompt:
            resp_text = _extract_message_text(mcontent)
            is_err = mtype == "error" or "error" in resp_text.lower()
            interactions.append(
                {
                    "conversation_id": session_id,
                    "source_file": log_file.name,
                    "step_index": 0,
                    "user_prompt": last_user_prompt,
                    "planner_response": resp_text,
                    "is_error": is_err,
                }
            )
            if mtype in ("bot", "model", "assistant"):
                last_user_prompt = None


def _parse_jsonl_transcript_file(
    log_file: Path, content_text: str, conv_id: str, interactions: list[dict[str, Any]]
) -> None:
    """Parse a JSON Lines transcript file (e.g. transcript.jsonl)."""
    last_user_prompt: str | None = None
    for line in content_text.splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        stype = data.get("type", "")
        content = data.get("content", "")
        status = data.get("status", "")
        if stype == "USER_INPUT":
            clean_p = extract_clean_user_prompt(str(content))
            if len(clean_p) >= 5 and clean_p.lower() not in IGNORABLE_CONTROL_COMMANDS:
                last_user_prompt = clean_p
        elif last_user_prompt:
            has_error = False
            response_snippet = ""
            content_str = str(content)
            if stype == "PLANNER_RESPONSE" and content:
                response_snippet = content_str
            elif stype in ("TOOL_EXECUTION", "RUN_COMMAND") and (
                status == "ERROR" or "Traceback" in content_str
            ):
                response_snippet = content_str
                has_error = True
            elif stype == "SYSTEM_MESSAGE" and (
                "Traceback" in content_str or "error" in content_str.lower()
            ):
                response_snippet = content_str
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
                content_text = f.read()
        except Exception as e:
            logger.error(f"❌ Lỗi đọc file {log_file.name}: {e}")
            continue

        if not content_text.strip():
            continue
        conv_id = log_file.parents[2].name if len(log_file.parents) >= 3 else log_file.parent.name
        if log_file.suffix.lower() == ".json":
            _parse_json_session_file(log_file, content_text, conv_id, interactions)
        else:
            _parse_jsonl_transcript_file(log_file, content_text, conv_id, interactions)

    logger.info(f"📊 Đã bóc tách được {len(interactions)} lượt tương tác người dùng.")
    return interactions


def _detect_interaction_failure(
    item: dict[str, Any], catalog_path: Path | str | None
) -> tuple[str | None, str]:
    """Classify a single interaction into OUTDATED_CITATION, ROUTER_DISCLAIMER, or TOOL_EXCEPTION."""
    response_text = str(item.get("planner_response", ""))
    response_lower = response_text.lower()
    user_prompt = str(item.get("user_prompt", ""))

    for pattern, explanation in OUTDATED_LEGAL_CITATIONS:
        if re.search(pattern, response_text, re.IGNORECASE):
            return "OUTDATED_CITATION", f"Detected citation of outdated decree: {explanation}"

    if any(kw in response_lower for kw in DISCLAIMER_KEYWORDS):
        target_skill = classify_target_skill(user_prompt, catalog_path=catalog_path)
        if target_skill != "general_domain":
            return (
                "ROUTER_DISCLAIMER",
                f"Agent issued a refusal disclaimer on potentially valid domain prompt "
                f"(target skill: {target_skill}).",
            )
        logger.debug(
            f"Disclaimer on out-of-scope prompt treated as expected success: {user_prompt[:50]}"
        )

    if item.get("is_error") or any(exc in response_lower for exc in EXCEPTION_KEYWORDS):
        return (
            "TOOL_EXCEPTION",
            "Tool execution crashed or encountered an unhandled exception.",
        )
    return None, ""


def identify_failures(
    interactions: list[dict[str, Any]],
    taxonomy_filter: str | None = None,
    catalog_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Identifies and classifies interaction failures into a 3-category taxonomy."""
    flagged_cases: list[dict[str, Any]] = []
    for item in interactions:
        user_prompt = str(item.get("user_prompt", ""))
        if not user_prompt or len(user_prompt) < 10:
            continue
        detected_type, reason = _detect_interaction_failure(item, catalog_path)
        if not detected_type:
            continue
        if taxonomy_filter and taxonomy_filter.upper() != detected_type:
            continue
        response_text = str(item.get("planner_response", ""))
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
        legacy_name = to_legacy_skill_name(skill_name)
        cid = f"test_{legacy_name}_mined_{case_index:02d}"
        pattern_opts = f"{skill_name}|{legacy_name}|xử lý|hướng dẫn|thực hiện|quy định"
        return {
            "id": cid,
            "prompt": prompt,
            "failure_type": ftype,
            "assertions": [
                {
                    "type": "regex",
                    "pattern": f"({pattern_opts})",
                }
            ],
        }

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


def _export_skill_failure_group(
    effective_output_dir: Path,
    target_skill: str,
    skill_cases: list[dict[str, Any]],
    format_type: str,
    auto_inject: bool,
    dry_run: bool,
) -> int:
    """Export mined failure cases for a single target skill into its evaluation JSON file."""
    target_json = resolve_output_test_file(effective_output_dir, target_skill)
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
            fcase, target_skill, len(existing_cases) + 1, format_type=format_type
        )
        existing_cases.append(eval_spec)
        existing_prompts.add(p_text)
        skill_exported += 1

    if skill_exported > 0 or auto_inject or dry_run:
        with open(target_json, "w", encoding="utf-8") as f:
            json.dump(existing_cases, f, ensure_ascii=False, indent=2)
        dest_desc = "[DRY-RUN SCRATCH]" if dry_run else "[PRODUCTION]"
        logger.info(
            f"✅ {dest_desc} Đã xuất {skill_exported} test cases thực chiến mới vào {target_json.name}"
        )
    return skill_exported


def mine_logs_and_export(
    log_dir: Path,
    output_dir: Path,
    skill_filter: str | None = None,
    taxonomy: str | None = None,
    format_type: str = "harness",
    auto_inject: bool = False,
    catalog_path: Path | str | None = None,
    dry_run: bool = False,
    scratch_dir: Path | None = None,
) -> int:
    """Main execution pipeline to mine logs, redact data, and export EvalItem test cases."""
    effective_output_dir = output_dir
    if dry_run:
        effective_output_dir = scratch_dir or DEFAULT_SCRATCH_DIR
        logger.info(
            f"🛡️ DRY-RUN KÍCH HOẠT: Xuất test cases an toàn vào '{effective_output_dir}' (không sửa đổi production)"
        )

    interactions = parse_transcript_logs(log_dir)
    failures = identify_failures(interactions, taxonomy_filter=taxonomy, catalog_path=catalog_path)
    if not failures:
        logger.info("🎉 Không phát hiện failures nào cần auto-tune.")
        return 0

    exported_count = 0
    effective_output_dir.mkdir(parents=True, exist_ok=True)
    grouped_failures: dict[str, list[dict[str, Any]]] = {}
    for fcase in failures:
        skill = skill_filter or classify_target_skill(
            fcase["user_prompt"], catalog_path=catalog_path
        )
        grouped_failures.setdefault(skill, []).append(fcase)

    for target_skill, skill_cases in grouped_failures.items():
        exported_count += _export_skill_failure_group(
            effective_output_dir, target_skill, skill_cases, format_type, auto_inject, dry_run
        )

    return exported_count

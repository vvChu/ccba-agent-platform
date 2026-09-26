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
import unicodedata
from pathlib import Path
from typing import Any

import yaml

# Sensitive Data Redaction Patterns (Maskara Privacy Standard & PII)
try:
    from ccba_maskara import REGEX_PATTERNS as MASKARA_REGEX_PATTERNS
except ImportError:
    MASKARA_REGEX_PATTERNS = {
        "anthropic-api-key": {"pattern": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")},
        "openai-api-key": {"pattern": re.compile(r"\bsk-(?!ant-)(?:proj-)?[A-Za-z0-9_-]{20,}\b")},
        "github-token": {
            "pattern": re.compile(
                r"\b(?:gh[pousr]_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{20,})\b"
            )
        },
        "aws-access-key": {"pattern": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")},
        "google-api-key": {"pattern": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")},
        "slack-token": {"pattern": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")},
        "stripe-live-key": {"pattern": re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b")},
        "jwt": {
            "pattern": re.compile(
                r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
            )
        },
        "database-url": {
            "pattern": re.compile(
                r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s\"'<>`]+"
            )
        },
        "private-key": {
            "pattern": re.compile(
                r"(?s)-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----"
            )
        },
        "env-secret": {
            "pattern": re.compile(
                r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|pwd|private[_-]?key|client[_-]?secret)\b\s*[:=]\s*[\"']?([^\s\"',`]{8,})"
            )
        },
    }

PII_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
    (re.compile(r"\b(?:0\d{9,10}|\+84\d{9,10})\b"), "[PHONE_REDACTED]"),
    (
        re.compile(
            r"\b(?:100\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3})\b"
        ),
        "[IP_REDACTED]",
    ),
]

# Legacy alias kept for backward compatibility if imported externally
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

# Configure logging
logger = logging.getLogger("ccba.eval.miner")

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

# Catalog SSOT Constants & Domain Mapping
DEFAULT_CATALOG_RELATIVE_PATH = Path(".agents/skills/platform-loader/catalog.yaml")

FIRE_SAFETY_KEYWORDS = {
    "pccc",
    "phòng cháy",
    "chữa cháy",
    "thoát nạn",
    "qcvn 06",
    "chịu lửa",
    "bậc chịu lửa",
    "giới hạn chịu lửa",
    "khói",
    "chống cháy",
    "báo cháy",
    "ngăn cháy",
    "sprinkler",
}

SKILL_DOMAIN_EXTENSIONS: dict[str, list[str]] = {
    "ccba-ai-qc-pccc-audit": [
        "pccc",
        "phòng cháy",
        "chữa cháy",
        "thoát nạn",
        "qcvn 06",
        "chịu lửa",
        "bậc chịu lửa",
        "giới hạn chịu lửa",
        "kiểm soát khói",
        "chống cháy",
        "báo cháy",
        "ngăn cháy",
        "sprinkler",
    ],
    "ccba-ai-qc": [
        "thẩm tra thiết kế",
        "thẩm tra chất lượng thiết kế",
        "kiểm tra chất lượng thiết kế",
        "thẩm tra đa bộ môn",
        "kiểm tra đa bộ môn",
        "chất lượng thiết kế",
        "heat map report",
        "quad-view",
        "qc audit",
        "qcauditpipeline",
    ],
    "ccba-academic-writing": [
        "bài báo khoa học",
        "bài báo",
        "imrad",
        "nghiên cứu khoa học",
        "học thuật",
        "academic writing",
        "cars model",
    ],
    "ccba-copywriting": [
        "soạn thảo hợp đồng",
        "hợp đồng",
        "công văn",
        "tờ trình",
        "văn bản hành chính",
        "biên bản",
        "soạn thảo",
        "copywriting",
    ],
    "ccba-legal-intel": [
        "pháp điển",
        "nghiên cứu văn bản",
        "nghị định 105",
        "nghị định 136",
        "thư viện pháp luật",
        "tra cứu luật",
        "luật xây dựng",
        "vbpl",
        "vbhn",
    ],
    "ccba-teamwork": [
        "teamwork_preview_",
        "forensic auditor",
        "team sheet",
        "orchestrator",
        "multi-agent",
    ],
}

CANONICAL_TO_LEGACY_MAP: dict[str, str] = {
    "ccba-ai-qc-pccc-audit": "pccc_audit",
    "ccba-legal-intel": "legal_intel",
    "bigbim-classification": "bigbim_classification",
    "bigbim-governance": "bigbim_governance",
    "bigbim-rase": "bigbim_rase",
    "ccba-academic-writing": "academic_writing",
    "ccba-copywriting": "copywriting",
    "ccba-markdown-document-processing": "markdown_document_processing",
    "ccba-pptx": "pptx",
    "ccba-seminar-builder": "seminar_builder",
    "ccba-xu-ly-van-phong": "xu_ly_van_phong",
    "ccba-teamwork": "agent_orchestration",
    "general_domain": "general_domain",
    "general-domain": "general_domain",
}

LEGACY_TO_CANONICAL_MAP: dict[str, str] = {
    "pccc_audit": "ccba-ai-qc-pccc-audit",
    "legal_intel": "ccba-legal-intel",
    "bigbim_classification": "bigbim-classification",
    "bigbim_governance": "bigbim-governance",
    "bigbim_rase": "bigbim-rase",
    "academic_writing": "ccba-academic-writing",
    "copywriting": "ccba-copywriting",
    "markdown_document_processing": "ccba-markdown-document-processing",
    "pptx": "ccba-pptx",
    "seminar_builder": "ccba-seminar-builder",
    "xu_ly_van_phong": "ccba-xu-ly-van-phong",
    "agent_orchestration": "ccba-teamwork",
    "general_domain": "general_domain",
}

LEGACY_SKILL_FILE_MAP: dict[str, str] = {
    "ccba-ai-qc-pccc-audit": "eval_pccc_audit.json",
    "pccc_audit": "eval_pccc_audit.json",
    "ccba-legal-intel": "eval_legal_intel.json",
    "legal_intel": "eval_legal_intel.json",
    "bigbim-classification": "eval_bigbim_classification.json",
    "bigbim_classification": "eval_bigbim_classification.json",
    "bigbim-governance": "eval_bigbim_governance.json",
    "bigbim_governance": "eval_bigbim_governance.json",
    "bigbim-rase": "eval_bigbim_rase.json",
    "bigbim_rase": "eval_bigbim_rase.json",
    "ccba-academic-writing": "eval_academic_writing.json",
    "academic_writing": "eval_academic_writing.json",
    "ccba-copywriting": "eval_copywriting.json",
    "copywriting": "eval_copywriting.json",
    "ccba-markdown-document-processing": "eval_copywriting.json",
    "markdown_document_processing": "eval_copywriting.json",
    "markdown-document-processing": "eval_copywriting.json",
    "ccba-pptx": "eval_copywriting.json",
    "pptx": "eval_copywriting.json",
    "ccba-seminar-builder": "eval_copywriting.json",
    "seminar_builder": "eval_copywriting.json",
    "seminar-builder": "eval_copywriting.json",
    "ccba-xu-ly-van-phong": "eval_copywriting.json",
    "xu_ly_van_phong": "eval_copywriting.json",
    "xu-ly-van-phong": "eval_copywriting.json",
    "office": "eval_copywriting.json",
    "ccba-teamwork": "eval_agent_orchestration.json",
    "agent_orchestration": "eval_agent_orchestration.json",
    "ccba-skill-repair": "eval_skill_repair.json",
    "skill-repair": "eval_skill_repair.json",
    "skill_repair": "eval_skill_repair.json",
    "ccba-design": "eval_visual_design.json",
    "visual_design": "eval_visual_design.json",
    "design": "eval_visual_design.json",
    "ccba-tvpl-vip-crawler": "eval_legal_tooling.json",
    "tvpl-vip-crawler": "eval_legal_tooling.json",
    "ccba-legal-ingest": "eval_legal_tooling.json",
    "legal-ingest": "eval_legal_tooling.json",
    "ccba-legal-document-tracker": "eval_legal_tooling.json",
    "legal-document-tracker": "eval_legal_tooling.json",
    "ccba-completion-checklist": "eval_legal_tooling.json",
    "completion-checklist": "eval_legal_tooling.json",
    "legal_tooling": "eval_legal_tooling.json",
    "platform_tooling": "eval_platform_tooling.json",
    "platform-tooling": "eval_platform_tooling.json",
    "general_domain": "eval_general_domain.json",
    "general-domain": "eval_general_domain.json",
}


DEFAULT_SCRATCH_DIR = Path(".md/scratch/eval_runs")


def redact_sensitive_info(text: str) -> str:
    """Redacts sensitive user credentials and PII using Maskara _rules.py standard."""
    if not text:
        return ""
    cleaned = text

    # 1. Apply Maskara secret rules
    for rule_id, rule_spec in MASKARA_REGEX_PATTERNS.items():
        pattern = rule_spec["pattern"]
        if rule_id == "env-secret":
            cleaned = pattern.sub(
                lambda m: m.group(0)[: m.start(1) - m.start(0)] + "[SECRET_REDACTED]",
                cleaned,
            )
        elif rule_id in (
            "openai-api-key",
            "anthropic-api-key",
            "google-api-key",
            "github-token",
            "aws-access-key",
            "slack-token",
            "stripe-live-key",
        ):
            cleaned = pattern.sub("[API_KEY_REDACTED]", cleaned)
        elif rule_id == "database-url":
            cleaned = pattern.sub("[DB_URL_REDACTED]", cleaned)
        elif rule_id == "private-key":
            cleaned = pattern.sub("[PRIVATE_KEY_REDACTED]", cleaned)
        elif rule_id == "jwt":
            cleaned = pattern.sub("[JWT_REDACTED]", cleaned)
        else:
            cleaned = pattern.sub(f"[{rule_id.upper().replace('-', '_')}_REDACTED]", cleaned)

    # 2. Apply PII patterns
    for p, r in PII_PATTERNS:
        cleaned = p.sub(r, cleaned)

    return cleaned.strip()


def extract_clean_user_prompt(raw_text: str) -> str:
    """Extracts clean user prompt, stripping XML enclosing tags and system metadata."""
    if not raw_text:
        return ""
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
    """Resolves log directory, checking configured dir, local logs, workspace chats, and brain."""
    if configured_dir:
        p = Path(configured_dir)
        if p.exists():
            return p

    # Fallback 1: Local workspace .system_generated/logs
    local_logs = Path(".system_generated/logs")
    if local_logs.exists():
        return local_logs

    # Fallback 2: ~/.gemini/antigravity/brain (Antigravity transcript logs)
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        return brain_dir

    # Fallback 3: ~/.gemini/tmp (Local session chat files)
    gemini_tmp = Path.home() / ".gemini" / "tmp"
    if gemini_tmp.exists():
        return gemini_tmp

    return Path(configured_dir or ".system_generated/logs")


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

    # 1. Check direct directory first
    for f in entries:
        if f.is_file():
            if f.name == "transcript.jsonl":
                log_files.append(f)
            elif (
                f.name.startswith("transcript")
                and f.name.endswith(".jsonl")
                and not f.name.endswith("_full.jsonl")
            ):
                log_files.append(f)
            elif f.name.startswith("session-") and (
                f.name.endswith(".json") or f.name.endswith(".jsonl")
            ):
                log_files.append(f)

    # 2. Shallow scan 1 level of subdirectories (e.g. brain/<conv_id> or workspace/chats)
    for sub in entries:
        if not sub.is_dir():
            continue

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
        else:
            try:
                for sf in sub.iterdir():
                    if sf.is_file():
                        if sf.name == "transcript.jsonl":
                            log_files.append(sf)
                        elif (
                            sf.name.startswith("transcript")
                            and sf.name.endswith(".jsonl")
                            and not sf.name.endswith("_full.jsonl")
                        ):
                            log_files.append(sf)
                        elif sf.name.startswith("session-") and (
                            sf.name.endswith(".json") or sf.name.endswith(".jsonl")
                        ):
                            log_files.append(sf)
            except (OSError, PermissionError):
                pass

    return sorted(set(log_files))


def to_canonical_skill_name(skill_name: str) -> str:
    """Converts a legacy shorthand skill name to its canonical name (e.g. 'pccc_audit' -> 'ccba-ai-qc-pccc-audit')."""
    if not skill_name or not isinstance(skill_name, str):
        return ""
    if skill_name in LEGACY_TO_CANONICAL_MAP:
        return LEGACY_TO_CANONICAL_MAP[skill_name]
    if skill_name.startswith("ccba-") or skill_name.startswith("bigbim-"):
        return skill_name

    candidate_ccba = f"ccba-{skill_name.replace('_', '-')}"
    candidate_bigbim = f"bigbim-{skill_name.replace('_', '-')}"
    skills = load_catalog()
    skill_names = {s.get("name") for s in skills}
    if candidate_ccba in skill_names:
        return candidate_ccba
    if candidate_bigbim in skill_names:
        return candidate_bigbim
    return skill_name


def to_legacy_skill_name(skill_name: str) -> str:
    """Converts a canonical skill name to its legacy shorthand (e.g. 'ccba-ai-qc-pccc-audit' -> 'pccc_audit')."""
    if not skill_name or not isinstance(skill_name, str):
        return ""
    if skill_name in CANONICAL_TO_LEGACY_MAP:
        return CANONICAL_TO_LEGACY_MAP[skill_name]
    clean = skill_name.replace("ccba-", "").replace("bigbim-", "").replace("-", "_")
    return clean


def strip_accents(text: str) -> str:
    """Strips Vietnamese diacritics for accent-insensitive trigger matching."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return stripped.replace("đ", "d").replace("Đ", "D")


def _find_project_root() -> Path:
    """Finds repository project root by checking for .agents/skills/platform-loader/catalog.yaml."""
    cur = Path(__file__).resolve()
    for parent in cur.parents:
        if (parent / ".agents" / "skills" / "platform-loader" / "catalog.yaml").exists():
            return parent
    return Path.cwd()


def resolve_catalog_path(configured_path: Path | str | None = None) -> Path:
    """Resolves path to catalog.yaml, checking configured path, cwd, and repository root."""
    if configured_path:
        return Path(configured_path)

    # Check relative to current working directory
    local_cat = DEFAULT_CATALOG_RELATIVE_PATH
    if local_cat.exists():
        return local_cat

    # Check relative to project root
    root = _find_project_root()
    root_cat = root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    if root_cat.exists():
        return root_cat

    return local_cat


_CATALOG_CACHE: dict[str, list[dict[str, Any]]] = {}


def clear_catalog_cache() -> None:
    """Clears the in-memory catalog cache."""
    global _CATALOG_CACHE
    _CATALOG_CACHE.clear()


def load_catalog(
    catalog_path: Path | str | None = None, reload: bool = False
) -> list[dict[str, Any]]:
    """Loads all skills and triggers from catalog.yaml as the Single Source of Truth (SSOT)."""
    target_path = resolve_catalog_path(catalog_path)
    cache_key = str(target_path.resolve()) if target_path.exists() else str(target_path)

    if not reload and cache_key in _CATALOG_CACHE:
        return _CATALOG_CACHE[cache_key]

    if not target_path.exists():
        logger.warning(f"⚠️ Không tìm thấy catalog.yaml tại '{target_path}'.")
        return []

    try:
        with open(target_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        skills = data.get("skills", [])
        if isinstance(skills, list):
            _CATALOG_CACHE[cache_key] = skills
            return skills
        return []
    except Exception as e:
        logger.error(f"❌ Lỗi nạp catalog.yaml: {e}")
        return []


def score_skill_match(
    skill: dict[str, Any], user_prompt: str, prompt_stripped: str | None = None
) -> float:
    """Computes a match score for a skill against a user prompt based on triggers and specificity."""
    if not user_prompt or not isinstance(user_prompt, str):
        return 0.0

    name = skill.get("name", "")
    score = 0.0

    if prompt_stripped is None:
        prompt_stripped = strip_accents(user_prompt)

    # 1. Exact command match (/ccba-...)
    cmd = skill.get("command")
    if cmd:
        cmd_clean = cmd.strip()
        if re.search(r"(?<!\w)" + re.escape(cmd_clean) + r"(?!\w)", user_prompt, re.IGNORECASE):
            score += 50.0

    # 2. Canonical name exact match & natural spaced variants
    if name:
        if re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", user_prompt, re.IGNORECASE):
            score += 40.0
        clean_name = name.replace("ccba-", "").replace("bigbim-", "")
        if clean_name and len(clean_name) > 4:
            if re.search(
                r"(?<!\w)" + re.escape(clean_name) + r"(?!\w)", user_prompt, re.IGNORECASE
            ):
                score += 20.0
            clean_spaced = clean_name.replace("-", " ")
            if clean_spaced != clean_name:
                pattern_spaced = r"(?<!\w)" + re.escape(clean_spaced) + r"(?!\w)"
                if re.search(pattern_spaced, user_prompt, re.IGNORECASE):
                    score += 20.0
                elif clean_spaced != strip_accents(clean_spaced) or len(clean_spaced.split()) >= 2:
                    pattern_spaced_strip = (
                        r"(?<!\w)" + re.escape(strip_accents(clean_spaced)) + r"(?!\w)"
                    )
                    if re.search(pattern_spaced_strip, prompt_stripped, re.IGNORECASE):
                        score += 20.0

    # 3. Triggers & domain extensions
    triggers = list(skill.get("triggers") or [])
    if name in SKILL_DOMAIN_EXTENSIONS:
        triggers.extend(SKILL_DOMAIN_EXTENSIONS[name])

    seen_triggers: set[str] = set()
    for t in triggers:
        t_str = str(t).strip()
        t_lower = t_str.lower()
        if not t_str or t_lower in seen_triggers:
            continue
        seen_triggers.add(t_lower)

        pattern = r"(?<!\w)" + re.escape(t_str) + r"(?!\w)"
        matched = bool(re.search(pattern, user_prompt, re.IGNORECASE))
        if not matched:
            t_strip = strip_accents(t_str)
            if t_str != t_strip or len(t_str.split()) >= 2:
                pattern_strip = r"(?<!\w)" + re.escape(t_strip) + r"(?!\w)"
                matched = bool(re.search(pattern_strip, prompt_stripped, re.IGNORECASE))

        if matched:
            words = t_str.split()
            num_words = len(words)
            char_len = len(t_str)

            if char_len <= 2:
                w = 1.0
            elif char_len == 3:
                w = 2.0
            elif num_words == 1:
                w = 4.0 + min(char_len * 0.2, 3.0)
            else:
                w = 6.0 + num_words * 4.0 + min(char_len * 0.2, 5.0)

            score += w

    # 4. Multi-agent orchestration cues
    if name == "ccba-teamwork":
        p_lower = user_prompt.lower()
        if (
            p_lower.startswith("you are teamwork_preview_")
            or p_lower.startswith("you are forensic auditor")
            or "teamwork_preview_" in p_lower
        ):
            score += 30.0

    # 5. Requirement 2: Strict domain-specific keyword gate for fire safety
    if name == "ccba-ai-qc-pccc-audit":
        has_fire_safety_kw = any(
            re.search(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", user_prompt, re.IGNORECASE)
            or re.search(
                r"(?<!\w)" + re.escape(strip_accents(kw)) + r"(?!\w)",
                prompt_stripped,
                re.IGNORECASE,
            )
            for kw in FIRE_SAFETY_KEYWORDS
        )
        if not has_fire_safety_kw:
            score = 0.0

    return score


def classify_target_skill(
    user_prompt: str,
    catalog_path: Path | str | None = None,
    canonical: bool = True,
) -> str:
    """Classifies user prompt to appropriate skill domain based on catalog.yaml SSOT and triggers.

    Args:
        user_prompt: Clean user prompt text to classify.
        catalog_path: Optional path to custom catalog.yaml.
        canonical: If True (default), returns canonical skill name (e.g. 'ccba-ai-qc-pccc-audit').
            If False, returns legacy shorthand (e.g. 'pccc_audit') for backward compatibility.
    """
    if not user_prompt or not isinstance(user_prompt, str) or not user_prompt.strip():
        return "general_domain"

    skills = load_catalog(catalog_path)
    if not skills:
        return "general_domain"

    best_skill = "general_domain"
    best_score = 0.0
    prompt_stripped = strip_accents(user_prompt)

    for s in skills:
        sc = score_skill_match(s, user_prompt, prompt_stripped=prompt_stripped)
        if sc > best_score:
            best_score = sc
            best_skill = s.get("name", "general_domain")

    if best_score <= 0.0 or best_skill == "general_domain":
        return "general_domain"

    if not canonical:
        return to_legacy_skill_name(best_skill)

    return best_skill


def resolve_output_test_file(output_dir: Path, target_skill: str) -> Path:
    """Standardizes output test suite file resolution preserving backward compatibility."""
    if not target_skill or not isinstance(target_skill, str):
        return output_dir / "eval_general_domain.json"

    # 1. If mapped legacy file exists on disk, use it
    if target_skill in LEGACY_SKILL_FILE_MAP:
        mapped_target = output_dir / LEGACY_SKILL_FILE_MAP[target_skill]
        if mapped_target.exists():
            return mapped_target

    # 2. Check candidate variants on disk
    clean = (
        target_skill.replace("ccba-", "")
        .replace("ccba_", "")
        .replace("bigbim-", "")
        .replace("-", "_")
    )
    clean_no_qc = clean.replace("ai_qc_", "")
    normalized = target_skill.replace("-", "_")
    candidates = [
        output_dir / f"eval_{target_skill}.json",
        output_dir / f"eval_{normalized}.json",
        output_dir / f"eval_{clean}.json",
        output_dir / f"eval_{clean_no_qc}.json",
    ]
    for cand in candidates:
        if cand.exists():
            return cand

    # 3. If file does not exist yet, prioritize mapped filename
    if target_skill in LEGACY_SKILL_FILE_MAP:
        return output_dir / LEGACY_SKILL_FILE_MAP[target_skill]

    # 4. Standard canonical snake_case filename default
    return output_dir / f"eval_{normalized}.json"


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
        last_user_prompt = None

        # Case 1: Standard JSON document (e.g. Gemini CLI session-*.json)
        if log_file.suffix.lower() == ".json":
            try:
                doc = json.loads(content_text)
            except Exception:
                continue

            if isinstance(doc, dict) and "messages" in doc and isinstance(doc["messages"], list):
                session_id = doc.get("sessionId", conv_id)
                for msg in doc["messages"]:
                    if not isinstance(msg, dict):
                        continue
                    mtype = str(msg.get("type", "")).lower()
                    mcontent = msg.get("content", "")

                    if mtype in ("user", "human"):
                        user_text = ""
                        if isinstance(mcontent, list):
                            for part in mcontent:
                                if isinstance(part, dict) and "text" in part:
                                    user_text += part["text"] + "\n"
                        elif isinstance(mcontent, str):
                            user_text = mcontent
                        clean_p = extract_clean_user_prompt(user_text)
                        if len(clean_p) >= 5 and clean_p.lower() not in IGNORABLE_CONTROL_COMMANDS:
                            last_user_prompt = clean_p
                    elif last_user_prompt:
                        resp_text = ""
                        if isinstance(mcontent, list):
                            for part in mcontent:
                                if isinstance(part, dict) and "text" in part:
                                    resp_text += part["text"] + "\n"
                        elif isinstance(mcontent, str):
                            resp_text = mcontent
                        else:
                            resp_text = str(mcontent)

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
            continue

        # Case 2: JSON Lines format (e.g. transcript.jsonl)
        lines = content_text.splitlines()
        for line in lines:
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

    logger.info(f"📊 Đã bóc tách được {len(interactions)} lượt tương tác người dùng.")
    return interactions


def identify_failures(
    interactions: list[dict[str, Any]],
    taxonomy_filter: str | None = None,
    catalog_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Identifies and classifies interaction failures into a 3-category taxonomy.

    Treats agent disclaimers on out-of-scope prompts as expected success, not failure.
    """
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
                target_skill = classify_target_skill(user_prompt, catalog_path=catalog_path)
                if target_skill != "general_domain":
                    detected_type = "ROUTER_DISCLAIMER"
                    reason = (
                        f"Agent issued a refusal disclaimer on potentially valid domain prompt "
                        f"(target skill: {target_skill})."
                    )
                else:
                    logger.debug(
                        f"Disclaimer on out-of-scope prompt treated as expected success: {user_prompt[:50]}"
                    )

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
    catalog_path: Path | str | None = None,
    dry_run: bool = False,
    scratch_dir: Path | None = None,
) -> int:
    """Main execution pipeline to mine logs, redact data, and export EvalItem test cases.

    Args:
        log_dir: Directory containing transcript logs.
        output_dir: Production output directory for test cases.
        skill_filter: Optional specific skill filter.
        taxonomy: Optional failure type filter.
        format_type: Output format ('harness' or 'legacy').
        auto_inject: If True, writes even if 0 new cases or forces overwrite.
        catalog_path: Optional custom catalog.yaml path.
        dry_run: If True, exports to scratch_dir and leaves output_dir untouched.
        scratch_dir: Optional scratch directory for dry-run export (default: .md/scratch/eval_runs).
    """
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

    # Group failures by skill
    grouped_failures: dict[str, list[dict[str, Any]]] = {}
    for fcase in failures:
        skill = skill_filter or classify_target_skill(
            fcase["user_prompt"], catalog_path=catalog_path
        )
        grouped_failures.setdefault(skill, []).append(fcase)

    for target_skill, skill_cases in grouped_failures.items():
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
                fcase,
                target_skill,
                len(existing_cases) + 1,
                format_type=format_type,
            )
            existing_cases.append(eval_spec)
            existing_prompts.add(p_text)
            skill_exported += 1
            exported_count += 1

        if skill_exported > 0 or auto_inject or dry_run:
            with open(target_json, "w", encoding="utf-8") as f:
                json.dump(existing_cases, f, ensure_ascii=False, indent=2)
            dest_desc = "[DRY-RUN SCRATCH]" if dry_run else "[PRODUCTION]"
            logger.info(
                f"✅ {dest_desc} Đã xuất {skill_exported} test cases thực chiến mới vào {target_json.name}"
            )

    return exported_count

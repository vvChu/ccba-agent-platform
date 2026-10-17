# packages/ccba-harness/src/ccba_harness/evals/_miner_catalog.py
"""_miner_catalog.py - Privacy redaction, catalog SSOT, and skill classification for Log Eval Miner."""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

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
                r"(?i)\b[A-Za-z0-9_]*(?:API[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSWD|PWD"
                r"|PRIVATE[_-]?KEY|CLIENT[_-]?SECRET|ACCESS[_-]?KEY|AUTH[_-]?TOKEN"
                r"|CREDENTIAL|MASTER[_-]?KEY|SERVICE[_-]?ACCOUNT)"
                r"[A-Za-z0-9_]*\s*[:=]\s*[\"']?([^\s\"',`\r\n]{8,})"
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

logger = logging.getLogger("ccba.eval.miner")

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
    local_cat = DEFAULT_CATALOG_RELATIVE_PATH
    if local_cat.exists():
        return local_cat
    root_cat = _find_project_root() / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    if root_cat.exists():
        return root_cat
    return local_cat


_CATALOG_CACHE: dict[str, list[dict[str, Any]]] = {}


def clear_catalog_cache() -> None:
    """Clears the in-memory catalog cache."""
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
    skill_names = {s.get("name") for s in load_catalog()}
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
    return skill_name.replace("ccba-", "").replace("bigbim-", "").replace("-", "_")


def _score_name_and_command(
    name: str, cmd: str | None, user_prompt: str, prompt_stripped: str
) -> float:
    """Computes match score contribution from command and canonical skill name variants."""
    score = 0.0
    if cmd:
        cmd_clean = cmd.strip()
        if re.search(r"(?<!\w)" + re.escape(cmd_clean) + r"(?!\w)", user_prompt, re.IGNORECASE):
            score += 50.0
    if not name:
        return score
    if re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", user_prompt, re.IGNORECASE):
        score += 40.0
    clean_name = name.replace("ccba-", "").replace("bigbim-", "")
    if clean_name and len(clean_name) > 4:
        if re.search(r"(?<!\w)" + re.escape(clean_name) + r"(?!\w)", user_prompt, re.IGNORECASE):
            score += 20.0
        clean_spaced = clean_name.replace("-", " ")
        if clean_spaced != clean_name:
            pat_spaced = r"(?<!\w)" + re.escape(clean_spaced) + r"(?!\w)"
            if re.search(pat_spaced, user_prompt, re.IGNORECASE):
                score += 20.0
            elif clean_spaced != strip_accents(clean_spaced) or len(clean_spaced.split()) >= 2:
                pat_strip = r"(?<!\w)" + re.escape(strip_accents(clean_spaced)) + r"(?!\w)"
                if re.search(pat_strip, prompt_stripped, re.IGNORECASE):
                    score += 20.0
    return score


def _score_triggers(triggers: list[Any], user_prompt: str, prompt_stripped: str) -> float:
    """Computes match score contribution from trigger keywords and domain extensions."""
    score = 0.0
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
                pat_strip = r"(?<!\w)" + re.escape(t_strip) + r"(?!\w)"
                matched = bool(re.search(pat_strip, prompt_stripped, re.IGNORECASE))
        if matched:
            num_words = len(t_str.split())
            char_len = len(t_str)
            if char_len <= 2:
                score += 1.0
            elif char_len == 3:
                score += 2.0
            elif num_words == 1:
                score += 4.0 + min(char_len * 0.2, 3.0)
            else:
                score += 6.0 + num_words * 4.0 + min(char_len * 0.2, 5.0)
    return score


def score_skill_match(
    skill: dict[str, Any], user_prompt: str, prompt_stripped: str | None = None
) -> float:
    """Computes a match score for a skill against a user prompt based on triggers and specificity."""
    if not user_prompt or not isinstance(user_prompt, str):
        return 0.0
    name = skill.get("name", "")
    if prompt_stripped is None:
        prompt_stripped = strip_accents(user_prompt)

    score = _score_name_and_command(name, skill.get("command"), user_prompt, prompt_stripped)
    triggers = list(skill.get("triggers") or [])
    if name in SKILL_DOMAIN_EXTENSIONS:
        triggers.extend(SKILL_DOMAIN_EXTENSIONS[name])
    score += _score_triggers(triggers, user_prompt, prompt_stripped)

    if name == "ccba-teamwork":
        p_lower = user_prompt.lower()
        if (
            p_lower.startswith("you are teamwork_preview_")
            or p_lower.startswith("you are forensic auditor")
            or "teamwork_preview_" in p_lower
        ):
            score += 30.0

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
    """Classifies user prompt to appropriate skill domain based on catalog.yaml SSOT and triggers."""
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

    if target_skill in LEGACY_SKILL_FILE_MAP:
        mapped_target = output_dir / LEGACY_SKILL_FILE_MAP[target_skill]
        if mapped_target.exists():
            return mapped_target

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

    if target_skill in LEGACY_SKILL_FILE_MAP:
        return output_dir / LEGACY_SKILL_FILE_MAP[target_skill]
    return output_dir / f"eval_{normalized}.json"

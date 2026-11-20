"""Statutory replacements, lifecycle warnings, relation synonyms, and delegation lookup."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.models import LegalDocStatus, LegalLifecycleInfo, normalize_doc_status

KNOWN_STATUTORY_REPLACEMENTS: dict[str, dict[str, str]] = {
    "15/2021/NĐ-CP": {
        "id": "ND-217-2026",
        "document_number": "217/2026/NĐ-CP",
        "title": "Nghị định 217/2026/NĐ-CP (Quản lý dự án đầu tư xây dựng)",
    },
    "15/2021/ND-CP": {
        "id": "ND-217-2026",
        "document_number": "217/2026/NĐ-CP",
        "title": "Nghị định 217/2026/NĐ-CP (Quản lý dự án đầu tư xây dựng)",
    },
    "35/2023/NĐ-CP": {
        "id": "ND-217-2026",
        "document_number": "217/2026/NĐ-CP",
        "title": "Nghị định 217/2026/NĐ-CP",
    },
    "35/2023/ND-CP": {
        "id": "ND-217-2026",
        "document_number": "217/2026/NĐ-CP",
        "title": "Nghị định 217/2026/NĐ-CP",
    },
    "06/2021/TT-BXD": {
        "id": "TT-34-2026-BXD",
        "document_number": "34/2026/TT-BXD",
        "title": "Thông tư 34/2026/TT-BXD (Phân cấp công trình xây dựng)",
    },
    "03/2016/TT-BXD": {
        "id": "TT-34-2026-BXD",
        "document_number": "34/2026/TT-BXD",
        "title": "Thông tư 34/2026/TT-BXD",
    },
    "06/2021/NĐ-CP": {
        "id": "ND-207-2026",
        "document_number": "207/2026/NĐ-CP",
        "title": "Nghị định 207/2026/NĐ-CP (Quản lý chất lượng & thi công xây dựng)",
    },
    "06/2021/ND-CP": {
        "id": "ND-207-2026",
        "document_number": "207/2026/NĐ-CP",
        "title": "Nghị định 207/2026/NĐ-CP (Quản lý chất lượng & thi công xây dựng)",
    },
    "46/2015/NĐ-CP": {
        "id": "ND-207-2026",
        "document_number": "207/2026/NĐ-CP",
        "title": "Nghị định 207/2026/NĐ-CP",
    },
    "46/2015/ND-CP": {
        "id": "ND-207-2026",
        "document_number": "207/2026/NĐ-CP",
        "title": "Nghị định 207/2026/NĐ-CP",
    },
    "12/2021/TT-BXD": {
        "id": "TT-38-2026-BXD",
        "document_number": "38/2026/TT-BXD",
        "title": "Thông tư 38/2026/TT-BXD (Định mức xây dựng và quản lý chi phí)",
    },
    "09/2024/TT-BXD": {
        "id": "TT-38-2026-BXD",
        "document_number": "38/2026/TT-BXD",
        "title": "Thông tư 38/2026/TT-BXD",
    },
    "50/2014/QH13": {
        "id": "LXD-2025",
        "document_number": "135/2025/QH15",
        "title": "Luật Xây dựng 2025 (135/2025/QH15)",
    },
    "62/2020/QH14": {
        "id": "LXD-2025",
        "document_number": "135/2025/QH15",
        "title": "Luật Xây dựng 2025 (135/2025/QH15)",
    },
    "27/2001/QH10": {
        "id": "LPCCC-2024",
        "document_number": "55/2024/QH15",
        "title": "Luật PCCC & CNCH 2024 (55/2024/QH15)",
    },
    "136/2020/NĐ-CP": {
        "id": "ND-105-2025",
        "document_number": "105/2025/NĐ-CP",
        "title": "Nghị định 105/2025/NĐ-CP (Quy định chi tiết Luật PCCC & CNCH)",
    },
    "136/2020/ND-CP": {
        "id": "ND-105-2025",
        "document_number": "105/2025/NĐ-CP",
        "title": "Nghị định 105/2025/NĐ-CP (Quy định chi tiết Luật PCCC & CNCH)",
    },
    "TCVN 2737:1995": {
        "id": "TCVN 2737:2023",
        "document_number": "TCVN 2737:2023",
        "title": "TCVN 2737:2023 (Tải trọng và tác động)",
    },
    "TCVN 5575:2012": {
        "id": "TCVN 5575:2024",
        "document_number": "TCVN 5575:2024",
        "title": "TCVN 5575:2024 (Kết cấu thép - Tiêu chuẩn thiết kế)",
    },
    "TCVN 9386:2012": {
        "id": "TCVN 9386:2025",
        "document_number": "TCVN 9386:2025",
        "title": "TCVN 9386:2025 (Thiết kế công trình chịu động đất)",
    },
}

DEFAULT_RELATION_SYNONYMS: dict[str, str] = {
    "Văn bản bị sửa đổi bổ sung": "amends_docs",
    "Văn bản bị sửa đổi, bổ sung": "amends_docs",
    "Văn bản bị thay thế": "replaced_docs",
    "Văn bản được dẫn chiếu": "referenced_docs",
    "Văn bản được căn cứ": "basis_docs",
    "Văn bản được hướng dẫn": "guided_docs",
    "Văn bản được hợp nhất": "consolidated_docs",
    "Văn bản hướng dẫn": "guiding_docs",
    "Văn bản hợp nhất": "consolidations",
    "Văn bản sửa đổi bổ sung": "amended_by_docs",
    "Văn bản sửa đổi, bổ sung": "amended_by_docs",
    "Văn bản thay thế": "replaced_by_docs",
    "Văn bản liên quan cùng nội dung": "related_docs",
}


def _norm_ref(val: str) -> str:
    """Normalize a statutory reference string for punctuation/case-insensitive lookup."""
    return re.sub(r"[\s\-_/.,:]+", "", val.lower()).replace("đ", "d")


def _extract_doc_replaces(doc: dict[str, Any]) -> list[Any]:
    """Collect replacement/supersession entries declared directly or under `relations`."""
    replaces_list: list[Any] = []
    sources: list[dict[str, Any]] = [doc]
    relations = doc.get("relations")
    if isinstance(relations, dict):
        sources.append(relations)
    for src in sources:
        for field_name in ("replaces", "supersedes", "replaced_docs"):
            val = src.get(field_name)
            if isinstance(val, list):
                replaces_list.extend(val)
            elif isinstance(val, str) and val.strip():
                replaces_list.append(val.strip())
    return replaces_list


def build_inverted_replacements(loaded: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build normalized index mapping superseded identifiers to their replacement documents."""
    index: dict[str, dict[str, Any]] = {}
    for old_ref, rep_meta in KNOWN_STATUTORY_REPLACEMENTS.items():
        index[_norm_ref(old_ref)] = {
            "id": rep_meta["id"],
            "document_number": rep_meta["document_number"],
            "title": rep_meta["title"],
            "short_name": rep_meta["document_number"],
            "status": "active",
        }
    for docs in loaded.values():
        if not isinstance(docs, list):
            continue
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            for rep in _extract_doc_replaces(doc):
                rep_str = (
                    str(rep.get("document_number") or rep.get("id") or "").strip()
                    if isinstance(rep, dict)
                    else str(rep).strip()
                )
                if rep_str:
                    index[_norm_ref(rep_str)] = doc
    return index


def _build_missing_doc_lifecycle(
    identifier: str,
    inverted_replacements: dict[str, dict[str, Any]],
    find_doc_fn: Callable[[str], dict[str, Any] | None],
) -> dict[str, Any]:
    """Build LegalLifecycleInfo dict when identifier is absent from loaded registry."""
    norm_id = _norm_ref(identifier)
    if norm_id not in inverted_replacements:
        return LegalLifecycleInfo(
            doc_id=identifier,
            document_number=identifier,
            title="",
            short_name=identifier,
            status=LegalDocStatus.UNVERIFIED,
            warning=f"⚠️ [CHƯA XÁC MINH]: Văn bản [{identifier}] không có trong cơ sở dữ liệu pháp luật chính thức. Cần kiểm tra kỹ tính pháp lý.",
            suggested_replacement=None,
        ).to_dict()

    rep_stub = inverted_replacements[norm_id]
    rep_id = str(rep_stub.get("id", rep_stub.get("document_number", "")))
    full_rep = find_doc_fn(rep_id) or rep_stub
    rep_num = str(full_rep.get("document_number") or rep_stub.get("document_number") or rep_id)
    rep_title = str(full_rep.get("title") or rep_stub.get("title") or rep_id)
    rep_short = str(full_rep.get("short_name") or rep_stub.get("short_name") or rep_num or rep_id)
    return LegalLifecycleInfo(
        doc_id=identifier,
        document_number=identifier,
        title=f"Văn bản đã hết hiệu lực (thay thế bởi {rep_short})",
        short_name=identifier,
        status=LegalDocStatus.SUPERSEDED,
        superseded_by=rep_id,
        warning=(
            f"⚠️ [CẢNH BÁO PHÁP LÝ]: Văn bản [{identifier}] đã HẾT HIỆU LỰC toàn bộ, "
            f"được thay thế bởi [{rep_title} - {rep_num}]. "
            "Cần kiểm tra kỹ các quy định chuyển tiếp hoặc áp dụng văn bản thay thế hiện hành."
        ),
        suggested_replacement={
            "id": full_rep.get("id", rep_id),
            "document_number": full_rep.get("document_number", rep_num),
            "title": full_rep.get("title", rep_title),
            "short_name": full_rep.get("short_name", rep_short),
            "status": normalize_doc_status(full_rep.get("status", "active")).value,
            "effective_date": full_rep.get("effective_date"),
        },
    ).to_dict()


def _extract_doc_relations(
    doc: dict[str, Any],
) -> tuple[list[str], str | None, list[str], list[str]]:
    """Extract normalized `(supersedes, superseded_by, amended_by, guiding_docs)` from a doc."""
    rel = raw_rel if isinstance(raw_rel := doc.get("relations"), dict) else {}
    raw_sup = (
        doc.get("supersedes")
        or doc.get("replaces")
        or doc.get("replaced_docs")
        or rel.get("replaces")
        or rel.get("supersedes")
        or []
    )
    supersedes = [raw_sup] if isinstance(raw_sup, str) else [str(s) for s in raw_sup]

    raw_by = (
        doc.get("superseded_by")
        or doc.get("replaced_by")
        or doc.get("replaced_by_docs")
        or rel.get("superseded_by")
        or rel.get("replaced_by")
    )
    if isinstance(raw_by, list) and raw_by:
        superseded_by: str | None = str(raw_by[0])
    else:
        superseded_by = str(raw_by) if raw_by else None

    raw_am = doc.get("amended_by") or doc.get("amendments") or doc.get("amends_docs") or []
    if isinstance(raw_am, list):
        amended_by = [
            str(a.get("title", a.get("ref", str(a)))) if isinstance(a, dict) else str(a)
            for a in raw_am
        ]
    else:
        amended_by = [raw_am] if isinstance(raw_am, str) else []

    raw_gd = doc.get("guiding_docs") or doc.get("guiding_decrees") or []
    guiding_docs = [str(g) for g in raw_gd] if isinstance(raw_gd, list) else [str(raw_gd)]
    return supersedes, superseded_by, amended_by, guiding_docs


def _build_lifecycle_warning_and_replacement(
    status_enum: LegalDocStatus,
    short_name: str,
    doc_num: str,
    doc_id: str,
    effective_date: str | None,
    superseded_date: str | None,
    superseded_by: str | None,
    amended_by: list[str],
    find_doc_fn: Callable[[str], dict[str, Any] | None],
) -> tuple[str | None, dict[str, Any] | None]:
    """Generate status warning banner and suggested replacement metadata if applicable."""
    warning: str | None = None
    suggested_replacement: dict[str, Any] | None = None
    label = f"{short_name} - {doc_num or doc_id}"
    if status_enum == LegalDocStatus.SUPERSEDED:
        date_str = f" từ ngày {superseded_date}" if superseded_date else ""
        rep_str = f", được thay thế bởi [{superseded_by}]" if superseded_by else ""
        warning = (
            f"⚠️ [CẢNH BÁO PHÁP LÝ]: Văn bản [{label}] đã HẾT HIỆU LỰC toàn bộ{date_str}{rep_str}. "
            "Cần kiểm tra kỹ các quy định chuyển tiếp hoặc áp dụng văn bản thay thế hiện hành."
        )
        if superseded_by and (rep_doc := find_doc_fn(superseded_by)):
            suggested_replacement = {
                "id": rep_doc.get("id"),
                "document_number": rep_doc.get("document_number"),
                "title": rep_doc.get("title"),
                "short_name": rep_doc.get("short_name"),
                "status": normalize_doc_status(rep_doc.get("status")).value,
                "effective_date": rep_doc.get("effective_date"),
            }
    elif status_enum == LegalDocStatus.PARTIALLY_AMENDED:
        amend_str = ", ".join(amended_by) if amended_by else "văn bản sửa đổi bổ sung"
        warning = f"ℹ️ [LƯU Ý PHÁP LÝ]: Văn bản [{label}] đã BỊ SỬA ĐỔI, BỔ SUNG một phần bởi: {amend_str}."
    elif status_enum == LegalDocStatus.PENDING_EFFECTIVE:
        eff_str = f" từ ngày {effective_date}" if effective_date else ""
        warning = f"⏳ [CHƯA CÓ HIỆU LỰC]: Văn bản [{label}] chưa có hiệu lực thi hành (dự kiến{eff_str})."
    elif status_enum == LegalDocStatus.DRAFT:
        warning = f"📝 [DỰ THẢO]: Văn bản [{short_name}] là bản DỰ THẢO đang lấy ý kiến, chưa có giá trị pháp lý thi hành."
    return warning, suggested_replacement


def _find_doc_with_ndcp_fallback(
    find_doc_fn: Callable[[str], dict[str, Any] | None],
    identifier: str,
) -> dict[str, Any] | None:
    """Resolve document by exact identifier or ASCII/Vietnamese NĐ-CP variant."""
    doc = find_doc_fn(identifier)
    if doc:
        return doc
    alt_id: str | None = None
    lower_id = identifier.lower()
    if "nd-cp" in lower_id or "nd_cp" in lower_id:
        alt_id = re.sub(r"(?i)nd[-_]cp", "NĐ-CP", identifier)
    elif "nđ-cp" in lower_id or "nđ_cp" in lower_id:
        alt_id = re.sub(r"(?i)nđ[-_]cp", "ND-CP", identifier)
    return find_doc_fn(alt_id) if alt_id else None


def resolve_document_lifecycle(
    find_doc_fn: Callable[[str], dict[str, Any] | None],
    inverted_replacements: dict[str, dict[str, Any]],
    identifier: str,
) -> dict[str, Any]:
    """Resolve full lifecycle status, warnings, and replacement info for a legal document."""
    doc = _find_doc_with_ndcp_fallback(find_doc_fn, identifier)
    if not doc:
        return _build_missing_doc_lifecycle(identifier, inverted_replacements, find_doc_fn)

    status_enum = normalize_doc_status(doc.get("status"))
    doc_id = str(doc.get("id", identifier))
    doc_num = str(doc.get("document_number", ""))
    short_name = str(doc.get("short_name", doc_id))
    effective_date = str(doc["effective_date"]) if doc.get("effective_date") else None
    superseded_date = str(doc["superseded_date"]) if doc.get("superseded_date") else None
    supersedes, superseded_by, amended_by, guiding_docs = _extract_doc_relations(doc)
    warning, suggested_replacement = _build_lifecycle_warning_and_replacement(
        status_enum,
        short_name,
        doc_num,
        doc_id,
        effective_date,
        superseded_date,
        superseded_by,
        amended_by,
        find_doc_fn,
    )
    territory = str(doc.get("territory", "VN"))
    hierarchy_default = "national" if territory == "VN" else "provincial"
    return LegalLifecycleInfo(
        doc_id=doc_id,
        document_number=doc_num,
        title=str(doc.get("title", "")),
        short_name=short_name,
        status=status_enum,
        effective_date=effective_date,
        superseded_date=superseded_date,
        supersedes=supersedes,
        superseded_by=superseded_by,
        amended_by=amended_by,
        guiding_docs=guiding_docs,
        territory=territory,
        hierarchy_level=str(doc.get("hierarchy_level", hierarchy_default)),
        temporal_context=doc.get("temporal_context"),
        successor_entity=doc.get("successor_entity"),
        warning=warning,
        suggested_replacement=suggested_replacement,
    ).to_dict()


def load_relation_synonyms_from_root(project_root: Path) -> dict[str, str]:
    """Load relation synonyms mapping from `relation_synonyms.yaml` under `project_root`."""
    synonyms_path = (
        project_root
        / ".agents"
        / "skills"
        / "ccba-legal-intel"
        / "resources"
        / "relation_synonyms.yaml"
    )
    if not synonyms_path.exists():
        print(f"[Registry] Synonyms config not found at {synonyms_path}. Using default synonyms.")
        return DEFAULT_RELATION_SYNONYMS.copy()
    try:
        with open(synonyms_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        mapping: dict[str, str] = {}
        for key, synonyms in config.get("relation_synonyms", {}).items():
            items = (
                synonyms
                if isinstance(synonyms, list)
                else ([synonyms] if isinstance(synonyms, str) else [])
            )
            for syn in items:
                mapping[syn] = key
                mapping[re.sub(r"\s+", " ", syn.replace(",", "")).strip()] = key
        return mapping
    except Exception as e:
        print(
            f"[Registry] Error reading relation synonyms from {synonyms_path}: {e}. Using default synonyms."
        )
        return DEFAULT_RELATION_SYNONYMS.copy()


def _matches_delegation_doc(
    doc: dict[str, Any], norm_jur: str, domain: str, target_date: str
) -> bool:
    """Return True if a registry document is an active delegation rule for territory/domain/date."""
    if str(doc.get("territory", "")).strip().upper() != norm_jur:
        return False
    if normalize_doc_status(doc.get("status")).value != LegalDocStatus.ACTIVE.value:
        return False
    topics = [str(t).lower() for t in doc.get("topics", [])]
    title = str(doc.get("title", "")).lower()
    is_delegation = (
        "phân cấp" in title
        or "ủy quyền" in title
        or any(k in topics for k in ("delegation", "phân cấp", "ủy quyền"))
        or doc.get("authority_type") == "delegation"
        or doc.get("is_delegation") is True
    )
    is_domain_match = (
        domain == "all"
        or domain in topics
        or "xây dựng" in title
        or "quy hoạch" in title
        or any(k in topics for k in ("construction", "planning"))
    )
    if not (is_delegation or is_domain_match):
        return False
    eff_date = str(doc.get("effective_date", ""))
    exp_date = str(doc.get("expiration_date", ""))
    return not ((eff_date and eff_date > target_date) or (exp_date and exp_date < target_date))


def find_active_delegation_document(
    data: dict[str, Any], norm_jur: str, domain: str, target_date: str
) -> dict[str, Any] | None:
    """Select the newest matching active delegation document for a jurisdiction."""
    candidates = [
        doc
        for docs in data.values()
        if isinstance(docs, list)
        for doc in docs
        if isinstance(doc, dict) and _matches_delegation_doc(doc, norm_jur, domain, target_date)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda d: str(d.get("effective_date", "")), reverse=True)
    return candidates[0]

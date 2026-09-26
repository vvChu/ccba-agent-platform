"""Dynamic Statutory Resolver — Hybrid Engine (ADR-0035, ADR-0050, ADR-0059).

Provides multi-tier statutory resolution across Hub Master Registry and Spoke Local Cache:
- Tier 1: Canonical Master Legal Registry (discover_master_registry_path) + Local Registry.
- Tier 2: Spoke Local Currency Card (.md/data/legal_currency_card.json).
- Tier 3: Deterministic In-Memory Statutory Fallback Map.

Guarantees Temporal Invariance (RULE-2.10) for any evaluation_date.
"""

from __future__ import annotations

import functools
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ccba_legal.registry import (
    discover_master_registry_path,
    load_legal_registry,
    resolve_project_root,
)

logger = logging.getLogger(__name__)


class StatutoryRole(str, Enum):
    """Canonical statutory domain roles in Vietnamese construction and fire safety law."""

    CONSTRUCTION_LAW = "CONSTRUCTION_LAW"
    CONSTRUCTION_GRADING = "CONSTRUCTION_GRADING"
    CONSTRUCTION_PROJECT_MANAGEMENT = "CONSTRUCTION_PROJECT_MANAGEMENT"
    CONSTRUCTION_QUALITY_MANAGEMENT = "CONSTRUCTION_QUALITY_MANAGEMENT"
    PCCC_LAW = "PCCC_LAW"
    PCCC_DECREE = "PCCC_DECREE"
    TECHNICAL_FIRE_SAFETY = "TECHNICAL_FIRE_SAFETY"


@dataclass
class StatutoryDocInfo:
    """Diagnostic outcome of resolving a statutory document for a specific role and date."""

    role: StatutoryRole
    doc_number: str
    title: str
    effective_date: str
    status: str = "active"
    superseded_by: str | None = None
    supersedes: list[str] = field(default_factory=list)
    source_origin: str = (
        "master_registry"  # "master_registry" | "local_registry" | "currency_card" | "fallback"
    )
    provenance_hash: str | None = None

    @property
    def citation_str(self) -> str:
        """Standard formatted citation string."""
        return f"{self.title} ({self.doc_number})"


# Canonical metadata mapping for fallback and registry correlation
ROLE_SPEC_TABLE: dict[StatutoryRole, dict[str, Any]] = {
    StatutoryRole.CONSTRUCTION_LAW: {
        "active_doc_number": "135/2025/QH15",
        "effective_date": "2026-07-01",
        "active_title": "Luật Xây dựng 2025 (Số 135/2025/QH15)",
        "superseded_doc_number": "50/2014/QH13",
        "superseded_title": "Luật Xây dựng 2014 (Số 50/2014/QH13)",
        "supersedes": ["50/2014/QH13", "62/2020/QH14"],
        "domain_key": "Luật Xây dựng",
    },
    StatutoryRole.CONSTRUCTION_GRADING: {
        "active_doc_number": "34/2026/TT-BXD",
        "effective_date": "2026-07-01",
        "active_title": "Thông tư 34/2026/TT-BXD quy định chi tiết về cấp công trình xây dựng",
        "superseded_doc_number": "06/2021/TT-BXD",
        "superseded_title": "Thông tư 06/2021/TT-BXD quy định về phân cấp công trình xây dựng",
        "supersedes": ["06/2021/TT-BXD", "03/2016/TT-BXD"],
        "domain_key": "Phân cấp công trình xây dựng (Cấp I)",
    },
    StatutoryRole.CONSTRUCTION_PROJECT_MANAGEMENT: {
        "active_doc_number": "217/2026/NĐ-CP",
        "effective_date": "2026-07-01",
        "active_title": "Nghị định 217/2026/NĐ-CP về Quản lý dự án đầu tư xây dựng",
        "superseded_doc_number": "15/2021/NĐ-CP",
        "superseded_title": "Nghị định 15/2021/NĐ-CP quy định chi tiết một số nội dung về quản lý dự án đầu tư xây dựng",
        "supersedes": ["15/2021/NĐ-CP", "35/2023/NĐ-CP", "59/2015/NĐ-CP"],
        "domain_key": "Quản lý dự án đầu tư xây dựng & Thẩm tra thiết kế",
    },
    StatutoryRole.CONSTRUCTION_QUALITY_MANAGEMENT: {
        "active_doc_number": "207/2026/NĐ-CP",
        "effective_date": "2026-07-01",
        "active_title": "Nghị định 207/2026/NĐ-CP về Quản lý chất lượng, thi công và bảo trì",
        "superseded_doc_number": "06/2021/NĐ-CP",
        "superseded_title": "Nghị định 06/2021/NĐ-CP quy định chi tiết về quản lý chất lượng, thi công xây dựng và bảo trì",
        "supersedes": ["06/2021/NĐ-CP", "46/2015/NĐ-CP"],
        "domain_key": "Quản lý chất lượng, thi công và bảo trì",
    },
    StatutoryRole.PCCC_LAW: {
        "active_doc_number": "55/2024/QH15",
        "effective_date": "2025-07-01",
        "active_title": "Luật Phòng cháy, chữa cháy và cứu nạn, cứu hộ 2024 (Số 55/2024/QH15)",
        "superseded_doc_number": "27/2001/QH10",
        "superseded_title": "Luật Phòng cháy và chữa cháy 2001 (Số 27/2001/QH10)",
        "supersedes": ["27/2001/QH10", "40/2013/QH13"],
        "domain_key": "PCCC và Cứu nạn, cứu hộ",
    },
    StatutoryRole.PCCC_DECREE: {
        "active_doc_number": "105/2025/NĐ-CP",
        "effective_date": "2025-07-01",
        "active_title": "Nghị định 105/2025/NĐ-CP quy định chi tiết thi hành Luật Phòng cháy, chữa cháy và cứu nạn, cứu hộ",
        "superseded_doc_number": "136/2020/NĐ-CP",
        "superseded_title": "Nghị định 136/2020/NĐ-CP quy định chi tiết một số điều của Luật Phòng cháy và chữa cháy",
        "supersedes": ["136/2020/NĐ-CP"],
        "domain_key": "Nghị định PCCC",
    },
    StatutoryRole.TECHNICAL_FIRE_SAFETY: {
        "active_doc_number": "QCVN 06:2022/BXD",
        "effective_date": "2023-01-16",
        "active_title": "QCVN 06:2022/BXD và Sửa đổi 1:2023 (Quy chuẩn kỹ thuật quốc gia về An toàn cháy)",
        "superseded_doc_number": "QCVN 06:2021/BXD",
        "superseded_title": "QCVN 06:2021/BXD về An toàn cháy cho nhà và công trình",
        "supersedes": ["QCVN 06:2021/BXD"],
        "domain_key": "An toàn cháy",
    },
}


def _normalize_date_str(d: str | date | datetime | None) -> str:
    """Normalize input date to YYYY-MM-DD format, supporting YYYY-MM-DD and DD/MM/YYYY."""
    if d is None:
        return datetime.now().strftime("%Y-%m-%d")
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d")
    if isinstance(d, date):
        return d.strftime("%Y-%m-%d")
    if isinstance(d, str):
        cleaned = d.strip()
        if not cleaned:
            return datetime.now().strftime("%Y-%m-%d")
        # Format 1: YYYY-MM-DD or YYYY/MM/DD
        match_iso = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", cleaned)
        if match_iso:
            year, month, day = match_iso.groups()
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        # Format 2: DD/MM/YYYY or DD-MM-YYYY (Vietnamese standard)
        match_vn = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", cleaned)
        if match_vn:
            day, month, year = match_vn.groups()
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        raise ValueError(
            f"Invalid evaluation_date format: '{d}'. Expected 'YYYY-MM-DD' or 'DD/MM/YYYY'."
        )
    return datetime.now().strftime("%Y-%m-%d")


def _find_doc_in_registry_data(
    registry_data: dict[str, Any], target_doc_number: str
) -> dict[str, Any] | None:
    """Traverse all document lists in registry dictionary to find by document_number."""
    norm_target = target_doc_number.strip().upper()
    for _key, value in registry_data.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    doc_num = str(item.get("document_number") or "").strip().upper()
                    if doc_num == norm_target:
                        return item
                    # Try matching by ID or title snippet
                    item_id = str(item.get("id") or "").strip().upper()
                    if norm_target in item_id:
                        return item
    return None


@functools.lru_cache(maxsize=16)
def _load_cached_registry(path_str: str) -> dict[str, Any]:
    """Load and cache registry YAML by resolved path string."""
    p = Path(path_str)
    if not p.is_file():
        return {}
    try:
        return load_legal_registry(p)
    except Exception as exc:
        logger.warning("Failed to load registry from %s: %s", path_str, exc)
        return {}


def _resolve_from_master_registry(
    role: StatutoryRole, eval_date: str, custom_path: Path | str | None = None
) -> StatutoryDocInfo | None:
    """Tier 1: Resolve statutory document against Hub Master Registry and local registry."""
    spec = ROLE_SPEC_TABLE[role]
    is_active = eval_date >= spec["effective_date"]
    target_num = spec["active_doc_number"] if is_active else spec["superseded_doc_number"]

    # 1. Try master registry discovery
    try:
        master_path = discover_master_registry_path(custom_path)
        if master_path and master_path.is_file():
            data = _load_cached_registry(str(master_path))
            item = _find_doc_in_registry_data(data, target_num)
            if item:
                return StatutoryDocInfo(
                    role=role,
                    doc_number=item.get("document_number") or target_num,
                    title=item.get("title")
                    or (spec["active_title"] if is_active else spec["superseded_title"]),
                    effective_date=item.get("effective_date") or spec["effective_date"],
                    status=str(item.get("status") or "active"),
                    superseded_by=item.get("superseded_by"),
                    supersedes=item.get("supersedes") or spec.get("supersedes", []),
                    source_origin="master_registry",
                    provenance_hash=item.get("sha256"),
                )
    except Exception as exc:
        logger.debug("Tier 1 master registry search error: %s", exc)

    # 2. Try local project registry (.md/data/legal_registry.yaml)
    try:
        proj_root = resolve_project_root()
        local_reg = proj_root / ".md" / "data" / "legal_registry.yaml"
        if local_reg.is_file():
            data = _load_cached_registry(str(local_reg))
            item = _find_doc_in_registry_data(data, target_num)
            if item:
                return StatutoryDocInfo(
                    role=role,
                    doc_number=item.get("document_number") or target_num,
                    title=item.get("title")
                    or (spec["active_title"] if is_active else spec["superseded_title"]),
                    effective_date=item.get("effective_date") or spec["effective_date"],
                    status=str(item.get("status") or "active"),
                    superseded_by=item.get("superseded_by"),
                    supersedes=item.get("supersedes") or spec.get("supersedes", []),
                    source_origin="local_registry",
                    provenance_hash=item.get("sha256"),
                )
    except Exception as exc:
        logger.debug("Tier 1 local registry search error: %s", exc)

    return None


def _discover_currency_card_path() -> Path | None:
    """Discover the canonical legal_currency_card.json across Monorepo root and Spoke cwd."""
    # 1. Check CCBA_HUB_PATH environment variable
    hub_env = os.environ.get("CCBA_HUB_PATH")
    if hub_env:
        cand = Path(hub_env) / ".md" / "data" / "legal_currency_card.json"
        if cand.is_file():
            return cand.resolve()

    # 2. Traverse upwards from current file to locate directory with .md/data/legal_currency_card.json
    current = Path(__file__).resolve()
    for parent in current.parents:
        cand = parent / ".md" / "data" / "legal_currency_card.json"
        if cand.is_file():
            return cand.resolve()

    # 3. Check current working directory and its parents
    try:
        cwd = Path.cwd().resolve()
        for parent in [cwd, *cwd.parents]:
            cand = parent / ".md" / "data" / "legal_currency_card.json"
            if cand.is_file():
                return cand.resolve()
    except Exception:
        pass

    return None


def _resolve_from_currency_card(role: StatutoryRole, eval_date: str) -> StatutoryDocInfo | None:
    """Tier 2: Resolve statutory document against Spoke Local Currency Card (.md/data/legal_currency_card.json)."""
    spec = ROLE_SPEC_TABLE[role]
    card_path = _discover_currency_card_path()
    if not card_path or not card_path.is_file():
        return None

    try:
        with open(card_path, encoding="utf-8") as f:
            card_data = json.load(f)

        target_domain = spec["domain_key"]
        for entry in card_data.get("statutory_replacements", []):
            if entry.get("domain") == target_domain or target_domain in str(
                entry.get("domain", "")
            ):
                eff_date = str(entry.get("effective_date") or spec["effective_date"])
                if eval_date >= eff_date:
                    doc_num = str(entry.get("document_number") or spec["active_doc_number"])
                    title = str(
                        entry.get("active_law")
                        or entry.get("active_decree")
                        or entry.get("active_circular")
                        or entry.get("active_standard")
                        or spec["active_title"]
                    )
                    return StatutoryDocInfo(
                        role=role,
                        doc_number=doc_num,
                        title=title,
                        effective_date=eff_date,
                        status="active",
                        supersedes=entry.get("supersedes", []),
                        source_origin="currency_card",
                    )
                else:
                    # Superseded historical period
                    supersedes_list = entry.get("supersedes", [])
                    old_num = (
                        supersedes_list[0] if supersedes_list else spec["superseded_doc_number"]
                    )
                    return StatutoryDocInfo(
                        role=role,
                        doc_number=old_num,
                        title=spec["superseded_title"],
                        effective_date="2021-01-01",
                        status="superseded",
                        superseded_by=entry.get("document_number"),
                        source_origin="currency_card",
                    )
    except Exception as exc:
        logger.warning("Tier 2 currency card parse error: %s", exc)

    return None


def resolve_statutory_doc(
    role: StatutoryRole | str,
    evaluation_date: str | date | datetime | None = None,
    registry_path: Path | str | None = None,
) -> StatutoryDocInfo:
    """Resolve statutory document under the Hybrid Architecture (Tier 1 -> Tier 2 -> Tier 3).

    Args:
        role: Canonical StatutoryRole enum or string name.
        evaluation_date: Project evaluation date string ('YYYY-MM-DD') or date object.
        registry_path: Optional explicit custom registry path.

    Returns:
        StatutoryDocInfo with resolved document number, title, effective date, and origin.
    """
    if isinstance(role, str):
        role_canonical = StatutoryRole(role)
    else:
        role_canonical = role

    eval_date = _normalize_date_str(evaluation_date)

    # Tier 1: Master Registry + Local Registry
    res = _resolve_from_master_registry(role_canonical, eval_date, custom_path=registry_path)
    if res is not None:
        return res

    # Tier 2: Spoke Local Currency Card Snapshot
    res = _resolve_from_currency_card(role_canonical, eval_date)
    if res is not None:
        return res

    # Tier 3: Deterministic In-Memory Fallback Invariant
    spec = ROLE_SPEC_TABLE[role_canonical]
    is_active = eval_date >= spec["effective_date"]
    return StatutoryDocInfo(
        role=role_canonical,
        doc_number=spec["active_doc_number"] if is_active else spec["superseded_doc_number"],
        title=spec["active_title"] if is_active else spec["superseded_title"],
        effective_date=spec["effective_date"] if is_active else "2021-01-01",
        status="active" if is_active else "superseded",
        supersedes=spec.get("supersedes", []),
        source_origin="fallback",
    )


def clear_resolver_cache() -> None:
    """Flush LRU cache for registry loaders."""
    _load_cached_registry.cache_clear()

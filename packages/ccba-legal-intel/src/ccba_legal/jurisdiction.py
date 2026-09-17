"""jurisdiction.py - Multi-Tier Territorial & Administrative Authority Resolution.

Manages temporal administrative succession, ISO 3166-2:VN jurisdiction normalization,
authority deprecation guardrails, and dual-pass RAG query expansion (ADR 0035, ADR 0050).

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AuthorityResolutionResult:
    """Represents the resolution of a government authority across time."""

    original_name: str
    current_authority: str
    is_deprecated: bool = False
    change_date: str | None = None
    legal_basis: str | None = None
    jurisdiction: str = "VN"
    transferred_functions: list[str] = field(default_factory=list)
    warning: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "original_name": self.original_name,
            "current_authority": self.current_authority,
            "is_deprecated": self.is_deprecated,
            "change_date": self.change_date,
            "legal_basis": self.legal_basis,
            "jurisdiction": self.jurisdiction,
            "transferred_functions": self.transferred_functions,
            "warning": self.warning,
        }


_ONTOLOGY_CACHE: dict[str, Any] | None = None


def get_default_ontology_path() -> Path:
    """Resolve the default absolute path to administrative_ontology.yaml."""
    env_path = os.environ.get("CCBA_ADMINISTRATIVE_ONTOLOGY_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p.resolve()

    return Path(__file__).resolve().parent / "resources" / "administrative_ontology.yaml"


def load_administrative_ontology(
    ontology_path: Path | str | None = None, reload: bool = False
) -> dict[str, Any]:
    """Load and cache the administrative ontology YAML.

    Args:
        ontology_path: Optional custom path to administrative_ontology.yaml.
        reload: If True, forces reloading from disk even if cached.

    Returns:
        Dictionary containing territories, territory_events, authorities, and authority_tiers.
    """
    global _ONTOLOGY_CACHE
    if _ONTOLOGY_CACHE is not None and not reload and ontology_path is None:
        return _ONTOLOGY_CACHE

    target_path = Path(ontology_path) if ontology_path else get_default_ontology_path()
    if not target_path.is_file():
        return {
            "territories": {},
            "territory_events": [],
            "authorities": {},
            "authority_tiers": {},
        }

    try:
        with open(target_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                data = {}
            if ontology_path is None:
                _ONTOLOGY_CACHE = data
            return data
    except Exception:
        return {
            "territories": {},
            "territory_events": [],
            "authorities": {},
            "authority_tiers": {},
        }


def normalize_jurisdiction(code_or_name: str | None) -> str:
    """Normalize a jurisdiction code, province name, or alias to canonical ISO 3166-2:VN.

    Examples:
        - 'Hà Nội', 'HN', 'Thủ đô Hà Nội' -> 'VN-HN'
        - 'TP.HCM', 'Hồ Chí Minh', 'VN-SG' -> 'VN-HCM'
        - 'Đà Nẵng', 'DN' -> 'VN-DN'
        - 'Toàn quốc', 'TW', None, '' -> 'VN'
    """
    if not code_or_name:
        return "VN"

    s = code_or_name.strip()
    if not s:
        return "VN"

    upper_s = s.upper().replace("_", "-")
    if upper_s in {"VN", "NATIONAL", "TOÀN QUỐC", "TOAN QUOC", "TW", "TRUNG ƯƠNG", "TRUNG_UONG"}:
        return "VN"

    ontology = load_administrative_ontology()
    territories = ontology.get("territories", {})

    # Check direct code
    if upper_s in territories:
        return upper_s

    # Check aliases
    s_lower = s.lower()
    for code, info in territories.items():
        if not isinstance(info, dict):
            continue
        aliases = [str(a).lower() for a in info.get("aliases", [])]
        name = str(info.get("name", "")).lower()
        if s_lower == name or s_lower in aliases:
            return str(code)

    # Fallback common heuristics
    if "hà nội" in s_lower or "ha noi" in s_lower or upper_s == "HN":
        return "VN-HN"
    if (
        "hồ chí minh" in s_lower
        or "ho chi minh" in s_lower
        or "sài gòn" in s_lower
        or upper_s in {"HCM", "TPHCM", "SG"}
    ):
        return "VN-HCM"
    if "đà nẵng" in s_lower or "da nang" in s_lower or upper_s == "DN":
        return "VN-DN"
    if "hải phòng" in s_lower or "hai phong" in s_lower or upper_s == "HP":
        return "VN-HP"
    if "hà tây" in s_lower or "ha tay" in s_lower:
        return "VN-HT"

    return upper_s if upper_s.startswith("VN-") else f"VN-{upper_s}"


def resolve_authority(
    entity_name: str,
    as_of_date: str | None = None,
    jurisdiction: str = "VN-HN",
    ontology_path: Path | str | None = None,
) -> AuthorityResolutionResult:
    """Resolve an administrative authority according to historical timeline and legal succession.

    Args:
        entity_name: Name of the authority (e.g. 'Sở Quy hoạch - Kiến trúc', 'Sở Xây dựng').
        as_of_date: Date to evaluate against ('YYYY-MM-DD'). Defaults to today if None.
        jurisdiction: ISO 3166-2:VN jurisdiction code (e.g. 'VN-HN').
        ontology_path: Optional custom ontology file path.

    Returns:
        AuthorityResolutionResult with legal successor, deprecation status, and warnings.
    """
    norm_jur = normalize_jurisdiction(jurisdiction)
    eval_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
    ontology = load_administrative_ontology(ontology_path)
    authorities = ontology.get("authorities", {}).get(norm_jur, [])

    entity_clean = entity_name.strip()
    entity_lower = entity_clean.lower()

    # Search through authorities and their predecessors
    for auth in authorities:
        if not isinstance(auth, dict):
            continue

        current_name = auth.get("current_name", "")
        current_name_lower = current_name.lower()

        # Check if matching current authority name directly
        if entity_lower == current_name_lower or entity_lower in current_name_lower:
            return AuthorityResolutionResult(
                original_name=entity_clean,
                current_authority=current_name,
                is_deprecated=False,
                jurisdiction=norm_jur,
                transferred_functions=auth.get("functions", []),
                warning=None,
            )

        # Check predecessors
        predecessors = auth.get("predecessors", [])
        for pred in predecessors:
            if not isinstance(pred, dict):
                continue

            pred_name = pred.get("name", "")
            pred_aliases = [str(a).lower() for a in pred.get("aliases", [])]
            pred_name_lower = pred_name.lower()

            if entity_lower == pred_name_lower or any(a in entity_lower for a in pred_aliases):
                dissolved_date = pred.get("dissolved_date") or pred.get("valid_to")
                is_dep = True
                if dissolved_date and eval_date < dissolved_date:
                    is_dep = False

                return AuthorityResolutionResult(
                    original_name=entity_clean,
                    current_authority=current_name,
                    is_deprecated=is_dep,
                    change_date=dissolved_date,
                    legal_basis=pred.get("legal_basis"),
                    jurisdiction=norm_jur,
                    transferred_functions=pred.get("transferred_functions", []),
                    warning=pred.get("warning") if is_dep else None,
                )

    # Fallback when entity not recognized in ontology
    return AuthorityResolutionResult(
        original_name=entity_clean,
        current_authority=entity_clean,
        is_deprecated=False,
        jurisdiction=norm_jur,
    )


def expand_jurisdiction_queries(
    query: str,
    jurisdiction: str | None = None,
    as_of_date: str | None = None,
    ontology_path: Path | str | None = None,
) -> list[str]:
    """Expand search query with historical names and predecessor entities for RAG (Dual-Pass).

    Forward & Backward Expansion:
    - If querying 'Hà Nội' for planning: expands to include 'Hà Tây', 'Mê Linh'.
    - If querying historical province 'Hà Tây': expands to include 'Hà Nội' and 'Sở Xây dựng'.
    - If querying deprecated agency 'Sở Quy hoạch - Kiến trúc': adds 'Sở Xây dựng'.

    Args:
        query: Original user or RAG query text.
        jurisdiction: Territory code or None to infer.
        as_of_date: Evaluation date ('YYYY-MM-DD').
        ontology_path: Optional custom ontology file path.

    Returns:
        List of expanded query variants.
    """
    norm_jur = normalize_jurisdiction(jurisdiction) if jurisdiction else "VN"
    ontology = load_administrative_ontology(ontology_path)
    events = ontology.get("territory_events", [])
    authorities = ontology.get("authorities", {}).get(norm_jur, [])

    expanded_terms: list[str] = [query]
    query_lower = query.lower()

    # 1. Geographic territory expansion
    for event in events:
        if not isinstance(event, dict):
            continue
        effective_date = event.get("effective_date", "9999-12-31")

        # Mergers into current jurisdiction
        successors = [str(s.get("code", "")) for s in event.get("successors", [])]
        if norm_jur in successors or any(s in norm_jur for s in successors):
            for pred in event.get("predecessors", []):
                pred_name = str(pred.get("name", ""))
                pred_code = str(pred.get("code", ""))
                # If historical date or general query, add predecessor
                if not as_of_date or as_of_date < effective_date:
                    if pred_name and pred_name.lower() not in query_lower:
                        expanded_terms.append(f"{query} {pred_name}")
                # If query explicitly names predecessor, add successor
                if pred_name.lower() in query_lower or pred_code.lower() in query_lower:
                    expanded_terms.append(f"{query} Hà Nội Sở Xây dựng")

    # 2. Authority agency expansion
    for auth in authorities:
        if not isinstance(auth, dict):
            continue
        current_name = auth.get("current_name", "")
        for pred in auth.get("predecessors", []):
            pred_name = pred.get("name", "")
            aliases = pred.get("aliases", [])
            if pred_name.lower() in query_lower or any(
                str(a).lower() in query_lower for a in aliases
            ):
                if current_name.lower() not in query_lower:
                    expanded_terms.append(f"{query} {current_name}")

    # Remove duplicates preserving order
    seen: set[str] = set()
    result: list[str] = []
    for term in expanded_terms:
        if term not in seen:
            seen.add(term)
            result.append(term)

    return result


def validate_authority_naming(
    text: str,
    jurisdiction: str = "VN",
    ontology_path: Path | str | None = None,
    as_of_date: str | None = None,
) -> list[dict[str, Any]]:
    """Scan text to detect usage of dissolved or merged authorities (Adversarial Guardrail).

    Args:
        text: Text to audit (e.g. AI answer, technical memo).
        jurisdiction: Jurisdiction code (default 'VN').
        ontology_path: Optional custom ontology file path.
        as_of_date: Date to evaluate against (YYYY-MM-DD), defaults to today.

    Returns:
        List of detected violations with replacement and legal basis.
    """
    norm_jur = normalize_jurisdiction(jurisdiction)
    ontology = load_administrative_ontology(ontology_path)
    eval_date = as_of_date or datetime.now().strftime("%Y-%m-%d")

    violations: list[dict[str, Any]] = []

    # 1. National Invariants: Abolition of District-level agencies post-2025-07-01
    national_invariants = ontology.get("national_invariants", {})
    district_info = national_invariants.get("district_level", {})
    district_dissolved_date = district_info.get("dissolved_date", "2025-07-01")

    if eval_date >= district_dissolved_date:
        district_entities = district_info.get(
            "entities",
            [
                "UBND Quận",
                "UBND Huyện",
                "UBND Thị xã",
                "Phòng Quản lý đô thị",
                "Phòng Kinh tế và Hạ tầng",
            ],
        )
        for dist_entity in district_entities:
            escaped = re.escape(dist_entity.strip())
            regex = re.compile(
                rf"(?<![a-zA-Z0-9_\u00C0-\u1EF9]){escaped}(?![a-zA-Z0-9_\u00C0-\u1EF9])",
                re.IGNORECASE,
            )
            match = regex.search(text)
            if match:
                snippet_window = text[
                    max(0, match.start() - 30) : min(len(text), match.end() + 30)
                ].lower()
                if any(
                    neg in snippet_window
                    for neg in ["đã giải thể", "đã kết thúc", "không còn", "bãi bỏ", "sáp nhập"]
                ):
                    continue
                violations.append(
                    {
                        "found_entity": match.group(0),
                        "replacement": "Sở Xây dựng (cấp tỉnh) hoặc UBND Xã/Phường (cấp cơ sở)",
                        "warning": f"Chính quyền cấp huyện ('{match.group(0)}') đã kết thúc hoạt động từ {district_dissolved_date} theo NQ 203/2025/QH15.",
                        "legal_basis": district_info.get(
                            "legal_basis", "Nghị quyết số 203/2025/QH15 sửa đổi Điều 110 Hiến pháp"
                        ),
                        "jurisdiction": "VN",
                    }
                )
                break

    # 2. Local Authority Predecessors
    authorities = ontology.get("authorities", {}).get(norm_jur, [])
    for auth in authorities:
        if not isinstance(auth, dict):
            continue

        current_name = auth.get("current_name", "")
        predecessors = auth.get("predecessors", [])

        for pred in predecessors:
            if not isinstance(pred, dict):
                continue

            dissolved_date = pred.get("dissolved_date") or pred.get("valid_to")
            if dissolved_date and eval_date < dissolved_date:
                continue  # Not yet dissolved on eval_date

            pred_name = pred.get("name", "")
            aliases = pred.get("aliases", [])
            patterns_to_check = [pred_name] + aliases

            for pattern in patterns_to_check:
                if not pattern or len(pattern.strip()) < 3:
                    continue
                escaped = re.escape(pattern.strip())
                regex = re.compile(
                    rf"(?<![a-zA-Z0-9_\u00C0-\u1EF9]){escaped}(?![a-zA-Z0-9_\u00C0-\u1EF9])",
                    re.IGNORECASE,
                )
                match = regex.search(text)
                if match:
                    violations.append(
                        {
                            "found_entity": match.group(0),
                            "replacement": current_name,
                            "warning": pred.get(
                                "warning",
                                f"Cơ quan '{pattern}' đã được sáp nhập vào '{current_name}'.",
                            ),
                            "legal_basis": pred.get(
                                "legal_basis", "Đề án sắp xếp cơ quan chuyên môn."
                            ),
                            "jurisdiction": norm_jur,
                        }
                    )
                    break

    return violations


def validate_tier_authority(
    text: str,
    jurisdiction: str = "VN",
    ontology_path: Path | str | None = None,
    as_of_date: str | None = None,
    registry_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Audit text to verify local authority tier compliance (e.g. communes cannot approve major planning without delegation).

    Detects violations where commune/ward level (UBND Xã/Phường) is advised as
    having authority to approve master plans, basic designs, or issue building permits without statutory or delegated authority.

    Args:
        text: Text to audit.
        jurisdiction: Territory code (default 'VN').
        ontology_path: Optional custom ontology path.
        as_of_date: Evaluation date (YYYY-MM-DD), defaults to current date.
        registry_path: Optional path to legal registry for dynamic delegation discovery.

    Returns:
        List of detected authority tier violations.
    """
    norm_jur = normalize_jurisdiction(jurisdiction)
    violations: list[dict[str, Any]] = []

    prohibited_regex = re.compile(
        r"(?:ubnd\s+(?:phường|xã|thị\s+trấn)|phường|xã)\s+.*?"
        r"(?:phê\s+duyệt|thẩm\s+định|chấp\s+thuận|cấp\s+giấy\s+phép|cấp\s+phép)\s+.*?"
        r"(?:quy\s+hoạch|tổng\s+mặt\s+bằng|1/500|tkcs|thiết\s+kế\s+cơ\s+sở|xây\s+dựng)",
        re.IGNORECASE,
    )

    legal_basis = "Quy định phân cấp quản lý của UBND cấp tỉnh và Luật Xây dựng hiện hành"
    try:
        from ccba_legal.registry import get_active_delegation_document

        delegation_doc = get_active_delegation_document(
            territory=norm_jur,
            as_of_date=as_of_date,
            registry_path=registry_path,
        )
        if delegation_doc:
            doc_num = (
                delegation_doc.get("document_number")
                or delegation_doc.get("short_name")
                or delegation_doc.get("id")
            )
            legal_basis = f"{doc_num} của UBND cấp tỉnh ({norm_jur})"
        elif norm_jur == "VN-HN":
            legal_basis = "Quyết định phân cấp của UBND TP. Hà Nội và Luật Thủ đô 2024"
    except Exception:
        pass

    violation_warning = "UBND Phường/Xã không có thẩm quyền thẩm định hay phê duyệt quy hoạch tổng mặt bằng 1/500, TKCS nếu không có văn bản phân cấp hợp lệ."

    for match in prohibited_regex.finditer(text):
        snippet = match.group(0)
        if "không" in snippet.lower() or "chưa" in snippet.lower():
            continue

        violations.append(
            {
                "violation_type": "COMMUNE_AUTHORITY_EXCEEDED",
                "snippet": snippet,
                "warning": violation_warning,
                "legal_basis": legal_basis,
                "jurisdiction": norm_jur,
            }
        )

    return violations


def generate_jurisdiction_guardrail_card(
    jurisdiction: str = "VN",
    as_of_date: str | None = None,
    ontology_path: Path | str | None = None,
    registry_path: Path | str | None = None,
) -> str:
    """Generate dynamic jurisdiction guardrail card for prompt injection (ADR 0035, ADR 0050).

    Args:
        jurisdiction: Territory code (e.g. 'VN-HN', 'VN-HCM', 'VN').
        as_of_date: Evaluation date (YYYY-MM-DD), defaults to today.
        ontology_path: Optional custom ontology path.
        registry_path: Optional custom registry path.

    Returns:
        Formatted markdown guardrail card.
    """
    norm_jur = normalize_jurisdiction(jurisdiction)
    ontology = load_administrative_ontology(ontology_path)
    eval_date = as_of_date or datetime.now().strftime("%Y-%m-%d")

    territory_info = ontology.get("territories", {}).get(norm_jur, {})
    territory_name = territory_info.get("name", norm_jur)
    governance_model = territory_info.get("governance_model", "standard")

    lines = [
        f"### 🛡️ Local Jurisdiction Guardrail Card [{norm_jur} - {territory_name}]",
        f"- **Mô hình quản trị**: `{governance_model}` | **Thời điểm áp dụng**: `{eval_date}`",
    ]

    district_info = ontology.get("national_invariants", {}).get("district_level", {})
    district_dissolved_date = district_info.get("dissolved_date", "2025-07-01")
    if eval_date >= district_dissolved_date:
        lines.append(
            f"- **Thể chế cấp huyện**: Đã kết thúc hoạt động từ {district_dissolved_date} (NQ 203/2025/QH15 & Luật 72/2025/QH15). "
            "Tuyệt đối KHÔNG viện dẫn UBND Quận/Huyện/Thị xã cho các thủ tục hành chính sau thời điểm này."
        )

    authorities = ontology.get("authorities", {}).get(norm_jur, [])
    dep_warnings = []
    for auth in authorities:
        if not isinstance(auth, dict):
            continue
        curr_name = auth.get("current_name", "")
        for pred in auth.get("predecessors", []):
            d_date = pred.get("dissolved_date") or pred.get("valid_to")
            if d_date and eval_date >= d_date:
                dep_warnings.append(f"{pred.get('name')} ➔ sáp nhập vào {curr_name} (từ {d_date})")

    if dep_warnings:
        lines.append(
            f"- **Cơ quan đã sáp nhập/chuyển giao**: {'; '.join(dep_warnings)}. Không hướng dẫn liên hệ cơ quan cũ."
        )

    try:
        from ccba_legal.registry import get_active_delegation_document

        delegation_doc = get_active_delegation_document(
            territory=norm_jur,
            as_of_date=eval_date,
            registry_path=registry_path,
        )
        if delegation_doc:
            doc_id = (
                delegation_doc.get("document_number")
                or delegation_doc.get("short_name")
                or delegation_doc.get("id")
            )
            doc_title = delegation_doc.get("title", doc_id)
            lines.append(
                f"- **Văn bản phân cấp chủ đạo**: [{doc_id}] {doc_title}. "
                "Mọi phát biểu về thẩm quyền cấp cơ sở/sở ngành bắt buộc phải căn cứ theo văn bản này hoặc luật chuyên ngành."
            )
        elif norm_jur != "VN":
            lines.append(
                "- **Văn bản phân cấp chủ đạo**: Chưa ghi nhận văn bản phân cấp địa phương trong Sổ bộ. "
                "Áp dụng quy định luật chuyên ngành Trung ương (Quốc gia) kèm lưu ý rà soát quy định phân cấp địa phương."
            )
    except Exception:
        pass

    lines.append(
        "- **Nguyên tắc thẩm quyền cơ sở**: UBND cấp xã/phường chỉ thực hiện các thẩm quyền được phân cấp cụ thể "
        "hoặc lấy ý kiến cộng đồng dân cư theo luật định. Bắt buộc trích dẫn căn cứ điều khoản khi tư vấn thẩm quyền."
    )

    return "\n".join(lines)


__all__ = [
    "AuthorityResolutionResult",
    "load_administrative_ontology",
    "normalize_jurisdiction",
    "resolve_authority",
    "expand_jurisdiction_queries",
    "validate_authority_naming",
    "validate_tier_authority",
    "generate_jurisdiction_guardrail_card",
    "get_default_ontology_path",
]

"""Registry manager for legal documents in CCBA.

Manages loading, updating, and saving information in the YAML registry
by dynamically resolving file paths relative to the project root.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.models import (
    LegalDocStatus,
    LegalLifecycleInfo,
    normalize_doc_status,
)


def resolve_project_root() -> Path:
    """Traverse upwards from the current file to find the project root directory.

    Looks for common project indicators such as a .git directory or a pyproject.toml file.
    If none is found, falls back to Path.cwd().
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def discover_master_registry_path(custom_path: Path | str | None = None) -> Path:
    """Discover the canonical Master Legal Registry path across Hub and Spoke environments (ADR 0050).

    Resolution Order (Priority 1 to 6):
    1. Explicit custom_path argument (if file or directory containing legal_registry.yaml).
    2. Environment variables CCBA_LEGAL_REGISTRY_PATH or CCBA_LEGAL_KNOWLEDGE_PATH.
    3. Local .md/workspace_context.yaml configuration (master_registry_path or knowledge_corpus).
    4. Hub's .md/data/spoke_registry_decrypted.yaml or spoke_registry.yaml (ccba-legal-knowledge spoke).
    5. Local candidate directories (e.g. D:/GitHubProjects/ccba-legal-knowledge).
    6. Fallback to local project's .md/data/legal_registry.yaml.

    Returns:
        Path: Resolved absolute path to legal_registry.yaml.
    """
    # Tier 1: Explicit custom_path
    if custom_path:
        p = Path(custom_path)
        if p.is_file():
            return p.resolve()
        if p.is_dir():
            for name in ["legal_registry.yaml", ".md/data/legal_registry.yaml"]:
                cand = p / name
                if cand.is_file():
                    return cand.resolve()

    # Tier 2: Environment variables
    env_reg = os.environ.get("CCBA_LEGAL_REGISTRY_PATH")
    if env_reg:
        p = Path(env_reg)
        if p.is_file():
            return p.resolve()
        if p.is_dir():
            for name in ["legal_registry.yaml", ".md/data/legal_registry.yaml"]:
                cand = p / name
                if cand.is_file():
                    return cand.resolve()

    env_know = os.environ.get("CCBA_LEGAL_KNOWLEDGE_PATH")
    if env_know:
        p = Path(env_know)
        for name in ["legal_registry.yaml", ".md/data/legal_registry.yaml"]:
            cand = p / name
            if cand.is_file():
                return cand.resolve()

    project_root = resolve_project_root()

    # Tier 3: Local workspace_context.yaml
    local_ctx_path = project_root / ".md" / "workspace_context.yaml"
    if local_ctx_path.is_file():
        try:
            with open(local_ctx_path, encoding="utf-8") as f:
                ctx = yaml.safe_load(f) or {}
            if isinstance(ctx, dict):
                # Direct master registry setting
                if ctx.get("master_registry_path"):
                    cand = Path(ctx["master_registry_path"])
                    if not cand.is_absolute():
                        cand = project_root / cand
                    if cand.is_file():
                        return cand.resolve()
                # Check if current workspace IS ccba-legal-knowledge
                proj = ctx.get("project", {})
                if isinstance(proj, dict) and (
                    proj.get("name") == "ccba-legal-knowledge"
                    or proj.get("archetype") == "knowledge_corpus"
                ):
                    for name in ["legal_registry.yaml", ".md/data/legal_registry.yaml"]:
                        cand = project_root / name
                        if cand.is_file():
                            return cand.resolve()
        except Exception:
            pass

    # Tier 4: Hub's spoke registry cache
    hub_candidates = []
    if local_ctx_path.is_file():
        try:
            with open(local_ctx_path, encoding="utf-8") as f:
                ctx = yaml.safe_load(f) or {}
            if isinstance(ctx, dict) and ctx.get("hub_path"):
                cand_h = Path(ctx["hub_path"])
                if not cand_h.is_absolute():
                    cand_h = project_root / cand_h
                hub_candidates.append(cand_h)
        except Exception:
            pass
    hub_candidates.extend(
        [
            project_root,
            project_root.parent / "ccba-agent-platform",
            Path("D:/GitHubProjects/ccba-agent-platform"),
            Path("C:/GitHubProjects/ccba-agent-platform"),
        ]
    )

    for h_path in hub_candidates:
        if not h_path.exists():
            continue
        for reg_name in ["spoke_registry_decrypted.yaml", "spoke_registry.yaml"]:
            spoke_reg_file = h_path / ".md" / "data" / reg_name
            if spoke_reg_file.is_file():
                try:
                    with open(spoke_reg_file, encoding="utf-8") as f:
                        spoke_data = yaml.safe_load(f) or {}
                    spokes = spoke_data.get("spokes", []) if isinstance(spoke_data, dict) else []
                    for sp in spokes:
                        if isinstance(sp, dict) and (
                            sp.get("name") == "ccba-legal-knowledge"
                            or "legal-knowledge" in str(sp.get("name", "")).lower()
                            or sp.get("archetype") == "knowledge_corpus"
                        ):
                            sp_path_str = sp.get("path")
                            if sp_path_str:
                                sp_p = Path(sp_path_str)
                                for name in ["legal_registry.yaml", ".md/data/legal_registry.yaml"]:
                                    cand = sp_p / name
                                    if cand.is_file():
                                        return cand.resolve()
                except Exception:
                    pass

    # Tier 5: Known local candidate paths
    candidates = [
        project_root.parent / "ccba-legal-knowledge",
        project_root / ".." / "ccba-legal-knowledge",
        Path("D:/GitHubProjects/ccba-legal-knowledge"),
        Path("C:/GitHubProjects/ccba-legal-knowledge"),
    ]
    try:
        candidates.extend(
            [
                Path.home() / "GitHubProjects" / "ccba-legal-knowledge",
                Path.home() / "ccba-legal-knowledge",
            ]
        )
    except Exception:
        pass
    for cand in candidates:
        try:
            resolved = cand.resolve()
            if resolved.exists():
                for name in ["legal_registry.yaml", ".md/data/legal_registry.yaml"]:
                    cand_file = resolved / name
                    if cand_file.is_file():
                        return cand_file.resolve()
        except Exception:
            continue

    # Tier 6: Fallback to local project legal_registry.yaml
    fallback_path = project_root / ".md" / "data" / "legal_registry.yaml"
    return fallback_path


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


class LegalRegistryManager:
    """Manages loading, updating, saving and lifecycle resolution of the CCBA Legal Document Registry (legal_registry.yaml)."""

    def __init__(self, registry_path: Path | str | None = None) -> None:
        """Initialize the manager, resolving default registry paths relative to the project root or canonical master registry."""
        if registry_path:
            self.registry_path = Path(registry_path)
        else:
            cwd_cand = Path.cwd() / ".md" / "data" / "legal_registry.yaml"
            if cwd_cand.is_file():
                self.registry_path = cwd_cand.resolve()
            else:
                self.registry_path = discover_master_registry_path()
        self._inverted_replacements: dict[str, dict[str, Any]] = {}

    def load(self) -> dict[str, Any]:
        """Load the legal document registry from YAML."""
        loaded: dict[str, Any] = {}
        if not self.registry_path.exists():
            print(
                f"[Registry] Warning: Registry file {self.registry_path} not found. Starting with empty registry."
            )
            loaded = {
                "metadata": {},
                "laws": [],
                "decrees": [],
                "circulars": [],
                "decisions": [],
                "resolutions": [],
            }
        else:
            with open(self.registry_path, encoding="utf-8") as f:
                try:
                    res = yaml.safe_load(f)
                    loaded = res if isinstance(res, dict) else {}
                except Exception as e:
                    print(f"[Registry] Error loading YAML: {e}")
                    loaded = {
                        "metadata": {},
                        "laws": [],
                        "decrees": [],
                        "circulars": [],
                        "decisions": [],
                        "resolutions": [],
                    }

        # Build inverted replacements index
        self._inverted_replacements = {}
        for old_ref, rep_meta in KNOWN_STATUTORY_REPLACEMENTS.items():
            norm_old = re.sub(r"[\s\-_/.,:]+", "", old_ref.lower()).replace("đ", "d")
            self._inverted_replacements[norm_old] = {
                "id": rep_meta["id"],
                "document_number": rep_meta["document_number"],
                "title": rep_meta["title"],
                "short_name": rep_meta["document_number"],
                "status": "active",
            }

        for _category, docs in loaded.items():
            if not isinstance(docs, list):
                continue
            for doc in docs:
                if not isinstance(doc, dict):
                    continue
                replaces_list = []
                for field in ["replaces", "supersedes", "replaced_docs"]:
                    val = doc.get(field)
                    if isinstance(val, list):
                        replaces_list.extend(val)
                    elif isinstance(val, str) and val.strip():
                        replaces_list.append(val.strip())
                relations = doc.get("relations")
                if isinstance(relations, dict):
                    for field in ["replaces", "supersedes", "replaced_docs"]:
                        val = relations.get(field)
                        if isinstance(val, list):
                            replaces_list.extend(val)
                        elif isinstance(val, str) and val.strip():
                            replaces_list.append(val.strip())

                for rep in replaces_list:
                    if isinstance(rep, dict):
                        rep_str = str(rep.get("document_number") or rep.get("id") or "").strip()
                    else:
                        rep_str = str(rep).strip()
                    if rep_str:
                        norm_key = re.sub(r"[\s\-_/.,:]+", "", rep_str.lower()).replace("đ", "d")
                        self._inverted_replacements[norm_key] = doc

        return loaded

    def save(
        self,
        data: dict[str, Any],
        max_retries: int = 3,
        retry_delay: float = 0.1,
    ) -> None:
        """Save the updated registry to YAML with Windows Read-Only clearance and lock retry."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(max_retries):
            try:
                if self.registry_path.exists():
                    try:
                        st = self.registry_path.stat()
                        os.chmod(self.registry_path, st.st_mode | stat.S_IWUSR)
                    except Exception:
                        try:
                            os.chmod(self.registry_path, stat.S_IWRITE | stat.S_IREAD)
                        except Exception:
                            pass
                with open(self.registry_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
                print(f"[Registry] Successfully saved registry to {self.registry_path}")
                return
            except (PermissionError, OSError):
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay)

    def register_document(self, doc_id: str, doc_data: dict[str, Any]) -> None:
        """Register or update a document in the registry."""
        doc_type = doc_data.get("type", "").lower()
        category = "laws"
        if "nghị định" in doc_type or "decree" in doc_type:
            category = "decrees"
        elif "thông tư" in doc_type or "circular" in doc_type:
            category = "circulars"
        elif "quyết định" in doc_type or "decision" in doc_type:
            category = "decisions"
        elif "nghị quyết" in doc_type or "resolution" in doc_type:
            category = "resolutions"
        self.add_or_update_doc(category, doc_id, doc_data)

    def add_or_update_doc(self, category: str, doc_id: str, doc_data: dict[str, Any]) -> None:
        """Add a new document entry or update an existing one under the specified category (laws / decrees)."""
        data = self.load()
        if category not in data:
            data[category] = []

        # Find existing document
        existing_idx = -1
        for idx, doc in enumerate(data[category]):
            if doc.get("id") == doc_id:
                existing_idx = idx
                break

        if existing_idx >= 0:
            # Update existing
            data[category][existing_idx].update(doc_data)
            print(f"[Registry] Updated doc ID {doc_id} in {category}")
        else:
            # Add new
            new_doc = {"id": doc_id}
            new_doc.update(doc_data)
            data[category].append(new_doc)
            print(f"[Registry] Added new doc ID {doc_id} to {category}")

        self.save(data)

    def update_clause_status(
        self,
        target_doc_id: str,
        clause_anchor: str,
        status: str,
        amended_by: str,
        source_doc_path: str,
    ) -> None:
        """Update the status of a specific clause in a registered document.

        Args:
            target_doc_id: The ID of the target document (e.g. 'ND-06-2021').
            clause_anchor: The anchor representing the clause (e.g. 'd15k2').
            status: The status (e.g., 'amended').
            amended_by: The source making the amendment (e.g., 'Điều 1 Thông tư B').
            source_doc_path: Path of the source document making the amendment.
        """
        data = self.load()
        norm_target = target_doc_id.lower().replace("-", "_")

        found = False
        # Iterate over lists in YAML (laws, decrees, circulars, etc.)
        for _category, docs in data.items():
            if isinstance(docs, list):
                for doc in docs:
                    if (
                        isinstance(doc, dict)
                        and doc.get("id")
                        and doc["id"].lower().replace("-", "_") == norm_target
                    ):
                        # Initialize clauses section under document metadata if not exists
                        if "clauses" not in doc or not isinstance(doc["clauses"], dict):
                            doc["clauses"] = {}

                        doc["clauses"][clause_anchor] = {
                            "status": status,
                            "amended_by": amended_by,
                            "source_doc_path": source_doc_path,
                        }
                        print(
                            f"[Registry] Set status of {target_doc_id} clause {clause_anchor} to '{status}'"
                        )
                        found = True
                        break
            if found:
                break

        if not found:
            print(
                f"[Registry] Warning: Target doc {target_doc_id} not found in registry. Clause status not updated."
            )
        else:
            self.save(data)

    def find_doc_by_id(self, doc_id: str) -> dict[str, Any] | None:
        """Find a document in the registry by its ID (case-insensitive)."""
        data = self.load()
        norm_id = doc_id.lower().replace("-", "_").replace("đ", "d")
        for _category, docs in data.items():
            if isinstance(docs, list):
                for doc in docs:
                    if (
                        isinstance(doc, dict)
                        and doc.get("id")
                        and doc["id"].lower().replace("-", "_").replace("đ", "d") == norm_id
                    ):
                        return doc
        return None

    def find_doc(self, identifier: str) -> dict[str, Any] | None:
        """Find a document by ID, document_number, or short_name (case and punctuation insensitive)."""
        data = self.load()
        norm_target = re.sub(r"[\s\-_/.,:]+", "", identifier.lower()).replace("đ", "d")

        for _category, docs in data.items():
            if isinstance(docs, list):
                for doc in docs:
                    if not isinstance(doc, dict):
                        continue
                    doc_id = re.sub(r"[\s\-_/.,:]+", "", str(doc.get("id", "")).lower()).replace(
                        "đ", "d"
                    )
                    doc_num = re.sub(
                        r"[\s\-_/.,:]+", "", str(doc.get("document_number", "")).lower()
                    ).replace("đ", "d")
                    short_name = re.sub(
                        r"[\s\-_/.,:]+", "", str(doc.get("short_name", "")).lower()
                    ).replace("đ", "d")

                    if (
                        norm_target in {doc_id, doc_num, short_name}
                        or (doc_id and doc_id == norm_target)
                        or (doc_num and doc_num == norm_target)
                    ):
                        return doc
        return None

    def get_lifecycle(self, identifier: str) -> dict[str, Any]:
        """Resolve full lifecycle information, validity status, and replacement warnings (ADR 0050).

        Args:
            identifier: Document ID (e.g. 'LXD-2014', 'ND-105-2025') or document number ('50/2014/QH13').

        Returns:
            Dictionary conforming to LegalLifecycleInfo with status, warning banner, and suggested replacement.
        """
        doc = self.find_doc(identifier)
        if not doc:
            # Fallback retry with alternate ND-CP / NĐ-CP variant if diacritic normalization missed
            alt_identifier: str | None = None
            if "nd-cp" in identifier.lower() or "nd_cp" in identifier.lower():
                alt_identifier = re.sub(r"(?i)nd[-_]cp", "NĐ-CP", identifier)
            elif "nđ-cp" in identifier.lower() or "nđ_cp" in identifier.lower():
                alt_identifier = re.sub(r"(?i)nđ[-_]cp", "ND-CP", identifier)

            if alt_identifier:
                doc = self.find_doc(alt_identifier)

        if not doc:
            norm_id = re.sub(r"[\s\-_/.,:]+", "", identifier.lower()).replace("đ", "d")
            if norm_id in self._inverted_replacements:
                rep_stub = self._inverted_replacements[norm_id]
                rep_id = str(rep_stub.get("id", rep_stub.get("document_number", "")))
                full_rep = self.find_doc(rep_id) or rep_stub
                rep_num = str(
                    full_rep.get("document_number") or rep_stub.get("document_number") or rep_id
                )
                rep_title = str(full_rep.get("title") or rep_stub.get("title") or rep_id)
                rep_short = str(
                    full_rep.get("short_name") or rep_stub.get("short_name") or rep_num or rep_id
                )
                rep_status = normalize_doc_status(full_rep.get("status", "active")).value

                info = LegalLifecycleInfo(
                    doc_id=identifier,
                    document_number=identifier,
                    title=f"Văn bản đã hết hiệu lực (thay thế bởi {rep_short})",
                    short_name=identifier,
                    status=LegalDocStatus.SUPERSEDED,
                    superseded_by=rep_id,
                    warning=(
                        f"⚠️ [CẢNH BÁO PHÁP LÝ]: Văn bản [{identifier}] đã HẾT HIỆU LỰC toàn bộ, "
                        f"được thay thế bởi [{rep_title} - {rep_num}]. "
                        f"Cần kiểm tra kỹ các quy định chuyển tiếp hoặc áp dụng văn bản thay thế hiện hành."
                    ),
                    suggested_replacement={
                        "id": full_rep.get("id", rep_id),
                        "document_number": full_rep.get("document_number", rep_num),
                        "title": full_rep.get("title", rep_title),
                        "short_name": full_rep.get("short_name", rep_short),
                        "status": rep_status,
                        "effective_date": full_rep.get("effective_date"),
                    },
                )
                return info.to_dict()

            info = LegalLifecycleInfo(
                doc_id=identifier,
                document_number=identifier,
                title="",
                short_name=identifier,
                status=LegalDocStatus.UNVERIFIED,
                warning=f"⚠️ [CHƯA XÁC MINH]: Văn bản [{identifier}] không có trong cơ sở dữ liệu pháp luật chính thức. Cần kiểm tra kỹ tính pháp lý.",
                suggested_replacement=None,
            )
            return info.to_dict()

        raw_status = doc.get("status")
        status_enum = normalize_doc_status(raw_status)
        doc_id = str(doc.get("id", identifier))
        doc_num = str(doc.get("document_number", ""))
        title = str(doc.get("title", ""))
        short_name = str(doc.get("short_name", doc_id))
        effective_date = str(doc["effective_date"]) if doc.get("effective_date") else None
        superseded_date = str(doc["superseded_date"]) if doc.get("superseded_date") else None

        # Resolve supersedes / replaced docs
        rel = doc.get("relations") if isinstance(doc.get("relations"), dict) else {}
        raw_supersedes = (
            doc.get("supersedes")
            or doc.get("replaces")
            or doc.get("replaced_docs")
            or rel.get("replaces")
            or rel.get("supersedes")
            or []
        )
        if isinstance(raw_supersedes, str):
            supersedes = [raw_supersedes]
        else:
            supersedes = [str(s) for s in raw_supersedes]

        # Resolve superseded_by / replacement doc
        raw_superseded_by = (
            doc.get("superseded_by")
            or doc.get("replaced_by")
            or doc.get("replaced_by_docs")
            or rel.get("superseded_by")
            or rel.get("replaced_by")
        )
        if isinstance(raw_superseded_by, list) and raw_superseded_by:
            superseded_by: str | None = str(raw_superseded_by[0])
        elif raw_superseded_by:
            superseded_by = str(raw_superseded_by)
        else:
            superseded_by = None

        # Resolve amendments
        raw_amendments = (
            doc.get("amended_by") or doc.get("amendments") or doc.get("amends_docs") or []
        )
        if isinstance(raw_amendments, list):
            amended_by: list[str] = [
                str(a.get("title", a.get("ref", str(a)))) if isinstance(a, dict) else str(a)
                for a in raw_amendments
            ]
        elif isinstance(raw_amendments, str):
            amended_by = [raw_amendments]
        else:
            amended_by = []

        # Resolve guiding docs
        raw_guiding = doc.get("guiding_docs") or doc.get("guiding_decrees") or []
        guiding_docs: list[str] = (
            [str(g) for g in raw_guiding] if isinstance(raw_guiding, list) else [str(raw_guiding)]
        )

        warning: str | None = None
        suggested_replacement: dict[str, Any] | None = None

        if status_enum == LegalDocStatus.SUPERSEDED:
            date_str = f" từ ngày {superseded_date}" if superseded_date else ""
            rep_str = f", được thay thế bởi [{superseded_by}]" if superseded_by else ""
            warning = (
                f"⚠️ [CẢNH BÁO PHÁP LÝ]: Văn bản [{short_name} - {doc_num or doc_id}] đã HẾT HIỆU LỰC toàn bộ{date_str}{rep_str}. "
                "Cần kiểm tra kỹ các quy định chuyển tiếp hoặc áp dụng văn bản thay thế hiện hành."
            )
            if superseded_by:
                rep_doc = self.find_doc(superseded_by)
                if rep_doc:
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
            warning = f"ℹ️ [LƯU Ý PHÁP LÝ]: Văn bản [{short_name} - {doc_num or doc_id}] đã BỊ SỬA ĐỔI, BỔ SUNG một phần bởi: {amend_str}."
        elif status_enum == LegalDocStatus.PENDING_EFFECTIVE:
            eff_str = f" từ ngày {effective_date}" if effective_date else ""
            warning = f"⏳ [CHƯA CÓ HIỆU LỰC]: Văn bản [{short_name} - {doc_num or doc_id}] chưa có hiệu lực thi hành (dự kiến{eff_str})."
        elif status_enum == LegalDocStatus.DRAFT:
            warning = f"📝 [DỰ THẢO]: Văn bản [{short_name}] là bản DỰ THẢO đang lấy ý kiến, chưa có giá trị pháp lý thi hành."

        territory = str(doc.get("territory", "VN"))
        hierarchy_level = str(
            doc.get("hierarchy_level", "national" if territory == "VN" else "provincial")
        )
        temporal_context = doc.get("temporal_context")
        successor_entity = doc.get("successor_entity")

        info = LegalLifecycleInfo(
            doc_id=doc_id,
            document_number=doc_num,
            title=title,
            short_name=short_name,
            status=status_enum,
            effective_date=effective_date,
            superseded_date=superseded_date,
            supersedes=supersedes,
            superseded_by=superseded_by,
            amended_by=amended_by,
            guiding_docs=guiding_docs,
            territory=territory,
            hierarchy_level=hierarchy_level,
            temporal_context=temporal_context,
            successor_entity=successor_entity,
            warning=warning,
            suggested_replacement=suggested_replacement,
        )
        return info.to_dict()

    def get_markdown_path_for_doc(self, doc_metadata: dict[str, Any]) -> Path | None:
        """Resolve the path to the main markdown file (full_text.md or doc_slug.md) for a document."""
        project_root = resolve_project_root()

        # 1. Check 'markdown_path' in metadata
        markdown_path_str = doc_metadata.get("markdown_path")
        if markdown_path_str:
            p = project_root / str(markdown_path_str)
            if p.exists():
                return p

        # 2. Check 'file_path' in metadata
        file_path_str = doc_metadata.get("file_path")
        if file_path_str:
            p = project_root / str(file_path_str)
            # Check for full_text.md in the folder of that file
            full_text_p = p.parent / "full_text.md"
            if full_text_p.exists():
                return full_text_p
            # Check if there is a .md file next to the .docx file
            md_p = p.with_suffix(".md")
            if md_p.exists():
                return md_p

        # 3. Fallback: search for files matching the title or short_name slug in legal_docs
        doc_id = str(doc_metadata.get("id", ""))
        slug = doc_id.lower().replace("-", "_")
        legal_docs_dir = project_root / ".md" / "legal_docs"
        if legal_docs_dir.exists():
            for p in legal_docs_dir.rglob("*.md"):
                if p.name == "full_text.md" and slug in p.parent.name.lower():
                    return p
                if p.stem.lower() == slug:
                    return p
        return None

    def search(
        self, query: str, top_k: int = 5, territory: str | None = None
    ) -> list[dict[str, Any]]:
        """Search legal registry documents matching query terms across titles, topics, and notes (ADR 0050).

        Args:
            query: Space-separated search query terms.
            top_k: Maximum number of top matching documents to return.
            territory: Optional ISO 3166-2:VN territory code (e.g. 'VN-HN') for geofencing.

        Returns:
            List of matching document dictionaries sorted descending by relevance score,
            annotated with normalized status, lifecycle warnings, and replacement suggestions.
        """
        data = self.load()
        query_terms = [t.lower() for t in query.split() if len(t) > 1]
        is_empty_query = len(query_terms) == 0

        matched_docs: list[tuple[int, dict[str, Any]]] = []
        categories = [
            "decrees",
            "laws",
            "circulars",
            "standards",
            "seminars",
            "decisions",
            "resolutions",
        ]

        target_territory: str | None = None
        if territory:
            from ccba_legal.jurisdiction import normalize_jurisdiction

            target_territory = normalize_jurisdiction(territory)

        for category in categories:
            docs = data.get(category, [])
            for doc in docs:
                if not isinstance(doc, dict):
                    continue

                doc_territory = str(doc.get("territory", "VN"))
                if target_territory and doc_territory not in {"VN", target_territory}:
                    continue

                if is_empty_query:
                    score = 1
                else:
                    score = 0
                    title = str(doc.get("title", "")).lower()
                    short_name = str(doc.get("short_name", "")).lower()
                    topics = [str(t).lower() for t in doc.get("topics", [])]
                    notes = str(doc.get("notes", "")).lower()
                    doc_num = str(doc.get("document_number", "")).lower()
                    doc_id = str(doc.get("id", "")).lower()

                    combined_text = (
                        f"{title} {short_name} {doc_num} {doc_id} {' '.join(topics)} {notes}"
                    )

                    for term in query_terms:
                        if term in combined_text:
                            score += 1
                        if term in title or term in short_name:
                            score += 2
                        if any(term in t for t in topics):
                            score += 3
                    if term in doc_num or term in doc_id:
                        score += 4

                if score > 0:
                    # Enrich doc with lifecycle metadata (ADR 0050)
                    doc_copy = dict(doc)
                    lifecycle = self.get_lifecycle(str(doc.get("id", "")))
                    doc_copy["status"] = lifecycle.get("status", LegalDocStatus.ACTIVE.value)
                    doc_copy["is_superseded"] = (
                        lifecycle.get("status") == LegalDocStatus.SUPERSEDED.value
                    )
                    doc_copy["territory"] = lifecycle.get("territory", doc_territory)
                    doc_copy["hierarchy_level"] = lifecycle.get(
                        "hierarchy_level",
                        "national" if doc_territory == "VN" else "provincial",
                    )
                    if lifecycle.get("warning"):
                        doc_copy["lifecycle_warning"] = lifecycle["warning"]
                    if lifecycle.get("suggested_replacement"):
                        doc_copy["suggested_replacement"] = lifecycle["suggested_replacement"]
                    matched_docs.append((score, doc_copy))

        matched_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in matched_docs[:top_k]]

    def merge_with_master_registry(
        self, master_registry_data: dict[str, Any], backup: bool = True
    ) -> dict[str, int]:
        """Perform Non-Destructive Additive Merge from master registry data (ADR 0050).

        - Creates an automatic timestamped backup (.bak) of the local registry.
        - Preserves local-only custom entries, notes, and fields.
        - Updates core SSOT metadata (status, effective_date, supersedes, superseded_by, etc.).

        Returns:
            Dictionary with counts: {'updated': int, 'added': int, 'preserved': int}
        """
        local_data = self.load()

        if backup and self.registry_path.exists():
            backup_dir = self.registry_path.parent.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            bak_path = backup_dir / f"{self.registry_path.name}.bak_{ts}"
            shutil.copy2(self.registry_path, bak_path)
            print(f"[Registry] Created local backup at: {bak_path}")

        counts = {"updated": 0, "added": 0, "preserved": 0}
        categories = [
            "laws",
            "decrees",
            "circulars",
            "standards",
            "seminars",
            "decisions",
            "resolutions",
        ]

        # Preserve metadata header
        if "metadata" not in local_data:
            local_data["metadata"] = master_registry_data.get("metadata", {})
        elif "metadata" in master_registry_data:
            local_data["metadata"]["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for category in categories:
            if category not in local_data or not isinstance(local_data[category], list):
                local_data[category] = []

            master_docs = master_registry_data.get(category, [])
            if not isinstance(master_docs, list):
                continue

            for m_doc in master_docs:
                if not isinstance(m_doc, dict) or not m_doc.get("id"):
                    continue

                m_id = str(m_doc["id"]).strip()
                m_num = str(m_doc.get("document_number", "")).strip()

                # Find in local list
                local_idx = -1
                for idx, l_doc in enumerate(local_data[category]):
                    if not isinstance(l_doc, dict):
                        continue
                    l_id = str(l_doc.get("id", "")).strip()
                    l_num = str(l_doc.get("document_number", "")).strip()
                    if (l_id and l_id.lower() == m_id.lower()) or (
                        m_num and l_num and l_num.lower() == m_num.lower()
                    ):
                        local_idx = idx
                        break

                if local_idx >= 0:
                    # Non-destructive update: preserve local custom fields if present
                    target = local_data[category][local_idx]
                    for k, v in m_doc.items():
                        if k == "notes" and target.get("notes") and target["notes"] != v:
                            # Keep local custom notes or append
                            pass
                        else:
                            target[k] = v
                    counts["updated"] += 1
                else:
                    local_data[category].append(dict(m_doc))
                    counts["added"] += 1

        self.save(local_data)
        return counts


DEFAULT_RELATION_SYNONYMS = {
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


def load_relation_synonyms(project_root: Path | None = None) -> dict[str, str]:
    """Load relation synonyms configuration from YAML and return a synonym-to-key mapping.

    If the configuration file is missing or invalid, falls back to a default mapping.

    Returns:
        dict[str, str]: A dictionary mapping Vietnamese synonym phrases to CCBA relation keys.
    """
    if project_root is None:
        project_root = resolve_project_root()

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

        synonyms_dict = config.get("relation_synonyms", {})
        mapping = {}
        for key, synonyms in synonyms_dict.items():
            if isinstance(synonyms, list):
                for syn in synonyms:
                    mapping[syn] = key
                    norm_syn = re.sub(r"\s+", " ", syn.replace(",", "")).strip()
                    mapping[norm_syn] = key
            elif isinstance(synonyms, str):
                mapping[synonyms] = key
                norm_syn = re.sub(r"\s+", " ", synonyms.replace(",", "")).strip()
                mapping[norm_syn] = key
        return mapping
    except Exception as e:
        print(
            f"[Registry] Error reading relation synonyms from {synonyms_path}: {e}. Using default synonyms."
        )
        return DEFAULT_RELATION_SYNONYMS.copy()


def format_citation(doc: dict[str, Any]) -> str:
    """Format a legal document citation strictly [Short Name - Doc Number].

    Args:
        doc: Dictionary containing document metadata fields (short_name, document_number, id).

    Returns:
        Formatted citation string, e.g. '[Luật XD 2025 - 135/2025/QH15]'.
    """
    short_name = doc.get("short_name") or doc.get("id", "VBPL")
    doc_num = doc.get("document_number")
    if doc_num:
        return f"[{short_name} - {doc_num}]"
    return f"[{short_name}]"


def load_legal_registry(registry_path: Path | str | None = None) -> dict[str, Any]:
    """Safely load and parse legal_registry.yaml into a dictionary.

    Args:
        registry_path: Optional path to the legal_registry.yaml file.

    Returns:
        Loaded registry dictionary or empty structure if not found.
    """
    mgr = LegalRegistryManager(registry_path=Path(registry_path) if registry_path else None)
    return mgr.load()


def search_legal_registry(
    query: str,
    registry_path: Path | str | None = None,
    top_k: int = 5,
    territory: str | None = None,
) -> list[dict[str, Any]]:
    """Search legal registry documents matching query terms across titles, topics, and notes.

    Args:
        query: Space-separated search query terms.
        registry_path: Optional path to legal_registry.yaml.
        top_k: Maximum number of top matching documents to return.
        territory: Optional ISO 3166-2:VN territory code (e.g. 'VN-HN') for geofencing.

    Returns:
        List of matching document dictionaries sorted descending by relevance score.
    """
    mgr = LegalRegistryManager(registry_path=Path(registry_path) if registry_path else None)
    return mgr.search(query=query, top_k=top_k, territory=territory)


def get_lifecycle(identifier: str, registry_path: Path | str | None = None) -> dict[str, Any]:
    """Resolve full lifecycle information, validity status, and replacement warnings (ADR 0050).

    Args:
        identifier: Document ID or document number (e.g. '50/2014/QH13', 'LXD-2014').
        registry_path: Optional custom path to legal_registry.yaml.

    Returns:
        Dictionary conforming to LegalLifecycleInfo with warning banner and replacement doc.
    """
    mgr = LegalRegistryManager(registry_path=Path(registry_path) if registry_path else None)
    return mgr.get_lifecycle(identifier)


def query(
    search_query: str, registry_path: Path | str | None = None, top_k: int = 5
) -> list[dict[str, Any]]:
    """High-level query API searching legal registry with automatic lifecycle warnings (ADR 0050).

    Delegates to LegalKnowledgeEngine for multi-tier master discovery and enriched search.

    Args:
        search_query: Search keywords or document number.
        registry_path: Optional custom path to legal_registry.yaml.
        top_k: Maximum number of top matching documents to return.

    Returns:
        List of enriched document dictionaries.
    """
    from ccba_legal.engine import LegalKnowledgeEngine

    engine = LegalKnowledgeEngine(registry_path=registry_path)
    return engine.search(query=search_query, top_k=top_k)


def get_active_delegation_document(
    territory: str,
    domain: str = "construction",
    as_of_date: str | None = None,
    registry_path: Path | str | None = None,
) -> dict[str, Any] | None:
    """Discover the active delegation document for a given territory and domain from the registry.

    Args:
        territory: ISO 3166-2:VN territory code (e.g. 'VN-HN', 'VN-HCM').
        domain: Domain of delegation (default: 'construction').
        as_of_date: Evaluation date in YYYY-MM-DD format (defaults to current date).
        registry_path: Optional custom path to legal_registry.yaml.

    Returns:
        Document dict representing the active delegation document, or None if not found.
    """
    from ccba_legal.jurisdiction import normalize_jurisdiction

    norm_jur = normalize_jurisdiction(territory)
    if norm_jur == "VN":
        return None

    mgr = LegalRegistryManager(registry_path=Path(registry_path) if registry_path else None)
    data = mgr.load()

    target_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
    candidates: list[dict[str, Any]] = []

    for _category, docs in data.items():
        if not isinstance(docs, list):
            continue
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            doc_territory = str(doc.get("territory", "")).strip().upper()
            if doc_territory != norm_jur:
                continue

            status = normalize_doc_status(doc.get("status")).value
            if status != LegalDocStatus.ACTIVE.value:
                continue

            topics = [str(t).lower() for t in doc.get("topics", [])]
            title = str(doc.get("title", "")).lower()

            is_delegation = (
                "phân cấp" in title
                or "ủy quyền" in title
                or "delegation" in topics
                or "phân cấp" in topics
                or "ủy quyền" in topics
                or doc.get("authority_type") == "delegation"
                or doc.get("is_delegation") is True
            )

            is_domain_match = (
                domain == "all"
                or domain in topics
                or "xây dựng" in title
                or "quy hoạch" in title
                or "construction" in topics
                or "planning" in topics
            )

            if is_delegation or is_domain_match:
                eff_date = str(doc.get("effective_date", ""))
                if eff_date and eff_date > target_date:
                    continue
                exp_date = str(doc.get("expiration_date", ""))
                if exp_date and exp_date < target_date:
                    continue
                candidates.append(doc)

    if not candidates:
        return None

    candidates.sort(key=lambda d: str(d.get("effective_date", "")), reverse=True)
    return candidates[0]


__all__ = [
    "LegalRegistryManager",
    "discover_master_registry_path",
    "format_citation",
    "load_legal_registry",
    "search_legal_registry",
    "get_lifecycle",
    "get_active_delegation_document",
    "query",
    "load_relation_synonyms",
    "resolve_project_root",
]

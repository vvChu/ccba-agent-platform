"""Universal Legal Knowledge Engine Facade (ADR 0035, ADR 0050).

Provides high-level search, document retrieval, AST clause slicing with
tier-awareness, and table matrix extraction with two-tier CWE-22 protection.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.models import LegalDocStatus
from ccba_legal.registry import (
    LegalRegistryManager,
    discover_master_registry_path,
    resolve_project_root,
)

SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")
SAFE_CLAUSE_PATTERN = re.compile(r"^[a-zA-Z0-9_\-.]+$")


def canonicalize_clause_id(clause_id: str) -> str:
    """Canonicalize clause aliases (d1, d15k2, d6k2a, 1.1, muc-1-1) to gold standard anchor format."""
    cid = clause_id.strip().lower()
    for pat in (
        r"^d(\d+[a-z]?)[-_]?k(\d+)[-_]?(?:d|diem[-_]?)?([a-z0-9]+)$",
        r"^dieu[-_](\d+[a-z]?)[-_]khoan[-_](\d+)[-_]diem[-_]([a-z0-9]+)$",
    ):
        m_dkd = re.match(pat, cid)
        if m_dkd:
            art = m_dkd.group(1)
            art_norm = str(int(art)) if art.isdigit() else art
            return f"dieu-{art_norm}-khoan-{int(m_dkd.group(2))}-diem-{m_dkd.group(3)}"

    for pat in (r"^d(\d+[a-z]?)[-_]?k(\d+)$", r"^dieu[-_](\d+[a-z]?)[-_]khoan[-_](\d+)$"):
        m_dk = re.match(pat, cid)
        if m_dk:
            art = m_dk.group(1)
            art_norm = str(int(art)) if art.isdigit() else art
            return f"dieu-{art_norm}-khoan-{int(m_dk.group(2))}"

    for pat in (r"^d(\d+[a-z]?)$", r"^dieu[-_](\d+[a-z]?)$"):
        m_d = re.match(pat, cid)
        if m_d:
            art = m_d.group(1)
            art_norm = str(int(art)) if art.isdigit() else art
            return f"dieu-{art_norm}"

    m_k = re.match(r"^k(\d+)$", cid)
    if m_k:
        return f"khoan-{int(m_k.group(1))}"

    m_muc = re.match(r"^(?:m|muc[-_]?)?(\d+(?:[.\-_]\d+)*)$", cid)
    if m_muc:
        sec_parts = re.split(r"[.\-_]", m_muc.group(1))
        return f"muc-{'-'.join(str(int(p)) if p.isdigit() else p for p in sec_parts)}"

    return cid.replace("_", "-")


def csv_to_markdown(csv_text: str) -> str:
    """Convert CSV table text to GitHub-flavored Markdown table with pipe escaping.

    Args:
        csv_text: Raw CSV string.

    Returns:
        Markdown table string.
    """
    if csv_text.startswith("\ufeff"):
        csv_text = csv_text[1:]
    f = io.StringIO(csv_text.strip())
    reader = csv.reader(f)
    rows = list(reader)
    if not rows:
        return ""

    max_cols = max(len(row) for row in rows)
    if max_cols == 0:
        return ""

    headers = [cell.replace("\n", " ").replace("|", "\\|").strip() for cell in rows[0]]
    if len(headers) < max_cols:
        headers.extend([""] * (max_cols - len(headers)))

    md_lines = ["| " + " | ".join(headers) + " |"]
    md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    for row in rows[1:]:
        cells = [cell.replace("\n", " ").replace("|", "\\|").strip() for cell in row]
        if len(cells) < max_cols:
            cells.extend([""] * (max_cols - len(cells)))
        md_lines.append("| " + " | ".join(cells[:max_cols]) + " |")

    return "\n".join(md_lines)


class LegalKnowledgeEngine:
    """Universal Legal Knowledge Engine (ADR 0035, ADR 0050).

    Coordinates multi-tier master discovery, cached OKF bundle reading,
    tier-aware AST clause slicing, and table matrix extraction with two-tier
    CWE-22 path traversal containment.
    """

    def __init__(
        self,
        registry_path: Path | str | None = None,
        corpus_dir: Path | str | None = None,
    ) -> None:
        """Initialize the Legal Knowledge Engine.

        Args:
            registry_path: Optional explicit path to legal_registry.yaml.
            corpus_dir: Optional explicit path to legal_docs knowledge directory.
        """
        if registry_path:
            self.registry_path = Path(registry_path).resolve()
        else:
            self.registry_path = discover_master_registry_path().resolve()

        self.registry_mgr = LegalRegistryManager(registry_path=self.registry_path)

        if corpus_dir:
            self.corpus_dir: Path | None = Path(corpus_dir).resolve()
        else:
            self.corpus_dir = self._discover_corpus_dir()

        self._bundle_cache: dict[str, dict[str, Any]] = {}

    def _discover_corpus_dir(self) -> Path | None:
        """Auto-discover canonical corpus directory from registry path or environment."""
        # 1. Check environment variable
        env_corpus = os.environ.get("CCBA_LEGAL_CORPUS_PATH")
        if env_corpus:
            p = Path(env_corpus).resolve()
            if p.is_dir():
                return p

        # 2. Check sibling or parent of registry_path
        reg_parent = self.registry_path.parent
        if (reg_parent / "legal_docs").is_dir():
            return (reg_parent / "legal_docs").resolve()

        if reg_parent.name == "data" and reg_parent.parent.name == ".md":
            project_root = reg_parent.parent.parent
            if (project_root / "legal_docs").is_dir():
                return (project_root / "legal_docs").resolve()
            if (project_root / ".md" / "legal_docs").is_dir():
                return (project_root / ".md" / "legal_docs").resolve()

        # 3. Check local project root
        root = resolve_project_root()
        if (root / "legal_docs").is_dir():
            return (root / "legal_docs").resolve()
        if (root / ".md" / "legal_docs").is_dir():
            return (root / ".md" / "legal_docs").resolve()

        # 4. Check known candidates
        candidates = [
            Path("D:/GitHubProjects/ccba-legal-knowledge/legal_docs"),  # ccba:allow-machine-path
            Path("C:/GitHubProjects/ccba-legal-knowledge/legal_docs"),  # ccba:allow-machine-path
            root.parent / "ccba-legal-knowledge" / "legal_docs",
        ]
        try:
            candidates.append(
                Path.home() / "GitHubProjects" / "ccba-legal-knowledge" / "legal_docs"
            )
        except Exception:
            pass
        for cand in candidates:
            if cand.is_dir():
                return cand.resolve()

        return None

    def search(
        self, query: str, top_k: int = 5, include_expired: bool = False
    ) -> list[dict[str, Any]]:
        """Search legal documents with lifecycle status, warnings, and replacements.

        Args:
            query: Keyword or document number query string.
            top_k: Maximum number of top matching documents to return.
            include_expired: Whether to include expired/superseded documents in results.

        Returns:
            List of matching document metadata dictionaries sorted by relevance.
        """
        return self.registry_mgr.search(query=query, top_k=top_k, include_expired=include_expired)

    def get_document(self, identifier: str) -> dict[str, Any] | None:
        """Retrieve a registered document by ID, number, or short name with lifecycle info.

        Args:
            identifier: Document ID (e.g. 'Luat-Xay-dung-2025-135-2025-QH15'), number, or alias.

        Returns:
            Document dictionary enriched with lifecycle info, or None if not found.
        """
        doc = self.registry_mgr.find_doc(identifier)
        if not doc:
            norm_id = re.sub(r"[\s\-_/.]+", "_", identifier.lower()).strip("_")
            data = self.registry_mgr.load()
            for _cat, items in data.items():
                if not isinstance(items, list):
                    continue
                for d in items:
                    if not isinstance(d, dict):
                        continue
                    d_id = re.sub(r"[\s\-_/.]+", "_", str(d.get("id", "")).lower()).strip("_")
                    d_num = re.sub(
                        r"[\s\-_/.]+", "_", str(d.get("document_number", "")).lower()
                    ).strip("_")
                    if d_id == norm_id or d_num == norm_id:
                        doc = d
                        break
                if doc:
                    break

        if not doc:
            return None

        doc_copy = dict(doc)
        lifecycle = self.registry_mgr.get_lifecycle(str(doc.get("id", "")))
        doc_copy["status"] = lifecycle.get("status", LegalDocStatus.ACTIVE.value)
        doc_copy["is_superseded"] = lifecycle.get("status") == LegalDocStatus.SUPERSEDED.value
        if lifecycle.get("warning"):
            doc_copy["lifecycle_warning"] = lifecycle["warning"]
        if lifecycle.get("suggested_replacement"):
            doc_copy["suggested_replacement"] = lifecycle["suggested_replacement"]
        return doc_copy

    @staticmethod
    def _verify_bundle_containment(b_path: Path, base_dir: Path) -> Path:
        """Verifies CWE-22 Tier 2 containment of a resolved bundle directory."""
        resolved = b_path.resolve()
        if not resolved.is_relative_to(base_dir.resolve()):
            raise ValueError(f"Path traversal detected: bundle '{resolved}' outside '{base_dir}'")
        return resolved

    def _collect_bundle_candidates(self) -> list[tuple[Path, Path]]:
        """Collects candidate (bundle_dir, base_dir) pairs across configured corpus directories."""
        search_dirs: list[Path] = []
        if self.corpus_dir and self.corpus_dir.is_dir():
            search_dirs.append(self.corpus_dir)
        for rel in ("legal_docs", ".md/legal_docs"):
            local_d = resolve_project_root() / rel
            if local_d.is_dir() and local_d not in search_dirs:
                search_dirs.append(local_d)

        all_candidates: list[tuple[Path, Path]] = []
        categories = {"01_vbpl", "02_qcvn", "03_tcvn", "04_appendices"}
        for s_dir in search_dirs:
            for child in sorted(s_dir.iterdir()):
                if not child.is_dir():
                    continue
                if child.name in categories:
                    all_candidates.extend(
                        (sub, s_dir) for sub in sorted(child.iterdir()) if sub.is_dir()
                    )
                else:
                    all_candidates.append((child, s_dir))
        return all_candidates

    def _match_bundle_by_metadata(
        self, all_candidates: list[tuple[Path, Path]], doc_id: str, norm_slug: str
    ) -> Path | None:
        """Matches a candidate bundle against its metadata.yaml id or document_number."""
        for b, s_dir in all_candidates:
            meta_p = b / "metadata.yaml"
            if not meta_p.is_file():
                continue
            try:
                meta = yaml.safe_load(meta_p.read_text(encoding="utf-8")) or {}
                m_id = str(meta.get("id") or meta.get("doc_id") or "")
                m_num = str(meta.get("document_number") or "")
                for candidate_val in (m_id, m_num):
                    if not candidate_val:
                        continue
                    c_norm = re.sub(r"[\s\-_/.]+", "_", candidate_val.lower()).strip("_")
                    if candidate_val.lower() == doc_id.lower() or c_norm == norm_slug:
                        return self._verify_bundle_containment(b, s_dir)
            except Exception:
                pass
        return None

    def find_bundle_dir(self, doc_id: str) -> Path | None:
        """Locate bundle directory for doc_id with two-tier CWE-22 containment check."""
        if not SAFE_IDENTIFIER_PATTERN.match(doc_id) or ".." in doc_id:
            raise ValueError(f"Path traversal detected in doc_id: '{doc_id}'")

        norm_slug = re.sub(r"[\s\-_/.]+", "_", doc_id.lower()).strip("_")
        simple_slug = re.sub(r"[^a-z0-9]", "", doc_id.lower())
        if norm_slug in self._bundle_cache:
            return self._bundle_cache[norm_slug]["bundle_dir"]

        all_candidates = self._collect_bundle_candidates()
        for b, s_dir in all_candidates:
            b_norm = re.sub(r"[\s\-_/.]+", "_", b.name.lower()).strip("_")
            b_simple = re.sub(r"[^a-z0-9]", "", b.name.lower())
            if b_norm == norm_slug or b_simple == simple_slug:
                return self._verify_bundle_containment(b, s_dir)

        meta_match = self._match_bundle_by_metadata(all_candidates, doc_id, norm_slug)
        if meta_match:
            return meta_match

        prefix_matches = [
            (b, s_dir)
            for b, s_dir in all_candidates
            if re.sub(r"[\s\-_/.]+", "_", b.name.lower()).strip("_").startswith(norm_slug + "_")
        ]
        if prefix_matches:
            prefix_matches.sort(key=lambda x: len(x[0].name))
            return self._verify_bundle_containment(prefix_matches[0][0], prefix_matches[0][1])

        sub_matches = [
            (b, s_dir)
            for b, s_dir in all_candidates
            if norm_slug in (bn := re.sub(r"[\s\-_/.]+", "_", b.name.lower()).strip("_"))
            or bn in norm_slug
        ]
        if sub_matches:
            sub_matches.sort(key=lambda x: abs(len(x[0].name) - len(doc_id)))
            return self._verify_bundle_containment(sub_matches[0][0], sub_matches[0][1])
        return None

    def _load_bundle(self, bundle_dir: Path, norm_slug: str) -> dict[str, Any]:
        """Load and cache bundle assets (metadata, clauses AST, markdown content)."""
        if norm_slug in self._bundle_cache:
            return self._bundle_cache[norm_slug]

        metadata: dict[str, Any] = {}
        meta_p = bundle_dir / "metadata.yaml"
        if meta_p.is_file():
            try:
                metadata = yaml.safe_load(meta_p.read_text(encoding="utf-8")) or {}
            except Exception:
                pass

        clauses: list[dict[str, Any]] = []
        clauses_p = bundle_dir / "clauses.json"
        if clauses_p.is_file():
            try:
                clauses = json.loads(clauses_p.read_text(encoding="utf-8"))
            except Exception:
                pass

        md_files = [
            p
            for p in bundle_dir.glob("*.md")
            if p.name not in {"index.md", "log.md", "dead_ends.md", "README.md"}
        ]
        main_md_path: Path | None = None
        md_text = ""
        if md_files:
            pref = [p for p in md_files if p.stem.lower() == bundle_dir.name.lower()]
            main_md_path = pref[0] if pref else md_files[0]
            try:
                md_text = main_md_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                md_text = main_md_path.read_text(encoding="utf-8-sig")

        cache_entry: dict[str, Any] = {
            "bundle_dir": bundle_dir,
            "metadata": metadata,
            "clauses": clauses,
            "main_md_path": main_md_path,
            "md_text": md_text,
        }
        self._bundle_cache[norm_slug] = cache_entry
        return cache_entry

    @staticmethod
    def _find_anchor_pos(text: str, anchor_id: str) -> int:
        """Find the start character index of an anchor tag in text."""
        for aid in (anchor_id, anchor_id.replace("-", "_"), anchor_id.replace("_", "-")):
            pat = re.compile(
                r"<a\s+(?:id|name)=[\"']" + re.escape(aid) + r"[\"']\s*(?:/>|>\s*</a>|>)",
                re.IGNORECASE,
            )
            m = pat.search(text)
            if m:
                return m.start()
        return -1

    def _slice_article_region(self, md_text: str, art_num: str) -> str | None:
        """Extracts full article text (Điều X) up to the next article or structural heading."""
        art_start = self._find_anchor_pos(md_text, f"dieu-{art_num}")
        if art_start == -1:
            m = re.search(r"(?m)^#{1,3}\s+Điều\s+0*" + re.escape(art_num) + r"\b.*$", md_text)
            if m:
                art_start = m.start()
        if art_start == -1:
            return None

        search_region = md_text[art_start:]
        stop_patterns = [
            re.compile(
                r"<a\s+(?:id|name)=[\"']dieu[-_](?!0*"
                + re.escape(art_num)
                + r"(?:[-_]khoan|[-_]diem|_|\b))[^\"']*[\"']",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?m)^#{1,3}\s+(?:Điều\s+(?!0*"
                + re.escape(art_num)
                + r"\b)|Chương|Mục|Phần|PHỤ LỤC|Phụ lục)"
            ),
        ]
        first_stop = len(search_region)
        for spat in stop_patterns:
            for sm in spat.finditer(search_region):
                if 10 < sm.start() < first_stop:
                    first_stop = sm.start()
        return search_region[:first_stop].strip()

    def _slice_clause_in_article(self, md_text: str, art_num: str, khoan_num: str) -> str | None:
        """Extracts a specific clause (Khoản Y) scoped within Article X."""
        art_text = self._slice_article_region(md_text, art_num) or md_text
        k_start = self._find_anchor_pos(art_text, f"dieu-{art_num}-khoan-{khoan_num}")
        if k_start == -1:
            k_start = self._find_anchor_pos(art_text, f"khoan-{khoan_num}")
        if k_start == -1:
            m = re.search(r"(?m)^\s*0*" + re.escape(khoan_num) + r"\.\s+", art_text)
            if m:
                k_start = m.start()
        if k_start == -1:
            return None

        k_region = art_text[k_start:]
        k_stops = [
            re.compile(
                r"<a\s+(?:id|name)=[\"'](?:dieu[-_]"
                + re.escape(art_num)
                + r"[-_])?khoan[-_](?!0*"
                + re.escape(khoan_num)
                + r"\b)[^\"']*[\"']",
                re.IGNORECASE,
            ),
            re.compile(r"(?m)^\s*(?!0*" + re.escape(khoan_num) + r"\b)\d+\.\s+"),
            re.compile(
                r"<a\s+(?:id|name)=[\"']dieu[-_](?!0*"
                + re.escape(art_num)
                + r"(?:[-_]khoan|[-_]diem|_|\b))[^\"']*[\"']",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?m)^#{1,3}\s+(?:Điều\s+(?!0*"
                + re.escape(art_num)
                + r"\b)|Chương|Mục|Phần|PHỤ LỤC|Phụ lục)"
            ),
        ]
        first_k_stop = len(k_region)
        for spat in k_stops:
            for sm in spat.finditer(k_region):
                if 10 < sm.start() < first_k_stop:
                    first_k_stop = sm.start()
        return k_region[:first_k_stop].strip()

    def _slice_point_in_clause(
        self, doc_id: str, art_num: str, khoan_num: str, diem_id: str
    ) -> str | None:
        """Extracts a specific point (Điểm Z) scoped within Điều X Khoản Y."""
        clause_dict = self.get_clause(doc_id, f"dieu-{art_num}-khoan-{khoan_num}")
        if not clause_dict or not clause_dict.get("content"):
            return None
        k_content = clause_dict["content"]

        d_start = self._find_anchor_pos(
            k_content, f"dieu-{art_num}-khoan-{khoan_num}-diem-{diem_id}"
        )
        if d_start == -1:
            d_start = self._find_anchor_pos(k_content, f"diem-{diem_id}")
        if d_start == -1:
            m = re.search(r"(?m)^\s*" + re.escape(diem_id) + r"\)\s+", k_content)
            if m:
                d_start = m.start()
        if d_start == -1:
            return None

        d_region = k_content[d_start:]
        first_line_end = d_region.find("\n")
        min_offset = first_line_end + 1 if first_line_end > 0 else 5
        d_stops = [
            re.compile(
                r"<a\s+(?:id|name)=[\"'][^\"']*diem[-_](?!0*"
                + re.escape(diem_id)
                + r"\b)[^\"']*[\"']",
                re.IGNORECASE,
            ),
            re.compile(r"(?m)^\s*(?!0*" + re.escape(diem_id) + r"\b)[a-z0-9]\)\s+"),
        ]
        first_d_stop = len(d_region)
        for spat in d_stops:
            for sm in spat.finditer(d_region):
                if min_offset <= sm.start() < first_d_stop:
                    first_d_stop = sm.start()
        return d_region[:first_d_stop].strip()

    def _slice_section_region(self, md_text: str, sec_id: str) -> str | None:
        """Extracts a numbered technical standard section (muc-1, muc-1-1)."""
        sec_dotted = sec_id.replace("-", ".")
        sec_start = self._find_anchor_pos(md_text, f"muc-{sec_id}")
        if sec_start == -1:
            m = re.search(r"(?m)^#{1,4}\s+" + re.escape(sec_dotted) + r"\b.*$", md_text)
            if m:
                sec_start = m.start()
        if sec_start == -1:
            return None

        search_region = md_text[sec_start:]
        stop_patterns = [
            re.compile(
                r"<a\s+(?:id|name)=[\"']muc-(?!(?:"
                + re.escape(sec_id)
                + r"\b|"
                + re.escape(sec_id + "-")
                + r"))[^\"']*[\"']",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?m)^#{1,3}\s+(?!(?:"
                + re.escape(sec_dotted)
                + r"\b|"
                + re.escape(sec_dotted + ".")
                + r"))\d+(?:\.\d+)*\b"
            ),
            re.compile(r"(?m)^#{1,3}\s+(?:Chương|Phần|PHỤ LỤC|Phụ lục)\b"),
        ]
        first_stop = len(search_region)
        first_line_end = search_region.find("\n")
        min_offset = first_line_end + 1 if first_line_end > 0 else 10
        lines = search_region.splitlines()
        if len(lines) > 1 and lines[1].startswith("#"):
            min_offset = len(lines[0]) + len(lines[1]) + 2
        for spat in stop_patterns:
            for sm in spat.finditer(search_region):
                if min_offset <= sm.start() < first_stop:
                    first_stop = sm.start()
        return search_region[:first_stop].strip()

    def _slice_fallback_anchor(
        self, md_text: str, canonical_id: str, m_khoan_top: re.Match[str] | None
    ) -> str | None:
        """Extracts top-level Khoản or generic anchor region."""
        start_idx = self._find_anchor_pos(md_text, canonical_id)
        if start_idx == -1 and m_khoan_top:
            m = re.search(r"(?m)^\s*0*" + re.escape(m_khoan_top.group(1)) + r"\.\s+", md_text)
            if m:
                start_idx = m.start()
        if start_idx == -1:
            return None

        search_region = md_text[start_idx:]
        first_line_end = search_region.find("\n")
        min_offset = first_line_end + 1 if first_line_end > 0 else 10
        lines = search_region.splitlines()
        if len(lines) > 1 and lines[1].startswith("#"):
            min_offset = len(lines[0]) + len(lines[1]) + 2
        stop_patterns = [
            re.compile(r"<a\s+(?:id|name)=[\"'][^\"']+[\"']", re.IGNORECASE),
            re.compile(r"(?m)^#{1,4}\s+"),
        ]
        first_stop = len(search_region)
        for spat in stop_patterns:
            for sm in spat.finditer(search_region):
                if min_offset <= sm.start() < first_stop:
                    first_stop = sm.start()
        return search_region[:first_stop].strip()

    def _dispatch_clause_slice(self, doc_id: str, md_text: str, canonical_id: str) -> str | None:
        if m_art := re.match(r"^dieu-(\d+[a-z]?)$", canonical_id):
            return self._slice_article_region(md_text, m_art.group(1))
        if m_clause := re.match(r"^dieu-(\d+[a-z]?)-khoan-(\d+)$", canonical_id):
            return self._slice_clause_in_article(md_text, m_clause.group(1), m_clause.group(2))
        if m_point := re.match(r"^dieu-(\d+[a-z]?)-khoan-(\d+)-diem-([a-z0-9]+)$", canonical_id):
            return self._slice_point_in_clause(
                doc_id, m_point.group(1), m_point.group(2), m_point.group(3)
            )
        if m_sec := re.match(r"^muc-(\d+(?:-\d+)*)$", canonical_id):
            return self._slice_section_region(md_text, m_sec.group(1))
        return self._slice_fallback_anchor(
            md_text, canonical_id, re.match(r"^khoan-(\d+)$", canonical_id)
        )

    def get_clause(self, doc_id: str, clause_id: str) -> dict[str, Any] | None:
        """Extract clause, article, point, or section Markdown from OKF bundle using tier-aware slicing."""
        if not SAFE_IDENTIFIER_PATTERN.match(doc_id) or ".." in doc_id:
            raise ValueError(f"Path traversal detected in doc_id: '{doc_id}'")
        if not SAFE_CLAUSE_PATTERN.match(clause_id) or ".." in clause_id:
            raise ValueError(f"Path traversal detected in clause_id: '{clause_id}'")
        canonical_id = canonicalize_clause_id(clause_id)
        if not SAFE_IDENTIFIER_PATTERN.match(canonical_id):
            raise ValueError(f"Path traversal detected in canonical clause_id: '{canonical_id}'")

        bundle_dir = self.find_bundle_dir(doc_id)
        if not bundle_dir:
            return None
        bundle_data = self._load_bundle(
            bundle_dir, re.sub(r"[\s\-_/.]+", "_", doc_id.lower()).strip("_")
        )
        if not bundle_data["md_text"]:
            return None
        extracted = self._dispatch_clause_slice(doc_id, bundle_data["md_text"], canonical_id)
        if not extracted:
            return None

        title = next(
            (
                c.get("title", "")
                for c in bundle_data.get("clauses", [])
                if c.get("clause_id") in (canonical_id, c.get("anchor"))
                or c.get("anchor") == canonical_id
            ),
            "",
        )
        if not title:
            lines = extracted.splitlines()
            title = (
                (lines[1] if len(lines) > 1 and lines[0].startswith("<a ") else lines[0])
                .lstrip("#")
                .strip()
            )

        return {
            "doc_id": doc_id,
            "clause_id": canonical_id,
            "title": title or canonical_id,
            "content": extracted,
            "bundle_path": str(bundle_dir),
            "source_file": bundle_data["main_md_path"].name if bundle_data["main_md_path"] else "",
        }

    def get_table(self, doc_id: str, table_id: str, format: str = "markdown") -> str | None:
        """Extract table data from OKF bundle in CSV or Markdown format."""
        clean_table_id = table_id[:-4] if table_id.lower().endswith(".csv") else table_id
        if not SAFE_IDENTIFIER_PATTERN.match(doc_id) or ".." in doc_id:
            raise ValueError(f"Path traversal detected in doc_id: '{doc_id}'")
        if not SAFE_IDENTIFIER_PATTERN.match(clean_table_id) or ".." in clean_table_id:
            raise ValueError(f"Path traversal detected in table_id: '{clean_table_id}'")

        bundle_dir = self.find_bundle_dir(doc_id)
        if not bundle_dir:
            return None

        cand_names = [
            f"{clean_table_id}.csv",
            f"{clean_table_id.replace('-', '_')}.csv",
            f"{clean_table_id.replace('_', '-')}.csv",
            clean_table_id,
        ]
        csv_candidates: list[Path] = []
        for sub_dir in (bundle_dir / "tables" / "csv", bundle_dir / "tables"):
            if sub_dir.is_dir():
                csv_candidates.extend(sub_dir / name for name in cand_names)

        target_file = next((cand for cand in csv_candidates if cand.is_file()), None)
        if not target_file:
            return None

        resolved = target_file.resolve()
        if not resolved.is_relative_to(bundle_dir.resolve()):
            raise ValueError(
                f"Path traversal detected: table '{resolved}' outside bundle directory '{bundle_dir}'"
            )

        try:
            raw_csv = resolved.read_text(encoding="utf-8-sig")
        except Exception:
            raw_csv = resolved.read_text(encoding="utf-8", errors="replace")

        return raw_csv if format.lower() == "csv" else csv_to_markdown(raw_csv)


__all__ = ["LegalKnowledgeEngine", "canonicalize_clause_id", "csv_to_markdown"]

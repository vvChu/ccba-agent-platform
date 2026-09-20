"""legal_index.py - Standalone In-Memory Legal Flat Index (ADR-0059).

Provides fast, in-memory provenance lookup for Vietnamese statutory documents,
clauses (Điều, Khoản, Mục, Bảng, Phụ lục), gazette citations, and cryptographic
SHA-256 signatures without requiring external repository cloning during CI runs.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_FLAT_INDEX_PATH = Path(__file__).resolve().parent / "datasets" / "legal_clauses_flat.json"


def normalize_clause_variants(ref: str) -> list[str]:
    """Generates normalized lookup variants for a statutory clause reference."""
    raw = ref.strip().lower()
    variants = [raw]

    # Remove Vietnamese accents for slug matching
    slug = "".join(c for c in unicodedata.normalize("NFD", raw) if unicodedata.category(c) != "Mn")
    slug = slug.replace("đ", "d")
    variants.append(slug)

    # Hyphenated slug
    hyphen_slug = re.sub(r"[\s\.\,\_\:]+", "-", slug).strip("-")
    variants.append(hyphen_slug)

    # Clause like 'Điều 15' -> 'dieu-15', 'điều 15'
    m_dieu = re.search(r"(?:điều|dieu)\s+(\d+)", raw)
    if m_dieu:
        d_num = m_dieu.group(1)
        variants.extend([f"dieu-{d_num}", f"điều {d_num}"])
        m_khoan = re.search(r"(?:khoản|khoan)\s+(\d+)", raw)
        if m_khoan:
            k_num = m_khoan.group(1)
            variants.append(f"dieu-{d_num}-khoan-{k_num}")

    # Section like 'Mục 1.4' -> '1.4', 'muc-1-4'
    m_muc = re.search(r"(?:mục|muc)\s+([0-9a-z\.\-]+)", raw)
    if m_muc:
        sec = m_muc.group(1)
        variants.extend([sec, sec.replace(".", "-"), f"muc-{sec.replace('.', '-')}"])

    # Table like 'Bảng A.1' -> 'bang-a.1', 'bang-a-1', 'a.1'
    m_bang = re.search(r"(?:bảng|bang)\s+([0-9a-z\.\-]+)", raw)
    if m_bang:
        tab = m_bang.group(1)
        variants.extend([f"bang-{tab}", f"bang-{tab.replace('.', '-')}", tab])

    # Annex like 'Phụ lục A' -> 'phu-luc-a', 'phụ lục a'
    m_pl = re.search(r"(?:phụ\s+lục|phu\s+luc)\s+([0-9a-z\.\-]+)", raw)
    if m_pl:
        pl = m_pl.group(1)
        variants.extend([f"phu-luc-{pl}", f"phụ lục {pl}"])

    return list(dict.fromkeys(variants))


@dataclass(frozen=True)
class StatutoryDocument:
    """Metadata and statutory keys for an official statutory document."""

    id: str
    document_number: str
    title: str
    status: str
    effective_date: str
    cong_bao_number: str
    pdf_sha256: str
    statutory_keys: tuple[str, ...]

    def has_clause(self, clause_ref: str) -> bool:
        """Checks whether a clause reference or key exists in this document."""
        variants = normalize_clause_variants(clause_ref)
        key_set = set(self.statutory_keys)
        return any(v in key_set for v in variants)


@dataclass(frozen=True)
class LegalFlatIndex:
    """Compiled in-memory index of statutory documents and cross-statute replacements."""

    schema_version: str
    total_documents: int
    total_statutory_keys: int
    replaces_map: dict[str, str]
    documents: dict[str, StatutoryDocument]

    def get_document(self, doc_number_or_alias: str) -> StatutoryDocument | None:
        """Looks up a document by exact document number or normalized title/alias."""
        norm = doc_number_or_alias.strip()
        if norm in self.documents:
            return self.documents[norm]

        norm_l = norm.lower()
        for num, doc in self.documents.items():
            if (
                norm_l == num.lower()
                or norm_l in doc.title.lower()
                or doc.id.lower() == norm_l
                or norm_l in num.lower()
            ):
                return doc
        return None

    def is_expired_or_replaced(self, doc_ref: str) -> tuple[bool, str | None]:
        """Checks if a cited document reference is expired or replaced (ADR-0059).

        Returns:
            Tuple of (is_expired, replacement_document_number_if_any).
        """
        ref_l = doc_ref.strip().lower()
        for old_doc, new_doc in self.replaces_map.items():
            if old_doc.lower() in ref_l or (len(ref_l) >= 7 and ref_l in old_doc.lower()):
                return True, new_doc
        return False, None


@lru_cache(maxsize=1)
def load_legal_flat_index(path: Path | str | None = None) -> LegalFlatIndex:
    """Loads and memoizes the statutory legal flat index from JSON.

    Args:
        path: Optional override path to legal_clauses_flat.json.

    Returns:
        LegalFlatIndex loaded into memory.
    """
    target = Path(path) if path is not None else DEFAULT_FLAT_INDEX_PATH
    if not target.exists():
        raise FileNotFoundError(
            f"Statutory flat index not found at: {target}. Run scripts/eval/compile_legal_flat_index.py."
        )

    with open(target, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    raw_docs = data.get("documents", {})
    parsed_docs: dict[str, StatutoryDocument] = {}
    for num, item in raw_docs.items():
        parsed_docs[num] = StatutoryDocument(
            id=item.get("id", ""),
            document_number=item.get("document_number", num),
            title=item.get("title", ""),
            status=item.get("status", "active"),
            effective_date=item.get("effective_date", ""),
            cong_bao_number=item.get("cong_bao_number", ""),
            pdf_sha256=item.get("pdf_sha256", ""),
            statutory_keys=tuple(item.get("statutory_keys", [])),
        )

    return LegalFlatIndex(
        schema_version=data.get("schema_version", "1.0.0"),
        total_documents=data.get("total_documents", len(parsed_docs)),
        total_statutory_keys=data.get("total_statutory_keys", 0),
        replaces_map=data.get("replaces_map", {}),
        documents=parsed_docs,
    )

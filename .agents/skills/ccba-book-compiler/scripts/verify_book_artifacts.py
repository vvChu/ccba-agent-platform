"""Thin adapter delegating C4 book artifact verification to pipeline.book_verification."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from pipeline.book_excalidraw_verifier import verify_single_excalidraw  # noqa: E402
from pipeline.book_verification import (  # noqa: E402
    _augment_linter_stems,
    _check_concept_profile,
    _check_mermaid_and_entity_hygiene,
    _check_profile_specific_rules,
    _check_source_profile,
    _collect_fallback_media_names,
    _media_embed_exists,
    _resolve_note_profile,
    _verify_toc_chapters,
    run_book_verification,
    verify_batch_body_links,
    verify_concepts_and_excalidraw,
    verify_corpus_and_toc,
    verify_single_markdown_note,
)

__all__ = [
    "_augment_linter_stems",
    "_check_concept_profile",
    "_check_mermaid_and_entity_hygiene",
    "_check_profile_specific_rules",
    "_check_source_profile",
    "_collect_fallback_media_names",
    "_media_embed_exists",
    "_resolve_note_profile",
    "_verify_toc_chapters",
    "run_book_verification",
    "verify_batch_body_links",
    "verify_concepts_and_excalidraw",
    "verify_corpus_and_toc",
    "verify_single_excalidraw",
    "verify_single_markdown_note",
]

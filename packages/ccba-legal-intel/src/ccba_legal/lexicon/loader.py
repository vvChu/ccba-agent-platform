"""Taxonomy Loader for CCILF with Offline Fallback (COND-17).

Provides unified access to the Canonical Construction Taxonomy, seamlessly
preferring the zero-IO static generated module when available, with dynamic
YAML fallback for development mode.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.lexicon.models import CanonicalTerm

logger = logging.getLogger(__name__)

DEFAULT_RESOURCE_PATH = (
    Path(__file__).parent.parent / "resources" / "canonical_construction_taxonomy.yaml"
)


def load_canonical_taxonomy(resource_path: Path | None = None) -> dict[str, Any]:
    """Loads the canonical construction taxonomy with offline static fallback.

    Args:
        resource_path: Optional explicit path to taxonomy YAML file.

    Returns:
        Taxonomy dictionary structure.
    """
    if resource_path is not None and resource_path.is_file():
        logger.debug("Loading taxonomy from explicit file: %s", resource_path)
        with open(resource_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    # Prefer static compiled module (zero file I/O)
    try:
        from ccba_legal.lexicon import _generated_taxonomy  # type: ignore

        if hasattr(_generated_taxonomy, "CANONICAL_TAXONOMY"):
            return _generated_taxonomy.CANONICAL_TAXONOMY
    except ImportError:
        logger.debug("Static _generated_taxonomy not available, falling back to YAML")

    if DEFAULT_RESOURCE_PATH.is_file():
        with open(DEFAULT_RESOURCE_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    return {}


def get_canonical_terms(resource_path: Path | None = None) -> list[CanonicalTerm]:
    """Loads and deserializes all canonical terms into CanonicalTerm models."""
    data = load_canonical_taxonomy(resource_path)
    terms: list[CanonicalTerm] = []

    term_candidates: list[dict[str, Any]] = []

    # Check top-level 'terms' dict or list
    raw_terms = data.get("terms")
    if isinstance(raw_terms, dict):
        term_candidates.extend(raw_terms.values())
    elif isinstance(raw_terms, list):
        term_candidates.extend(raw_terms)

    # Check legacy/domain sections
    for section in [
        "statutory_definitions",
        "technical_construction_standards",
        "internal_governance_taxonomy",
    ]:
        sec_items = data.get(section, [])
        if isinstance(sec_items, list):
            term_candidates.extend(sec_items)
        elif isinstance(sec_items, dict):
            term_candidates.extend(sec_items.values())

    for item in term_candidates:
        if isinstance(item, dict) and "canonical_id" in item:
            try:
                terms.append(CanonicalTerm.model_validate(item))
            except Exception as e:
                logger.warning(
                    "Failed to validate canonical term %s: %s", item.get("canonical_id"), e
                )

    return terms

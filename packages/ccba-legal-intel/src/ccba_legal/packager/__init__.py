"""Modular Packager package for CCBA Legal Intelligence Platform."""

from __future__ import annotations

from .bundle_writer import (
    package_bundle,
    package_bundle_v2,
    validate_bundle_provenance,
    write_concept,
    write_logs_and_index,
    write_logs_and_index_v2,
)
from .clause_indexer import generate_clauses_json, write_qa_benchmark
from .link_standardizer import (
    integrate_tables,
    organize_bundle_structure,
    standardize_bundle_links,
)
from .packager_facade import OKFBundlePackager
from .slug_utils import sanitize_slug

__all__ = [
    "OKFBundlePackager",
    "sanitize_slug",
    "write_concept",
    "write_logs_and_index",
    "write_logs_and_index_v2",
    "package_bundle",
    "package_bundle_v2",
    "validate_bundle_provenance",
    "standardize_bundle_links",
    "organize_bundle_structure",
    "integrate_tables",
    "generate_clauses_json",
    "write_qa_benchmark",
]

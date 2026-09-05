"""Thin CLI Delegate for Loading, Indexing, and Searching legal_registry.yaml.

Delegates core registry operations and search to the deep seam in ``ccba_legal.registry``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ccba_legal.registry import (  # type: ignore[import-untyped]
    format_citation,
    load_legal_registry,
    search_legal_registry,
)

__all__ = [
    "load_legal_registry",
    "format_citation",
    "search_legal_registry",
]


def main() -> None:
    """CLI test entry point."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

    default_path = Path(".agents/skills/ccba-legal-document-tracker/resources/legal_registry.yaml")
    data = load_legal_registry(default_path)
    print(f"✅ Loaded legal registry with metadata: {data.get('metadata')}")
    results = search_legal_registry("PCCC", registry_path=default_path, top_k=2)
    print(f"✅ Search results for 'PCCC': {len(results)} found")


if __name__ == "__main__":
    main()

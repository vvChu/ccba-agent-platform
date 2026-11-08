#!/usr/bin/env python3
"""
Logo Design Core - BM25 search engine for logo design guidelines
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from bm25_engine import BM25  # noqa: E402
from bm25_engine import search_csv as _search_csv  # noqa: E402

__all__ = [
    "BM25",
    "CSV_CONFIG",
    "DATA_DIR",
    "DOMAIN_KEYWORDS",
    "detect_domain",
    "search",
    "search_all",
]

# ============ CONFIGURATION ============
DATA_DIR: Path = _SCRIPTS_ROOT.parent / "data" / "logo"
MAX_RESULTS: int = 3

CSV_CONFIG: dict[str, dict[str, Any]] = {
    "style": {
        "file": "styles.csv",
        "search_cols": ["Style Name", "Category", "Keywords", "Best For"],
        "output_cols": [
            "Style Name",
            "Category",
            "Keywords",
            "Primary Colors",
            "Secondary Colors",
            "Typography",
            "Effects",
            "Best For",
            "Avoid For",
            "Complexity",
            "Era",
        ],
    },
    "color": {
        "file": "colors.csv",
        "search_cols": ["Palette Name", "Category", "Keywords", "Psychology", "Best For"],
        "output_cols": [
            "Palette Name",
            "Category",
            "Keywords",
            "Primary Hex",
            "Secondary Hex",
            "Accent Hex",
            "Background Hex",
            "Text Hex",
            "Psychology",
            "Best For",
            "Avoid For",
        ],
    },
    "industry": {
        "file": "industries.csv",
        "search_cols": ["Industry", "Keywords", "Recommended Styles", "Mood"],
        "output_cols": [
            "Industry",
            "Keywords",
            "Recommended Styles",
            "Primary Colors",
            "Typography",
            "Common Symbols",
            "Mood",
            "Best Practices",
            "Avoid",
        ],
    },
}


DOMAIN_KEYWORDS = {
    "style": (
        "style",
        "minimalist",
        "vintage",
        "modern",
        "retro",
        "geometric",
        "abstract",
        "emblem",
        "badge",
        "wordmark",
        "mascot",
        "luxury",
        "playful",
        "corporate",
    ),
    "color": (
        "color",
        "palette",
        "hex",
        "#",
        "rgb",
        "blue",
        "red",
        "green",
        "gold",
        "warm",
        "cool",
        "vibrant",
        "pastel",
    ),
    "industry": (
        "tech",
        "healthcare",
        "finance",
        "legal",
        "restaurant",
        "food",
        "fashion",
        "beauty",
        "education",
        "sports",
        "fitness",
        "real estate",
        "crypto",
        "gaming",
    ),
}


def detect_domain(query: str) -> str:
    """Auto-detect the most relevant domain from query using deterministic tie-breaking."""
    query_lower = query.lower()
    domain_order = ("style", "color", "industry")
    scored = [
        (dom, sum(1 for kw in DOMAIN_KEYWORDS[dom] if kw in query_lower)) for dom in domain_order
    ]
    ranked = sorted(scored, key=lambda item: (-item[1], domain_order.index(item[0])))
    return ranked[0][0] if ranked[0][1] > 0 else "style"


def search(query: str, domain: str | None = None, max_results: int = MAX_RESULTS) -> dict[str, Any]:
    """Main search function with auto-domain detection."""
    if domain is None:
        domain = detect_domain(query)

    config = CSV_CONFIG.get(domain, CSV_CONFIG["style"])
    filepath = DATA_DIR / str(config["file"])

    if not filepath.exists():
        return {"error": f"File not found: {filepath}", "domain": domain}

    results = _search_csv(
        filepath,
        list(config["search_cols"]),
        list(config["output_cols"]),
        query,
        max_results,
    )

    return {
        "domain": domain,
        "query": query,
        "file": str(config["file"]),
        "count": len(results),
        "results": results,
    }


def search_all(query: str, max_results: int = 2) -> dict[str, list[dict[str, str]]]:
    """Search across all domains and combine results."""
    all_results: dict[str, list[dict[str, str]]] = {}
    for domain in CSV_CONFIG.keys():
        result = search(query, domain, max_results)
        if result.get("results"):
            all_results[domain] = list(result["results"])
    return all_results

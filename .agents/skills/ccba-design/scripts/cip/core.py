#!/usr/bin/env python3
"""
CIP Design Core - BM25 search engine for Corporate Identity Program design guidelines
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
    "get_cip_brief",
    "search",
    "search_all",
]

# ============ CONFIGURATION ============
DATA_DIR: Path = _SCRIPTS_ROOT.parent / "data" / "cip"
MAX_RESULTS: int = 3

CSV_CONFIG: dict[str, dict[str, Any]] = {
    "deliverable": {
        "file": "deliverables.csv",
        "search_cols": ["Deliverable", "Category", "Keywords", "Description", "Mockup Context"],
        "output_cols": [
            "Deliverable",
            "Category",
            "Keywords",
            "Description",
            "Dimensions",
            "File Format",
            "Logo Placement",
            "Color Usage",
            "Typography Notes",
            "Mockup Context",
            "Best Practices",
            "Avoid",
        ],
    },
    "style": {
        "file": "styles.csv",
        "search_cols": ["Style Name", "Category", "Keywords", "Description", "Mood"],
        "output_cols": [
            "Style Name",
            "Category",
            "Keywords",
            "Description",
            "Primary Colors",
            "Secondary Colors",
            "Typography",
            "Materials",
            "Finishes",
            "Mood",
            "Best For",
            "Avoid For",
        ],
    },
    "industry": {
        "file": "industries.csv",
        "search_cols": ["Industry", "Keywords", "CIP Style", "Mood"],
        "output_cols": [
            "Industry",
            "Keywords",
            "CIP Style",
            "Primary Colors",
            "Secondary Colors",
            "Typography",
            "Key Deliverables",
            "Mood",
            "Best Practices",
            "Avoid",
        ],
    },
    "mockup": {
        "file": "mockup-contexts.csv",
        "search_cols": ["Context Name", "Category", "Keywords", "Scene Description"],
        "output_cols": [
            "Context Name",
            "Category",
            "Keywords",
            "Scene Description",
            "Lighting",
            "Environment",
            "Props",
            "Camera Angle",
            "Background",
            "Style Notes",
            "Best For",
            "Prompt Modifiers",
        ],
    },
}


DOMAIN_KEYWORDS = {
    "deliverable": (
        "card",
        "letterhead",
        "envelope",
        "folder",
        "shirt",
        "cap",
        "badge",
        "signage",
        "vehicle",
        "car",
        "van",
        "stationery",
        "uniform",
        "merchandise",
        "packaging",
        "banner",
        "booth",
    ),
    "style": (
        "style",
        "minimal",
        "modern",
        "luxury",
        "vintage",
        "industrial",
        "elegant",
        "bold",
        "corporate",
        "organic",
        "playful",
    ),
    "industry": (
        "tech",
        "finance",
        "legal",
        "healthcare",
        "hospitality",
        "food",
        "fashion",
        "retail",
        "construction",
        "logistics",
    ),
    "mockup": (
        "mockup",
        "scene",
        "context",
        "photo",
        "shot",
        "lighting",
        "background",
        "studio",
        "lifestyle",
    ),
}


def detect_domain(query: str) -> str:
    """Auto-detect the most relevant domain from query using deterministic tie-breaking."""
    query_lower = query.lower()
    domain_order = ("deliverable", "style", "industry", "mockup")
    scored = [
        (dom, sum(1 for kw in DOMAIN_KEYWORDS[dom] if kw in query_lower)) for dom in domain_order
    ]
    ranked = sorted(scored, key=lambda item: (-item[1], domain_order.index(item[0])))
    return ranked[0][0] if ranked[0][1] > 0 else "deliverable"


def search(query: str, domain: str | None = None, max_results: int = MAX_RESULTS) -> dict[str, Any]:
    """Main search function with auto-domain detection."""
    if domain is None:
        domain = detect_domain(query)

    config = CSV_CONFIG.get(domain, CSV_CONFIG["deliverable"])
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


def get_cip_brief(
    brand_name: str, industry_query: str, style_query: str | None = None
) -> dict[str, Any]:
    """Generate a comprehensive CIP brief for a brand."""
    industry_results = search(industry_query, "industry", 1)
    industry = industry_results.get("results", [{}])[0] if industry_results.get("results") else {}

    resolved_style_query = style_query or str(industry.get("CIP Style", "corporate minimal"))
    style_results = search(resolved_style_query, "style", 1)
    style = style_results.get("results", [{}])[0] if style_results.get("results") else {}

    key_deliverables = str(industry.get("Key Deliverables", "")).split()
    deliverable_results: list[dict[str, str]] = []
    for item in key_deliverables[:5]:
        result = search(item, "deliverable", 1)
        if result.get("results"):
            deliverable_results.append(result["results"][0])

    return {
        "brand_name": brand_name,
        "industry": industry,
        "style": style,
        "recommended_deliverables": deliverable_results,
        "color_system": {
            "primary": style.get("Primary Colors", industry.get("Primary Colors", "")),
            "secondary": style.get("Secondary Colors", industry.get("Secondary Colors", "")),
        },
        "typography": style.get("Typography", industry.get("Typography", "")),
        "materials": style.get("Materials", ""),
        "finishes": style.get("Finishes", ""),
    }

"""uniclass_index.py - Standalone In-Memory Uniclass 200 & ISO 12006-2 Flat Index (TICKET-005).

Provides fast in-memory lookup, classification verification, and anti-trap validation
for Uniclass 200 tables (Co, En, SL, EF, Ss, Pr, PM) and ISO 12006-2 layers.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger("ccba.eval.uniclass_index")

DEFAULT_UNICLASS_INDEX_PATH = (
    Path(__file__).resolve().parent / "datasets" / "uniclass_tables_flat.json"
)


@dataclass
class UniclassEntry:
    """Represents a single verified Uniclass 200 classification entry."""

    code: str
    table: str
    table_name: str
    table_name_vi: str
    iso_12006_layer: str
    title_vi: str
    title_en: str
    example_naming: str | None = None
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Converts entry to JSON-serializable dictionary."""
        return {
            "code": self.code,
            "table": self.table,
            "table_name": self.table_name,
            "table_name_vi": self.table_name_vi,
            "iso_12006_layer": self.iso_12006_layer,
            "title_vi": self.title_vi,
            "title_en": self.title_en,
            "example_naming": self.example_naming,
        }


class UniclassFlatIndex:
    """In-memory searchable index of Uniclass 200 classification codes and ISO 12006-2 rules."""

    def __init__(self, raw_data: dict[str, Any]) -> None:
        self.metadata = raw_data.get("metadata", {})
        self.tables: dict[str, dict[str, str]] = raw_data.get("tables", {})
        self.anti_traps: dict[str, dict[str, Any]] = raw_data.get("anti_traps", {})

        table_canonical = {
            "CO": "Co",
            "EN": "En",
            "SL": "SL",
            "EF": "EF",
            "SS": "Ss",
            "PR": "Pr",
            "PM": "PM",
            "TE": "TE",
            "RO": "Ro",
        }

        self.entries_by_code: dict[str, UniclassEntry] = {}
        for code, cdata in raw_data.get("codes", {}).items():
            raw_table = cdata.get("table", code.split("_")[0]).upper()
            canonical_table = table_canonical.get(raw_table, raw_table)
            entry = UniclassEntry(
                code=code,
                table=canonical_table,
                table_name=cdata.get("table_name", canonical_table),
                table_name_vi=cdata.get("table_name_vi", canonical_table),
                iso_12006_layer=cdata.get("iso_12006_layer", "Result"),
                title_vi=cdata.get("title_vi", ""),
                title_en=cdata.get("title_en", code),
                example_naming=cdata.get("example_naming"),
                sources=cdata.get("sources", []),
            )
            # Store normalized uppercase code
            self.entries_by_code[code.upper()] = entry

    def lookup_code(self, code: str) -> UniclassEntry | None:
        """Looks up an exact Uniclass code (case-insensitive)."""
        normalized = code.strip().replace("-", "_").upper()
        return self.entries_by_code.get(normalized)

    def is_valid_code(self, code: str) -> bool:
        """Checks if a Uniclass code is validly registered in the flat index."""
        normalized = code.strip().replace("-", "_").upper()
        return normalized in self.entries_by_code

    def extract_uniclass_codes(self, text: str) -> list[str]:
        """Extracts all candidate Uniclass 200 code patterns from text."""
        # Uniclass patterns like EF_20_10_15 or SL_25_10_72 or Co_25_10_55
        pattern = re.compile(
            r"\b(Co|En|SL|EF|Ss|Pr|PM|TE|Ro)_(?:\d{2})(?:_\d{2})*(?:_\d{2})*\b",
            re.IGNORECASE,
        )
        matches = [m.group(0).upper() for m in pattern.finditer(text)]
        # Deduplicate preserving order
        seen = set()
        unique_matches = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                unique_matches.append(m)
        return unique_matches

    def validate_iso_19650_naming(self, name_str: str) -> bool:
        """Validates ISO 19650 Information Container naming syntax for rooms/spaces.

        Syntax: [Project]-[Building]-[Floor]-[Uniclass_SL]-[Seq]
        Example: HUB-LIB-B1-L03-SL_25_10_72-002
        """
        pattern = re.compile(
            r"^[A-Z0-9_\-]+-[A-Z0-9_\-]+-[A-Z0-9_\-]+-SL_\d{2}(?:_\d{2})+-[A-Z0-9]+$",
            re.IGNORECASE,
        )
        return bool(pattern.search(name_str.strip()))

    def validate_ifc_alignment_naming(self, name_str: str) -> bool:
        """Validates IFC Alignment linear infrastructure naming syntax.

        Syntax: [Route]-[Chainage/KM]-[Element]-[Uniclass_EF]
        Example: CT01-KM015_350-P04-EF_20_10 or CT05-KM002_150_KM002_450-EF_10_10
        """
        pattern = re.compile(
            r"^[A-Z0-9]+-KM\d+_\d+(?:_KM\d+_\d+)?-(?:[A-Z0-9_]+-)?EF_\d{2}(?:_\d{2})*",
            re.IGNORECASE,
        )
        return bool(pattern.search(name_str.strip()))

    def check_anti_traps(self, output: str) -> tuple[bool, str | None]:
        """Checks text against known redteam anti-traps. Returns (has_trap, reason)."""
        for _trap_id, tdata in self.anti_traps.items():
            for pat in tdata.get("forbidden_patterns", []):
                if re.search(pat, output, re.IGNORECASE):
                    return True, f"Anti-Trap Violation ({tdata.get('name')}): {tdata.get('rule')}"
        return False, None


@lru_cache(maxsize=4)
def load_uniclass_flat_index(index_path: Path | None = None) -> UniclassFlatIndex:
    """Loads Uniclass flat index into memory with LRU caching."""
    target = index_path or DEFAULT_UNICLASS_INDEX_PATH
    if not target.exists():
        logger.warning(f"Uniclass flat index file not found at {target}, using empty index")
        return UniclassFlatIndex({})

    with open(target, encoding="utf-8") as f:
        data = json.load(f)
    return UniclassFlatIndex(data)

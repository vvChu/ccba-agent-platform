"""Thin CLI Delegate for Legal Grounding Gate and Citation Verifier.

Delegates core verification logic to the deep seam in ``ccba_legal.grounding``.
"""

from __future__ import annotations

import sys
from typing import Any

from ccba_legal.grounding import (
    LEGAL_DISCLAIMER,
    LegalGroundingGate,
    format_grounded_response,
    verify_legal_grounding,
)

__all__ = [
    "verify_legal_grounding",
    "format_grounded_response",
    "LegalGroundingGate",
    "LEGAL_DISCLAIMER",
]


def main() -> None:
    """CLI test entry point."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

    sample_retrieved: list[dict[str, Any]] = [
        {"short_name": "NĐ 207/2026", "document_number": "207/2026/NĐ-CP", "id": "ND-207-2026"}
    ]
    sample_text = "Theo quy định tại [NĐ 207/2026 - 207/2026/NĐ-CP], nghiệm thu công trình theo Điều 12."
    result = verify_legal_grounding(sample_text, sample_retrieved)
    print(f"Grounding verification result: {result}")
    formatted = format_grounded_response(sample_text, sample_retrieved)
    print(f"\nFormatted Output:\n{formatted}")


if __name__ == "__main__":
    main()

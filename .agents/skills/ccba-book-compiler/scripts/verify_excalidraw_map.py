"""Thin adapter delegating Excalidraw 16:9 verification to pipeline.book_excalidraw_verifier."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[4] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from pipeline.book_excalidraw_verifier import (  # noqa: E402
    _element_x_bounds,
    _extract_excalidraw_json,
    _LzBitReader,
    decompress_lz_base64,
    verify_single_excalidraw,
)

__all__ = [
    "_LzBitReader",
    "_element_x_bounds",
    "_extract_excalidraw_json",
    "decompress_lz_base64",
    "verify_single_excalidraw",
]

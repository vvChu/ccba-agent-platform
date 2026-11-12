"""Excalidraw 16:9 geometry & LZString compressed-json verifier for /ccba-book-compiler."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_DRAWING_JSON_RE = re.compile(r"## Drawing\s+```json\s*(\{.*?\})\s*```", re.DOTALL)
_DRAWING_COMPRESSED_RE = re.compile(
    r"## Drawing\s+```compressed-json\s*([A-Za-z0-9+/=\s]+?)\s*```", re.DOTALL
)
_B64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
_B64_MAP = {ch: idx for idx, ch in enumerate(_B64_ALPHABET)}


class _LzBitReader:
    """Stateful 6-bit base64 stream reader for Obsidian Excalidraw LZString payloads."""

    def __init__(self, payload: str) -> None:
        self.payload = payload
        self.length = len(payload)
        self.val = _B64_MAP.get(payload[0], 0) if payload else 0
        self.pos = 32
        self.idx = 1

    def read_bits(self, nbits: int) -> int:
        """Read nbits little-endian bits from the base64 stream."""
        bits = 0
        for shift in range(nbits):
            resb = self.val & self.pos
            self.pos >>= 1
            if self.pos == 0:
                self.pos = 32
                self.val = _B64_MAP.get(self.payload[self.idx], 0) if self.idx < self.length else 0
                self.idx += 1
            if resb > 0:
                bits |= 1 << shift
        return bits


def decompress_lz_base64(compressed: str) -> str:
    """Decompress LZString.compressToBase64 blocks saved by Obsidian Excalidraw."""
    clean = re.sub(r"\s+", "", compressed)
    if not clean or any(ch not in _B64_MAP for ch in clean):
        return ""
    reader = _LzBitReader(clean)
    first = reader.read_bits(2)
    if first not in (0, 1):
        return ""
    c = chr(reader.read_bits(8 if first == 0 else 16))
    dictionary: dict[int, str] = {3: c}
    enlarge_in, dict_size, num_bits = 4, 4, 3
    w = c
    out = [c]
    while reader.idx <= reader.length + 1:
        cc = reader.read_bits(num_bits)
        if cc in (0, 1):
            dictionary[dict_size] = chr(reader.read_bits(8 if cc == 0 else 16))
            cc = dict_size
            dict_size += 1
            enlarge_in -= 1
        elif cc == 2:
            return "".join(out)
        if enlarge_in == 0:
            enlarge_in = 1 << num_bits
            num_bits += 1
        entry = dictionary[cc] if cc in dictionary else (w + w[0] if cc == dict_size else "")
        if not entry:
            return ""
        out.append(entry)
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        enlarge_in -= 1
        w = entry
        if enlarge_in == 0:
            enlarge_in = 1 << num_bits
            num_bits += 1
    return ""


def _extract_excalidraw_json(etxt: str, filename: str) -> tuple[dict[str, Any] | None, str | None]:
    """Parse Excalidraw scene dict from either raw ```json or Obsidian ```compressed-json."""
    if raw_match := _DRAWING_JSON_RE.search(etxt):
        raw_json = raw_match.group(1)
    elif comp_match := _DRAWING_COMPRESSED_RE.search(etxt):
        raw_json = decompress_lz_base64(comp_match.group(1))
        if not raw_json:
            return None, f"Failed to decompress compressed-json block in {filename}"
    else:
        return None, f"Missing JSON or compressed-json block under '## Drawing' in {filename}"
    try:
        return json.loads(raw_json), None
    except json.JSONDecodeError as exc:
        return None, f"Invalid Excalidraw JSON in {filename}: {exc}"


def _element_x_bounds(el: dict[str, Any]) -> list[float]:
    """Compute horizontal X coordinates for a single Excalidraw element including 2D arrow points."""
    x0 = float(el.get("x") or 0.0)
    if el.get("type") in {"arrow", "line"} and isinstance(el.get("points"), list) and el["points"]:
        pts = [
            x0 + float(pt[0])
            for pt in el["points"]
            if isinstance(pt, (list, tuple)) and len(pt) >= 2
        ]
        if pts:
            return pts
    return [x0, x0 + float(el.get("width") or 0.0)]


def verify_single_excalidraw(excalidraw_path: Path) -> list[str]:
    """Verify Excalidraw ## Text Elements, 16:9 horizontal span [1000..1150px], and fontSize >= 13."""
    if not excalidraw_path.is_file():
        return [f"Missing Excalidraw file: {excalidraw_path}"]
    etxt = excalidraw_path.read_text(encoding="utf-8")
    errors: list[str] = []
    if "## Text Elements" not in etxt:
        errors.append(f"Missing '## Text Elements' in {excalidraw_path.name}")
    data, parse_err = _extract_excalidraw_json(etxt, excalidraw_path.name)
    if parse_err or data is None:
        return [*errors, parse_err or f"Unparseable Excalidraw scene in {excalidraw_path.name}"]
    active = [
        el for el in data.get("elements", []) if isinstance(el, dict) and not el.get("isDeleted")
    ]
    if not active:
        return [*errors, f"Excalidraw has zero active elements: {excalidraw_path.name}"]
    xs = [coord for el in active for coord in _element_x_bounds(el)]
    span_w = max(xs) - min(xs)
    if not (1000.0 <= span_w <= 1150.0):
        errors.append(
            f"Excalidraw horizontal span {span_w:.1f}px outside [1000.0, 1150.0]px in {excalidraw_path.name}"
        )
    for el in active:
        if el.get("type") == "text" and float(el.get("fontSize") or 0.0) < 13.0:
            errors.append(
                f"Excalidraw text '{el.get('id')}' fontSize={el.get('fontSize')} < 13px in {excalidraw_path.name}"
            )
    return errors

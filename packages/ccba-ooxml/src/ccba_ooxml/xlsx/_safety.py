"""Pure-stdlib preflight archive checks and cell value sanitization for XLSX files."""

from __future__ import annotations

import posixpath
import re
import zipfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ._models import XlsxFillConfig, XlsxMediaLimitError

_ILLEGAL_XML_CHARS_RE = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]")
_FORMULA_PREFIXES = ("=", "+", "-", "@")
_OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_ZIP_MAGIC = b"PK"


def _check_archive_header(file_path: Path) -> None:
    """Validate existence, non-empty size, and ZIP magic bytes before opening."""
    if not file_path.is_file():
        raise FileNotFoundError(f"XLSX file not found: {file_path}")
    if file_path.stat().st_size == 0:
        raise zipfile.BadZipFile(f"corrupted_zip: XLSX file is empty: {file_path}")
    with file_path.open("rb") as fh:
        header = fh.read(8)
    if header.startswith(_OLE2_MAGIC):
        raise zipfile.BadZipFile(
            f"corrupted_zip: Encrypted OOXML/EncryptionInfo OLE2 container unsupported: {file_path}"
        )
    if not header.startswith(_ZIP_MAGIC):
        raise zipfile.BadZipFile(f"corrupted_zip: Missing ZIP PK magic header: {file_path}")


def _validate_entry_path(raw_name: str) -> str:
    """Normalize a ZIP entry path with posixpath and reject traversal/backslash attacks."""
    if "\\" in raw_name or raw_name.startswith("/") or ".." in raw_name.split("/"):
        raise zipfile.BadZipFile(f"corrupted_zip: Unsafe ZIP entry path '{raw_name}'")
    norm = posixpath.normpath(raw_name)
    if norm.startswith("/") or norm == ".." or norm.startswith("../"):
        raise zipfile.BadZipFile(f"corrupted_zip: Unsafe normalized ZIP entry path '{raw_name}'")
    return norm


def _check_zip_entries(
    infos: list[zipfile.ZipInfo],
    file_path: Path,
    cfg: XlsxFillConfig,
) -> None:
    """Check entry count, uncompressed sizes, EncryptionInfo, and xl/media/* limits."""
    if len(infos) > cfg.max_entries:
        raise XlsxMediaLimitError(
            f"XLSX archive '{file_path}' has {len(infos)} entries, exceeding max_entries={cfg.max_entries}."
        )
    total_bytes = 0
    for info in infos:
        norm = _validate_entry_path(info.filename)
        lower = norm.lower()
        if lower == "encryptioninfo" or lower.endswith("/encryptioninfo"):
            raise zipfile.BadZipFile(
                f"corrupted_zip: EncryptionInfo entry detected in '{file_path}'"
            )
        size = info.file_size
        if size > cfg.max_entry_bytes:
            raise XlsxMediaLimitError(
                f"ZIP entry '{norm}' uncompressed size {size} bytes exceeds max_entry_bytes={cfg.max_entry_bytes}."
            )
        total_bytes += size
        if total_bytes > cfg.max_total_bytes:
            raise XlsxMediaLimitError(
                f"XLSX archive '{file_path}' total uncompressed size exceeds max_total_bytes={cfg.max_total_bytes}."
            )
        if lower.startswith("xl/media/") and size > cfg.max_media_bytes:
            raise XlsxMediaLimitError(
                f"Embedded media '{norm}' size {size} bytes exceeds max_media_bytes={cfg.max_media_bytes}."
            )


def verify_xlsx_zip_safety(
    path: Path | str,
    config: XlsxFillConfig | None = None,
) -> None:
    """Inspect XLSX ZIP central directory using uncompressed ``ZipInfo.file_size`` limits.

    Raises:
        FileNotFoundError: If ``path`` does not exist or is not a file.
        zipfile.BadZipFile: On empty, non-ZIP, encrypted, or traversal-tainted archives.
        XlsxMediaLimitError: When entry count or uncompressed sizes exceed ``config`` ceilings.
    """
    cfg = config or XlsxFillConfig()
    file_path = Path(path)
    _check_archive_header(file_path)
    with zipfile.ZipFile(file_path, "r") as zf:
        _check_zip_entries(zf.infolist(), file_path, cfg)


def sanitize_xlsx_value(
    val: Any,
    *,
    allow_formulas: bool = False,
    date_as_iso: bool = True,
) -> Any:
    """Sanitize a value for safe Excel cell assignment and formula-injection defense."""
    if val is None:
        return ""
    if isinstance(val, bool):
        return val
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, (datetime, date)):
        return val.isoformat() if date_as_iso else val
    text = val if isinstance(val, str) else str(val)
    cleaned = _ILLEGAL_XML_CHARS_RE.sub("", text)
    if not allow_formulas:
        stripped = cleaned.lstrip()
        if cleaned.startswith(("\t", "\r")) or (stripped and stripped[0] in _FORMULA_PREFIXES):
            return f"'{cleaned}"
    return cleaned

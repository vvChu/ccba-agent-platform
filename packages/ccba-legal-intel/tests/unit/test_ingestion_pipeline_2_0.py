"""Unit tests for Ingestion Pipeline 2.0 and Tri-Tier Google Drive Vault (ADR 0035)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from ccba_legal.gdrive_vault import GoogleDriveVault, compute_file_sha256
from ccba_legal.table_cleaner import (
    clean_markdown_tables_and_notes,
    enforce_monotonic_footnotes,
    flatten_table_headers,
)


def test_flatten_table_headers() -> None:
    """Test that broken or wrapped table headers are cleanly flattened."""
    broken_table = """### Bảng 2.17 - Quy định về các loại đường

| Cấp đường | Loại đường | Khoảng cách hai đường (m) | Mật độ đường
(km/$km^{2}$) |
| :--- | :--- | :--- | :---: |
| Cấp đô thị | 1. Đường cao tốc đô thị | 4 800 - 8 000 | 0,4 - 0,25 |
"""
    cleaned = flatten_table_headers(broken_table)
    assert (
        "| Cấp đường | Loại đường | Khoảng cách hai đường (m) | Mật độ đường (km/$km^{2}$) |"
        in cleaned
    )
    assert "| :--- | :--- | :--- | :---: |" in cleaned


def test_enforce_monotonic_footnotes() -> None:
    """Test that missing CHÚ THÍCH 1 is automatically restored when CHÚ THÍCH 2 exists."""
    raw_footnotes = """_CHÚ THÍCH:_

Chu kỳ lặp lại trận mưa gây tràn cống không sử dụng để tính toán.

**CHÚ THÍCH 2:** Khi tính toán hệ thống thoát nước mặt phải xem xét.
"""
    repaired = enforce_monotonic_footnotes(raw_footnotes)
    assert "**CHÚ THÍCH 1:** Chu kỳ lặp lại trận mưa" in repaired
    assert "**CHÚ THÍCH 2:** Khi tính toán" in repaired


def test_clean_markdown_tables_and_notes_unified() -> None:
    """Test full unified cleaner."""
    sample = """### Bảng 1 - Chỉ tiêu

| Cột 1 | Cột 2
(m) |
| :--- | :--- |
| A | B |

_CHÚ THÍCH:_

Nội dung chú thích đầu.

**CHÚ THÍCH 2:** Nội dung chú thích hai.
"""
    cleaned = clean_markdown_tables_and_notes(sample)
    assert "**CHÚ THÍCH 1:** Nội dung chú thích đầu." in cleaned
    assert "**CHÚ THÍCH 2:** Nội dung chú thích hai." in cleaned


def test_compute_file_sha256() -> None:
    """Test standard SHA-256 calculation."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
        f.write("CCBA Legal Intelligence Standard")
        temp_path = Path(f.name)

    try:
        digest = compute_file_sha256(temp_path)
        assert len(digest) == 64
        assert isinstance(digest, str)
    finally:
        temp_path.unlink()


def test_gdrive_vault_offline_mode() -> None:
    """Test GoogleDriveVault offline fallback when credentials are not configured."""
    vault = GoogleDriveVault(credentials_path=Path("/non/existent/path/drive_token.json"))
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
        f.write("Dummy PDF Content")
        temp_file = Path(f.name)

    try:
        res = vault.upload_asset(temp_file, "02_qcvn", "qcvn_01_2021_bxd")
        assert "sha256" in res
        assert res["file_name"] == temp_file.name
        assert "vault_path" in res
    finally:
        temp_file.unlink()

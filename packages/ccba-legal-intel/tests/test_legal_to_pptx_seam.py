"""Unit tests for Legal-to-PPTX Thin Seam (ADR-0044)."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from ccba_legal.cli import build_parser, handle_pptx

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_pptx_parser_configuration() -> None:
    """Verify 'pptx' subcommand parser options and arguments."""
    parser = build_parser()
    subparsers_action = next(a for a in parser._actions if a.dest == "command")
    assert "pptx" in subparsers_action.choices

    pptx_parser = subparsers_action.choices["pptx"]
    arg_names = [a.dest for a in pptx_parser._actions]
    assert "input_markdown" in arg_names
    assert "output" in arg_names


def test_handle_pptx_missing_input_file(tmp_path: Path) -> None:
    """Verify handle_pptx returns exit code 1 when input file is not found."""
    non_existent = tmp_path / "not_found.md"
    out_pptx = tmp_path / "output.pptx"
    args = argparse.Namespace(input_markdown=non_existent, output=out_pptx)

    code = handle_pptx(args)
    assert code == 1
    assert not out_pptx.exists()


def test_handle_pptx_directory_input_rejected(tmp_path: Path) -> None:
    """Verify handle_pptx returns exit code 1 when input path is a directory."""
    input_dir = tmp_path / "folder_not_file"
    input_dir.mkdir(parents=True, exist_ok=True)
    out_pptx = tmp_path / "output.pptx"
    args = argparse.Namespace(input_markdown=input_dir, output=out_pptx)

    code = handle_pptx(args)
    assert code == 1
    assert not out_pptx.exists()


def test_handle_pptx_successful_generation(tmp_path: Path) -> None:
    """Verify handle_pptx generates valid PowerPoint deck from sample markdown."""
    sample_md = tmp_path / "legal_presentation.md"
    sample_md.write_text(
        """# Quy Định Thẩm Duyệt Thiết Kế PCCC Mới
## Tổng quan Luật số 55/2024/QH15 & Nghị định 105/2025/NĐ-CP

---

## 1. Phân Định Thẩm Quyền Kép (Dual-Pathway)
- Cơ quan Chuyên môn về Xây dựng (CQCMVXD): Thẩm tra kiến trúc, bậc chịu lửa, thoát nạn.
- Cơ quan Cảnh sát PCCC (C07/PC07): Thẩm duyệt thiết bị MEP, hệ thống chữa cháy, báo cháy.
- Chủ đầu tư tự thẩm định: Mẫu PC13 đối với các công trình quy mô nhỏ ngoài Phụ lục III.

---

## 2. Kết Luận & Khuyến Nghị
- Rà soát hồ sơ thiết kế kỹ thuật trước khi nộp cơ quan chức năng.
- Đồng bộ thông số kỹ thuật giữa bản vẽ và thuyết minh.
""",
        encoding="utf-8",
    )

    out_pptx = tmp_path / "output.pptx"
    args = argparse.Namespace(input_markdown=sample_md, output=out_pptx)

    code = handle_pptx(args)
    assert code == 0
    assert out_pptx.exists()
    assert out_pptx.stat().st_size > 1000  # Valid PPTX zip package


def test_handle_pptx_default_output_path(tmp_path: Path) -> None:
    """Verify default output path uses input file stem with .pptx suffix."""
    sample_md = tmp_path / "summary.md"
    sample_md.write_text("# Test Presentation\n\nContent here", encoding="utf-8")

    args = argparse.Namespace(input_markdown=sample_md, output=None)
    code = handle_pptx(args)
    assert code == 0

    expected_out = tmp_path / "summary.pptx"
    assert expected_out.exists()
    assert expected_out.stat().st_size > 500


def test_handle_pptx_import_error_resilience(tmp_path: Path) -> None:
    """Verify graceful error reporting when ccba_ooxml is not importable."""
    sample_md = tmp_path / "test.md"
    sample_md.write_text("# Hello", encoding="utf-8")
    args = argparse.Namespace(input_markdown=sample_md, output=tmp_path / "test.pptx")

    with patch.dict("sys.modules", {"ccba_ooxml.pptx.deck_builder": None}):
        code = handle_pptx(args)
        assert code == 1

"""test_linter.py - Unit tests for visual parity & cross-link linter in ccba-legal-intel."""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_legal.linter import lint_bundle_links, lint_markdown_file, lint_target_path

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_lint_markdown_file_clean(tmp_path: Path) -> None:
    """Verify lint_markdown_file returns 0 errors for clean OKF markdown."""
    f = tmp_path / "doc.md"
    f.write_text(
        """# Điều 1. Phạm vi điều chỉnh
\\- Nội dung gạch đầu dòng thứ nhất.
&nbsp;&nbsp;\\+ Nội dung dấu cộng thứ hai.
""",
        encoding="utf-8",
    )
    errors = lint_markdown_file(f)
    assert len(errors) == 0


def test_lint_markdown_file_redundant_bullet(tmp_path: Path) -> None:
    """Verify lint_markdown_file detects redundant bullet before CHÚ THÍCH."""
    f = tmp_path / "doc.md"
    f.write_text(
        """# Bảng 1
- **CHÚ THÍCH 1: Nội dung ghi chú lỗi
""",
        encoding="utf-8",
    )
    errors = lint_markdown_file(f)
    assert len(errors) == 1
    assert "Redundant bullet" in errors[0]


def test_lint_markdown_file_raw_html_table(tmp_path: Path) -> None:
    """Verify lint_markdown_file detects unclean raw HTML table tags."""
    f = tmp_path / "doc.md"
    f.write_text(
        """# Phụ lục
<table><tr><td>Lỗi</td></tr></table>
""",
        encoding="utf-8",
    )
    errors = lint_markdown_file(f)
    assert len(errors) == 1
    assert "raw HTML table" in errors[0]


def test_lint_bundle_links(tmp_path: Path) -> None:
    """Verify lint_bundle_links detects broken anchors and valid anchors."""
    bundle_dir = tmp_path / "my_bundle"
    bundle_dir.mkdir()

    main_doc = bundle_dir / "main.md"
    main_doc.write_text(
        """# Văn bản chính
<a id="dieu-1"></a>
Liên kết đúng: [Điều 1](#dieu-1)
Liên kết sai: [Điều 99](#dieu-99)
""",
        encoding="utf-8",
    )

    errors = lint_bundle_links(bundle_dir)
    assert len(errors) == 1
    assert "#dieu-99" in errors[0]


def test_lint_target_path(tmp_path: Path) -> None:
    """Verify lint_target_path runs end-to-end on directory."""
    bundle_dir = tmp_path / "my_bundle"
    bundle_dir.mkdir()
    (bundle_dir / "clean.md").write_text("# Sạch 100%", encoding="utf-8")

    res = lint_target_path(bundle_dir)
    assert res["files_scanned"] == 1
    assert res["total_errors"] == 0

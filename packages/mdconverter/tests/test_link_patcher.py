"""
Tests for LinkPatcher deep module interface and relative link patching in mdconverter.
"""

from pathlib import Path
import pytest
from mdconverter.core.link_patcher import LinkPatcher


def test_link_patcher_content_text_and_images():
    patcher = LinkPatcher()
    content = """# Document

Refer to [Appendix 1](appendices/phu_luc_01.md) and see image below:
![Diagram](appendices/images/chart.png)

Existing correct links:
[Correct Link 1](./appendices/valid.md)
[Correct Link 2](../appendices/valid.md)
"""

    patched, count = patcher.patch_content(content)
    assert count == 2
    assert "[Appendix 1](./appendices/phu_luc_01.md)" in patched
    assert "![Diagram](./appendices/images/chart.png)" in patched
    assert "[Correct Link 1](./appendices/valid.md)" in patched
    assert "[Correct Link 2](../appendices/valid.md)" in patched


def test_link_patcher_no_changes():
    patcher = LinkPatcher()
    content = """# Clean Document

[Valid Link](./appendices/doc.md)
"""
    patched, count = patcher.patch_content(content)
    assert count == 0
    assert patched == content


def test_link_patcher_file_and_directory(tmp_path: Path):
    doc_path = tmp_path / "main.md"
    doc_path.write_text("See [Phu Luc](appendices/phu_luc.md)", encoding="utf-8")

    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()
    sub_doc = sub_dir / "sub_main.md"
    sub_doc.write_text("See image ![Fig](appendices/fig.png)", encoding="utf-8")

    patcher = LinkPatcher()
    modified = patcher.patch_links(tmp_path)

    assert len(modified) == 2
    assert doc_path in modified
    assert sub_doc in modified

    assert "[Phu Luc](./appendices/phu_luc.md)" in doc_path.read_text(encoding="utf-8")
    assert "![Fig](./appendices/fig.png)" in sub_doc.read_text(encoding="utf-8")

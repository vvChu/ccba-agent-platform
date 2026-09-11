"""Unit tests verifying DOCX DOM cleanup, runs merging, and redlines simplification."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ccba_ooxml.docx import (
    clone_xml_text,
    get_tracked_change_authors,
    merge_runs,
    simplify_redlines,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


@pytest.fixture
def temp_unpacked_docx():
    """Create a temporary unpacked docx folder structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        word_dir = temp_path / "word"
        word_dir.mkdir(parents=True)
        yield temp_path


def test_merge_runs_identical_formatting(temp_unpacked_docx: Path):
    """Test merging adjacent runs with identical formatting."""
    doc_xml = temp_unpacked_docx / "word" / "document.xml"
    xml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p>"
        "<w:r><w:rPr><w:b/></w:rPr><w:t>Hello </w:t></w:r>"
        "<w:r><w:rPr><w:b/></w:rPr><w:t>World</w:t></w:r>"
        "</w:p>"
        "</w:body>"
        "</w:document>"
    )
    doc_xml.write_text(xml_content, encoding="utf-8")

    count, msg = merge_runs(temp_unpacked_docx)
    assert count == 1
    assert "Merged 1 runs" in msg

    result_xml = doc_xml.read_text(encoding="utf-8")
    assert "Hello World" in result_xml


def test_merge_runs_different_formatting(temp_unpacked_docx: Path):
    """Test that runs with different formatting are not merged."""
    doc_xml = temp_unpacked_docx / "word" / "document.xml"
    xml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p>"
        "<w:r><w:rPr><w:b/></w:rPr><w:t>Bold</w:t></w:r>"
        "<w:r><w:rPr><w:i/></w:rPr><w:t>Italic</w:t></w:r>"
        "</w:p>"
        "</w:body>"
        "</w:document>"
    )
    doc_xml.write_text(xml_content, encoding="utf-8")

    count, msg = merge_runs(temp_unpacked_docx)
    assert count == 0
    assert "Merged 0 runs" in msg


def test_merge_runs_missing_dir():
    """Test merge_runs error on missing word/document.xml."""
    count, msg = merge_runs("non_existent_directory_xyz")
    assert count == 0
    assert "Error" in msg


def test_simplify_redlines_same_author(temp_unpacked_docx: Path):
    """Test merging adjacent tracked insertions from the same author."""
    doc_xml = temp_unpacked_docx / "word" / "document.xml"
    xml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p>"
        '<w:ins w:id="1" w:author="Alice" w:date="2026-01-01T00:00:00Z">'
        "<w:r><w:t>Part 1 </w:t></w:r>"
        "</w:ins>"
        '<w:ins w:id="2" w:author="Alice" w:date="2026-01-01T00:00:00Z">'
        "<w:r><w:t>Part 2</w:t></w:r>"
        "</w:ins>"
        "</w:p>"
        "</w:body>"
        "</w:document>"
    )
    doc_xml.write_text(xml_content, encoding="utf-8")

    count, msg = simplify_redlines(temp_unpacked_docx)
    assert count == 1
    assert "Simplified 1 tracked changes" in msg

    authors = get_tracked_change_authors(doc_xml)
    assert authors.get("Alice") == 1


def test_simplify_redlines_different_authors(temp_unpacked_docx: Path):
    """Test that redlines from different authors are not merged."""
    doc_xml = temp_unpacked_docx / "word" / "document.xml"
    xml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p>"
        '<w:ins w:id="1" w:author="Alice" w:date="2026-01-01T00:00:00Z">'
        "<w:r><w:t>By Alice</w:t></w:r>"
        "</w:ins>"
        '<w:ins w:id="2" w:author="Bob" w:date="2026-01-01T00:00:00Z">'
        "<w:r><w:t>By Bob</w:t></w:r>"
        "</w:ins>"
        "</w:p>"
        "</w:body>"
        "</w:document>"
    )
    doc_xml.write_text(xml_content, encoding="utf-8")

    count, msg = simplify_redlines(temp_unpacked_docx)
    assert count == 0


def test_clone_xml_text(temp_unpacked_docx: Path):
    """Test clone_xml_text keyword replacement."""
    doc_xml = temp_unpacked_docx / "word" / "document.xml"
    doc_xml.write_text("<w:t>{{PROJECT_NAME}} is {{STATUS}}</w:t>", encoding="utf-8")

    map_file = temp_unpacked_docx / "map.json"
    map_file.write_text(
        json.dumps({"{{PROJECT_NAME}}": "Skyline Tower", "{{STATUS}}": "Active"}),
        encoding="utf-8",
    )

    changes = clone_xml_text(doc_xml, map_file)
    assert changes == 2

    content = doc_xml.read_text(encoding="utf-8")
    assert "Skyline Tower is Active" in content


def test_clone_xml_text_missing_file():
    """Test clone_xml_text error handling for missing files."""
    with pytest.raises(FileNotFoundError):
        clone_xml_text("missing.xml", "missing.json")

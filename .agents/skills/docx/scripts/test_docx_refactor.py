"""Unit tests verifying Document comments and tracked changes refactoring."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from .document import Document


@pytest.fixture
def mock_unpacked_docx():
    """Create a temporary unpacked docx folder layout with minimal templates."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        word_dir = temp_path / "word"
        word_dir.mkdir(parents=True)
        rels_dir = word_dir / "_rels"
        rels_dir.mkdir()

        # Create templates directory mock for peoples/comments Extended templates
        templates_dir = Path(__file__).parent / "templates"
        templates_dir.mkdir(exist_ok=True)

        # Ensure people.xml template exists
        people_tpl = templates_dir / "people.xml"
        if not people_tpl.exists():
            people_tpl.write_text(
                '<?xml version="1.0" encoding="UTF-8"?><w15:people xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml"></w15:people>',
                encoding="utf-8",
            )

        comments_tpl = templates_dir / "comments.xml"
        if not comments_tpl.exists():
            comments_tpl.write_text(
                '<?xml version="1.0" encoding="UTF-8"?><w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"></w:comments>',
                encoding="utf-8",
            )

        # Create minimal required XMLs in the unpacked directory
        (temp_path / "[Content_Types].xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>',
            encoding="utf-8",
        )
        (rels_dir / "document.xml.rels").write_text(
            '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>',
            encoding="utf-8",
        )
        (word_dir / "settings.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?><w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"></w:settings>',
            encoding="utf-8",
        )
        (word_dir / "document.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"><body><w:p w14:paraId="11111111"><w:r><w:t>Hello World</w:t></w:r></w:p></body></w:document>',
            encoding="utf-8",
        )

        yield temp_path


def test_document_commenting(mock_unpacked_docx):
    """Test creating a comment and verifying XML file structures are registered."""
    doc = Document(mock_unpacked_docx, rsid="00FF00FF", author="TestAuthor", initials="TA")

    # Get nodes
    doc["word/document.xml"].get_node(tag="w:p")
    run = doc["word/document.xml"].get_node(tag="w:r")

    # Add comment
    comment_id = doc.add_comment(start=run, end=run, text="Fix this word")
    assert comment_id == 0

    # Ensure document.xml contains comment range start/end and reference
    doc_xml_content = doc["word/document.xml"].dom.toxml()
    assert "commentRangeStart" in doc_xml_content
    assert "commentRangeEnd" in doc_xml_content
    assert "commentReference" in doc_xml_content

    # Ensure comments.xml contains the text
    comments_xml_content = doc["word/comments.xml"].dom.toxml()
    assert "Fix this word" in comments_xml_content
    assert 'w:author="TestAuthor"' in comments_xml_content

    # Ensure people.xml exists
    people_xml_content = doc["word/people.xml"].dom.toxml()
    assert 'w15:author="TestAuthor"' in people_xml_content


def test_tracked_changes_deletion(mock_unpacked_docx):
    """Test suggesting deletions and rejecting insertions."""
    doc = Document(mock_unpacked_docx, rsid="00FF00FF")

    run = doc["word/document.xml"].get_node(tag="w:r")

    # Suggest deletion
    del_node = doc["word/document.xml"].suggest_deletion(run)
    assert del_node.tagName == "w:del"

    doc_xml_content = doc["word/document.xml"].dom.toxml()
    assert "<w:del" in doc_xml_content
    assert "delText" in doc_xml_content  # w:t converted to w:delText

"""Tests for Docx DOM manipulation, tracking, and comment engine."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import pytest

from ccba_ooxml import OOXMLWorkspace
from ccba_ooxml.docx import (
    DocxDocument,
    XMLEditor,
    revert_deletion,
    revert_insertion,
)


@pytest.fixture
def minimal_docx_tree() -> tempfile.TemporaryDirectory[str]:
    tmp = tempfile.TemporaryDirectory(prefix="test_docx_tree_")
    root = Path(tmp.name)

    (root / "word").mkdir(parents=True, exist_ok=True)
    (root / "word" / "_rels").mkdir(parents=True, exist_ok=True)

    # [Content_Types].xml
    (root / "[Content_Types].xml").write_text(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
        "</Types>",
        encoding="utf-8",
    )

    # word/_rels/document.xml.rels
    (root / "word" / "_rels" / "document.xml.rels").write_text(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        "</Relationships>",
        encoding="utf-8",
    )

    # word/settings.xml
    (root / "word" / "settings.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        "</w:settings>",
        encoding="utf-8",
    )

    # word/document.xml
    (root / "word" / "document.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        "  <w:body>\n"
        '    <w:p w:rsidR="00112233">\n'
        "      <w:r>\n"
        "        <w:t>Hello World</w:t>\n"
        "      </w:r>\n"
        "    </w:p>\n"
        "  </w:body>\n"
        "</w:document>",
        encoding="utf-8",
    )

    return tmp


def test_xml_editor_line_tracking_and_node_lookup(
    minimal_docx_tree: tempfile.TemporaryDirectory[str],
) -> None:
    doc_path = Path(minimal_docx_tree.name) / "word" / "document.xml"
    editor = XMLEditor(doc_path)

    # Test get_node with contains
    node = editor.get_node("w:r", contains="Hello World")
    assert node is not None
    assert editor._get_element_text(node) == "Hello World"

    # Test replace_node
    editor.replace_node(node, "<w:r><w:t>Hello CCBA</w:t></w:r>")
    editor.save()

    # Re-read
    editor2 = XMLEditor(doc_path)
    node2 = editor2.get_node("w:r", contains="Hello CCBA")
    assert node2 is not None


def test_docx_document_add_comment(minimal_docx_tree: tempfile.TemporaryDirectory[str]) -> None:
    doc = DocxDocument(
        minimal_docx_tree.name,
        author="Auditor",
        initials="AU",
        in_place=True,
    )

    p_elem = doc["word/document.xml"].get_node("w:p")
    comment_id = doc.add_comment(p_elem, p_elem, "Please review this clause.")
    assert comment_id == 0

    doc.save()

    # Verify comments file was created
    comments_file = Path(minimal_docx_tree.name) / "word" / "comments.xml"
    assert comments_file.exists()
    content = comments_file.read_text(encoding="utf-8")
    assert "Please review this clause." in content
    assert 'w:author="Auditor"' in content


def test_docx_document_reply_comment(minimal_docx_tree: tempfile.TemporaryDirectory[str]) -> None:
    doc = DocxDocument(
        minimal_docx_tree.name,
        author="Auditor",
        initials="AU",
        in_place=True,
    )

    p_elem = doc["word/document.xml"].get_node("w:p")
    cid = doc.add_comment(p_elem, p_elem, "Initial note")
    reply_id = doc.reply_to_comment(cid, "Confirmed and accepted.")
    assert reply_id == 1

    doc.save()
    content = (Path(minimal_docx_tree.name) / "word" / "comments.xml").read_text(encoding="utf-8")
    assert "Confirmed and accepted." in content


def test_change_engine_suggest_deletion_and_paragraph(
    minimal_docx_tree: tempfile.TemporaryDirectory[str],
) -> None:
    doc = DocxDocument(
        minimal_docx_tree.name,
        author="Reviewer",
        in_place=True,
    )
    editor = doc["word/document.xml"]
    r_elem = editor.get_node("w:r", contains="Hello World")

    del_node = editor.suggest_deletion(r_elem)
    assert del_node.tagName == "w:del"

    # Test suggest_paragraph
    new_p_xml = "<w:p><w:r><w:t>New Paragraph</w:t></w:r></w:p>"
    tracked_p_xml = editor.suggest_paragraph(new_p_xml)
    assert "<w:ins>" in tracked_p_xml


def test_change_engine_revert_operations(
    minimal_docx_tree: tempfile.TemporaryDirectory[str],
) -> None:
    doc = DocxDocument(minimal_docx_tree.name, author="Reviewer", in_place=True)
    editor = doc["word/document.xml"]

    # Insert an ins element
    p_elem = editor.get_node("w:p")
    ins_nodes = editor.append_to(
        p_elem, '<w:ins w:id="99"><w:r><w:t>Added Text</w:t></w:r></w:ins>'
    )
    ins_node = ins_nodes[0]

    # Revert insertion
    reverted_nodes = revert_insertion(editor, ins_node)
    assert len(reverted_nodes) > 0
    assert len(editor.dom.getElementsByTagName("w:del")) > 0

    # Test revert deletion
    del_elem = editor.dom.getElementsByTagName("w:del")[0]
    revert_res = revert_deletion(editor, del_elem)
    assert len(revert_res) > 0


def test_workspace_get_docx_document_in_place() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        docx_file = temp_path / "test.docx"

        # Create zip
        with zipfile.ZipFile(docx_file, "w") as zf:
            zf.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
                '  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
                "</Types>",
            )
            zf.writestr(
                "word/document.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
                "  <w:body>\n"
                '    <w:p w:rsidR="00112233">\n'
                "      <w:r><w:t>Sample Text</w:t></w:r>\n"
                "    </w:p>\n"
                "  </w:body>\n"
                "</w:document>",
            )
            zf.writestr(
                "word/_rels/document.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                "</Relationships>",
            )
            zf.writestr(
                "word/settings.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
                "</w:settings>",
            )

        with OOXMLWorkspace(docx_file, validate=False) as ws:
            docx_doc = ws.get_docx_document(author="AI Architect", initials="AA")
            p = docx_doc["word/document.xml"].get_node("w:p")
            docx_doc.add_comment(p, p, "In-place workspace comment")
            docx_doc.save()

        # Check repacked zip contains comment
        with zipfile.ZipFile(docx_file) as zf:
            assert "word/comments.xml" in zf.namelist()
            comments_content = zf.read("word/comments.xml").decode("utf-8")
            assert "In-place workspace comment" in comments_content
            assert 'w:author="AI Architect"' in comments_content

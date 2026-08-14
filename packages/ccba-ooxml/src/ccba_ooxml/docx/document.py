"""Library for working with Word documents: comments, tracked changes, and DOM editing."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ccba_ooxml.pack import pack_document
from ccba_ooxml.validation import OOXMLValidator

from .comment_engine import CommentEngine
from .utilities import XMLEditor, _generate_hex_id, _generate_rsid

if TYPE_CHECKING:
    from xml.dom.minidom import Element


class DocxXMLEditor(XMLEditor):
    """XMLEditor that automatically applies RSID, author, and date to new elements."""

    def __init__(
        self, xml_path: str | Path, rsid: str, author: str = "Claude", initials: str = "C"
    ) -> None:
        super().__init__(xml_path)
        self.rsid = rsid
        self.author = author
        self.initials = initials

    def _get_next_change_id(self) -> int:
        """Get the next available change ID by checking all tracked change elements."""
        max_id = -1
        for tag in ("w:ins", "w:del"):
            elements = self.dom.getElementsByTagName(tag)
            for elem in elements:
                change_id = elem.getAttribute("w:id")
                if change_id:
                    try:
                        max_id = max(max_id, int(change_id))
                    except ValueError:
                        pass
        return max_id + 1

    def _ensure_w16du_namespace(self) -> None:
        """Ensure w16du namespace is declared on the root element."""
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w16du"):
            root.setAttribute(
                "xmlns:w16du",
                "http://schemas.microsoft.com/office/word/2023/wordml/word16du",
            )

    def _ensure_w16cex_namespace(self) -> None:
        """Ensure w16cex namespace is declared on the root element."""
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w16cex"):
            root.setAttribute(
                "xmlns:w16cex",
                "http://schemas.microsoft.com/office/word/2018/wordml/cex",
            )

    def _ensure_w14_namespace(self) -> None:
        """Ensure w14 namespace is declared on the root element."""
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w14"):
            root.setAttribute(
                "xmlns:w14",
                "http://schemas.microsoft.com/office/word/2010/wordml",
            )

    def _inject_attributes_to_nodes(self, nodes: list[Element]) -> None:
        """Inject RSID, author, and date attributes into DOM nodes where applicable."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        def is_inside_deletion(elem: Any) -> bool:
            parent = elem.parentNode
            while parent:
                if parent.nodeType == parent.ELEMENT_NODE and parent.tagName == "w:del":
                    return True
                parent = parent.parentNode
            return False

        def add_rsid_to_p(elem: Any) -> None:
            if not elem.hasAttribute("w:rsidR"):
                elem.setAttribute("w:rsidR", self.rsid)
            if not elem.hasAttribute("w:rsidRDefault"):
                elem.setAttribute("w:rsidRDefault", self.rsid)
            if not elem.hasAttribute("w:rsidP"):
                elem.setAttribute("w:rsidP", self.rsid)
            if not elem.hasAttribute("w14:paraId"):
                self._ensure_w14_namespace()
                elem.setAttribute("w14:paraId", _generate_hex_id())
            if not elem.hasAttribute("w14:textId"):
                self._ensure_w14_namespace()
                elem.setAttribute("w14:textId", _generate_hex_id())

        def add_rsid_to_r(elem: Any) -> None:
            if is_inside_deletion(elem):
                if not elem.hasAttribute("w:rsidDel"):
                    elem.setAttribute("w:rsidDel", self.rsid)
            else:
                if not elem.hasAttribute("w:rsidR"):
                    elem.setAttribute("w:rsidR", self.rsid)

        def add_tracked_change_attrs(elem: Any) -> None:
            if not elem.hasAttribute("w:id"):
                elem.setAttribute("w:id", str(self._get_next_change_id()))
            if not elem.hasAttribute("w:author"):
                elem.setAttribute("w:author", self.author)
            if not elem.hasAttribute("w:date"):
                elem.setAttribute("w:date", timestamp)
            if elem.tagName in ("w:ins", "w:del") and not elem.hasAttribute("w16du:dateUtc"):
                self._ensure_w16du_namespace()
                elem.setAttribute("w16du:dateUtc", timestamp)

        def add_comment_attrs(elem: Any) -> None:
            if not elem.hasAttribute("w:author"):
                elem.setAttribute("w:author", self.author)
            if not elem.hasAttribute("w:date"):
                elem.setAttribute("w:date", timestamp)
            if not elem.hasAttribute("w:initials"):
                elem.setAttribute("w:initials", self.initials)

        def add_comment_extensible_date(elem: Any) -> None:
            if not elem.hasAttribute("w16cex:dateUtc"):
                self._ensure_w16cex_namespace()
                elem.setAttribute("w16cex:dateUtc", timestamp)

        def add_xml_space_to_t(elem: Any) -> None:
            if elem.firstChild and elem.firstChild.nodeType == elem.firstChild.TEXT_NODE:
                text = elem.firstChild.data
                if text and (text[0].isspace() or text[-1].isspace()):
                    if not elem.hasAttribute("xml:space"):
                        elem.setAttribute("xml:space", "preserve")

        for node in nodes:
            if node.nodeType != node.ELEMENT_NODE:
                continue

            if node.tagName == "w:p":
                add_rsid_to_p(node)
            elif node.tagName == "w:r":
                add_rsid_to_r(node)
            elif node.tagName == "w:t":
                add_xml_space_to_t(node)
            elif node.tagName in ("w:ins", "w:del"):
                add_tracked_change_attrs(node)
            elif node.tagName == "w:comment":
                add_comment_attrs(node)
            elif node.tagName == "w16cex:commentExtensible":
                add_comment_extensible_date(node)

            for elem in node.getElementsByTagName("w:p"):
                add_rsid_to_p(elem)
            for elem in node.getElementsByTagName("w:r"):
                add_rsid_to_r(elem)
            for elem in node.getElementsByTagName("w:t"):
                add_xml_space_to_t(elem)
            for tag in ("w:ins", "w:del"):
                for elem in node.getElementsByTagName(tag):
                    add_tracked_change_attrs(elem)
            for elem in node.getElementsByTagName("w:comment"):
                add_comment_attrs(elem)
            for elem in node.getElementsByTagName("w16cex:commentExtensible"):
                add_comment_extensible_date(elem)

    def replace_node(self, elem: Element, new_content: str) -> list[Element]:
        nodes = super().replace_node(elem, new_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def insert_after(self, elem: Element, xml_content: str) -> list[Element]:
        nodes = super().insert_after(elem, xml_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def insert_before(self, elem: Element, xml_content: str) -> list[Element]:
        nodes = super().insert_before(elem, xml_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def append_to(self, elem: Element, xml_content: str) -> list[Element]:
        nodes = super().append_to(elem, xml_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def revert_insertion(self, elem: Element) -> list[Element]:
        """Reject an insertion by wrapping its content in a deletion."""
        from .change_engine import revert_insertion

        return revert_insertion(self, elem)

    def revert_deletion(self, elem: Element) -> list[Element]:
        """Reject a deletion by re-inserting the deleted content."""
        from .change_engine import revert_deletion

        return revert_deletion(self, elem)

    @staticmethod
    def suggest_paragraph(xml_content: str) -> str:
        """Transform paragraph XML to add tracked change wrapping for insertion."""
        from .change_engine import suggest_paragraph

        return suggest_paragraph(xml_content)

    def suggest_deletion(self, elem: Element) -> Element:
        """Mark a w:r or w:p element as deleted with tracked changes."""
        from .change_engine import suggest_deletion

        return suggest_deletion(self, elem)


class DocxDocument:
    """Manages comments and tracked changes in Word OOXML documents."""

    def __init__(
        self,
        unpacked_dir: str | Path,
        rsid: str | None = None,
        track_revisions: bool = False,
        author: str = "Claude",
        initials: str = "C",
        in_place: bool = False,
    ) -> None:
        self.original_path = Path(unpacked_dir)
        self.in_place = in_place

        if not self.original_path.exists() or not self.original_path.is_dir():
            raise ValueError(f"Directory not found: {unpacked_dir}")

        if self.in_place:
            self.temp_dir = None
            self.unpacked_path = self.original_path
            self.original_docx = None
        else:
            self.temp_dir = tempfile.mkdtemp(prefix="docx_")
            self.unpacked_path = Path(self.temp_dir) / "unpacked"
            shutil.copytree(self.original_path, self.unpacked_path)
            self.original_docx = Path(self.temp_dir) / "original.docx"
            pack_document(self.original_path, self.original_docx, validate=False)

        self.word_path = self.unpacked_path / "word"
        self.rsid = rsid if rsid else _generate_rsid()

        self.author = author
        self.initials = initials
        self.track_revisions_flag = track_revisions

        self._editors: dict[str, DocxXMLEditor] = {}

        # Comment paths
        self.comments_path = self.word_path / "comments.xml"
        self.comments_extended_path = self.word_path / "commentsExtended.xml"
        self.comments_ids_path = self.word_path / "commentsIds.xml"
        self.comments_extensible_path = self.word_path / "commentsExtensible.xml"

        # Delegate comment setup to CommentEngine
        self.comment_engine = CommentEngine(self)

    def __getitem__(self, xml_path: str) -> DocxXMLEditor:
        if xml_path not in self._editors:
            file_path = self.unpacked_path / xml_path
            if not file_path.exists():
                raise ValueError(f"XML file not found: {xml_path}")
            self._editors[xml_path] = DocxXMLEditor(
                file_path, rsid=self.rsid, author=self.author, initials=self.initials
            )
        return self._editors[xml_path]

    def add_comment(self, start: Element, end: Element, text: str) -> int:
        """Add a comment spanning from start to end elements."""
        return self.comment_engine.add_comment(start, end, text)

    def reply_to_comment(self, parent_comment_id: int, text: str) -> int:
        """Add a reply to an existing comment."""
        return self.comment_engine.reply_to_comment(parent_comment_id, text)

    def __del__(self) -> None:
        if getattr(self, "temp_dir", None) and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def validate(self) -> None:
        """Validate the document against XSD schema and redlining rules."""
        if self.original_docx and self.original_docx.exists():
            validator = OOXMLValidator(self.unpacked_path, self.original_docx, verbose=False)
            if not validator.validate():
                raise ValueError("Document validation failed")

    def save(self, destination: str | Path | None = None, validate: bool = True) -> None:
        """Save all modified XML files to disk and copy to destination directory."""
        if self.comments_path.exists():
            self.comment_engine._ensure_comment_relationships()
            self.comment_engine._ensure_comment_content_types()

        for editor in self._editors.values():
            editor.save()

        if validate and not self.in_place:
            self.validate()

        if destination:
            target_path = Path(destination)
            if target_path != self.unpacked_path:
                shutil.copytree(self.unpacked_path, target_path, dirs_exist_ok=True)
        elif not self.in_place:
            shutil.copytree(self.unpacked_path, self.original_path, dirs_exist_ok=True)

    def _has_relationship(self, editor: DocxXMLEditor, target: str) -> bool:
        for rel_elem in editor.dom.getElementsByTagName("Relationship"):
            if rel_elem.getAttribute("Target") == target:
                return True
        return False

    def _has_override(self, editor: DocxXMLEditor, part_name: str) -> bool:
        for override_elem in editor.dom.getElementsByTagName("Override"):
            if override_elem.getAttribute("PartName") == part_name:
                return True
        return False


# Alias Document to DocxDocument for backward compatibility
Document = DocxDocument

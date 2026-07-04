"""Comment engine for managing Word document comments."""

from __future__ import annotations

import html
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from .utilities import _generate_hex_id

if TYPE_CHECKING:
    from xml.dom.minidom import Element

    from .document import Document, DocxXMLEditor

TEMPLATE_DIR = Path(__file__).parent / "templates"
REGISTRY_FILE = Path(".md/data/notebook_registry.yaml")  # dummy config path if needed


class CommentEngine:
    """Handles XML modifications for docx comments, people registry, and settings."""

    def __init__(self, doc: Document):
        """Initialize with parent Document.

        Args:
            doc: The Document instance to manage comments on.
        """
        self.doc = doc
        self.word_path = doc.word_path
        self.comments_path = doc.comments_path
        self.comments_extended_path = doc.comments_extended_path
        self.comments_ids_path = doc.comments_ids_path
        self.comments_extensible_path = doc.comments_extensible_path

        # Initialise registry and ID counters
        self.existing_comments = self._load_existing_comments()
        self.next_comment_id = self._get_next_comment_id()

        # Setup tracking infrastructure and people
        self._setup_tracking(track_revisions=doc.track_revisions_flag)
        self._add_author_to_people(doc.author)

    @property
    def _document(self) -> DocxXMLEditor:
        return self.doc["word/document.xml"]

    def add_comment(self, start: Element, end: Element, text: str) -> int:
        """Add a comment spanning from start to end elements."""
        comment_id = self.next_comment_id
        para_id = _generate_hex_id()
        durable_id = _generate_hex_id()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Insert comment markup in document.xml
        self._document.insert_before(start, self._comment_range_start_xml(comment_id))

        if end.tagName == "w:p":
            self._document.append_to(end, self._comment_range_end_xml(comment_id))
        else:
            self._document.insert_after(end, self._comment_range_end_xml(comment_id))

        # Update comments XMLs
        self._add_to_comments_xml(
            comment_id, para_id, text, self.doc.author, self.doc.initials, timestamp
        )
        self._add_to_comments_extended_xml(para_id, parent_para_id=None)
        self._add_to_comments_ids_xml(para_id, durable_id)
        self._add_to_comments_extensible_xml(durable_id)

        # Update local cache
        self.existing_comments[comment_id] = {"para_id": para_id}
        self.next_comment_id += 1

        return comment_id

    def reply_to_comment(self, parent_comment_id: int, text: str) -> int:
        """Add a reply to an existing comment."""
        if parent_comment_id not in self.existing_comments:
            raise ValueError(f"Parent comment with id={parent_comment_id} not found")

        parent_info = self.existing_comments[parent_comment_id]
        comment_id = self.next_comment_id
        para_id = _generate_hex_id()
        durable_id = _generate_hex_id()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        parent_start_elem = self._document.get_node(
            tag="w:commentRangeStart", attrs={"w:id": str(parent_comment_id)}
        )
        parent_ref_elem = self._document.get_node(
            tag="w:commentReference", attrs={"w:id": str(parent_comment_id)}
        )

        self._document.insert_after(parent_start_elem, self._comment_range_start_xml(comment_id))
        parent_ref_run = parent_ref_elem.parentNode
        self._document.insert_after(parent_ref_run, f'<w:commentRangeEnd w:id="{comment_id}"/>')
        self._document.insert_after(parent_ref_run, self._comment_ref_run_xml(comment_id))

        self._add_to_comments_xml(
            comment_id, para_id, text, self.doc.author, self.doc.initials, timestamp
        )
        self._add_to_comments_extended_xml(para_id, parent_para_id=parent_info["para_id"])
        self._add_to_comments_ids_xml(para_id, durable_id)
        self._add_to_comments_extensible_xml(durable_id)

        self.existing_comments[comment_id] = {"para_id": para_id}
        self.next_comment_id += 1

        return comment_id

    # ==================== Private: Initialization ====================

    def _get_next_comment_id(self) -> int:
        """Get the next available comment ID."""
        if not self.comments_path.exists():
            return 0

        editor = self.doc["word/comments.xml"]
        max_id = -1
        for comment_elem in editor.dom.getElementsByTagName("w:comment"):
            comment_id = comment_elem.getAttribute("w:id")
            if comment_id:
                try:
                    max_id = max(max_id, int(comment_id))
                except ValueError:
                    pass
        return max_id + 1

    def _load_existing_comments(self) -> dict[int, dict[str, str]]:
        """Load existing comments from files to enable replies."""
        if not self.comments_path.exists():
            return {}

        editor = self.doc["word/comments.xml"]
        existing = {}

        for comment_elem in editor.dom.getElementsByTagName("w:comment"):
            comment_id = comment_elem.getAttribute("w:id")
            if not comment_id:
                continue

            para_id = None
            for p_elem in comment_elem.getElementsByTagName("w:p"):
                para_id = p_elem.getAttribute("w14:paraId")
                if para_id:
                    break

            if not para_id:
                continue

            existing[int(comment_id)] = {"para_id": para_id}

        return existing

    # ==================== Private: Setup Methods ====================

    def _setup_tracking(self, track_revisions: bool = False) -> None:
        """Set up comment infrastructure in unpacked directory."""
        people_file = self.word_path / "people.xml"
        self._update_people_xml(people_file)

        self._add_content_type_for_people()
        self._add_relationship_for_people()

        self._update_settings(self.word_path / "settings.xml", track_revisions=track_revisions)

    def _update_people_xml(self, path: Path) -> None:
        """Create people.xml if it doesn't exist."""
        if not path.exists():
            shutil.copy(TEMPLATE_DIR / "people.xml", path)

    def _add_content_type_for_people(self) -> None:
        """Add people.xml content type to [Content_Types].xml."""
        editor = self.doc["[Content_Types].xml"]

        if self.doc._has_override(editor, "/word/people.xml"):
            return

        root = editor.dom.documentElement
        override_xml = '<Override PartName="/word/people.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.people+xml"/>'
        editor.append_to(root, override_xml)

    def _add_relationship_for_people(self) -> None:
        """Add people.xml relationship to document.xml.rels."""
        editor = self.doc["word/_rels/document.xml.rels"]

        if self.doc._has_relationship(editor, "people.xml"):
            return

        root = editor.dom.documentElement
        root_tag = root.tagName  # type: ignore
        prefix = root_tag.split(":")[0] + ":" if ":" in root_tag else ""
        next_rid = editor.get_next_rid()

        rel_xml = f'<{prefix}Relationship Id="{next_rid}" Type="http://schemas.microsoft.com/office/2011/relationships/people" Target="people.xml"/>'
        editor.append_to(root, rel_xml)

    def _update_settings(self, path: Path, track_revisions: bool = False) -> None:
        """Add RSID and optionally enable track revisions in settings.xml."""
        editor = self.doc["word/settings.xml"]
        root = editor.get_node(tag="w:settings")
        prefix = root.tagName.split(":")[0] if ":" in root.tagName else "w"

        if track_revisions:
            track_revisions_exists = any(
                elem.tagName == f"{prefix}:trackRevisions"
                for elem in editor.dom.getElementsByTagName(f"{prefix}:trackRevisions")
            )

            if not track_revisions_exists:
                track_rev_xml = f"<{prefix}:trackRevisions/>"
                inserted = False
                for tag in [f"{prefix}:documentProtection", f"{prefix}:defaultTabStop"]:
                    elements = editor.dom.getElementsByTagName(tag)
                    if elements:
                        editor.insert_before(elements[0], track_rev_xml)
                        inserted = True
                        break
                if not inserted:
                    if root.firstChild:
                        editor.insert_before(root.firstChild, track_rev_xml)
                    else:
                        editor.append_to(root, track_rev_xml)

        rsids_elements = editor.dom.getElementsByTagName(f"{prefix}:rsids")

        if not rsids_elements:
            rsids_xml = f'''<{prefix}:rsids>
  <{prefix}:rsidRoot {prefix}:val="{self.doc.rsid}"/>
  <{prefix}:rsid {prefix}:val="{self.doc.rsid}"/>
</{prefix}:rsids>'''

            inserted = False
            compat_elements = editor.dom.getElementsByTagName(f"{prefix}:compat")
            if compat_elements:
                editor.insert_after(compat_elements[0], rsids_xml)
                inserted = True

            if not inserted:
                clr_elements = editor.dom.getElementsByTagName(f"{prefix}:clrSchemeMapping")
                if clr_elements:
                    editor.insert_before(clr_elements[0], rsids_xml)
                    inserted = True

            if not inserted:
                editor.append_to(root, rsids_xml)
        else:
            rsids_elem = rsids_elements[0]
            rsid_exists = any(
                elem.getAttribute(f"{prefix}:val") == self.doc.rsid
                for elem in rsids_elem.getElementsByTagName(f"{prefix}:rsid")
            )

            if not rsid_exists:
                rsid_xml = f'<{prefix}:rsid {prefix}:val="{self.doc.rsid}"/>'
                editor.append_to(rsids_elem, rsid_xml)

    # ==================== Private: XML File Creation ====================

    def _add_to_comments_xml(
        self, comment_id: int, para_id: str, text: str, author: str, initials: str, timestamp: str
    ) -> None:
        """Add a single comment to comments.xml."""
        if not self.comments_path.exists():
            shutil.copy(TEMPLATE_DIR / "comments.xml", self.comments_path)

        editor = self.doc["word/comments.xml"]
        root = editor.get_node(tag="w:comments")

        escaped_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        comment_xml = f'''<w:comment w:id="{comment_id}">
  <w:p w14:paraId="{para_id}" w14:textId="77777777">
    <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:annotationRef/></w:r>
    <w:r><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>{escaped_text}</w:t></w:r>
  </w:p>
</w:comment>'''
        editor.append_to(root, comment_xml)

    def _add_to_comments_extended_xml(self, para_id: str, parent_para_id: str | None) -> None:
        """Add a single comment to commentsExtended.xml."""
        if not self.comments_extended_path.exists():
            shutil.copy(TEMPLATE_DIR / "commentsExtended.xml", self.comments_extended_path)

        editor = self.doc["word/commentsExtended.xml"]
        root = editor.get_node(tag="w15:commentsEx")

        if parent_para_id:
            xml = f'<w15:commentEx w15:paraId="{para_id}" w15:paraIdParent="{parent_para_id}" w15:done="0"/>'
        else:
            xml = f'<w15:commentEx w15:paraId="{para_id}" w15:done="0"/>'
        editor.append_to(root, xml)

    def _add_to_comments_ids_xml(self, para_id: str, durable_id: str) -> None:
        """Add a single comment to commentsIds.xml."""
        if not self.comments_ids_path.exists():
            shutil.copy(TEMPLATE_DIR / "commentsIds.xml", self.comments_ids_path)

        editor = self.doc["word/commentsIds.xml"]
        root = editor.get_node(tag="w16cid:commentsIds")

        xml = f'<w16cid:commentId w16cid:paraId="{para_id}" w16cid:durableId="{durable_id}"/>'
        editor.append_to(root, xml)

    def _add_to_comments_extensible_xml(self, durable_id: str) -> None:
        """Add a single comment to commentsExtensible.xml."""
        if not self.comments_extensible_path.exists():
            shutil.copy(TEMPLATE_DIR / "commentsExtensible.xml", self.comments_extensible_path)

        editor = self.doc["word/commentsExtensible.xml"]
        root = editor.get_node(tag="w16cex:commentsExtensible")

        xml = f'<w16cex:commentExtensible w16cex:durableId="{durable_id}"/>'
        editor.append_to(root, xml)

    # ==================== Private: XML Fragments ====================

    def _comment_range_start_xml(self, comment_id: int) -> str:
        """Generate XML for comment range start."""
        return f'<w:commentRangeStart w:id="{comment_id}"/>'

    def _comment_range_end_xml(self, comment_id: int) -> str:
        """Generate XML for comment range end with reference run."""
        return f'''<w:commentRangeEnd w:id="{comment_id}"/>
<w:r>
  <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
  <w:commentReference w:id="{comment_id}"/>
</w:r>'''

    def _comment_ref_run_xml(self, comment_id: int) -> str:
        """Generate XML for comment reference run."""
        return f'''<w:r>
  <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
  <w:commentReference w:id="{comment_id}"/>
</w:r>'''

    # ==================== Private: People Registration ====================

    def _add_author_to_people(self, author: str) -> None:
        """Add author to people.xml."""
        people_path = self.word_path / "people.xml"

        if not people_path.exists():
            raise ValueError("people.xml should exist after _setup_tracking")

        editor = self.doc["word/people.xml"]
        root = editor.get_node(tag="w15:people")

        if self._has_author(editor, author):
            return

        escaped_author = html.escape(author, quote=True)
        person_xml = f'''<w15:person w15:author="{escaped_author}">
  <w15:presenceInfo w15:providerId="None" w15:userId="{escaped_author}"/>
</w15:person>'''
        editor.append_to(root, person_xml)

    def _has_author(self, editor: DocxXMLEditor, author: str) -> bool:
        """Check if an author already exists in people.xml."""
        for person_elem in editor.dom.getElementsByTagName("w15:person"):
            if person_elem.getAttribute("w15:author") == author:
                return True
        return False

"""cleanup.py - DOCX DOM Cleaners, Runs Consolidation & Redlines Simplification.

Provides core OpenXML DOM optimizations (ADR-0035, ADR-0057):
1. merge_runs: Merges adjacent <w:r> elements with identical formatting (<w:rPr>).
2. simplify_redlines: Merges adjacent tracked changes (<w:ins>, <w:del>) from identical authors.
3. clone_xml_text: Injects keyword mapping text directly into document.xml preserving styles.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

import defusedxml.minidom

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def merge_runs(input_dir: str | Path) -> tuple[int, str]:
    """Merge adjacent runs with identical formatting in DOCX word/document.xml.

    Args:
        input_dir: Directory containing unpacked DOCX file structure.

    Returns:
        tuple of (merge_count, status_message).
    """
    doc_xml = Path(input_dir) / "word" / "document.xml"
    if not doc_xml.exists():
        return 0, f"Error: {doc_xml} not found"

    try:
        dom = defusedxml.minidom.parseString(doc_xml.read_text(encoding="utf-8"))
        root = dom.documentElement

        _remove_elements(root, "proofErr")
        _strip_run_rsid_attrs(root)

        containers = {run.parentNode for run in _find_elements(root, "r")}
        merge_count = 0
        for container in containers:
            if container:
                merge_count += _merge_runs_in(container)

        doc_xml.write_bytes(dom.toxml(encoding="UTF-8"))
        return merge_count, f"Merged {merge_count} runs"
    except Exception as e:
        return 0, f"Error: {e}"


def simplify_redlines(input_dir: str | Path) -> tuple[int, str]:
    """Simplify tracked changes by merging adjacent w:ins or w:del elements from the same author.

    Args:
        input_dir: Directory containing unpacked DOCX file structure.

    Returns:
        tuple of (merge_count, status_message).
    """
    doc_xml = Path(input_dir) / "word" / "document.xml"
    if not doc_xml.exists():
        return 0, f"Error: {doc_xml} not found"

    try:
        dom = defusedxml.minidom.parseString(doc_xml.read_text(encoding="utf-8"))
        root = dom.documentElement

        merge_count = 0
        containers = _find_elements(root, "p") + _find_elements(root, "tc")
        for container in containers:
            merge_count += _merge_tracked_changes_in(container, "ins")
            merge_count += _merge_tracked_changes_in(container, "del")

        doc_xml.write_bytes(dom.toxml(encoding="UTF-8"))
        return merge_count, f"Simplified {merge_count} tracked changes"
    except Exception as e:
        return 0, f"Error: {e}"


def clone_xml_text(xml_file: str | Path, map_file: str | Path) -> int:
    """Inject new text mapping into raw XML document.xml while preserving structure.

    Args:
        xml_file: Path to document.xml.
        map_file: Path to JSON file containing key-value replacements.

    Returns:
        Number of replacements made.
    """
    x_path = Path(xml_file)
    m_path = Path(map_file)
    if not x_path.exists():
        raise FileNotFoundError(f"File not found: {xml_file}")
    if not m_path.exists():
        raise FileNotFoundError(f"File not found: {map_file}")

    with open(m_path, encoding="utf-8") as f:
        mapping: dict[str, str] = json.load(f)

    with open(x_path, encoding="utf-8") as f:
        content = f.read()

    changes_made = 0
    for key, value in mapping.items():
        if key in content:
            content = content.replace(key, value)
            changes_made += 1

    with open(x_path, "w", encoding="utf-8") as f:
        f.write(content)

    return changes_made


def get_tracked_change_authors(doc_xml_path: Path | str) -> dict[str, int]:
    """Inspect document.xml and count tracked change annotations per author."""
    p = Path(doc_xml_path)
    if not p.exists():
        return {}

    try:
        tree = ET.parse(p)
        root = tree.getroot()
    except Exception:
        return {}

    author_attr = f"{{{WORD_NS}}}author"
    authors: dict[str, int] = {}
    for tag in ["ins", "del"]:
        for elem in root.iter(f"{{{WORD_NS}}}{tag}"):
            author = elem.get(author_attr)
            if author:
                authors[author] = authors.get(author, 0) + 1
    return authors


def get_authors_from_docx(docx_path: Path | str) -> dict[str, int]:
    """Extract tracked change authors and counts directly from a .docx file."""
    p = Path(docx_path)
    if not p.exists():
        return {}

    try:
        with zipfile.ZipFile(p, "r") as zf:
            if "word/document.xml" not in zf.namelist():
                return {}
            with zf.open("word/document.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()

                namespaces = {"w": WORD_NS}
                author_attr = f"{{{WORD_NS}}}author"

                authors: dict[str, int] = {}
                for tag in ["ins", "del"]:
                    for elem in root.findall(f".//w:{tag}", namespaces):
                        author = elem.get(author_attr)
                        if author:
                            authors[author] = authors.get(author, 0) + 1
                return authors
    except (zipfile.BadZipFile, ET.ParseError):
        return {}


# Backward-compatibility alias
_get_authors_from_docx = get_authors_from_docx


def infer_author(
    modified_dir: Path | str, original_docx: Path | str, default: str = "Claude"
) -> str:
    """Infer the principal author who contributed new tracked changes.

    Args:
        modified_dir: Directory containing unpacked modified DOCX.
        original_docx: Path to original unmodified .docx file.
        default: Fallback author name if no new authors found.

    Returns:
        Name of the inferred author.
    """
    m_dir = Path(modified_dir)
    o_docx = Path(original_docx)
    modified_xml = m_dir / "word" / "document.xml"
    modified_authors = get_tracked_change_authors(modified_xml)

    if not modified_authors:
        return default

    original_authors = get_authors_from_docx(o_docx)

    new_changes: dict[str, int] = {}
    for author, count in modified_authors.items():
        original_count = original_authors.get(author, 0)
        diff = count - original_count
        if diff > 0:
            new_changes[author] = diff

    if not new_changes:
        return default

    if len(new_changes) == 1:
        return next(iter(new_changes))

    raise ValueError(
        f"Multiple authors added new changes: {new_changes}. Cannot infer which author to validate."
    )


# ----------------------------------------------------------------------
# Internal DOM Tree Manipulation Helpers
# ----------------------------------------------------------------------


def _find_elements(root: Any, tag: str) -> list[Any]:
    results = []

    def traverse(node: Any) -> None:
        if node.nodeType == node.ELEMENT_NODE:
            name = node.localName or node.tagName
            if name == tag or name.endswith(f":{tag}"):
                results.append(node)
            for child in node.childNodes:
                traverse(child)

    traverse(root)
    return results


def _get_child(parent: Any, tag: str) -> Any | None:
    for child in parent.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            name = child.localName or child.tagName
            if name == tag or name.endswith(f":{tag}"):
                return child
    return None


def _get_children(parent: Any, tag: str) -> list[Any]:
    results = []
    for child in parent.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            name = child.localName or child.tagName
            if name == tag or name.endswith(f":{tag}"):
                results.append(child)
    return results


def _is_adjacent(elem1: Any, elem2: Any) -> bool:
    node = elem1.nextSibling
    while node:
        if node == elem2:
            return True
        if node.nodeType == node.ELEMENT_NODE:
            return False
        if node.nodeType == node.TEXT_NODE and node.data.strip():
            return False
        node = node.nextSibling
    return False


def _remove_elements(root: Any, tag: str) -> None:
    for elem in _find_elements(root, tag):
        if elem.parentNode:
            elem.parentNode.removeChild(elem)


def _strip_run_rsid_attrs(root: Any) -> None:
    for run in _find_elements(root, "r"):
        if hasattr(run, "attributes") and run.attributes:
            for attr in list(run.attributes.values()):
                if "rsid" in attr.name.lower():
                    run.removeAttribute(attr.name)


def _merge_runs_in(container: Any) -> int:
    merge_count = 0
    run = _first_child_run(container)

    while run:
        while True:
            next_elem = _next_element_sibling(run)
            if next_elem and _is_run(next_elem) and _can_merge(run, next_elem):
                _merge_run_content(run, next_elem)
                container.removeChild(next_elem)
                merge_count += 1
            else:
                break

        _consolidate_text(run)
        run = _next_sibling_run(run)

    return merge_count


def _first_child_run(container: Any) -> Any | None:
    for child in container.childNodes:
        if child.nodeType == child.ELEMENT_NODE and _is_run(child):
            return child
    return None


def _next_element_sibling(node: Any) -> Any | None:
    sibling = node.nextSibling
    while sibling:
        if sibling.nodeType == sibling.ELEMENT_NODE:
            return sibling
        sibling = sibling.nextSibling
    return None


def _next_sibling_run(node: Any) -> Any | None:
    sibling = node.nextSibling
    while sibling:
        if sibling.nodeType == sibling.ELEMENT_NODE and _is_run(sibling):
            return sibling
        sibling = sibling.nextSibling
    return None


def _is_run(node: Any) -> bool:
    name = node.localName or node.tagName
    return name == "r" or name.endswith(":r")


def _can_merge(run1: Any, run2: Any) -> bool:
    rpr1 = _get_child(run1, "rPr")
    rpr2 = _get_child(run2, "rPr")

    if (rpr1 is None) != (rpr2 is None):
        return False
    if rpr1 is None:
        return True
    return rpr1.toxml() == rpr2.toxml()


def _merge_run_content(target: Any, source: Any) -> None:
    for child in list(source.childNodes):
        if child.nodeType == child.ELEMENT_NODE:
            name = child.localName or child.tagName
            if name != "rPr" and not name.endswith(":rPr"):
                target.appendChild(child)


def _consolidate_text(run: Any) -> None:
    t_elements = _get_children(run, "t")
    for i in range(len(t_elements) - 1, 0, -1):
        curr, prev = t_elements[i], t_elements[i - 1]
        if _is_adjacent(prev, curr):
            prev_text = prev.firstChild.data if prev.firstChild else ""
            curr_text = curr.firstChild.data if curr.firstChild else ""
            merged = prev_text + curr_text

            if prev.firstChild:
                prev.firstChild.data = merged
            else:
                prev.appendChild(run.ownerDocument.createTextNode(merged))

            if merged.startswith(" ") or merged.endswith(" "):
                prev.setAttribute("xml:space", "preserve")
            elif prev.hasAttribute("xml:space"):
                prev.removeAttribute("xml:space")

            run.removeChild(curr)


def _merge_tracked_changes_in(container: Any, tag: str) -> int:
    merge_count = 0
    tracked = [
        child
        for child in container.childNodes
        if child.nodeType == child.ELEMENT_NODE and _is_element(child, tag)
    ]

    if len(tracked) < 2:
        return 0

    i = 0
    while i < len(tracked) - 1:
        curr = tracked[i]
        next_elem = tracked[i + 1]

        if _can_merge_tracked(curr, next_elem):
            _merge_tracked_content(curr, next_elem)
            container.removeChild(next_elem)
            tracked.pop(i + 1)
            merge_count += 1
        else:
            i += 1

    return merge_count


def _is_element(node: Any, tag: str) -> bool:
    name = node.localName or node.tagName
    return name == tag or name.endswith(f":{tag}")


def _get_author(elem: Any) -> str:
    author = elem.getAttribute("w:author")
    if not author and hasattr(elem, "attributes") and elem.attributes:
        for attr in elem.attributes.values():
            if attr.localName == "author" or attr.name.endswith(":author"):
                return attr.value
    return author or ""


def _can_merge_tracked(elem1: Any, elem2: Any) -> bool:
    if _get_author(elem1) != _get_author(elem2):
        return False

    node = elem1.nextSibling
    while node and node != elem2:
        if node.nodeType == node.ELEMENT_NODE:
            return False
        if node.nodeType == node.TEXT_NODE and node.data.strip():
            return False
        node = node.nextSibling

    return True


def _merge_tracked_content(target: Any, source: Any) -> None:
    while source.firstChild:
        child = source.firstChild
        source.removeChild(child)
        target.appendChild(child)

"""Tracked changes (redlining) engine for Word documents."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from xml.dom import minidom
from typing import TYPE_CHECKING, Any

from .utilities import _generate_hex_id

if TYPE_CHECKING:
    from xml.dom.minidom import Element
    from .document import DocxXMLEditor


def revert_insertion(editor: DocxXMLEditor, elem: Element) -> list[Element]:
    """Reject an insertion by wrapping its content in a deletion."""
    ins_elements = []
    if elem.tagName == "w:ins":
        ins_elements.append(elem)
    else:
        ins_elements.extend(elem.getElementsByTagName("w:ins"))

    if not ins_elements:
        raise ValueError(
            f"revert_insertion requires w:ins elements. "
            f"The provided element <{elem.tagName}> contains no insertions. "
        )

    for ins_elem in ins_elements:
        runs = list(ins_elem.getElementsByTagName("w:r"))
        if not runs:
            continue

        del_wrapper = editor.dom.createElement("w:del")

        for run in runs:
            if run.hasAttribute("w:rsidR"):
                run.setAttribute("w:rsidDel", run.getAttribute("w:rsidR"))
                run.removeAttribute("w:rsidR")
            elif not run.hasAttribute("w:rsidDel"):
                run.setAttribute("w:rsidDel", editor.rsid)

            for t_elem in list(run.getElementsByTagName("w:t")):
                del_text = editor.dom.createElement("w:delText")
                while t_elem.firstChild:
                    del_text.appendChild(t_elem.firstChild)
                for i in range(t_elem.attributes.length):
                    attr = t_elem.attributes.item(i)
                    del_text.setAttribute(attr.name, attr.value)
                t_elem.parentNode.replaceChild(del_text, t_elem)

        while ins_elem.firstChild:
            del_wrapper.appendChild(ins_elem.firstChild)

        ins_elem.appendChild(del_wrapper)
        editor._inject_attributes_to_nodes([del_wrapper])

    return [elem]


def revert_deletion(editor: DocxXMLEditor, elem: Element) -> list[Element]:
    """Reject a deletion by re-inserting the deleted content."""
    del_elements = []
    is_single_del = elem.tagName == "w:del"

    if is_single_del:
        del_elements.append(elem)
    else:
        del_elements.extend(elem.getElementsByTagName("w:del"))

    if not del_elements:
        raise ValueError(
            f"revert_deletion requires w:del elements. "
            f"The provided element <{elem.tagName}> contains no deletions. "
        )

    created_insertion = None

    for del_elem in del_elements:
        runs = list(del_elem.getElementsByTagName("w:r"))
        if not runs:
            continue

        ins_elem = editor.dom.createElement("w:ins")

        for run in runs:
            new_run = run.cloneNode(True)

            for del_text in list(new_run.getElementsByTagName("w:delText")):
                t_elem = editor.dom.createElement("w:t")
                while del_text.firstChild:
                    t_elem.appendChild(del_text.firstChild)
                for i in range(del_text.attributes.length):
                    attr = del_text.attributes.item(i)
                    t_elem.setAttribute(attr.name, attr.value)
                del_text.parentNode.replaceChild(t_elem, del_text)

            if new_run.hasAttribute("w:rsidDel"):
                new_run.setAttribute("w:rsidR", new_run.getAttribute("w:rsidDel"))
                new_run.removeAttribute("w:rsidDel")
            elif not new_run.hasAttribute("w:rsidR"):
                new_run.setAttribute("w:rsidR", editor.rsid)

            ins_elem.appendChild(new_run)

        nodes = editor.insert_after(del_elem, ins_elem.toxml())
        if is_single_del and nodes:
            created_insertion = nodes[0]

    if is_single_del and created_insertion:
        return [elem, created_insertion]
    else:
        return [elem]


def suggest_paragraph(xml_content: str) -> str:
    """Transform paragraph XML to add tracked change wrapping for insertion."""
    wrapper = f'<root xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">{xml_content}</root>'
    doc = minidom.parseString(wrapper)
    para = doc.getElementsByTagName("w:p")[0]

    pPr_list = para.getElementsByTagName("w:pPr")
    if not pPr_list:
        pPr = doc.createElement("w:pPr")
        para.insertBefore(pPr, para.firstChild) if para.firstChild else para.appendChild(pPr)
    else:
        pPr = pPr_list[0]

    rPr_list = pPr.getElementsByTagName("w:rPr")
    if not rPr_list:
        rPr = doc.createElement("w:rPr")
        pPr.appendChild(rPr)
    else:
        rPr = rPr_list[0]

    ins_marker = doc.createElement("w:ins")
    rPr.insertBefore(ins_marker, rPr.firstChild) if rPr.firstChild else rPr.appendChild(ins_marker)

    ins_wrapper = doc.createElement("w:ins")
    for child in [c for c in para.childNodes if c.nodeName != "w:pPr"]:
        para.removeChild(child)
        ins_wrapper.appendChild(child)
    para.appendChild(ins_wrapper)

    return para.toxml()


def suggest_deletion(editor: DocxXMLEditor, elem: Element) -> Element:
    """Mark a w:r or w:p element as deleted with tracked changes."""
    if elem.nodeName == "w:r":
        if elem.getElementsByTagName("w:delText"):
            raise ValueError("w:r element already contains w:delText")

        for t_elem in list(elem.getElementsByTagName("w:t")):
            del_text = editor.dom.createElement("w:delText")
            while t_elem.firstChild:
                del_text.appendChild(t_elem.firstChild)
            for i in range(t_elem.attributes.length):
                attr = t_elem.attributes.item(i)
                del_text.setAttribute(attr.name, attr.value)
            t_elem.parentNode.replaceChild(del_text, t_elem)

        if elem.hasAttribute("w:rsidR"):
            elem.setAttribute("w:rsidDel", elem.getAttribute("w:rsidR"))
            elem.removeAttribute("w:rsidR")
        elif not elem.hasAttribute("w:rsidDel"):
            elem.setAttribute("w:rsidDel", editor.rsid)

        del_wrapper = editor.dom.createElement("w:del")
        parent = elem.parentNode
        parent.insertBefore(del_wrapper, elem)
        parent.removeChild(elem)
        del_wrapper.appendChild(elem)

        editor._inject_attributes_to_nodes([del_wrapper])
        return del_wrapper

    elif elem.nodeName == "w:p":
        if elem.getElementsByTagName("w:ins") or elem.getElementsByTagName("w:del"):
            raise ValueError("w:p element already contains tracked changes")

        pPr_list = elem.getElementsByTagName("w:pPr")
        is_numbered = pPr_list and pPr_list[0].getElementsByTagName("w:numPr")

        if is_numbered:
            pPr = pPr_list[0]
            rPr_list = pPr.getElementsByTagName("w:rPr")

            if not rPr_list:
                rPr = editor.dom.createElement("w:rPr")
                pPr.appendChild(rPr)
            else:
                rPr = rPr_list[0]

            del_marker = editor.dom.createElement("w:del")
            rPr.insertBefore(del_marker, rPr.firstChild) if rPr.firstChild else rPr.appendChild(del_marker)

        for t_elem in list(elem.getElementsByTagName("w:t")):
            del_text = editor.dom.createElement("w:delText")
            while t_elem.firstChild:
                del_text.appendChild(t_elem.firstChild)
            for i in range(t_elem.attributes.length):
                attr = t_elem.attributes.item(i)
                del_text.setAttribute(attr.name, attr.value)
            t_elem.parentNode.replaceChild(del_text, t_elem)

        for run in elem.getElementsByTagName("w:r"):
            if run.hasAttribute("w:rsidR"):
                run.setAttribute("w:rsidDel", run.getAttribute("w:rsidR"))
                run.removeAttribute("w:rsidR")
            elif not run.hasAttribute("w:rsidDel"):
                run.setAttribute("w:rsidDel", editor.rsid)

        del_wrapper = editor.dom.createElement("w:del")
        for child in [c for c in elem.childNodes if c.nodeName != "w:pPr"]:
            elem.removeChild(child)
            del_wrapper.appendChild(child)
        elem.appendChild(del_wrapper)

        editor._inject_attributes_to_nodes([del_wrapper])
        return elem

    else:
        raise ValueError(f"Element must be w:r or w:p, got {elem.nodeName}")

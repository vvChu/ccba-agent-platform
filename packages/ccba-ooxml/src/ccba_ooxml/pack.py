"""Tool to pack a directory into a .docx, .pptx, or .xlsx file with XML formatting undone."""

from __future__ import annotations

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import defusedxml.minidom

from .soffice import validate_document


def pack_document(input_dir: str | Path, output_file: str | Path, validate: bool = False) -> bool:
    """Pack a directory into an Office file (.docx/.pptx/.xlsx).

    Args:
        input_dir: Path to unpacked Office document directory
        output_file: Path to output Office file
        validate: If True, validates with soffice (default: False)

    Returns:
        bool: True if successful, False if validation failed
    """
    input_dir = Path(input_dir)
    output_file = Path(output_file)

    if not input_dir.is_dir():
        raise ValueError(f"{input_dir} is not a directory")
    if output_file.suffix.lower() not in {".docx", ".pptx", ".xlsx"}:
        raise ValueError(f"{output_file} must be a .docx, .pptx, or .xlsx file")

    # Work in temporary directory to avoid modifying original
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_content_dir = Path(temp_dir) / "content"
        shutil.copytree(input_dir, temp_content_dir)

        # Process XML files deterministically to remove pretty-printing whitespace
        xml_candidates = sorted(
            [*temp_content_dir.rglob("*.xml"), *temp_content_dir.rglob("*.rels")],
            key=lambda p: p.relative_to(temp_content_dir).as_posix(),
        )
        for xml_file in xml_candidates:
            condense_xml(xml_file)

        # Create final deterministic Office file as zip archive
        output_file.parent.mkdir(parents=True, exist_ok=True)
        _write_deterministic_zip(temp_content_dir, output_file)

        # Validate if requested
        if validate:
            if not validate_document(output_file):
                output_file.unlink()  # Delete the corrupt file
                return False

    return True


def _write_deterministic_zip(content_dir: Path, output_file: Path) -> None:
    """Write directory contents into a reproducible byte-identical ZIP archive."""
    archive_files = sorted(
        (f for f in content_dir.rglob("*") if f.is_file()),
        key=lambda f: f.relative_to(content_dir).as_posix(),
    )
    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in archive_files:
            rel_posix = f.relative_to(content_dir).as_posix()
            zinfo = zipfile.ZipInfo(rel_posix, date_time=(1980, 1, 1, 0, 0, 0))
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zinfo, f.read_bytes())


def condense_xml(xml_file: str | Path) -> None:
    """Strip unnecessary whitespace and remove comments."""
    try:
        with open(xml_file, encoding="utf-8") as f:
            dom = defusedxml.minidom.parse(f)
    except Exception as e:
        print(f"Warning: Could not condense {xml_file}: {e}", file=sys.stderr)
        return

    # Process each element to remove whitespace and comments
    for element in dom.getElementsByTagName("*"):
        # Skip w:t elements and their processing
        if element.tagName.endswith(":t"):
            continue

        # Remove whitespace-only text nodes and comment nodes
        for child in list(element.childNodes):
            if (
                child.nodeType == child.TEXT_NODE
                and child.nodeValue
                and child.nodeValue.strip() == ""
            ) or child.nodeType == child.COMMENT_NODE:
                element.removeChild(child)

    # Write back the condensed XML
    with open(xml_file, "wb") as f:
        f.write(dom.toxml(encoding="UTF-8"))


__all__ = ["condense_xml", "pack_document", "validate_document"]

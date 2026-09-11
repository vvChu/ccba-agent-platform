#!/usr/bin/env python3
"""Unpack and format XML contents of Office files (.docx, .pptx, .xlsx)"""

import sys
import zipfile
from pathlib import Path

import defusedxml.minidom


def unpack_document(input_file: str | Path, output_dir: str | Path) -> None:
    """Unpack an Office document (.docx/.pptx/.xlsx) and pretty-print its XML.

    Args:
        input_file: Path to the original Office document
        output_dir: Path to the directory where contents should be unpacked
    """
    input_path = Path(input_file)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(input_path) as zf:
        zf.extractall(output_path)

    # Pretty print all XML files
    xml_files = list(output_path.rglob("*.xml")) + list(output_path.rglob("*.rels"))
    for xml_file in xml_files:
        try:
            content = xml_file.read_text(encoding="utf-8")
            dom = defusedxml.minidom.parseString(content)
            xml_file.write_bytes(dom.toprettyxml(indent="  ", encoding="utf-8"))
        except Exception as e:
            # Fallback or log if some XML is malformed or binary
            print(f"Warning: Could not pretty print {xml_file}: {e}", file=sys.stderr)


__all__ = ["unpack_document"]

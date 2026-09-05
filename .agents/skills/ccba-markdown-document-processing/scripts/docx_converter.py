"""CCBA Master Skill: Markdown Document Processing Engine (Docx Converter).

Converts official .docx documents (QCVN 06:2022/BXD) to GFM Markdown with
clean 2D Pipe Tables, standardized section headings (### 1.1),
and full Gold Standard OKF v0.2 integration.
"""

import re
import sys
from pathlib import Path
import mammoth
from scripts.gold_standard_processor import process_okf_bundle
from scripts.qcvn_md_table_formatter import format_all_qcvn_md_tables

sys.stdout.reconfigure(encoding="utf-8")


def normalize_docx_markdown(md_text: str) -> str:
    """Normalize mammoth converted markdown headings and clean up escape chars."""
    # Remove escaped dots, hyphens, and brackets
    md_text = md_text.replace(r"\.", ".").replace(r"\-", "-").replace(r"\(", "(").replace(r"\)", ")")

    # Clean double ### headers if any exist
    md_text = re.sub(r"(###\s*)+", "### ", md_text)

    # Replace bold section headings __1.1 Title__ with ### 1.1 Title
    md_text = re.sub(r'<a id="[^"]+"></a>\s*__(\d+(?:\.\d+)*)\.?\s*([^_]+)__', r"### \1 \2", md_text)
    md_text = re.sub(r"__(\d+(?:\.\d+)*)\.?\s*([^_]+)__", r"### \1 \2", md_text)

    # Replace bold table headings __Bảng X - Title__ with ### Bảng X - Title
    md_text = re.sub(r"__Bảng\s+([A-Z0-9]+(?:\.[0-9]+)?)\s*[-–:]\s*([^_]+)__", r"### Bảng \1 - \2", md_text)

    # Clean any duplicate ### ### prefixes
    md_text = re.sub(r"###\s*###\s*", "### ", md_text)

    return md_text


def convert_docx_to_okf_bundle(docx_path: Path, target_bundle_dir: Path) -> dict:
    """Convert .docx file to Gold Standard OKF Markdown bundle."""
    if not docx_path.exists():
        raise FileNotFoundError(f"Input file not found: {docx_path}")

    target_bundle_dir.mkdir(parents=True, exist_ok=True)
    target_md_path = target_bundle_dir / "qcvn_06_2022_bxd.md"

    print(f"[1/4] Converting {docx_path.name} to Markdown via Mammoth Engine...")
    with open(docx_path, "rb") as docx_file:
        result = mammoth.convert_to_markdown(docx_file)
        raw_md = result.value

    print("[2/4] Normalizing section headings & typography (Sub-skill: vn-legal-normalizer)...")
    normalized_md = normalize_docx_markdown(raw_md)

    # Backup converted md to Layer 1 store
    raw_md_store = docx_path.parent / f"{docx_path.stem}_from_docx.md"
    raw_md_store.write_text(normalized_md, encoding="utf-8")
    print(f"  [Saved] Layer 1 Raw Docx Markdown: {raw_md_store} ({len(normalized_md)} bytes)")

    # Write normalized markdown to target bundle
    target_md_path.write_text(normalized_md, encoding="utf-8")

    print("[3/4] Reconstructing 2D GFM Pipe Tables (Sub-skill: table-reconstructor)...")
    formatted_tables = format_all_qcvn_md_tables(target_md_path)
    print(f"  [Table Reconstructor] Formatted {formatted_tables} 2D GFM Pipe Tables")

    print("[4/4] Packing Gold Standard OKF v0.2 Bundle...")
    bundle_result = process_okf_bundle(target_bundle_dir)
    return bundle_result


if __name__ == "__main__":
    docx_file = Path(".md/extracted_docs/qcvn_06_2022_bxd/qcvn_06_2022_bxd.docx")
    bundle_dir = Path("legal_docs/02_qcvn/qcvn_06_2022_bxd")
    res = convert_docx_to_okf_bundle(docx_file, bundle_dir)
    print("\n[COMPLETE OKF BUNDLE RESULT]:", res)

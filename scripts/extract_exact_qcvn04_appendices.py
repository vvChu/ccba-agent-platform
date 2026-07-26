"""Script to inspect concept.md and extract exact full text of Appendices A, B, and C."""

import sys
import re
from pathlib import Path

# Force UTF-8 encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def extract_appendices():
    bundle_dir = Path("d:/GitHubProjects/ccba-agent-platform/.md/legal_docs/qcvn_04_2021_bxd")
    concept_file = bundle_dir / "concept.md"
    appendices_dir = bundle_dir / "guiding_docs" / "appendices"
    appendices_dir.mkdir(parents=True, exist_ok=True)

    text = concept_file.read_text(encoding="utf-8")
    lines = text.splitlines()

    print(f"Total lines in concept.md: {len(lines)}")

    # Find line indices for PHỤ LỤC A, B, C
    idx_a = -1
    idx_b = -1
    idx_c = -1

    for i, line in enumerate(lines):
        line_clean = line.strip().upper()
        if "PHỤ LỤC A" in line_clean:
            idx_a = i
            print(f"Found PHỤ LỤC A at line {i+1}: {line}")
        elif "PHỤ LỤC B" in line_clean:
            idx_b = i
            print(f"Found PHỤ LỤC B at line {i+1}: {line}")
        elif "PHỤ LỤC C" in line_clean:
            idx_c = i
            print(f"Found PHỤ LỤC C at line {i+1}: {line}")

    if idx_a != -1:
        end_a = idx_b if idx_b != -1 else (idx_c if idx_c != -1 else len(lines))
        text_a = "\n".join(lines[idx_a:end_a]).strip()
        (appendices_dir / "phu_luc_a_phan_cap_nha_chung_cu.md").write_text(
            f"# {text_a}", encoding="utf-8"
        )
        print(f" ✅ Extracted Phụ lục A: {len(text_a):,} characters, {len(text_a.splitlines())} lines")

    if idx_b != -1:
        end_b = idx_c if idx_c != -1 else len(lines)
        text_b = "\n".join(lines[idx_b:end_b]).strip()
        (appendices_dir / "phu_luc_b_dien_tich_can_ho_va_cho_de_xe.md").write_text(
            f"# {text_b}", encoding="utf-8"
        )
        print(f" ✅ Extracted Phụ lục B: {len(text_b):,} characters, {len(text_b.splitlines())} lines")

    if idx_c != -1:
        text_c = "\n".join(lines[idx_c:]).strip()
        (appendices_dir / "phu_luc_c_an_toan_pccc_nha_chung_cu.md").write_text(
            f"# {text_c}", encoding="utf-8"
        )
        print(f" ✅ Extracted Phụ lục C: {len(text_c):,} characters, {len(text_c.splitlines())} lines")

if __name__ == "__main__":
    extract_appendices()

"""linter.py - Visual Parity, Cross-Link & Context-Aware Legal Currency Linter (ADR 0029, ADR 0030, ADR 0050, ADR 0058)."""

from __future__ import annotations

import functools
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

# Authoritative registry of repealed/obsolete legal documents and their recommended replacements
OBSOLETE_LEGAL_PATTERNS: list[dict[str, Any]] = [
    {
        "id": "15/2021/NĐ-CP",
        "name": "Nghị định 15/2021/NĐ-CP",
        "pattern": re.compile(
            r"(?:\b(?:Nghị\s*định|NĐ|ND)\s*(?:số\s*)?)?15/2021/(?:NĐ-CP|ND-CP)\b|\b(?:Nghị\s*định|NĐ|ND)\s*(?:số\s*)?15/2021\b",
            re.IGNORECASE,
        ),
        "replacement": "Nghị định 217/2026/NĐ-CP (Quản lý dự án đầu tư xây dựng)",
        "severity": "ERROR",
    },
    {
        "id": "35/2023/NĐ-CP",
        "name": "Nghị định 35/2023/NĐ-CP",
        "pattern": re.compile(
            r"(?:\b(?:Nghị\s*định|NĐ|ND)\s*(?:số\s*)?)?35/2023/(?:NĐ-CP|ND-CP)\b|\b(?:Nghị\s*định|NĐ|ND)\s*(?:số\s*)?35/2023\b",
            re.IGNORECASE,
        ),
        "replacement": "Nghị định 217/2026/NĐ-CP",
        "severity": "ERROR",
    },
    {
        "id": "06/2021/TT-BXD",
        "name": "Thông tư 06/2021/TT-BXD",
        "pattern": re.compile(
            r"(?:\b(?:Thông\s*tư|TT)\s*(?:số\s*)?)?0?6/2021/TT-BXD\b|\b(?:Thông\s*tư|TT)\s*(?:số\s*)?0?6/2021\b",
            re.IGNORECASE,
        ),
        "replacement": "Thông tư 34/2026/TT-BXD (Phân cấp công trình xây dựng)",
        "severity": "ERROR",
    },
    {
        "id": "03/2016/TT-BXD",
        "name": "Thông tư 03/2016/TT-BXD",
        "pattern": re.compile(
            r"(?:\b(?:Thông\s*tư|TT)\s*(?:số\s*)?)?0?3/2016/TT-BXD\b|\b(?:Thông\s*tư|TT)\s*(?:số\s*)?0?3/2016\b",
            re.IGNORECASE,
        ),
        "replacement": "Thông tư 34/2026/TT-BXD",
        "severity": "ERROR",
    },
    {
        "id": "06/2021/NĐ-CP",
        "name": "Nghị định 06/2021/NĐ-CP",
        "pattern": re.compile(
            r"(?:\b(?:Nghị\s*định|NĐ|ND)\s*(?:số\s*)?)?0?6/2021/(?:NĐ-CP|ND-CP)\b|\b(?:Nghị\s*định|NĐ|ND)\s*(?:số\s*)?0?6/2021\b",
            re.IGNORECASE,
        ),
        "replacement": "Nghị định 207/2026/NĐ-CP (Quản lý chất lượng & thi công xây dựng)",
        "severity": "ERROR",
    },
    {
        "id": "46/2015/NĐ-CP",
        "name": "Nghị định 46/2015/NĐ-CP",
        "pattern": re.compile(
            r"(?:\b(?:Nghị\s*định|NĐ|ND)\s*(?:số\s*)?)?46/2015/(?:NĐ-CP|ND-CP)\b|\b(?:Nghị\s*định|NĐ|ND)\s*(?:số\s*)?46/2015\b",
            re.IGNORECASE,
        ),
        "replacement": "Nghị định 207/2026/NĐ-CP",
        "severity": "ERROR",
    },
    {
        "id": "12/2021/TT-BXD",
        "name": "Thông tư 12/2021/TT-BXD",
        "pattern": re.compile(
            r"(?:\b(?:Thông\s*tư|TT)\s*(?:số\s*)?)?12/2021/TT-BXD\b|\b(?:Thông\s*tư|TT)\s*(?:số\s*)?12/2021\b",
            re.IGNORECASE,
        ),
        "replacement": "Thông tư 38/2026/TT-BXD (Định mức xây dựng và quản lý chi phí)",
        "severity": "ERROR",
    },
    {
        "id": "09/2024/TT-BXD",
        "name": "Thông tư 09/2024/TT-BXD",
        "pattern": re.compile(
            r"(?:\b(?:Thông\s*tư|TT)\s*(?:số\s*)?)?0?9/2024/TT-BXD\b|\b(?:Thông\s*tư|TT)\s*(?:số\s*)?0?9/2024\b",
            re.IGNORECASE,
        ),
        "replacement": "Thông tư 38/2026/TT-BXD",
        "severity": "ERROR",
    },
    {
        "id": "50/2014/QH13",
        "name": "Luật Xây dựng 2014 (50/2014/QH13)",
        "pattern": re.compile(
            r"(?:\bLuật\s*(?:số\s*)?)?50/2014/QH13\b|\bLuật\s+Xây\s+dựng\s+(?:năm\s+)?2014\b|\bLuật\s+XD\s+(?:năm\s+)?2014\b",
            re.IGNORECASE,
        ),
        "replacement": "Luật Xây dựng 2025 (135/2025/QH15)",
        "severity": "ERROR",
    },
    {
        "id": "62/2020/QH14",
        "name": "Luật 62/2020/QH14",
        "pattern": re.compile(
            r"(?:\bLuật\s*(?:số\s*)?)?62/2020/QH14\b|\bLuật\s+62/2020\b",
            re.IGNORECASE,
        ),
        "replacement": "Luật Xây dựng 2025 (135/2025/QH15)",
        "severity": "ERROR",
    },
    {
        "id": "27/2001/QH10",
        "name": "Luật PCCC 2001 (27/2001/QH10)",
        "pattern": re.compile(
            r"(?:\bLuật\s*(?:số\s*)?)?27/2001/QH10\b|\bLuật\s+PCCC\s+(?:năm\s+)?2001\b|\bLuật\s+Phòng\s+cháy\s+(?:chữa\s+cháy|và\s+chữa\s+cháy)\s+(?:năm\s+)?2001\b",
            re.IGNORECASE,
        ),
        "replacement": "Luật PCCC & CNCH 2024 (55/2024/QH15)",
        "severity": "ERROR",
    },
    {
        "id": "136/2020/NĐ-CP",
        "name": "Nghị định 136/2020/NĐ-CP",
        "pattern": re.compile(
            r"(?:\b(?:Nghị\s*định|NĐ|ND)\s*(?:số\s*)?)?136/2020/(?:NĐ-CP|ND-CP)\b|\b(?:Nghị\s*định|NĐ|ND)\s*(?:số\s*)?136/2020\b",
            re.IGNORECASE,
        ),
        "replacement": "Nghị định 105/2025/NĐ-CP (Quy định chi tiết Luật PCCC & CNCH)",
        "severity": "ERROR",
    },
    {
        "id": "TCVN 2737:1995",
        "name": "TCVN 2737:1995",
        "pattern": re.compile(
            r"\bTCVN\s*2737(?::|-)?1995\b",
            re.IGNORECASE,
        ),
        "replacement": "TCVN 2737:2023 (Tải trọng và tác động)",
        "severity": "ERROR",
    },
    {
        "id": "TCVN 5575:2012",
        "name": "TCVN 5575:2012",
        "pattern": re.compile(
            r"\bTCVN\s*5575(?::|-)?2012\b",
            re.IGNORECASE,
        ),
        "replacement": "TCVN 5575:2024 (Kết cấu thép - Tiêu chuẩn thiết kế)",
        "severity": "ERROR",
    },
    {
        "id": "TCVN 9386:2012",
        "name": "TCVN 9386:2012",
        "pattern": re.compile(
            r"\bTCVN\s*9386(?::|-)?2012\b",
            re.IGNORECASE,
        ),
        "replacement": "TCVN 9386:2025 (Thiết kế công trình chịu động đất)",
        "severity": "ERROR",
    },
]

# Synchronize suggested replacement text directly from canonical KNOWN_STATUTORY_REPLACEMENTS (ADR 0050)
from ccba_legal.registry import KNOWN_STATUTORY_REPLACEMENTS

for _entry in OBSOLETE_LEGAL_PATTERNS:
    _sid = _entry.get("id", "")
    if _sid in KNOWN_STATUTORY_REPLACEMENTS and "title" in KNOWN_STATUTORY_REPLACEMENTS[_sid]:
        _entry["replacement"] = KNOWN_STATUTORY_REPLACEMENTS[_sid]["title"]


def normalize_statute_code(code: str) -> str:
    """Normalize statutory citation code for robust comparison (handles Đ/D and casing)."""
    return code.upper().replace("Đ", "D")


# Canonical active 2024-2026 statutes to avoid false warnings
KNOWN_ACTIVE_STATUTES: set[str] = {
    "135/2025/QH15",
    "217/2026/NĐ-CP",
    "217/2026/ND-CP",
    "207/2026/NĐ-CP",
    "207/2026/ND-CP",
    "34/2026/TT-BXD",
    "38/2026/TT-BXD",
    "55/2024/QH15",
    "105/2025/NĐ-CP",
    "105/2025/ND-CP",
}


@functools.lru_cache(maxsize=16)
def get_cached_active_docs(registry_path_str: str | None) -> frozenset[str]:
    """Retrieve canonical active document codes, cached across file linting calls."""
    active: set[str] = {normalize_statute_code(s) for s in KNOWN_ACTIVE_STATUTES}
    if registry_path_str:
        p = Path(registry_path_str)
        if p.exists():
            try:
                from ccba_legal.registry import LegalRegistryManager

                reg_mgr = LegalRegistryManager(p)
                reg_data = reg_mgr.load()
                for cat in ["laws", "decrees", "circulars", "decisions"]:
                    for d in reg_data.get(cat, []):
                        if isinstance(d, dict) and str(d.get("status", "")).lower() in {
                            "active",
                            "current",
                            "còn hiệu lực",
                        }:
                            if d.get("document_number"):
                                active.add(normalize_statute_code(str(d["document_number"])))
            except Exception:
                pass
    return frozenset(active)


# Regex to detect statutory references for two-tier unverified audit
GENERIC_STATUTE_REGEX = re.compile(
    r"\b(\d{1,4}/\d{4}/(?:NĐ-CP|ND-CP|TT-BXD|QH\d{2}))\b",
    re.IGNORECASE,
)

# Transitional or comparative phrasing that exempts citations from being flagged as violations
TRANSITIONAL_REGEX = re.compile(
    r"(?:"
    r"thay\s+thế|bãi\s+bỏ|hết\s+hiệu\s+lực|hết\s+hiệu\s+lực\s+toàn\s+bộ|"
    r"trước\s+đây(?:\s+là)?|tiền\s+thân|kế\s+thừa|so\s+sánh|đối\s+chiếu|"
    r"chuyển\s+tiếp|quy\s+định\s+chuyển\s+tiếp|áp\s+dụng\s+giai\s+đoạn\s+cũ|"
    r"supersed\w*|replac\w*|formerly|prior\s+to|previous(?:ly)?|"
    r"obsolete|deprecated|transition\w*"
    r")",
    re.IGNORECASE,
)

# Standard directories to ignore during recursive scans
IGNORED_SCAN_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
}


def is_ignored_path(path: Path) -> bool:
    """Check if path should be skipped during directory linter scans."""
    for part in path.parts:
        if part in IGNORED_SCAN_DIRS:
            return True
        if part.startswith(".") and part not in {".md", ".agents", "."}:
            return True
    posix_path = path.as_posix().lower()
    if "/legal_docs/" in posix_path or posix_path.endswith("/legal_docs"):
        return True
    return False


def collect_scannable_files(
    target_dir: Path,
    valid_exts: set[str],
) -> list[Path]:
    """Collect scannable files while pruning ignored directories top-down for optimal performance."""
    collected: list[Path] = []
    for root, dirnames, filenames in os.walk(target_dir, topdown=True):
        # Prune ignored directories in-place so os.walk does not descend into them
        dirnames[:] = [
            d
            for d in dirnames
            if d not in IGNORED_SCAN_DIRS
            and not (d.startswith(".") and d not in {".md", ".agents"})
            and d != "legal_docs"
        ]
        root_path = Path(root)
        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext in valid_exts:
                fpath = root_path / fname
                if not is_ignored_path(fpath):
                    collected.append(fpath)
    return sorted(collected)


def safe_parse_xml(xml_bytes: bytes) -> ET.Element:
    """Parse XML bytes safely with entity resolution disabled (mitigates XML entity expansion / DTD DoS)."""
    try:
        import defusedxml.ElementTree as DefusedET

        return DefusedET.fromstring(xml_bytes)
    except ImportError:
        # Strictly forbid external DTD and entity declarations in stdlib fallback to prevent security downgrade
        if b"<!DOCTYPE" in xml_bytes or b"<!ENTITY" in xml_bytes:
            raise ValueError(
                "Insecure XML with DTD or external entity detected, and defusedxml is not installed."
            ) from None
        parser = ET.XMLParser()
        return ET.fromstring(xml_bytes, parser=parser)


def get_sentence_context(text: str, match_start: int, match_end: int) -> str:
    """Extract the sentence or clause surrounding a match."""
    start = 0
    for i in range(match_start - 1, -1, -1):
        if text[i] in "\n\r;":
            start = i + 1
            break
        if (
            text[i] in ".!?"
            and (i == 0 or not text[i - 1].isdigit())
            and (i + 1 == len(text) or text[i + 1].isspace())
        ):
            start = i + 1
            break

    end = len(text)
    for i in range(match_end, len(text)):
        if text[i] in "\n\r;":
            end = i
            break
        if (
            text[i] in ".!?"
            and (i == 0 or not text[i - 1].isdigit())
            and (i + 1 == len(text) or text[i + 1].isspace())
        ):
            end = i
            break

    return text[start:end].strip()


def is_transitional_context(clause: str, line_context: str = "") -> bool:
    """Check if the context around a citation indicates transitional or comparative usage."""
    if TRANSITIONAL_REGEX.search(clause):
        return True
    if line_context and len(line_context) <= 200 and TRANSITIONAL_REGEX.search(line_context):
        return True
    return False


MAX_XML_ENTRY_SIZE = 50 * 1024 * 1024  # 50 MB safety limit for uncompressed XML entries


def extract_file_lines(file_path: Path) -> list[tuple[int, str, str]]:
    """Extract lines and location labels across Markdown, Text, PPTX, and DOCX files.

    Returns:
        list of tuples: (index, location_label, text)
    """
    ext = file_path.suffix.lower()

    if ext in {".md", ".markdown", ".txt"}:
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            return [(idx, f"Line {idx}", line) for idx, line in enumerate(lines, 1)]
        except Exception as e:
            return [(1, "Error", f"Failed to read text file: {e}")]

    if ext == ".pptx":
        results: list[tuple[int, str, str]] = []
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                slide_files = [
                    n for n in z.namelist() if re.match(r"^ppt/slides/slide\d+\.xml$", n)
                ]
                slide_files.sort(
                    key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 0
                )
                for s_name in slide_files:
                    s_num = (
                        int(re.search(r"\d+", s_name).group()) if re.search(r"\d+", s_name) else 1
                    )
                    zinfo = z.getinfo(s_name)
                    if zinfo.file_size > MAX_XML_ENTRY_SIZE:
                        results.append(
                            (
                                s_num,
                                f"Slide {s_num}",
                                f"Slide XML exceeds maximum allowed size ({zinfo.file_size} bytes)",
                            )
                        )
                        continue
                    tree = safe_parse_xml(z.read(zinfo))
                    p_idx = 0
                    for node in tree.iter():
                        if node.tag.endswith("}p"):
                            p_idx += 1
                            p_text = "".join(
                                t.text for t in node.iter() if t.tag.endswith("}t") and t.text
                            ).strip()
                            if p_text:
                                results.append((s_num, f"Slide {s_num}:P{p_idx}", p_text))
        except Exception as e:
            results.append((1, "Error", f"Failed to parse PPTX {file_path.name}: {e}"))
        return results

    if ext == ".docx":
        results = []
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                if "word/document.xml" in z.namelist():
                    zinfo = z.getinfo("word/document.xml")
                    if zinfo.file_size > MAX_XML_ENTRY_SIZE:
                        results.append(
                            (
                                1,
                                "Error",
                                f"Document XML exceeds maximum allowed size ({zinfo.file_size} bytes)",
                            )
                        )
                        return results
                    tree = safe_parse_xml(z.read(zinfo))
                    p_idx = 0
                    for node in tree.iter():
                        if node.tag.endswith("}p"):
                            p_idx += 1
                            p_text = "".join(
                                t.text for t in node.iter() if t.tag.endswith("}t") and t.text
                            ).strip()
                            if p_text:
                                results.append((p_idx, f"Para {p_idx}", p_text))
        except Exception as e:
            results.append((1, "Error", f"Failed to parse DOCX {file_path.name}: {e}"))
        return results

    return []


def lint_file_currency(
    file_path: Path,
    registry_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Audit legal citations in a file for obsolete statutes and unverified references."""
    lines_data = extract_file_lines(file_path)
    findings: list[dict[str, Any]] = []

    reg_key = str(registry_path.resolve()) if registry_path else None
    active_docs = get_cached_active_docs(reg_key)

    for line_no, loc_label, text in lines_data:
        if not text.strip():
            continue

        # 1. Check known obsolete statutory patterns
        matched_statute_ids_on_line: set[str] = set()
        for item in OBSOLETE_LEGAL_PATTERNS:
            for match in item["pattern"].finditer(text):
                matched_str = match.group(0)
                sentence = get_sentence_context(text, match.start(), match.end())

                if is_transitional_context(sentence, text):
                    continue

                matched_statute_ids_on_line.add(normalize_statute_code(item["id"]))
                for gm in GENERIC_STATUTE_REGEX.finditer(matched_str):
                    matched_statute_ids_on_line.add(normalize_statute_code(gm.group(1)))

                findings.append(
                    {
                        "file": str(file_path),
                        "line": line_no,
                        "location": loc_label,
                        "matched_text": matched_str,
                        "obsolete_doc": item["name"],
                        "replacement": item["replacement"],
                        "severity": item.get("severity", "ERROR"),
                        "context": sentence,
                    }
                )

        # 2. Check for generic statutory references (Two-tier severity: WARNING if unverified)
        for gen_match in GENERIC_STATUTE_REGEX.finditer(text):
            gen_str = gen_match.group(1)
            norm_gen = normalize_statute_code(gen_str)
            if norm_gen in matched_statute_ids_on_line:
                continue
            if norm_gen in active_docs:
                continue

            sentence = get_sentence_context(text, gen_match.start(), gen_match.end())
            if is_transitional_context(sentence, text):
                continue

            findings.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "location": loc_label,
                    "matched_text": gen_str,
                    "obsolete_doc": gen_str,
                    "replacement": "Tra cứu legal_registry.yaml hoặc cập nhật văn bản hiện hành",
                    "severity": "WARNING",
                    "context": sentence,
                }
            )

    return findings


def lint_markdown_file(md_path: Path) -> list[str]:
    """Lint a single Markdown file for visual formatting issues (ADR 0029, ADR 0030)."""
    errors: list[str] = []
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()

        # 1. Check redundant bullet before CHÚ THÍCH / GHI CHÚ
        if re.match(
            r"^[-*+]\s+(?:\*\*)?(?:CHÚ THÍCH|GHI CHÚ|Chú thích|Ghi chú)\s*\d*[:\.]?", stripped
        ):
            if re.search(r"^[-*+]\s+(?:\*\*)?CHÚ THÍCH\s+\d+:", stripped):
                errors.append(f"Line {idx}: Redundant bullet before footnote header: '{stripped}'")

        # 2. Check raw HTML table tags (unless exempted)
        if re.search(r"<(?:table|thead|tbody|tr|th|td)\b", stripped, re.IGNORECASE):
            errors.append(f"Line {idx}: Unclean raw HTML table tag found: '{stripped}'")

    return errors


def lint_bundle_links(bundle_dir: Path) -> list[str]:
    """Verify internal anchors and relative markdown links across an OKF bundle."""
    errors: list[str] = []
    md_files = list(bundle_dir.rglob("*.md"))

    file_anchors: dict[str, set[str]] = {}
    file_contents: dict[str, str] = {}

    for md_f in md_files:
        rel_key = str(md_f.relative_to(bundle_dir)).replace("\\", "/")
        text = md_f.read_text(encoding="utf-8")
        anchors = set(re.findall(r'<a\s+(?:id|name)="([^"]+)"', text))
        file_anchors[rel_key] = anchors
        file_contents[rel_key] = text

    for rel_key, text in file_contents.items():
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)
        for _link_text, target in links:
            target_clean = target.strip()
            if target_clean.startswith("http://") or target_clean.startswith("https://"):
                continue

            # Anchor in same or other bundle file
            if target_clean.startswith("#"):
                anchor = target_clean[1:]
                if anchor not in file_anchors[rel_key]:
                    found = any(anchor in anc_set for anc_set in file_anchors.values())
                    if not found:
                        errors.append(
                            f"[{rel_key}] Broken anchor link '{target}': anchor not found"
                        )
            else:
                parts = target_clean.split("#", 1)
                target_rel_path = parts[0]
                target_anchor = parts[1] if len(parts) > 1 else None

                current_dir = (bundle_dir / rel_key).parent
                target_file_path = (current_dir / target_rel_path).resolve()

                if not target_file_path.exists():
                    errors.append(
                        f"[{rel_key}] Broken relative link '{target}': target file does not exist"
                    )
                elif target_anchor:
                    try:
                        target_rel_key = str(target_file_path.relative_to(bundle_dir)).replace(
                            "\\", "/"
                        )
                        if (
                            target_rel_key in file_anchors
                            and target_anchor not in file_anchors[target_rel_key]
                        ):
                            errors.append(
                                f"[{rel_key}] Broken anchor '#{target_anchor}' in target file '{target_rel_key}'"
                            )
                    except ValueError:
                        pass

    return errors


def lint_target_path(
    target_path: Path,
    check_links: bool = True,
    check_currency: bool = False,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    """Lint a file or directory for visual parity, link integrity, and legal currency."""
    result: dict[str, Any] = {
        "files_scanned": 0,
        "format_errors": 0,
        "link_errors": 0,
        "currency_errors": 0,
        "currency_warnings": 0,
        "currency_findings": [],
        "details": [],
    }

    supported_currency_exts = {".md", ".markdown", ".txt", ".pptx", ".docx"}

    if target_path.is_file():
        ext = target_path.suffix.lower()
        if ext in {".md", ".markdown"}:
            result["files_scanned"] = 1
            errs = lint_markdown_file(target_path)
            if errs:
                result["format_errors"] += len(errs)
                result["details"].append({"file": str(target_path), "errors": errs})
            if check_currency:
                c_findings = lint_file_currency(target_path, registry_path=registry_path)
                for f in c_findings:
                    if f["severity"] == "ERROR":
                        result["currency_errors"] += 1
                    else:
                        result["currency_warnings"] += 1
                    result["currency_findings"].append(f)
        elif check_currency and ext in supported_currency_exts:
            result["files_scanned"] = 1
            c_findings = lint_file_currency(target_path, registry_path=registry_path)
            for f in c_findings:
                if f["severity"] == "ERROR":
                    result["currency_errors"] += 1
                else:
                    result["currency_warnings"] += 1
                result["currency_findings"].append(f)

    elif target_path.is_dir():
        scan_exts = supported_currency_exts if check_currency else {".md", ".markdown"}
        target_files = collect_scannable_files(target_path, scan_exts)
        result["files_scanned"] = len(target_files)

        for f in target_files:
            if f.suffix.lower() in {".md", ".markdown"}:
                errs = lint_markdown_file(f)
                if errs:
                    result["format_errors"] += len(errs)
                    result["details"].append({"file": str(f), "errors": errs})

            if check_currency:
                c_findings = lint_file_currency(f, registry_path=registry_path)
                for item in c_findings:
                    if item["severity"] == "ERROR":
                        result["currency_errors"] += 1
                    else:
                        result["currency_warnings"] += 1
                    result["currency_findings"].append(item)

        if check_links:
            link_errs = lint_bundle_links(target_path)
            if link_errs:
                result["link_errors"] += len(link_errs)
                result["details"].append({"file": str(target_path), "link_errors": link_errs})

    result["total_errors"] = (
        result["format_errors"] + result["link_errors"] + result["currency_errors"]
    )
    result["total_warnings"] = result["currency_warnings"]
    return result

#!/usr/bin/env python3
"""microstructure_audit.py - Audits academic writing draft papers for stylistic compliance.

Key features:
- Section-Based Thresholds for passive voice checking.
- Signal Phrases Matcher for Swales & Feak's 3-move CARS model.
- Typo & Abbreviation Dictionary for Vietnamese/BIM terminology.
- Weak verbs and nominalizations detection.
"""

import sys
import re
import os
from pathlib import Path

# Regex Patterns
PASSIVE_VOICE_RE = re.compile(
    r"\b(was|were|is|are|be|been|being|am)\s+([a-z]+ed|shown|done|written|found|made|seen|built|taken|kept|given|run|spent|evaluated|utilized|analyzed|presented|discussed|extracted|created|implemented)\b",
    re.IGNORECASE
)

INTENSIFIERS = {
    "clearly": "Clearly appeals to emotion and lowers objectivity.",
    "obviously": "Obviously assumes facts and reduces scientific tone.",
    "basically": "Basically is too informal for academic writing.",
    "really": "Really is an informal intensifier that should be omitted.",
    "very": "Very is a weak intensifier; select a stronger adjective instead.",
    "fairly": "Fairly reduces preciseness and authority.",
    "rather": "Rather weakens the assertiveness of the claim.",
    "quite": "Quite is vague and adds unnecessary wordiness."
}

NOMINALIZATIONS = {
    r"\bthere\s+(is|are)\b": "Weak existential construction; use an active verb.",
    r"\bprovide\s+(an\s+)?argument\b": "Rườm rà (nominalization); use active verb 'argue'.",
    r"\bmake\s+(a\s+)?decision\b": "Rườm rà (nominalization); use active verb 'decide'.",
    r"\bcause\s+(a\s+)?disruption\b": "Rườm rà (nominalization); use active verb 'disrupt'.",
    r"\bperform\s+(an\s+)?analysis\b": "Rườm rà (nominalization); use active verb 'analyze'."
}

VIETNAMESE_TYPOS = {
    r"\bbetong\b": "bê tông",
    r"\bthep\b": "thép",
    r"\bcua\s+di\b": "cửa đi",
    r"\bxay\s+dung\b": "xây dựng",
    r"\bcb\b": "cảm biến (viết tắt phi tiêu chuẩn)",
    r"\bdt\b": "dự toán (viết tắt phi tiêu chuẩn)",
    r"\bpccc\b": "phòng cháy chữa cháy (viết tắt - khuyến nghị viết rõ)",
    r"\bmep\b": "cơ điện - MEP (viết tắt - khuyến nghị viết rõ)",
    r"\btk\b": "thiết kế (viết tắt phi tiêu chuẩn)",
    r"\btc\b": "thi công (viết tắt phi tiêu chuẩn)"
}

CARS_SIGNALS = {
    "Move 1 (Territory)": [
        "has been widely studied", "play a key role", "recent advances in", 
        "traditionally", "important role", "critical issue", "widely used",
        "đã được nghiên cứu rộng rãi", "đóng vai trò quan trọng", "những tiến bộ gần đây",
        "theo truyền thống", "đóng vai trò quyết định", "áp dụng rộng rãi", "bối cảnh nghiên cứu"
    ],
    "Move 2 (Niche)": [
        "however", "although", "yet", "little research", "remains unclear", 
        "fails to", "is limited", "not fully understood", "challenging task",
        "tuy nhiên", "mặc dù vậy", "chưa được nghiên cứu", "vẫn chưa rõ ràng",
        "còn hạn chế", "chưa được hiểu đầy đủ", "chưa thể phát hiện", "khoảng trống"
    ],
    "Move 3 (Occupy)": [
        "in this paper", "we propose", "this study aims to", "we present", 
        "in this study", "we introduce", "this paper presents",
        "trong bài báo này", "chúng tôi đề xuất", "nghiên cứu này nhằm",
        "chúng tôi trình bày", "trong nghiên cứu này", "giải pháp đề xuất"
    ]
}


def parse_sections(content: str) -> dict[str, list[str]]:
    """Parse Markdown content into academic sections based on heading keywords."""
    sections = {
        "Introduction": [],
        "Methods": [],
        "Results": [],
        "Discussion": [],
        "Other": []
    }
    
    current_section = "Other"
    
    for line in content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("#"):
            # Check for section keywords
            lower_header = trimmed.lower()
            if any(k in lower_header for k in ["introduction", "mở đầu", "mở bài"]):
                current_section = "Introduction"
            elif any(k in lower_header for k in ["method", "material", "phương pháp", "vật liệu"]):
                current_section = "Methods"
            elif any(k in lower_header for k in ["result", "kết quả"]):
                current_section = "Results"
            elif any(k in lower_header for k in ["discussion", "thảo luận"]):
                current_section = "Discussion"
            else:
                current_section = "Other"
        
        sections[current_section].append(line)
        
    return sections


def analyze_passive_voice(lines: list[str]) -> tuple[int, int, float]:
    """Calculate total sentences, passive sentences, and passive voice percentage."""
    text = " ".join(lines)
    # Split text into sentences using simple heuristics
    sentences = [s.strip() for s in re.split(r'\. |\? |\! ', text) if s.strip()]
    if not sentences:
        return 0, 0, 0.0
        
    passive_count = sum(1 for s in sentences if PASSIVE_VOICE_RE.search(s))
    ratio = (passive_count / len(sentences)) * 100
    return len(sentences), passive_count, ratio


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # sys.stdout might not support reconfigure in some test environments
        
    if len(sys.argv) < 2:
        print("Usage: python microstructure_audit.py <path_to_markdown_file>")
        sys.exit(1)
        
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)
        
    content = file_path.read_text(encoding="utf-8")
    sections = parse_sections(content)
    
    print("=" * 60)
    print("ACADEMIC WRITING AUDIT REPORT")
    print(f"Target File: {file_path.name}")
    print("=" * 60)
    
    # 1. Passive Voice Analysis
    print("\n1. PASSIVE VOICE ANALYSIS (Section-Based Thresholds)")
    print("-" * 60)
    
    thresholds = {
        "Introduction": (0, 40, "Max: 40%"),
        "Methods": (60, 80, "Range: 60%-80%"),
        "Results": (0, 40, "Max: 40%"),
        "Discussion": (0, 30, "Max: 30%")
    }
    
    for section_name, (min_t, max_t, desc) in thresholds.items():
        lines = sections[section_name]
        total_s, passive_s, ratio = analyze_passive_voice(lines)
        if total_s == 0:
            print(f"- Section: {section_name} -> No sentences detected.")
            continue
            
        status = "PASS"
        if ratio < min_t or ratio > max_t:
            status = "FAIL"
            
        print(f"- Section: {section_name} ({desc}) -> Actual: {ratio:.1f}% ({passive_s}/{total_s}) [{status}]")
        if status == "FAIL":
            if section_name == "Methods":
                print(f"  [Warning] Methods section has low passive voice ({ratio:.1f}%). Use passive voice to maintain experimental objectivity.")
            elif section_name == "Discussion":
                print(f"  [Warning] Discussion section has excessive passive voice ({ratio:.1f}%). Use active voice ('We found', 'Our results indicate') to convey authority.")
            else:
                print(f"  [Warning] {section_name} section has high passive voice ({ratio:.1f}%). Prefer active voice.")
                
    # 2. Stylistic Checks
    print("\n2. STYLISTIC CHECKS")
    print("-" * 60)
    style_warnings = 0
    
    for idx, line in enumerate(content.splitlines()):
        line_num = idx + 1
        # Skip markdown code blocks
        if line.strip().startswith("```"):
            continue
            
        # Check Intensifiers
        for word, msg in INTENSIFIERS.items():
            pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
            if pattern.search(line):
                print(f"- [L{line_num}] Intensifier Alert: '{word}' - {msg}")
                style_warnings += 1
                
        # Check Nominalizations
        for pattern_str, msg in NOMINALIZATIONS.items():
            pattern = re.compile(pattern_str, re.IGNORECASE)
            if pattern.search(line):
                print(f"- [L{line_num}] Nominalization Alert: '{pattern_str}' - {msg}")
                style_warnings += 1
                
    if style_warnings == 0:
        print("No style warnings found. Excellent job!")
        
    # 3. Vietnamese Typo & Abbreviation Dictionary
    print("\n3. VIETNAMESE TYPO & ABBREVIATION DICTIONARY")
    print("-" * 60)
    typo_warnings = 0
    
    for idx, line in enumerate(content.splitlines()):
        line_num = idx + 1
        if line.strip().startswith("```"):
            continue
            
        for pattern_str, suggest in VIETNAMESE_TYPOS.items():
            pattern = re.compile(pattern_str, re.IGNORECASE)
            if pattern.search(line):
                clean_pattern = pattern_str.replace(r'\b', '')
                print(f"- [L{line_num}] Typo/Abbreviation Alert: '{clean_pattern}' -> Suggest: '{suggest}'")
                typo_warnings += 1
                
    if typo_warnings == 0:
        print("No spelling or abbreviation warnings found.")
        
    # 4. CARS Model Checks (Introduction)
    print("\n4. CARS MODEL CHECKS (Introduction)")
    print("-" * 60)
    intro_text = " ".join(sections["Introduction"]).lower()
    
    for move_name, signals in CARS_SIGNALS.items():
        found = False
        for signal in signals:
            if signal.lower() in intro_text:
                print(f"- {move_name}: Detected ('{signal}')")
                found = True
                break
        if not found:
            print(f"- {move_name}: NOT detected. [Warning] Make sure to explicitly establish, niche, or occupy this move.")
            
    print("=" * 60)


if __name__ == "__main__":
    main()

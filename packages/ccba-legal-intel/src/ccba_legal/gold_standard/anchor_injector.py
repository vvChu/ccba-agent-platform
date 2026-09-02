"""Config-driven Semantic Anchor Injector."""

from __future__ import annotations

import re

from ccba_legal.gold_standard.profiles import DocProfile, get_doc_profile
from ccba_legal.gold_standard.sanitizers import strip_existing_anchors


def inject_semantic_anchors(
    text: str, profile: DocProfile | str | None = None, archetype: str | None = None
) -> str:
    """Inject hidden inline semantic anchors into Markdown text (idempotent)."""
    if isinstance(profile, str) or profile is None:
        p_name = profile or archetype or "vbpl"
        profile = get_doc_profile(str(p_name))
    text = strip_existing_anchors(text)
    lines = text.splitlines()
    processed_lines: list[str] = []
    current_dieu = ""
    for line in lines:
        stripped = line.strip()
        if re.match(r"^([-*]\s+)+", stripped):
            stripped = re.sub(r"^([-*]\s+)+", "- ", stripped)
            line = stripped
        dieu_match = profile.dieu_pattern.match(stripped)
        if dieu_match:
            current_dieu = dieu_match.group(2)
            anchor = f'<a id="dieu-{current_dieu}"></a>'
            processed_lines.append(f"\n{anchor}\n### {dieu_match.group(1)}")
            continue
        sec_match = profile.sec_pattern.match(stripped)
        if sec_match:
            sec_num = sec_match.group(2).replace(".", "-")
            anchor = f'<a id="{profile.section_prefix}-{sec_num}"></a>'
            processed_lines.append(f"\n{anchor}\n### {sec_match.group(1)}")
            continue
        khoan_match = profile.khoan_pattern.match(stripped)
        if khoan_match and current_dieu:
            khoan_num = khoan_match.group(1) or khoan_match.group(2)
            khoan_rest = khoan_match.group(3)
            anchor = f'<a id="dieu-{current_dieu}-khoan-{khoan_num}"></a>'
            processed_lines.append(f"{anchor}\n**{khoan_num}.** {khoan_rest}")
            continue
        processed_lines.append(line)
    return "\n".join(processed_lines)

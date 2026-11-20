"""Markdown AST parser for CCBA PPTX presentation decks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..tables import StructuredTable
from ._deck_models import CardItem, SlideSpec, SlideType

_CALLOUT_KIND_MAP: dict[str, str] = {
    "note": "info",
    "info": "info",
    "tip": "success",
    "important": "warning",
    "warning": "warning",
    "caution": "danger",
    "arch": "arch",
    "struct": "struct",
    "mep": "mep",
    "ai": "ai",
}

_CALLOUT_RE = re.compile(
    r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION|INFO|ARCH|STRUCT|MEP|AI)\]\s*(.*)$",
    re.IGNORECASE,
)


@dataclass
class _SectionParseState:
    """Mutable accumulator state while parsing one markdown slide section."""

    title: str = ""
    subtitle: str = ""
    badge: str = ""
    bullets: list[str] = field(default_factory=list)
    left_col: list[str] = field(default_factory=list)
    right_col: list[str] = field(default_factory=list)
    left_title: str = ""
    right_title: str = ""
    cards: list[CardItem] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    active_step: int = 1
    quote_text: str = ""
    quote_author: str = ""
    notes: str = ""
    table: StructuredTable | None = None
    slide_type: SlideType = SlideType.STANDARD
    in_callout: bool = False
    current_kind: str = "info"
    current_card_title: str = ""
    current_card_body: list[str] = field(default_factory=list)
    is_split: bool = False
    current_col: int = 0
    in_steps: bool = False
    in_big_idea: bool = False
    in_agenda: bool = False
    in_quote: bool = False
    big_idea_lines: list[str] = field(default_factory=list)
    quote_lines: list[str] = field(default_factory=list)


def _extract_heading_and_subtitle(lines: list[str]) -> tuple[str, str, str, int]:
    """Extract optional slide badge, H1/H2 title, H3 subtitle, and body start index."""
    title = ""
    subtitle = ""
    badge = ""
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue
        if line.startswith("# ") or line.startswith("## "):
            raw_title = re.sub(r"^#+\s*", "", line)
            badge_match = re.match(r"^\[([^\]]+)\]\s*(.*)$", raw_title)
            if badge_match:
                badge = badge_match.group(1).strip()
                title = badge_match.group(2).strip()
            else:
                title = raw_title
            idx += 1
            if idx < len(lines) and lines[idx].strip().startswith("### "):
                subtitle = re.sub(r"^###\s*", "", lines[idx].strip())
                idx += 1
            break
        idx += 1
    return title, subtitle, badge, idx


def _handle_directive_line(l_strip: str, state: _SectionParseState) -> bool:
    """Handle `:::` directive openers and closers; return True if line was consumed."""
    if l_strip.startswith("::: big-idea") or l_strip.startswith("::: big_idea"):
        state.in_big_idea = True
        state.slide_type = SlideType.BIG_IDEA
        return True
    if l_strip.startswith("::: steps") or l_strip.startswith("::: process"):
        state.in_steps = True
        state.slide_type = SlideType.STEPS
        return True
    if l_strip.startswith("::: agenda"):
        state.in_agenda = True
        state.slide_type = SlideType.AGENDA
        act_match = re.search(r"active=(\d+)", l_strip)
        if act_match:
            state.active_step = int(act_match.group(1))
        return True
    if l_strip.startswith("::: quote"):
        state.in_quote = True
        state.slide_type = SlideType.QUOTE
        return True
    if l_strip.startswith("::: split"):
        state.is_split = True
        state.current_col = 1
        return True
    if l_strip.startswith("::: col-2") or l_strip.startswith("::: col-right"):
        state.current_col = 2
        return True
    if l_strip.startswith(":::"):
        state.in_big_idea = state.in_steps = state.in_agenda = state.in_quote = False
        state.current_col = 0
        return True
    return False


def _collect_directive_content(l_strip: str, state: _SectionParseState) -> bool:
    """Collect lines inside an active directive block; return True if consumed."""
    if state.in_big_idea:
        if l_strip:
            state.big_idea_lines.append(l_strip)
        return True
    if state.in_quote:
        if l_strip.startswith(("👤", "author:", "--")):
            cleaned_author = l_strip.replace("👤", "").replace("author:", "").replace("--", "")
            state.quote_author = cleaned_author.strip()
        elif l_strip:
            state.quote_lines.append(l_strip)
        return True
    if state.in_steps or state.in_agenda:
        if l_strip.startswith(("- ", "* ")) or re.match(r"^\d+\.\s*", l_strip):
            state.steps.append(re.sub(r"^(?:[-*]|\d+\.)\s*", "", l_strip))
        return True
    return False


def _flush_callout(state: _SectionParseState) -> None:
    """Append the buffered callout CardItem into state.cards and reset buffer."""
    state.cards.append(
        CardItem(
            state.current_card_title,
            "\n".join(state.current_card_body),
            state.current_kind,
        )
    )
    state.current_card_body = []


def _handle_callout_line(l_strip: str, state: _SectionParseState) -> bool:
    """Handle callout headers and blockquote continuation lines; return True if consumed."""
    callout_match = _CALLOUT_RE.match(l_strip)
    if callout_match:
        if state.in_callout and state.current_card_title:
            _flush_callout(state)
        state.in_callout = True
        kind_str = callout_match.group(1).lower()
        state.current_kind = _CALLOUT_KIND_MAP.get(kind_str, "info")
        state.current_card_title = callout_match.group(2).strip() or kind_str.upper()
        return True
    if not state.in_callout:
        return False
    if l_strip.startswith(">"):
        state.current_card_body.append(l_strip.lstrip("> ").strip())
        return True
    if l_strip == "":
        return True
    _flush_callout(state)
    state.in_callout = False
    return False


def _handle_split_or_standard_line(l_strip: str, state: _SectionParseState) -> None:
    """Handle 2-column split content or standard slide bullets/subtitles."""
    if state.is_split:
        is_heading = l_strip.startswith(("### ", "## "))
        is_bullet = l_strip.startswith(("- ", "* "))
        if state.current_col == 1:
            if is_heading:
                state.left_title = re.sub(r"^#+\s*", "", l_strip)
            elif is_bullet:
                state.left_col.append(l_strip[2:].strip())
            elif l_strip:
                state.left_col.append(l_strip)
        elif state.current_col == 2:
            if is_heading:
                state.right_title = re.sub(r"^#+\s*", "", l_strip)
            elif is_bullet:
                state.right_col.append(l_strip[2:].strip())
            elif l_strip:
                state.right_col.append(l_strip)
        return
    if state.table:
        return
    if l_strip.startswith("### ") and not state.subtitle:
        state.subtitle = l_strip[4:].strip()
    elif l_strip.startswith(("- ", "* ")):
        state.bullets.append(l_strip[2:].strip())
    elif l_strip.startswith(("1. ", "2. ", "3. ")):
        state.bullets.append(l_strip[3:].strip())
    elif l_strip.startswith("👤 ") and not state.quote_author:
        state.quote_author = l_strip.replace("👤 ", "").strip()


def _finalize_section_spec(state: _SectionParseState) -> SlideSpec:
    """Finalize parsed state into a SlideSpec with resolved slide_type."""
    if state.in_callout and state.current_card_title:
        _flush_callout(state)
    if state.big_idea_lines:
        state.quote_text = " ".join(state.big_idea_lines)
    elif state.quote_lines:
        state.quote_text = " ".join(state.quote_lines)

    story_types = (SlideType.BIG_IDEA, SlideType.STEPS, SlideType.AGENDA, SlideType.QUOTE)
    if state.slide_type not in story_types:
        if state.cards and len(state.cards) >= 1:
            state.slide_type = SlideType.CARDS
        elif state.is_split or (state.left_col and state.right_col):
            state.slide_type = SlideType.SPLIT

    return SlideSpec(
        title=state.title or "NỘI DUNG THUYẾT TRÌNH",
        subtitle=state.subtitle,
        slide_type=state.slide_type,
        badge=state.badge,
        bullets=state.bullets,
        left_column=state.left_col,
        right_column=state.right_col,
        left_title=state.left_title,
        right_title=state.right_title,
        table=state.table,
        cards=state.cards,
        steps=state.steps,
        active_step=state.active_step,
        quote_text=state.quote_text,
        quote_author=state.quote_author,
        notes=state.notes.strip(),
    )


def _is_table_separator_row(line: str) -> bool:
    """Return True when a markdown line is a valid pipe-table separator row."""
    cells = [c.strip() for c in line.strip("|").split("|")]
    return bool(cells) and all(c and set(c).issubset({"-", ":", " "}) for c in cells)


class MarkdownDeckParser:
    """Parses markdown text into a sequence of SlideSpec AST nodes."""

    @classmethod
    def parse_markdown(cls, md_text: str) -> list[SlideSpec]:
        """Parse full markdown document into a list of SlideSpecs."""
        specs: list[SlideSpec] = []
        raw_text = md_text.strip()
        if raw_text.startswith("---"):
            parts = raw_text.split("---", 2)
            if len(parts) >= 3:
                cover_spec = cls._parse_frontmatter(parts[1].strip())
                specs.append(cover_spec)
                raw_text = parts[2].strip()

        raw_slides = re.split(r"\n\s*(?:---|___|\*\*\*)\s*\n", raw_text)
        for sec in raw_slides:
            sec_clean = sec.strip()
            if not sec_clean:
                continue
            slide_spec = cls._parse_section(sec_clean)
            if slide_spec:
                specs.append(slide_spec)
        return specs

    @classmethod
    def _parse_frontmatter(cls, yaml_str: str) -> SlideSpec:
        """Extract metadata from YAML frontmatter into a Cover SlideSpec."""
        title = ""
        subtitle = ""
        author = ""
        date = ""
        org = "TRUNG TÂM TƯ VẤN & ỨNG DỤNG BIM TRONG XÂY DỰNG (CCBA) — VIỆN KHCN XÂY DỰNG (IBST)"
        for line in yaml_str.splitlines():
            line = line.strip()
            if line.startswith("title:"):
                title = line[6:].strip().strip("\"'")
            elif line.startswith("subtitle:"):
                subtitle = line[9:].strip().strip("\"'")
            elif line.startswith(("author:", "speaker:")):
                author = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("date:"):
                date = line[5:].strip().strip("\"'")
            elif line.startswith(("org:", "organization:")):
                org = line.split(":", 1)[1].strip().strip("\"'")

        return SlideSpec(
            title=title or "BÁO CÁO KỸ THUẬT & HỘI THẢO CHUYÊN ĐỀ",
            subtitle=subtitle,
            slide_type=SlideType.COVER,
            author=author,
            date=date,
            organization=org,
        )

    @classmethod
    def _parse_section(cls, sec_text: str) -> SlideSpec | None:
        """Parse an individual markdown section into a SlideSpec."""
        lines = sec_text.splitlines()
        if not lines:
            return None
        title, subtitle, badge, idx = _extract_heading_and_subtitle(lines)
        content_lines = lines[idx:]
        table = cls._parse_markdown_table(content_lines)
        state = _SectionParseState(
            title=title,
            subtitle=subtitle,
            badge=badge,
            table=table,
            slide_type=SlideType.TABLE if table else SlideType.STANDARD,
        )
        for line in content_lines:
            l_strip = line.strip()
            if l_strip.startswith("<!-- notes:") or l_strip.startswith("> **Speaker Notes:**"):
                note = l_strip.replace("<!-- notes:", "").replace("-->", "")
                state.notes += note.replace("> **Speaker Notes:**", "").strip() + " "
            elif _handle_directive_line(l_strip, state):
                continue
            elif _collect_directive_content(l_strip, state):
                continue
            elif _handle_callout_line(l_strip, state):
                continue
            else:
                _handle_split_or_standard_line(l_strip, state)
        return _finalize_section_spec(state)

    @classmethod
    def _parse_markdown_table(cls, lines: list[str]) -> StructuredTable | None:
        """Parse pipe table lines into a StructuredTable object."""
        table_lines: list[str] = []
        in_table = False
        for i, line in enumerate(lines):
            l_strip = line.strip()
            if not l_strip or "|" not in l_strip:
                if in_table:
                    break
                continue
            if not in_table:
                if i + 1 < len(lines) and _is_table_separator_row(lines[i + 1].strip()):
                    in_table = True
                    table_lines.append(l_strip)
                continue
            table_lines.append(l_strip)

        if len(table_lines) < 2:
            return None
        headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
        rows = [
            [c.strip() for c in line.strip("|").split("|")]
            for idx, line in enumerate(table_lines[1:], start=1)
            if not (idx == 1 and _is_table_separator_row(line))
        ]
        if not headers or not rows:
            return None
        return StructuredTable(
            table_id="slide_table",
            num="1",
            title="Bảng số liệu",
            headers=headers,
            rows=rows,
            cols_count=len(headers),
        )

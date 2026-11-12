"""Deterministic C4 artifact verification engine for /ccba-book-compiler (v1.5.0)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment]

_THIS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _THIS_DIR.parents[3] / "scripts"
for _p in (str(_THIS_DIR), str(_SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.config import cfg  # noqa: E402
from core.frontmatter import extract_body, normalize_stem, parse_frontmatter  # noqa: E402
from core.markdown_sanitizer import (  # noqa: E402
    detect_ascii_box_art,
    has_chained_mermaid_edges,
    strip_fenced_code_blocks,
)
from pipeline.post_process import _validate_quality  # noqa: E402
from services.wiki_health.linter import (  # noqa: E402
    _LINK_PATTERN,
    MEDIA_EXTENSIONS,
    LintReport,
    VaultLinter,
)
from verify_excalidraw_map import verify_single_excalidraw  # noqa: E402

_CHIMERIC_MERMAID_RE = re.compile(
    r'(?:<=+\s*"[^"]+"\s*=+>|-\.\s*"[^"]+"\s*[-.]*->|(?<!<)=+\s*"[^"]+"\s*=+>|<\.->)'
)
_MD_TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$", re.MULTILINE)


def verify_corpus_and_toc(corpus_dir: Path, toc_path: Path | None) -> list[str]:
    """Verify corpus has zero raw PNG/JPEG files, WebP <= 1200px, and non-empty valid TOC files."""
    if not corpus_dir.is_dir():
        return [f"Missing corpus directory: {corpus_dir}"]
    errors: list[str] = []
    if (corpus_dir / ".incomplete_corpus").exists():
        errors.append(f"Incomplete corpus marker present in: {corpus_dir}")
    for p in sorted(corpus_dir.rglob("*"), key=lambda x: str(x)):
        if not p.is_file():
            continue
        if p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            errors.append(f"Raw un-transcoded image in corpus: {p.name}")
        elif p.suffix.lower() == ".webp":
            if Image is None:
                errors.append(f"Pillow (PIL) required to verify WebP dimensions: {p.name}")
            else:
                try:
                    with Image.open(p) as img:
                        if max(img.size) > 1200:
                            errors.append(f"WebP exceeds 1200px ({img.size}): {p.name}")
                except OSError as exc:
                    errors.append(f"Corrupt WebP {p.name}: {exc}")
    orig_toc = corpus_dir / "_toc_original.json"
    if not orig_toc.is_file():
        errors.append(f"Missing _toc_original.json in corpus: {orig_toc}")
    else:
        errors.extend(_verify_toc_chapters(corpus_dir, orig_toc))
    if toc_path is not None:
        if not toc_path.is_file():
            errors.append(f"Missing workspace TOC file: {toc_path}")
        else:
            errors.extend(_verify_toc_chapters(corpus_dir, toc_path))
    return errors


def _verify_toc_chapters(corpus_dir: Path, toc_file: Path) -> list[str]:
    """Validate TOC JSON syntax, non-empty chapters list, and in-corpus .md chapter existence."""
    errors: list[str] = []
    try:
        toc = json.loads(toc_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Invalid TOC JSON {toc_file}: {exc}"]
    chapters = toc.get("chapters") if isinstance(toc, dict) else None
    if not isinstance(chapters, list) or not chapters:
        return [f"TOC has empty or invalid chapters list ({toc_file.name})"]
    resolved_corpus = corpus_dir.resolve()
    for idx, ch in enumerate(chapters, start=1):
        if not isinstance(ch, dict):
            errors.append(f"TOC chapter #{idx} is not an object ({toc_file.name})")
            continue
        ep_file = ch.get("epub_file")
        if not isinstance(ep_file, str) or not ep_file.endswith(".md"):
            errors.append(
                f"TOC chapter #{idx} missing valid .md epub_file ({toc_file.name}): {ep_file!r}"
            )
            continue
        candidate = (corpus_dir / ep_file).resolve()
        if candidate.parent != resolved_corpus or not candidate.is_file():
            errors.append(f"TOC epub_file missing or escapes corpus ({toc_file.name}): {ep_file}")
    return errors


def _check_mermaid_and_entity_hygiene(txt: str, filename: str) -> list[str]:
    """Detect chimeric Mermaid arrows inside mermaid fences and #40;/#41; leakage outside fences."""
    body = extract_body(txt)
    errors: list[str] = []
    in_mermaid = False
    in_other_fence = False
    for line_no, raw_line in enumerate(body.split("\n"), start=1):
        stripped = raw_line.lstrip(">").strip()
        if not in_other_fence and not in_mermaid and stripped.startswith("```mermaid"):
            in_mermaid = True
        elif in_mermaid and stripped.startswith("```"):
            in_mermaid = False
        elif in_mermaid:
            if _CHIMERIC_MERMAID_RE.search(raw_line):
                errors.append(f"Chimeric Mermaid edge syntax in {filename} (body line {line_no})")
        elif stripped.startswith(("```", "~~~")):
            in_other_fence = not in_other_fence
        elif not in_other_fence and ("#40;" in raw_line or "#41;" in raw_line):
            errors.append(
                f"Leaked HTML entity (#40;/#41;) outside Mermaid in {filename} (body line {line_no})"
            )
    if in_mermaid or in_other_fence:
        errors.append(f"Unclosed fenced code block in {filename}")
    return errors


def _resolve_note_profile(note_path: Path, fm: dict[str, Any], forced_profile: str | None) -> str:
    """Resolve verification profile ('source', 'topic', or 'concept')."""
    if forced_profile in {"source", "topic", "concept"}:
        return forced_profile
    raw_type = str(fm.get("type") or "").strip().lower()
    if raw_type in {"source", "topic", "concept"}:
        return raw_type
    parent = note_path.parent.name.lower()
    if parent == "sources":
        return "source"
    return "topic" if parent == "topics" else "concept"


def _check_source_profile(
    cp: Path, txt: str, fm: dict[str, Any], tags: list[str], *, extended: bool
) -> list[str]:
    """Validate source note schema and reject un-enriched Phase 1 stubs."""
    errors: list[str] = []
    if str(fm.get("type") or "").strip().lower() != "source":
        errors.append(f"Invalid source type '{fm.get('type')}' in {cp.name}")
    if str(fm.get("origin") or "").strip().lower() != "book":
        errors.append(f"Missing 'origin: book' in source note {cp.name}")
    if "knowledge" not in tags:
        errors.append(f"Missing 'knowledge' tag in source note {cp.name}")
    if not str(fm.get("source") or "").strip():
        errors.append(f"Missing 'source:' filename field in source note {cp.name}")
    if extended:
        if "Source summary pending ingestion." in txt:
            errors.append(f"Un-enriched Phase 1 stub placeholder still present in {cp.name}")
        if "source/book" not in tags:
            errors.append(f"Missing 'source/book' tag in source note {cp.name}")
        aliases = fm.get("aliases")
        if not isinstance(aliases, list) or not any(str(a).strip() for a in aliases):
            errors.append(f"Missing non-empty 'aliases' list in source note {cp.name}")
    return errors


def _check_profile_specific_rules(
    cp: Path, txt: str, fm: dict[str, Any], profile: str, *, check_extended_schema: bool = True
) -> list[str]:
    """Validate schema and quality rules specific to source, topic, or concept notes."""
    origin = str(fm.get("origin") or "").strip().lower()
    tags = (
        [str(t).strip() for t in (fm.get("tags") or [])] if isinstance(fm.get("tags"), list) else []
    )
    if profile == "source":
        return _check_source_profile(cp, txt, fm, tags, extended=check_extended_schema)
    errors: list[str] = []
    if profile == "topic":
        if origin not in {"book", "command"}:
            errors.append(
                f"Invalid topic origin '{origin}' in {cp.name}; expected 'book' or 'command'"
            )
        if (
            check_extended_schema
            and origin == "book"
            and str(fm.get("source_type") or "").strip().lower() != "compiled"
        ):
            errors.append(f"Book-compiled topic {cp.name} missing 'source_type: compiled'")
        body = strip_fenced_code_blocks(extract_body(txt))
        if check_extended_schema and ".excalidraw" in body:
            after_embed = body.split(".excalidraw", 1)[1]
            if not _MD_TABLE_SEP_RE.search(after_embed):
                errors.append(
                    f"Topic {cp.name} embeds Excalidraw without mandatory Markdown spec table below embed"
                )
        return errors
    if origin != "book":
        errors.append(f"Missing 'origin: book' in {cp.name}")
    if "## 📖 Bản gốc & Ngữ cảnh mở rộng (Ground Truth)" not in txt:
        errors.append(f"Missing Ground Truth section in {cp.name}")
    hooks = [ln for ln in txt.split("## Core Idea")[0].splitlines() if ln.strip().startswith('> "')]
    if not (1 <= len(hooks) <= 3):
        errors.append(f"Invalid hook count ({len(hooks)}) in {cp.name}; expected 1..3")
    if check_extended_schema:
        for q_err in _validate_quality(txt, cp.stem):
            errors.append(f"Quality gate failed in {cp.name}: {q_err}")
    return errors


def verify_single_markdown_note(
    cp: Path, forced_profile: str | None = None, *, check_extended_schema: bool = True
) -> list[str]:
    """Verify ergonomics and profile invariants for a source, concept, or topic markdown file."""
    errors: list[str] = []
    if re.search(r"_[2-9]\.md$", cp.name):
        errors.append(f"Duplicate suffix file prohibited: {cp.name}")
    if not cp.is_file():
        return [*errors, f"Missing markdown file: {cp}"]
    txt = cp.read_text(encoding="utf-8")
    fm = parse_frontmatter(txt) or {}
    profile = _resolve_note_profile(cp, fm, forced_profile)
    print(f"[BOOK-VERIFY-ROUTE] {cp.name} -> profile={profile}")
    if box_lines := detect_ascii_box_art(txt):
        errors.append(f"ASCII/Unicode box-art detected in {cp.name} at fence line(s): {box_lines}")
    if chained := has_chained_mermaid_edges(txt):
        errors.append(f"Chained Mermaid edges (>=2 ops/line) in {cp.name} at line(s): {chained}")
    errors.extend(_check_mermaid_and_entity_hygiene(txt, cp.name))
    if re.search(r"`!?\[\[.*?\]\]`", strip_fenced_code_blocks(txt)):
        errors.append(f"Code-pill wikilink found in {cp.name}")
    errors.extend(
        _check_profile_specific_rules(
            cp, txt, fm, profile, check_extended_schema=check_extended_schema
        )
    )
    return errors


def verify_concepts_and_excalidraw(
    concepts: list[Path], excalidraw_path: Path | None, topics: list[Path] | None = None
) -> list[str]:
    """Backward-compatible routing helper for unit tests calling _verify_concepts_and_excalidraw."""
    errors: list[str] = []
    seen: set[Path] = set()
    for cp in sorted(concepts, key=lambda x: str(x)):
        seen.add(cp)
        errors.extend(
            verify_single_markdown_note(cp, forced_profile=None, check_extended_schema=False)
        )
    for tp in sorted(topics or [], key=lambda x: str(x)):
        if tp not in seen:
            errors.extend(
                verify_single_markdown_note(tp, forced_profile="topic", check_extended_schema=False)
            )
    if excalidraw_path and excalidraw_path.is_file():
        errors.extend(verify_single_excalidraw(excalidraw_path))
    return errors


def _collect_fallback_media_names() -> set[str]:
    """Lazily collect lowercased media filenames via os.walk (zero per-file stat over FUSE)."""
    import os

    names: set[str] = set()
    for root in [cfg.resources_books_dir, cfg.archive_dir]:
        if not root.is_dir():
            continue
        for _dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for fname in sorted(filenames):
                low = fname.lower()
                names.add(low)
                if low.endswith(".excalidraw.md"):
                    names.add(low[:-3])
    return names


def _media_embed_exists(
    link: str, corpus_dir: Path, excalidraw_files: list[Path], fallback_cache: dict[str, set[str]]
) -> bool:
    """Resolve media/diagram embed via O(1) direct paths before lazy fallback scan."""
    low = link.lower()
    for ep in excalidraw_files:
        if ep.is_file() and (
            ep.name.lower() == low
            or (ep.name.lower().endswith(".excalidraw.md") and ep.name[:-3].lower() == low)
        ):
            return True
    attach_dir = cfg.vault_root / "03 - Resources" / "attachments"
    direct_candidates = [
        corpus_dir / link,
        attach_dir / link,
        attach_dir / f"{link}.md",
        cfg.vault_root / link,
    ]
    if any(cand.is_file() for cand in direct_candidates):
        return True
    if "names" not in fallback_cache:
        fallback_cache["names"] = _collect_fallback_media_names()
    return low in fallback_cache["names"]


def _augment_linter_stems(linter: VaultLinter, target_files: list[Path], corpus_dir: Path) -> None:
    """Register stems and aliases of newly compiled batch files and corpus chapters into VaultLinter."""
    if corpus_dir.is_dir():
        for ch_f in sorted(corpus_dir.rglob("*.md"), key=lambda p: str(p)):
            linter.existing_stems.add(normalize_stem(ch_f.stem))
    for fp in sorted(target_files, key=lambda p: str(p)):
        if not fp.is_file():
            continue
        linter.existing_stems.add(normalize_stem(fp.stem))
        fm = parse_frontmatter(fp.read_text(encoding="utf-8")) or {}
        aliases = fm.get("aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                if alias and isinstance(alias, str):
                    linter.existing_stems.add(normalize_stem(alias))


def verify_batch_body_links(
    target_files: list[Path], corpus_dir: Path, excalidraw_files: list[Path]
) -> list[str]:
    """Verify 0 broken_body_links via VaultLinter parity plus physical media embed existence."""
    valid_targets = [p for p in sorted(set(target_files), key=lambda x: str(x)) if p.is_file()]
    if not valid_targets:
        return []
    linter = VaultLinter()
    _augment_linter_stems(linter, valid_targets, corpus_dir)
    fallback_cache: dict[str, set[str]] = {}
    report: LintReport = {
        "broken_links": [],
        "broken_body_links": [],
        "prospective_related_seeds": [],
    }
    errors: list[str] = []
    for fp in valid_targets:
        txt = fp.read_text(encoding="utf-8")
        clean_body = strip_fenced_code_blocks(extract_body(txt), strip_multi_token_inline=True)
        links = [
            lnk.strip().rstrip("\\") for lnk in _LINK_PATTERN.findall(clean_body) if lnk.strip()
        ]
        seen_broken: set[tuple[str, str]] = set()
        for link in links:
            if any(link.lower().endswith(ext) for ext in MEDIA_EXTENSIONS):
                if not _media_embed_exists(link, corpus_dir, excalidraw_files, fallback_cache):
                    errors.append(f"Broken media/diagram embed in {fp.name}: '[[{link}]]'")
            else:
                linter._record_link_target(fp.stem, link, "body", report, set(), seen_broken)
    for broken in report["broken_body_links"]:
        errors.append(f"Broken body wikilink in {broken['from']}.md: '[[{broken['to']}]]'")
    return errors


def run_book_verification(args: argparse.Namespace) -> int:
    """Execute full C4 verification across corpus, TOC, source, concepts, topics, Excalidraw, and links."""
    corpus_dir = Path(args.dir)
    toc_p = Path(args.toc) if getattr(args, "toc", None) else None
    errs = verify_corpus_and_toc(corpus_dir, toc_p)

    source_p = Path(args.source) if getattr(args, "source", None) else None
    concepts = [Path(c) for c in (getattr(args, "concepts", None) or [])]
    topics = [Path(t) for t in (getattr(args, "topics", None) or [])]
    raw_excal = getattr(args, "excalidraw", None) or []
    excalidraws = [Path(raw_excal)] if isinstance(raw_excal, str) else [Path(e) for e in raw_excal]

    seen: set[Path] = set()
    if source_p is not None:
        seen.add(source_p)
        errs.extend(verify_single_markdown_note(source_p, forced_profile="source"))
    for cp in sorted(concepts, key=lambda x: str(x)):
        if cp not in seen:
            seen.add(cp)
            errs.extend(verify_single_markdown_note(cp, forced_profile=None))
    for tp in sorted(topics, key=lambda x: str(x)):
        if tp not in seen:
            seen.add(tp)
            errs.extend(verify_single_markdown_note(tp, forced_profile="topic"))
    for ep in sorted(excalidraws, key=lambda x: str(x)):
        errs.extend(verify_single_excalidraw(ep))

    errs.extend(verify_batch_body_links(list(seen), corpus_dir, excalidraws))
    if errs:
        for err in errs:
            print(f"[BOOK-VERIFY-FAIL] {err}", file=sys.stderr)
        return 1
    print("[BOOK-VERIFY-OK] All book compilation artifacts passed C4 verification.")
    return 0

"""graduation.py - Closed-Loop Graduation Supersession & Layer-2 Rules Link Parity (Issue #520).

Handles archiving pre-graduation Spoke drafts in .md/knowledge/* into .md/knowledge/archive/
with a Canonical Pointer Stub, syncing Layer 2 constitutional rules into <spoke>/.agents/rules/,
normalizing relative links in <spoke>/.agents/AGENTS.md, and running in-process LinkAuditor
checks on Spoke markdown entrypoints.
"""

from __future__ import annotations

import hashlib
import re
import shutil
from collections.abc import Callable
from pathlib import Path

import yaml

from .base import are_text_files_identical

GRADUATED_STUB_MARKER = "<!-- CCBA_GRADUATED_STUB -->"

CORE_LAYER2_RULES: tuple[str, ...] = (
    "docs/rules/execution_guardrails.md",
    "docs/rules/git_conventions.md",
    "docs/rules/code_quality.md",
    ".github/bugbot-rules.md",
)

DEFAULT_GRADUATED_SPOKE_DOCS: dict[str, dict[str, str]] = {
    ".md/knowledge/platform_aware_kiss_standard.md": {
        "hub_adr": "docs/adr/0061-platform-aware-kiss-v2-and-quarantine-governance.md",
        "spoke_rule": ".agents/rules/code_quality.md",
        "summary": (
            "Tiêu chuẩn Platform-Aware KISS v2.0 và cơ chế cách ly `# ccba:quarantine` "
            "(thay thế cú pháp nháp `# ccba:seam-escape`) đã được chuẩn hóa thành Hiến pháp "
            "Layer 1 & Layer 2 tại Hub (ADR-0061)."
        ),
    },
}

INVARIANT_KEY_ALIASES: dict[str, str] = {
    "reuse-first gate": "reuse-first gate & platform-aware kiss",
    "automation-first quality": "automation-first quality & deterministic hard completion lock",
}


def normalize_invariant_key(key: str) -> str:
    """Normalizes a Core Invariant bullet title for version-resilient deduplication.

    Args:
        key: Raw invariant key extracted from bold markdown bullet.

    Returns:
        Canonical lowercase key with trailing ADR/version tags stripped.
    """
    cleaned = key.strip().rstrip(":").strip().lower()
    cleaned = re.sub(r"\s*\(adr[- ]?\d+\)\s*$", "", cleaned)
    cleaned = re.sub(r"\s+v\d+(?:\.\d+)*\s*$", "", cleaned)
    cleaned = cleaned.strip()
    return INVARIANT_KEY_ALIASES.get(cleaned, cleaned)


def split_markdown_sections(text: str) -> list[tuple[str, str]]:
    """Splits markdown text into (heading, section_body) tuples at level-2 headings.

    Args:
        text: Full markdown string.

    Returns:
        Ordered list of (heading, raw_section_text) pairs.
    """
    lines = text.splitlines(keepends=True)
    sections: list[tuple[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if current_lines or current_heading:
                sections.append((current_heading, "".join(current_lines)))
                current_lines = []
            current_heading = line.strip()
        current_lines.append(line)
    if current_lines or current_heading:
        sections.append((current_heading, "".join(current_lines)))
    return sections


def merge_core_invariants_block(
    hub_inv_content: str,
    spoke_inv_content: str,
    parse_fn: Callable[[str], tuple[str, list[tuple[str, str]]]],
) -> str:
    """Merges Hub and Spoke Core Invariants while deduplicating evolved Hub keys.

    Args:
        hub_inv_content: Raw markdown of Hub's '## Core Invariants' section.
        spoke_inv_content: Raw markdown of Spoke's '## Core Invariants' section.
        parse_fn: Parser function returning (preamble, list of (key, item_text)).

    Returns:
        Merged '## Core Invariants' section string.
    """
    _, hub_items = parse_fn(hub_inv_content)
    _, spoke_items = parse_fn(spoke_inv_content)
    hub_keys_norm = {normalize_invariant_key(k) for k, _ in hub_items}
    custom_spoke_items = [
        item_text for k, item_text in spoke_items if normalize_invariant_key(k) not in hub_keys_norm
    ]
    if not custom_spoke_items:
        return hub_inv_content
    clean_hub_inv = hub_inv_content.rstrip()
    joined_spoke = "".join(
        item if item.endswith("\n") else item + "\n" for item in custom_spoke_items
    )
    return f"{clean_hub_inv}\n{joined_spoke}\n"


def normalize_spoke_agents_links(content: str, spoke_root: Path | None = None) -> str:
    """Normalizes Hub-relative Layer 2 rule links in Spoke .agents/AGENTS.md (COND-01).

    Args:
        content: Merged AGENTS.md markdown content.
        spoke_root: Optional Spoke root directory to check existence of CONTEXT.md / docs/adr/.

    Returns:
        Normalized markdown string with LF line endings and valid relative links.
    """
    normalized = content.replace("\r\n", "\n")
    normalized = re.sub(
        r"\]\((?:\.\./)?docs/rules/([a-zA-Z0-9_-]+\.md(?:#[a-zA-Z0-9_-]+)?)\)",
        r"](rules/\1)",
        normalized,
    )
    normalized = re.sub(
        r"\]\((?:\.\./)?\.github/bugbot-rules\.md((?:#[a-zA-Z0-9_-]+)?)\)",
        r"](rules/bugbot-rules.md\1)",
        normalized,
    )
    if spoke_root is not None:
        if not (spoke_root / "CONTEXT.md").exists():
            normalized = re.sub(
                r"\[`?CONTEXT\.md`?\]\(\.\./CONTEXT\.md\)", "`CONTEXT.md`", normalized
            )
        if not (spoke_root / "docs" / "adr").exists():
            normalized = re.sub(r"\[`?docs/adr/`?\]\(\.\./docs/adr/\)", "`docs/adr/`", normalized)
    return normalized


def sync_layer2_rules(
    spoke_root: Path,
    hub_root: Path,
    dry_run: bool = False,
) -> list[dict[str, str]]:
    """Syncs core Layer 2 rule documents from Hub to <spoke>/.agents/rules/ (Issue #520).

    Args:
        spoke_root: Target Spoke workspace root directory.
        hub_root: Source Hub repository root directory.
        dry_run: If True, simulates actions without modifying disk.

    Returns:
        List of synchronization action dictionaries for reporting.
    """
    actions: list[dict[str, str]] = []
    spoke_rules_dir = spoke_root / ".agents" / "rules"
    for rel_src in CORE_LAYER2_RULES:
        src = hub_root / rel_src
        if not src.exists():
            continue
        dest = spoke_rules_dir / src.name
        if src.resolve() == dest.resolve():
            status = "UNCHANGED"
        elif not dest.exists():
            status = "NEW"
        elif are_text_files_identical(src, dest):
            status = "UNCHANGED"
        else:
            status = "UPDATED"
        actions.append(
            {
                "type": "Rule",
                "name": f"rules/{src.name}",
                "status": status,
                "path": str(dest.relative_to(spoke_root)),
            }
        )
        if not dry_run and status in ("NEW", "UPDATED"):
            spoke_rules_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    return actions


def _extract_proposal_graduations(proposal_file: Path) -> dict[str, dict[str, str]]:
    """Extracts superseded spoke doc mappings from a single proposal YAML frontmatter."""
    try:
        raw = proposal_file.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not raw.startswith("---"):
        return {}
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        meta = yaml.safe_load(parts[1])
    except Exception:
        return {}
    if not isinstance(meta, dict) or str(meta.get("status", "")).lower() not in (
        "merged",
        "graduated",
    ):
        return {}
    superseded = meta.get("supersedes_spoke_docs")
    if not isinstance(superseded, list):
        return {}
    graduated_to = str(meta.get("graduated_to") or "docs/adr/")
    spoke_rule = str(meta.get("spoke_rule") or ".agents/rules/code_quality.md")
    result: dict[str, dict[str, str]] = {}
    for item in superseded:
        if isinstance(item, str) and item.strip():
            result[item.strip().replace("\\", "/")] = {
                "hub_adr": graduated_to,
                "spoke_rule": spoke_rule,
                "summary": f"Đã tốt nghiệp qua đề xuất `{proposal_file.name}`.",
            }
    return result


def load_graduated_spoke_docs(hub_root: Path) -> dict[str, dict[str, str]]:
    """Loads graduated Spoke document mappings from defaults and .agents/proposals/*.md.

    Args:
        hub_root: Hub repository root directory.

    Returns:
        Mapping from Spoke-relative draft path to graduation metadata.
    """
    registry: dict[str, dict[str, str]] = {
        k: dict(v) for k, v in DEFAULT_GRADUATED_SPOKE_DOCS.items()
    }
    proposals_dir = hub_root / ".agents" / "proposals"
    if not proposals_dir.is_dir():
        return registry
    for prop_path in sorted(proposals_dir.glob("*.md"), key=lambda p: p.stem):
        if prop_path.name == "TEMPLATE.md":
            continue
        registry.update(_extract_proposal_graduations(prop_path))
    return registry


def _render_graduated_stub(rel_path: str, meta: dict[str, str], archive_rel: str) -> str:
    """Renders the Canonical Pointer Stub replacing a graduated Spoke draft."""
    hub_adr = meta.get("hub_adr", "docs/adr/")
    spoke_rule = meta.get("spoke_rule", ".agents/rules/code_quality.md")
    summary = meta.get("summary", "Tài liệu này đã được chuẩn hóa và hợp nhất lên Hub SSOT.")
    return (
        f"{GRADUATED_STUB_MARKER}\n"
        f"# [GRADUATED TO HUB] {Path(rel_path).name}\n\n"
        f"> [!IMPORTANT]\n"
        f"> **Tài liệu bản thảo cục bộ này đã tốt nghiệp (Graduated) và được thay thế bởi chuẩn chính thức từ Hub.**\n"
        f"> - {summary}\n"
        f"> - **Quy tắc Layer 2 tại Spoke:** [`{spoke_rule}`](../../{spoke_rule})\n"
        f"> - **Tài liệu kiến trúc tại Hub (SSOT):** `{hub_adr}`\n"
        f"> - **Bản lưu trữ lịch sử (Archive):** [`{Path(archive_rel).name}`](archive/{Path(archive_rel).name})\n"
    )


def _archive_and_write_stub(target_file: Path, archive_dir: Path, stub_content: str) -> None:
    """Archives original Spoke draft with SHA-256 collision branching and writes stub (COND-02)."""
    content_norm = target_file.read_text(encoding="utf-8").replace("\r\n", "\n")
    archive_dir.mkdir(parents=True, exist_ok=True)
    canonical_archive = archive_dir / target_file.name
    if canonical_archive.exists():
        existing_norm = canonical_archive.read_text(encoding="utf-8").replace("\r\n", "\n")
        if existing_norm != content_norm:
            sha8 = hashlib.sha256(content_norm.encode("utf-8")).hexdigest()[:8]
            branched = archive_dir / f"{target_file.stem}.{sha8}{target_file.suffix}"
            branched.write_text(content_norm, encoding="utf-8", newline="\n")
    else:
        canonical_archive.write_text(content_norm, encoding="utf-8", newline="\n")
    target_file.write_text(stub_content, encoding="utf-8", newline="\n")


def supersede_graduated_spoke_docs(
    spoke_root: Path,
    hub_root: Path,
    dry_run: bool = False,
) -> list[dict[str, str]]:
    """Archives graduated Spoke drafts in .md/knowledge/* and replaces with pointer stubs (COND-02).

    Args:
        spoke_root: Target Spoke root directory.
        hub_root: Source Hub root directory.
        dry_run: If True, simulates actions without modifying disk.

    Returns:
        List of action dictionaries for sync table reporting.
    """
    actions: list[dict[str, str]] = []
    spoke_resolved = spoke_root.resolve()
    graduated_map = load_graduated_spoke_docs(hub_root)
    for rel_path, meta in sorted(graduated_map.items(), key=lambda item: item[0]):
        target_file = (spoke_resolved / rel_path).resolve()
        if not target_file.is_relative_to(spoke_resolved) or not target_file.is_file():
            continue
        raw_text = target_file.read_text(encoding="utf-8").replace("\r\n", "\n")
        archive_dir = target_file.parent / "archive"
        archive_rel = str((archive_dir / target_file.name).relative_to(spoke_resolved))
        stub_content = _render_graduated_stub(rel_path, meta, archive_rel)
        if GRADUATED_STUB_MARKER in raw_text and raw_text == stub_content:
            actions.append(
                {"type": "Doc", "name": target_file.name, "status": "UNCHANGED", "path": rel_path}
            )
            continue
        if not dry_run:
            if GRADUATED_STUB_MARKER not in raw_text:
                _archive_and_write_stub(target_file, archive_dir, stub_content)
            else:
                target_file.write_text(stub_content, encoding="utf-8", newline="\n")
        actions.append(
            {
                "type": "Doc",
                "name": target_file.name,
                "status": "DEPRECATED_REPLACED",
                "path": f"{rel_path} (archived -> {archive_rel})",
            }
        )
    return actions


def _fix_redundant_md_prefix_in_index(index_file: Path, spoke_root: Path) -> bool:
    """Strips redundant '.md/' link prefixes inside <spoke>/.md/INDEX.md when target exists."""
    raw = index_file.read_text(encoding="utf-8")
    pattern = re.compile(r"\]\(\.md/([^)#\s]+)((?:#[^)\s]+)?)\)")

    def _repl(match: re.Match[str]) -> str:
        rel_target, anchor = match.group(1), match.group(2)
        if (spoke_root / ".md" / rel_target).exists() and not (
            spoke_root / ".md" / ".md" / rel_target
        ).exists():
            return f"]({rel_target}{anchor})"
        return match.group(0)

    updated = pattern.sub(_repl, raw)
    if updated != raw:
        index_file.write_text(updated, encoding="utf-8", newline="\n")
        return True
    return False


def audit_spoke_markdown_links(spoke_root: Path, apply_fixes: bool = False) -> list[str]:
    """Audits and optionally fixes internal links in Spoke .agents/AGENTS.md and .md/INDEX.md (COND-04).

    Args:
        spoke_root: Target Spoke workspace root directory.
        apply_fixes: If True, auto-fixes file:// and redundant .md/ links before validating.

    Returns:
        List of remaining broken link diagnostic strings (empty list means 100% valid).
    """
    from scripts.governance.link_auditor import LinkAuditor

    spoke_resolved = spoke_root.resolve()
    auditor = LinkAuditor(spoke_resolved)
    targets = [
        spoke_resolved / ".agents" / "AGENTS.md",
        spoke_resolved / ".md" / "INDEX.md",
    ]
    errors: list[str] = []
    for md_file in targets:
        if not md_file.is_file():
            continue
        if apply_fixes:
            if md_file.name == "INDEX.md":
                _fix_redundant_md_prefix_in_index(md_file, spoke_resolved)
            auditor.fix_relative_links(md_file)
        issues = auditor.validate_markdown_file(md_file, fix=False)
        rel_file = md_file.relative_to(spoke_resolved).as_posix()
        for line_num, href, msg in issues.get("links", []):
            errors.append(f"{rel_file}:{line_num} -> '{href}' ({msg})")
    return errors

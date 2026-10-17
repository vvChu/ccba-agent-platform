"""coordinator.py - Coordinator & Orchestration Engine for Spoke Synchronization.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import difflib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .backup import GitWorkingTreeGuard, SpokeBackupManager
from .base import HubNotFoundError, are_dirs_identical, are_files_identical, load_yaml, safe_remove
from .discovery import HubDiscoverer
from .graduation import (
    audit_spoke_markdown_links,
    merge_core_invariants_block,
    normalize_spoke_agents_links,
    split_markdown_sections,
    supersede_graduated_spoke_docs,
    sync_layer2_rules,
)
from .registry import SpokeRegistrar
from .sdk_inspector import (
    LegalKnowledgeSyncOrchestrator,
    SharedSdkInspector,
    TestGuardrailCopier,
)

# =============================================================================
# SKILL DEPRECATION & NAMESPACE ALIASES (ADR-0040 & ADR-0051)
# =============================================================================
SKILL_DEPRECATION_ALIASES: dict[str, str] = {
    "academic_writing": "ccba-academic-writing",
    "ai-gateway-sdk": "ccba-ai-gateway-sdk",
    "api-circuit-breaker": "ccba-api-circuit-breaker",
    "append-only-logger": "ccba-append-only-logger",
    "ask": "ccba-ask",
    "code-review": "ccba-code-review",
    "codebase-design": "ccba-codebase-design",
    "completion-checklist": "ccba-completion-checklist",
    "copywriting": "ccba-copywriting",
    "design": "ccba-design",
    "diagnosing-bugs": "ccba-diagnosing-bugs",
    "docs_manager": "ccba-docs-manager",
    "domain-modeling": "ccba-domain-modeling",
    "eval-gate": "ccba-eval-gate",
    "excalidraw-diagram": "ccba-excalidraw-diagram",
    "file-stability-guard": "ccba-file-stability-guard",
    "git-guardrails": "ccba-git-guardrails",
    "grilling": "ccba-grilling",
    "handoff": "ccba-handoff",
    "hybrid-rag-search": "ccba-hybrid-rag-search",
    "implement": "ccba-implement",
    "legal-advisor": "ccba-legal-advisor",
    "legal-document-tracker": "ccba-legal-document-tracker",
    "llm-pipeline-patterns": "ccba-llm-pipeline-patterns",
    "markdown-processing": "ccba-markdown-document-processing",
    "maskara": "ccba-maskara",
    "notebooklm-connector": "ccba-notebooklm-connector",
    "pptx": "ccba-pptx",
    "seminar-builder": "ccba-seminar-builder",
    "session_retrospective": "ccba-session-retrospective",
    "setup-skills": "ccba-setup-skills",
    "spoke-adopter": "ccba-spoke-adopter",
    "tdd": "ccba-tdd",
    "to-spec": "ccba-to-spec",
    "update-spoke": "ccba-update-spoke",
    "wayfinder": "ccba-wayfinder",
    "web-testing": "ccba-web-testing",
    "xia": "ccba-xia",
    "xu-ly-van-phong": "ccba-xu-ly-van-phong",
    "youtube-learn": "ccba-youtube-learn",
    # --- 3-Tier Architecture Migration: Tier 2A Progressive References (34 Micro-Skills) ---
    "ccba-docx": "ccba-xu-ly-van-phong",
    "docx": "ccba-xu-ly-van-phong",
    "ccba-viet-chuyen-nghiep": "ccba-copywriting",
    "viet-chuyen-nghiep": "ccba-copywriting",
    "ccba-discard-feature": "ccba-implement",
    "discard-feature": "ccba-implement",
    "ccba-mock-debugger": "ccba-diagnosing-bugs",
    "mock-debugger": "ccba-diagnosing-bugs",
    "ccba-pccc-cdt-tuthamdinh": "ccba-ai-qc-pccc-audit",
    "pccc-cdt-tuthamdinh": "ccba-ai-qc-pccc-audit",
    "workflow_pccc_cdt_tuthamdinh": "ccba-ai-qc-pccc-audit",
    "workflow-pccc-cdt-tuthamdinh": "ccba-ai-qc-pccc-audit",
    "ccba-pccc-thamdinh-congan": "ccba-ai-qc-pccc-audit",
    "pccc-thamdinh-congan": "ccba-ai-qc-pccc-audit",
    "workflow_pccc_thamdinh_congan": "ccba-ai-qc-pccc-audit",
    "workflow-pccc-thamdinh-congan": "ccba-ai-qc-pccc-audit",
    "ccba-pccc-thamdinh-cqxd": "ccba-ai-qc-pccc-audit",
    "pccc-thamdinh-cqxd": "ccba-ai-qc-pccc-audit",
    "workflow_pccc_thamdinh_cqxd": "ccba-ai-qc-pccc-audit",
    "workflow-pccc-thamdinh-cqxd": "ccba-ai-qc-pccc-audit",
    "ccba-update-legal-registry": "ccba-legal-document-tracker",
    "update-legal-registry": "ccba-legal-document-tracker",
    "ccba-setup-pre-commit": "ccba-setup-skills",
    "setup-pre-commit": "ccba-setup-skills",
    "ccba-setup-ts-deep-modules": "ccba-setup-skills",
    "setup-ts-deep-modules": "ccba-setup-skills",
    "ccba-long-form-writer": "ccba-academic-writing",
    "long-form-writer": "ccba-academic-writing",
    "ccba-docs-validator": "ccba-docs-manager",
    "docs-validator": "ccba-docs-manager",
    "ccba-propose-to-hub": "ccba-contribute-to-hub",
    "propose-to-hub": "ccba-contribute-to-hub",
    "ccba-wait-what": "ccba-ask",
    "wait-what": "ccba-ask",
    "ccba-wizard": "ccba-init-spoke",
    "wizard": "ccba-init-spoke",
    "ccba-prototype": "ccba-implement",
    "prototype": "ccba-implement",
    "ccba-resolving-merge-conflicts": "ccba-git-guardrails",
    "resolving-merge-conflicts": "ccba-git-guardrails",
    "ccba-create-pr": "ccba-contribute-to-hub",
    "create-pr": "ccba-contribute-to-hub",
    "ccba-improve-codebase-architecture": "ccba-codebase-design",
    "improve-codebase-architecture": "ccba-codebase-design",
    "ccba-server-deploy": "ccba-init-spoke",
    "server-deploy": "ccba-init-spoke",
    "ccba-to-tickets": "ccba-to-spec",
    "to-tickets": "ccba-to-spec",
    "ccba-to-questionnaire": "ccba-to-spec",
    "to-questionnaire": "ccba-to-spec",
    "ccba-writing-great-skills": "ccba-build-skill",
    "writing-great-skills": "ccba-build-skill",
    "ccba-review-skill": "ccba-build-skill",
    "review-skill": "ccba-build-skill",
    "review_skill": "ccba-build-skill",
    "ccba-review-proposal": "ccba-contribute-to-hub",
    "review-proposal": "ccba-contribute-to-hub",
    "ccba-architecture-sync": "ccba-adr-lifecycle",
    "architecture-sync": "ccba-adr-lifecycle",
    "ccba-triage": "ccba-issue-to-hub",
    "triage": "ccba-issue-to-hub",
    "sync-upstream": "ccba-sync-upstream",
    "ccba-teach": "ccba-seminar-builder",
    "teach": "ccba-seminar-builder",
    "ccba-show-me": "ccba-excalidraw-diagram",
    "show-me": "ccba-excalidraw-diagram",
    "ccba-skills-eval": "ccba-eval-gate",
    "skills-eval": "ccba-eval-gate",
    "ccba-loop-me": "ccba-grilling",
    "loop-me": "ccba-grilling",
    "ccba-brainstorm": "ccba-ask",
    "brainstorm": "ccba-ask",
    "ccba-sequential-thinking": "ccba-research",
    "sequential-thinking": "ccba-research",
    # --- Un-prefixed short names for Standalone Skills ---
    "tvpl-vip-crawler": "ccba-tvpl-vip-crawler",
    "sharepoint-iac": "ccba-sharepoint-iac",
    # Legacy Workflows -> Modern Skills Aliases (ADR-0040 & ADR-0051)
    "adopt-spoke": "ccba-spoke-adopter",
    "ccba-adopt-spoke": "ccba-spoke-adopter",
    "convert-markdown": "ccba-markdown-document-processing",
    "ccba-convert-markdown": "ccba-markdown-document-processing",
    "prepare-seminar": "ccba-seminar-builder",
    "ccba-prepare-seminar": "ccba-seminar-builder",
    "run-qc-pipeline": "ccba-ai-qc",
    "ccba-run-qc-pipeline": "ccba-ai-qc",
    "notebooklm": "ccba-notebooklm-connector",
    "ccba-notebooklm": "ccba-notebooklm-connector",
    "docs": "ccba-docs-manager",
    "ccba-docs": "ccba-docs-manager",
    "extract-style": "ccba-copywriting",
    "ccba-extract-style": "ccba-copywriting",
    "grill-with-docs": "ccba-grilling",
    "ccba-grill-with-docs": "ccba-grilling",
    "init-spoke": "ccba-init-spoke",
    "new-feature": "ccba-new-feature",
    "release-feature": "ccba-release-feature",
    "contribute-to-hub": "ccba-contribute-to-hub",
    "issue-to-hub": "ccba-issue-to-hub",
    "session-retrospective": "ccba-session-retrospective",
    "skill-repair": "ccba-skill-repair",
    "repair-skill": "ccba-skill-repair",
    "promote-sandbox": "ccba-promote-sandbox",
    "graduate-rd": "ccba-graduate-rd",
    "knowledge-loop": "ccba-knowledge-loop",
    "autoresearch": "ccba-autoresearch",
    "build-skill": "ccba-build-skill",
}

# =============================================================================
# PROJECT TYPE SYNONYMS & ALIAS MAPPING
# =============================================================================
PROJECT_TYPE_ALIASES: dict[str, str] = {
    # Pháp điển
    "kho tri thức pháp lý": "Pháp điển",
    "kho tri thức pháp lý & quy chuẩn": "Pháp điển",
    "kho tri thuc phap ly": "Pháp điển",
    "kho tri thuc phap ly & quy chuan": "Pháp điển",
    "pháp lý & quy chuẩn": "Pháp điển",
    "phap ly & quy chuan": "Pháp điển",
    "pháp lý": "Pháp điển",
    "phap ly": "Pháp điển",
    "tri thức pháp lý": "Pháp điển",
    "tri thuc phap ly": "Pháp điển",
    "legal knowledge": "Pháp điển",
    "legal": "Pháp điển",
    "pháp điển": "Pháp điển",
    "phap dien": "Pháp điển",
    "tra cứu": "Pháp điển",
    "tra cuu": "Pháp điển",
    "lookup": "Pháp điển",
    "Tra cứu": "Pháp điển",
    # Phần mềm
    "software": "Phần mềm",
    "phần mềm": "Phần mềm",
    "phan mem": "Phần mềm",
    "tooling": "Phần mềm",
    "development": "Phần mềm",
    "phần mềm & công cụ": "Phần mềm",
    "phan mem & cong cu": "Phần mềm",
    # Thẩm tra thiết kế
    "thẩm tra": "Thẩm tra thiết kế",
    "tham tra": "Thẩm tra thiết kế",
    "tư vấn & thẩm tra": "Thẩm tra thiết kế",
    "tu van & tham tra": "Thẩm tra thiết kế",
    "tư vấn thẩm tra": "Thẩm tra thiết kế",
    "tu van tham tra": "Thẩm tra thiết kế",
    "thẩm tra thiết kế": "Thẩm tra thiết kế",
    "tham tra thiet ke": "Thẩm tra thiết kế",
    "design review": "Thẩm tra thiết kế",
    "qc": "Thẩm tra thiết kế",
    "thẩm tra pccc": "Thẩm tra thiết kế",
    "thẩm tra mep": "Thẩm tra thiết kế",
    # Thiết kế
    "design": "Thiết kế",
    "thiết kế": "Thiết kế",
    "thiet ke": "Thiết kế",
    "thiết kế kỹ thuật": "Thiết kế",
    # Kiểm định
    "kiểm định chất lượng": "Kiểm định",
    "kiem dinh chat luong": "Kiểm định",
    "kiểm định": "Kiểm định",
    "kiem dinh": "Kiểm định",
    "assessment": "Kiểm định",
    "kiểm định công trình": "Kiểm định",
    # BIM
    "bim": "BIM",
    "bim modeling": "BIM",
    "bim consulting": "BIM",
    "tư vấn bim": "BIM",
    "tu van bim": "BIM",
    # Tác vụ Admin (General Knowledge Bases & Second Brain)
    "admin": "Tác vụ Admin",
    "tác vụ admin": "Tác vụ Admin",
    "tac vu admin": "Tác vụ Admin",
    "tác vụ hành chính": "Tác vụ Admin",
    "tac vu hanh chinh": "Tác vụ Admin",
    "hành chính": "Tác vụ Admin",
    "hanh chinh": "Tác vụ Admin",
    "enterprise_governance": "Tác vụ Admin",
    "knowledge_corpus": "Tác vụ Admin",
    "knowledge-base": "Tác vụ Admin",
    "knowledge_base": "Tác vụ Admin",
    "second-brain": "Tác vụ Admin",
    "second_brain": "Tác vụ Admin",
}


def resolve_canonical_project_type(
    raw_type: str, bundle_defs: dict[str, Any]
) -> tuple[str | None, str | None]:
    """Resolves a raw project type string into a canonical registered catalog enum.

    Args:
        raw_type: The raw string from workspace_context.yaml.
        bundle_defs: Dictionary of registered bundles from catalog.yaml.

    Returns:
        tuple[canonical_type, note_or_suggestion]:
        - (canonical_type, None): Exact match found.
        - (canonical_type, note): Resolved via alias or case correction.
        - (None, suggestion): Unresolved type with "Did you mean '...'?" or None.
    """
    if not raw_type:
        return None, "Loại dự án (project_type) bị trống."

    cleaned = raw_type.strip()
    if not cleaned:
        return None, "Loại dự án (project_type) bị trống."

    # 1. Exact match with registered bundle keys
    if cleaned in bundle_defs:
        return cleaned, None

    # 2. Case-insensitive exact match with registered bundle keys
    for k in bundle_defs:
        if k.lower() == cleaned.lower():
            return k, f"Đã tự động chuẩn hóa chữ hoa/thường: '{raw_type}' -> '{k}'"

    # 3. Alias / Synonyms match
    lower_cleaned = cleaned.lower()
    if lower_cleaned in PROJECT_TYPE_ALIASES:
        canonical = PROJECT_TYPE_ALIASES[lower_cleaned]
        if canonical in bundle_defs:
            return canonical, f"Đã tự động ánh xạ bí danh (Alias): '{raw_type}' -> '{canonical}'"

    # 4. Fuzzy match using difflib
    pool = list(bundle_defs.keys()) + list(PROJECT_TYPE_ALIASES.keys())
    matches = difflib.get_close_matches(lower_cleaned, pool, n=1, cutoff=0.45)
    if matches:
        matched_candidate = matches[0]
        suggested = PROJECT_TYPE_ALIASES.get(matched_candidate, matched_candidate)
        if suggested not in bundle_defs and matched_candidate in bundle_defs:
            suggested = matched_candidate
        return None, f"Có phải ý bạn là: '{suggested}'?"

    return None, None


INVARIANT_BULLET_PATTERN = re.compile(
    r"^[ \t]*(?:[-*]|\d+\.)[ \t]+\*\*([^*:]+)(?::\*\*|\*\*:)[\t ]*(.*)"
)


def parse_invariants_section(content: str) -> tuple[str, list[tuple[str, str]]]:
    """Parse an Invariants section into preamble and individual bullet items (multiline-aware)."""
    lines = content.splitlines(keepends=True)
    preamble_lines: list[str] = []
    items: list[tuple[str, list[str]]] = []
    current_key: str | None = None
    current_item_lines: list[str] = []

    for line in lines:
        m = INVARIANT_BULLET_PATTERN.match(line)
        if m:
            if current_key is not None:
                items.append((current_key, current_item_lines))
                current_item_lines = []
            current_key = m.group(1).strip()
            current_item_lines.append(line)
        else:
            if current_key is None:
                preamble_lines.append(line)
            else:
                current_item_lines.append(line)

    if current_key is not None:
        items.append((current_key, current_item_lines))

    item_tuples = [(k, "".join(l_lines)) for k, l_lines in items]
    return "".join(preamble_lines), item_tuples


def merge_agents_constitution(
    hub_text: str,
    spoke_text: str,
    spoke_root: Path | None = None,
) -> str:
    """Merge Hub constitution into Spoke AGENTS.md while preserving custom Spoke sections and invariants.

    Args:
        hub_text: Content of Hub's AGENTS.md (canonical constitution).
        spoke_text: Content of Spoke's existing AGENTS.md.
        spoke_root: Optional Spoke root directory for conditional link normalization.

    Returns:
        Merged content containing Hub's updated constitution, merged Core Invariants,
        normalized Layer 2 rule links, and preserving any custom sections present in Spoke.
    """
    if not hub_text.strip():
        return spoke_text
    if not spoke_text.strip():
        return normalize_spoke_agents_links(hub_text, spoke_root=spoke_root)

    hub_sections = split_markdown_sections(hub_text)
    spoke_sections = split_markdown_sections(spoke_text)
    hub_dict = dict(hub_sections)
    spoke_dict = dict(spoke_sections)

    inv_heading = "## Core Invariants"
    if inv_heading in hub_dict and inv_heading in spoke_dict:
        hub_dict[inv_heading] = merge_core_invariants_block(
            hub_dict[inv_heading], spoke_dict[inv_heading], parse_invariants_section
        )

    merged_sections = [hub_dict[heading].rstrip() for heading, _ in hub_sections]
    hub_headings = {h for h, _ in hub_sections if h}
    for heading, content in spoke_sections:
        if heading and heading not in hub_headings:
            merged_sections.append(content.rstrip())

    merged = "\n\n".join(merged_sections).rstrip() + "\n"
    return normalize_spoke_agents_links(merged, spoke_root=spoke_root)


def ensure_peer_exchange_scaffold(spoke_root: Path, hub_root: Path, dry_run: bool = False) -> None:
    """Ensures .md/peer_exchange directory and starter handshake files exist in Spoke workspace."""
    peer_dir = spoke_root / ".md" / "peer_exchange"
    if not dry_run:
        peer_dir.mkdir(parents=True, exist_ok=True)
        handshake_file = peer_dir / "PEER_HANDSHAKE.md"
        hub_handshake = hub_root / ".md" / "peer_exchange" / "PEER_HANDSHAKE.md"
        if not handshake_file.exists() and hub_handshake.exists():
            handshake_file.write_text(hub_handshake.read_text(encoding="utf-8"), encoding="utf-8")

        readme_file = peer_dir / "README.md"
        hub_readme = hub_root / ".md" / "peer_exchange" / "README.md"
        if not readme_file.exists() and hub_readme.exists():
            readme_file.write_text(hub_readme.read_text(encoding="utf-8"), encoding="utf-8")


def _format_freshness_detail(detail: object) -> str:
    """Render a freshness diff (string or sequence) for stderr."""
    if isinstance(detail, (list, tuple)):
        return "\n".join(str(item) for item in detail)
    return str(detail)


def _handle_freshness_check_error(
    exc: Exception,
    spoke_root: Path,
    dry_run: bool,
    allow_stale_catalog: bool,
    recompile_cmd: str,
) -> str | None:
    """Handle exceptions raised during catalog freshness check."""
    if allow_stale_catalog:
        print(
            "[Sync] AUDIT: CATALOG_STALE_BYPASS "
            f"flag=--allow-stale-catalog reason=check_failed "
            f"error={type(exc).__name__}: {exc} spoke={spoke_root}",
            file=sys.stderr,
        )
        return None
    if not dry_run:
        print(
            "[Sync] ERROR: Cannot apply sync because Hub catalog.yaml is out of sync "
            f"(freshness check failed: {type(exc).__name__}: {exc}).",
            file=sys.stderr,
        )
        print(f"  Remediation (run in the Hub root): {recompile_cmd}", file=sys.stderr)
        return "catalog_stale"
    print(
        "[Sync] WARNING: Hub catalog.yaml is out of sync "
        f"(freshness check failed: {type(exc).__name__}: {exc}).",
        file=sys.stderr,
    )
    return None


def _handle_stale_catalog_result(
    detail: object,
    spoke_root: Path,
    dry_run: bool,
    allow_stale_catalog: bool,
    recompile_cmd: str,
) -> str | None:
    """Format and emit diagnostics when catalog.yaml is out of sync."""
    detail_text = _format_freshness_detail(detail)
    if allow_stale_catalog:
        print(
            f"[Sync] AUDIT: CATALOG_STALE_BYPASS flag=--allow-stale-catalog spoke={spoke_root}",
            file=sys.stderr,
        )
        if detail_text:
            print(detail_text, file=sys.stderr)
        return None

    if dry_run:
        print(
            "[Sync] WARNING: Hub catalog.yaml is out of sync. "
            "This preview uses the stale catalog. "
            "--apply will exit 1 until the Hub catalog is recompiled.",
            file=sys.stderr,
        )
        if detail_text:
            print(detail_text, file=sys.stderr)
        print(f"  Remediation (run in the Hub root): {recompile_cmd}", file=sys.stderr)
        return None

    print(
        "[Sync] ERROR: Cannot apply sync because Hub catalog.yaml is out of sync.",
        file=sys.stderr,
    )
    if detail_text:
        print(detail_text, file=sys.stderr)
    print(f"  Remediation (run in the Hub root): {recompile_cmd}", file=sys.stderr)
    return "catalog_stale"


def assess_catalog_freshness(
    hub_root: Path,
    spoke_root: Path,
    dry_run: bool = False,
    allow_stale_catalog: bool = False,
) -> str | None:
    """Return ``catalog_stale`` when ``--apply`` must stop (ADR-0062 fail-closed gate).

    Dry-run prints a warning and returns None. ``allow_stale_catalog`` prints an
    audit line and returns None for both a stale catalog and a check exception.
    The ``except`` branch checks ``allow_stale_catalog`` before any other decision.
    """
    from scripts.governance.compile_catalog import (
        CATALOG_RECOMPILE_COMMAND,
        check_catalog_in_sync,
    )

    try:
        is_in_sync, detail = check_catalog_in_sync(hub_root)
    except Exception as exc:
        return _handle_freshness_check_error(
            exc, spoke_root, dry_run, allow_stale_catalog, CATALOG_RECOMPILE_COMMAND
        )

    if is_in_sync:
        return None

    return _handle_stale_catalog_result(
        detail, spoke_root, dry_run, allow_stale_catalog, CATALOG_RECOMPILE_COMMAND
    )


class SpokeSynchronizer:
    """Deep Engine managing Spoke workspace synchronization with non-destructive selective merge."""

    def __init__(
        self,
        spoke_path: str | Path | None = None,
        spoke_root: str | Path | None = None,
        hub_root: str | Path | None = None,
    ) -> None:
        target = spoke_path or spoke_root or "."
        self.spoke_root = Path(target).resolve()
        self.hub_root = Path(hub_root).resolve() if hub_root else None

    def _sync_single_skill_entry(
        self,
        spoke_root: Path,
        hub_root: Path,
        spoke_skills_dir: Path,
        catalog: dict[str, Any],
        sync_item: str,
        dry_run: bool,
    ) -> tuple[bool, int]:
        """Attempt to sync a single skill entry from catalog."""
        for skill_entry in catalog.get("skills", []):
            if skill_entry.get("name") != sync_item:
                continue
            skill_path_rel = skill_entry.get("skill_path")
            src = hub_root / Path(skill_path_rel).parent
            dest = spoke_skills_dir / Path(skill_path_rel).parent.name
            if not src.exists():
                print(f"[Sync] Error: Skill source path not found at {src}", file=sys.stderr)
                return True, 1
            if src.resolve() == dest.resolve():
                return True, 0
            rel_dest = dest.relative_to(spoke_root)
            if dry_run:
                print(f"[Sync] [DRY-RUN] Would copy skill [{sync_item}] -> {rel_dest}")
            else:
                print(f"[Sync] Copying skill [{sync_item}] -> {rel_dest}")
                dest.parent.mkdir(parents=True, exist_ok=True)
                safe_remove(dest)
                shutil.copytree(src, dest)
            return True, 0
        return False, 0

    def _sync_single_workflow_entry(
        self,
        spoke_root: Path,
        hub_root: Path,
        spoke_workflows_dir: Path,
        catalog: dict[str, Any],
        sync_item: str,
        dry_run: bool,
    ) -> tuple[bool, int]:
        """Attempt to sync a single workflow entry from catalog."""
        for wf_entry in catalog.get("workflows", []):
            if wf_entry.get("name") != sync_item:
                continue
            wf_path_rel = wf_entry.get("workflow_path")
            src = hub_root / wf_path_rel
            dest = spoke_workflows_dir / Path(wf_path_rel).name
            if not src.exists():
                print(f"[Sync] Error: Workflow source file not found at {src}", file=sys.stderr)
                return True, 1
            if src.resolve() == dest.resolve():
                return True, 0
            rel_dest = dest.relative_to(spoke_root)
            if dry_run:
                print(f"[Sync] [DRY-RUN] Would copy workflow [{sync_item}] -> {rel_dest}")
            else:
                print(f"[Sync] Copying workflow [{sync_item}] -> {rel_dest}")
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    dest.unlink()
                shutil.copy2(src, dest)
            return True, 0
        return False, 0

    def _sync_single_item_constitution(
        self,
        spoke_root: Path,
        hub_root: Path,
        spoke_agents_dir: Path,
        dry_run: bool,
    ) -> None:
        """Sync Layer 2 rules and merge AGENTS.md during single-item sync."""
        sync_layer2_rules(spoke_root, hub_root, dry_run=dry_run)
        hub_agents_md = hub_root / ".agents" / "AGENTS.md"
        spoke_agents_md = spoke_agents_dir / "AGENTS.md"
        if hub_agents_md.exists() and hub_agents_md.resolve() != spoke_agents_md.resolve():
            hub_content = hub_agents_md.read_text(encoding="utf-8")
            spoke_content = (
                spoke_agents_md.read_text(encoding="utf-8") if spoke_agents_md.exists() else ""
            )
            merged_content = merge_agents_constitution(
                hub_content, spoke_content, spoke_root=spoke_root
            )
            if dry_run:
                rel_agents = spoke_agents_md.relative_to(spoke_root)
                print(f"[Sync] [DRY-RUN] Would sync constitutional rules -> {rel_agents}")
            else:
                spoke_agents_dir.mkdir(parents=True, exist_ok=True)
                spoke_agents_md.write_text(merged_content, encoding="utf-8", newline="\n")

    def _sync_single_item(
        self,
        spoke_root: Path,
        hub_root: Path,
        catalog: dict[str, Any],
        sync_item: str,
        dry_run: bool = False,
    ) -> int:
        """On-Demand synchronization for a single skill or workflow."""
        canonical_item = SKILL_DEPRECATION_ALIASES.get(sync_item, sync_item)
        if canonical_item != sync_item:
            print(f"  [Alias Redirect] '{sync_item}' -> '{canonical_item}' (ADR-0040 Namespace)")
            sync_item = canonical_item

        mode_str = " [DRY-RUN]" if dry_run else ""
        print(f"Mode: On-Demand Synchronization for '{sync_item}'{mode_str}")
        spoke_agents_dir = spoke_root / ".agents"

        found, err_code = self._sync_single_skill_entry(
            spoke_root, hub_root, spoke_agents_dir / "skills", catalog, sync_item, dry_run
        )
        if err_code != 0:
            return err_code

        if not found:
            found, err_code = self._sync_single_workflow_entry(
                spoke_root, hub_root, spoke_agents_dir / "workflows", catalog, sync_item, dry_run
            )
            if err_code != 0:
                return err_code

        if not found:
            print(
                f"[Sync] Error: Item '{sync_item}' not found in Hub catalog.yaml.", file=sys.stderr
            )
            return 1

        self._sync_single_item_constitution(spoke_root, hub_root, spoke_agents_dir, dry_run)
        if dry_run:
            print("\n=== [DRY-RUN] On-Demand Sync Simulation Completed ===")
        else:
            print("\n=== Sync Completed Successfully ===")
        return 0

    def _expand_additional_bundles(
        self,
        required_bundles: list[str],
        additional_bundles: list[str],
        bundle_defs: dict[str, Any],
    ) -> None:
        """Append additional bundle definitions into required_bundles in place."""
        for add_b in additional_bundles:
            add_b_str = str(add_b).strip()
            if not add_b_str:
                continue
            if add_b_str.startswith("_"):
                if add_b_str not in required_bundles:
                    required_bundles.append(add_b_str)
            elif add_b_str in bundle_defs:
                for b_item in bundle_defs[add_b_str]:
                    if b_item not in required_bundles:
                        required_bundles.append(b_item)
            else:
                canon, _ = resolve_canonical_project_type(add_b_str, bundle_defs)
                if canon and canon in bundle_defs:
                    for b_item in bundle_defs[canon]:
                        if b_item not in required_bundles:
                            required_bundles.append(b_item)
                elif add_b_str not in required_bundles:
                    required_bundles.append(add_b_str)

    def _resolve_required_bundles(
        self,
        project_type: str,
        bundle_defs: dict[str, Any],
        additional_bundles: list[str] | None,
        dry_run: bool,
    ) -> tuple[str | None, list[str]]:
        """Resolve canonical project type and compute required bundle list."""
        if not project_type:
            print(
                "[Sync] Error: 'project_type' is not defined in workspace_context.yaml.",
                file=sys.stderr,
            )
            return None, []

        canonical_type, note = resolve_canonical_project_type(project_type, bundle_defs)
        if not canonical_type:
            available_types = ", ".join(bundle_defs.keys())
            print(
                f"[Sync] Error: Project type '{project_type}' is not registered in catalog.yaml.",
                file=sys.stderr,
            )
            if note:
                print(f"[Sync] 💡 {note}", file=sys.stderr)
            print(f"[Sync] Registered types: {available_types}", file=sys.stderr)
            return None, []

        if note:
            print(f"[Sync] ℹ️  {note}")

        mode_banner = " [DRY-RUN MODE]" if dry_run else ""
        print(f"Project Type: {canonical_type}{mode_banner}")

        required_bundles = list(bundle_defs[canonical_type])
        if additional_bundles:
            self._expand_additional_bundles(required_bundles, additional_bundles, bundle_defs)
            print(f"Additional Bundles: {additional_bundles}")

        print(f"Required Bundles: {required_bundles}")
        return canonical_type, required_bundles

    def _collect_sync_targets(
        self,
        catalog: dict[str, Any],
        hub_root: Path,
        required_bundles: list[str],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Collect skills and workflows matching required_bundles or _core."""
        skills_to_sync: list[dict[str, Any]] = []
        wfs_to_sync: list[dict[str, Any]] = []

        for skill_entry in catalog.get("skills", []):
            skill_bundle = skill_entry.get("bundle")
            if skill_bundle in required_bundles or skill_bundle == "_core":
                skill_path_rel = skill_entry.get("skill_path")
                skills_to_sync.append(
                    {
                        "name": skill_entry.get("name"),
                        "src_dir": hub_root / Path(skill_path_rel).parent,
                        "dest_name": Path(skill_path_rel).parent.name,
                    }
                )

        for wf_entry in catalog.get("workflows", []):
            wf_bundle = wf_entry.get("bundle")
            if wf_bundle in required_bundles or wf_bundle == "_core":
                wf_path_rel = wf_entry.get("workflow_path")
                wfs_to_sync.append(
                    {
                        "name": wf_entry.get("name"),
                        "src_file": hub_root / wf_path_rel,
                        "filename": Path(wf_path_rel).name,
                    }
                )
        return skills_to_sync, wfs_to_sync

    def _reconcile_existing_skills(
        self,
        spoke_root: Path,
        spoke_skills_dir: Path,
        synced_skill_folders: set[str],
        dry_run: bool,
    ) -> list[dict[str, Any]]:
        """Preserve custom Spoke skills and remove deprecated skill aliases."""
        actions: list[dict[str, Any]] = []
        if not spoke_skills_dir.exists():
            return actions
        for existing_skill in spoke_skills_dir.iterdir():
            if not existing_skill.is_dir() or existing_skill.name in synced_skill_folders:
                continue
            replacement = SKILL_DEPRECATION_ALIASES.get(existing_skill.name)
            rel_path = str(existing_skill.relative_to(spoke_root))
            if replacement and replacement in synced_skill_folders:
                actions.append(
                    {
                        "type": "Skill",
                        "name": existing_skill.name,
                        "status": "DEPRECATED_REPLACED",
                        "path": rel_path,
                    }
                )
                if not dry_run:
                    safe_remove(existing_skill)
            else:
                actions.append(
                    {
                        "type": "Skill",
                        "name": existing_skill.name,
                        "status": "PRESERVED",
                        "path": rel_path,
                    }
                )
        return actions

    def _sync_skills_phase(
        self,
        spoke_root: Path,
        spoke_skills_dir: Path,
        skills_to_sync: list[dict[str, Any]],
        dry_run: bool,
    ) -> tuple[set[str], list[dict[str, Any]]]:
        """Synchronize target skills into Spoke and return synced folder set and actions."""
        if not dry_run:
            spoke_skills_dir.mkdir(parents=True, exist_ok=True)
        synced_skill_folders = {sk["dest_name"] for sk in skills_to_sync}
        actions = self._reconcile_existing_skills(
            spoke_root, spoke_skills_dir, synced_skill_folders, dry_run
        )

        for sk in skills_to_sync:
            src = sk["src_dir"]
            dest = spoke_skills_dir / sk["dest_name"]
            if not src.exists():
                print(f"  - [Warning] Skill source path not found: {src}", file=sys.stderr)
                continue
            rel_dest = str(dest.relative_to(spoke_root))
            if src.resolve() == dest.resolve() or (dest.exists() and are_dirs_identical(src, dest)):
                actions.append(
                    {"type": "Skill", "name": sk["name"], "status": "UNCHANGED", "path": rel_dest}
                )
            elif not dest.exists():
                actions.append(
                    {"type": "Skill", "name": sk["name"], "status": "NEW", "path": rel_dest}
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                actions.append(
                    {"type": "Skill", "name": sk["name"], "status": "UPDATED", "path": rel_dest}
                )
                if not dry_run:
                    safe_remove(dest)
                    shutil.copytree(src, dest, dirs_exist_ok=True)
        return synced_skill_folders, actions

    def _reconcile_existing_workflows(
        self,
        spoke_root: Path,
        spoke_workflows_dir: Path,
        synced_wf_filenames: set[str],
        synced_skill_folders: set[str],
        dry_run: bool,
    ) -> list[dict[str, Any]]:
        """Archive workflows migrated to skills and preserve custom Spoke workflows."""
        actions: list[dict[str, Any]] = []
        if not spoke_workflows_dir.exists():
            return actions
        for existing_wf in spoke_workflows_dir.iterdir():
            if not existing_wf.is_file() or existing_wf.name in synced_wf_filenames:
                continue
            stem = existing_wf.stem
            clean_name = stem.replace("ccba-", "")
            replacement = (
                SKILL_DEPRECATION_ALIASES.get(stem)
                or SKILL_DEPRECATION_ALIASES.get(clean_name)
                or (f"ccba-{clean_name}" if f"ccba-{clean_name}" in synced_skill_folders else None)
                or (stem if stem in synced_skill_folders else None)
            )
            rel_path = str(existing_wf.relative_to(spoke_root))
            if existing_wf.suffix == ".md" and replacement and replacement in synced_skill_folders:
                actions.append(
                    {
                        "type": "Workflow",
                        "name": stem,
                        "status": "DEPRECATED_MIGRATED_TO_SKILL",
                        "path": rel_path,
                    }
                )
                if not dry_run:
                    bak_path = existing_wf.with_suffix(".md.bak")
                    if bak_path.exists():
                        safe_remove(bak_path)
                    existing_wf.rename(bak_path)
            else:
                actions.append(
                    {"type": "Workflow", "name": stem, "status": "PRESERVED", "path": rel_path}
                )
        return actions

    def _sync_workflows_phase(
        self,
        spoke_root: Path,
        spoke_workflows_dir: Path,
        wfs_to_sync: list[dict[str, Any]],
        synced_skill_folders: set[str],
        dry_run: bool,
    ) -> list[dict[str, Any]]:
        """Synchronize target workflows into Spoke and return workflow actions."""
        if not dry_run and wfs_to_sync:
            spoke_workflows_dir.mkdir(parents=True, exist_ok=True)
        synced_wf_filenames = {wf["filename"] for wf in wfs_to_sync}
        actions = self._reconcile_existing_workflows(
            spoke_root, spoke_workflows_dir, synced_wf_filenames, synced_skill_folders, dry_run
        )

        for wf in wfs_to_sync:
            src = wf["src_file"]
            dest = spoke_workflows_dir / wf["filename"]
            if not src.exists():
                print(f"  - [Warning] Workflow source file not found: {src}", file=sys.stderr)
                continue
            rel_dest = str(dest.relative_to(spoke_root))
            if src.resolve() == dest.resolve() or (
                dest.exists() and are_files_identical(src, dest)
            ):
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "UNCHANGED",
                        "path": rel_dest,
                    }
                )
            elif not dest.exists():
                actions.append(
                    {"type": "Workflow", "name": wf["name"], "status": "NEW", "path": rel_dest}
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
            else:
                actions.append(
                    {"type": "Workflow", "name": wf["name"], "status": "UPDATED", "path": rel_dest}
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
        return actions

    def _sync_constitution_and_rules_phase(
        self, spoke_root: Path, hub_root: Path, project_type: str, dry_run: bool, force: bool
    ) -> list[dict[str, Any]]:
        """Merge AGENTS.md constitution, sync Layer 2 rules, supersede graduated docs, and copy guardrails."""
        actions: list[dict[str, Any]] = []
        spoke_agents_dir = spoke_root / ".agents"
        hub_agents_md = hub_root / ".agents" / "AGENTS.md"
        spoke_agents_md = spoke_agents_dir / "AGENTS.md"
        if hub_agents_md.exists() and hub_agents_md.resolve() != spoke_agents_md.resolve():
            hub_content = hub_agents_md.read_text(encoding="utf-8")
            spoke_content = (
                spoke_agents_md.read_text(encoding="utf-8") if spoke_agents_md.exists() else ""
            )
            merged_content = merge_agents_constitution(
                hub_content, spoke_content, spoke_root=spoke_root
            )
            if not spoke_agents_md.exists():
                rule_status = "NEW"
            elif merged_content == spoke_content.replace("\r\n", "\n"):
                rule_status = "UNCHANGED"
            else:
                rule_status = "UPDATED"
            actions.append(
                {
                    "type": "Rule",
                    "name": "AGENTS.md",
                    "status": rule_status,
                    "path": str(spoke_agents_md.relative_to(spoke_root)),
                }
            )
            if not dry_run and rule_status in ("NEW", "UPDATED"):
                spoke_agents_dir.mkdir(parents=True, exist_ok=True)
                spoke_agents_md.write_text(merged_content, encoding="utf-8", newline="\n")

        actions.extend(sync_layer2_rules(spoke_root, hub_root, dry_run=dry_run))
        actions.extend(supersede_graduated_spoke_docs(spoke_root, hub_root, dry_run=dry_run))
        if not dry_run:
            audit_spoke_markdown_links(spoke_root, apply_fixes=True)
        actions.extend(
            TestGuardrailCopier(spoke_root, hub_root, project_type).copy_if_needed(
                dry_run=dry_run, force=force
            )
        )
        ensure_peer_exchange_scaffold(spoke_root, hub_root, dry_run=dry_run)
        return actions

    def _refresh_telemetry_and_register(
        self,
        spoke_root: Path,
        hub_root: Path,
        project_name: str,
        project_type: str,
        archetype: str,
        dry_run: bool,
    ) -> None:
        """Refresh Spoke telemetry summary and register Spoke in Hub Registry."""
        if not dry_run:
            try:
                import json

                from ccba_harness.fleet import scan_spoke_telemetry
                from scripts.spoke.spoke_bootstrap import SpokeBootstrapper

                SpokeBootstrapper(spoke_root, hub_root).ensure_gitignore_rule(dry_run=dry_run)
                summary = scan_spoke_telemetry(
                    {
                        "name": project_name,
                        "path": str(spoke_root.resolve()),
                        "project_type": project_type,
                        "is_sandbox": False,
                    }
                )
                telemetry_file = spoke_root / ".md" / "data" / "telemetry_summary.json"
                telemetry_file.parent.mkdir(parents=True, exist_ok=True)
                telemetry_file.write_text(
                    json.dumps(summary.to_dict(), indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            except Exception:
                pass

        SpokeRegistrar().register(
            spoke_root, hub_root, project_name, project_type, archetype=archetype, dry_run=dry_run
        )

    def _print_sync_summary_report(self, actions: list[dict[str, Any]], dry_run: bool) -> None:
        """Render formatted ASCII summary table for Spoke synchronization."""
        new_count = sum(1 for a in actions if a["status"] == "NEW")
        updated_count = sum(1 for a in actions if a["status"] == "UPDATED")
        unchanged_count = sum(1 for a in actions if a["status"] == "UNCHANGED")
        preserved_count = sum(1 for a in actions if a["status"] == "PRESERVED")
        deprecated_count = sum(1 for a in actions if a["status"] == "DEPRECATED_REPLACED")

        print("\n" + "=" * 90)
        print(f" CCBA SPOKE SYNC REPORT — {'[DRY-RUN SIMULATION]' if dry_run else '[EXECUTION]'}")
        print("=" * 90)
        print(f"{'Loại':<10} | {'Tên Kỹ Năng / Quy Trình':<30} | {'Trạng Thái':<12} | {'Đích Đến'}")
        print("-" * 90)
        status_map = {
            "NEW": "🟢 NEW",
            "UPDATED": "🔄 UPDATED",
            "UNCHANGED": "⚪ UNCHANGED",
            "PRESERVED": "🛡️ PRESERVED",
            "DEPRECATED_REPLACED": "🗑️ DEPRECATED",
        }
        for act in actions:
            status_symbol = status_map.get(act["status"], act["status"])
            print(f"{act['type']:<10} | {act['name']:<30} | {status_symbol:<12} | {act['path']}")
        print("-" * 90)
        print(
            f"Tổng kết: {new_count} mới, {updated_count} cập nhật, {unchanged_count} không đổi, "
            f"{deprecated_count} dọn dẹp cũ, {preserved_count} giữ nguyên nội bộ."
        )

    def _run_bootstrap_and_legal_sync(
        self,
        spoke_root: Path,
        hub_root: Path,
        project_type: str,
        archetype: str,
        bootstrap: bool,
        dry_run: bool,
        force: bool,
        pull_assets: bool,
    ) -> int:
        """Execute 1-click SDK bootstrap or print recommendations, followed by legal knowledge sync."""
        if bootstrap:
            try:
                from scripts.spoke.spoke_bootstrap import SpokeBootstrapper

                print("\n🚀 [1-Click Bootstrap] Tự động liên kết Hub Packages (ADR 0044):")
                boot_code = SpokeBootstrapper(spoke_root, hub_root).bootstrap(
                    dry_run=dry_run, force=force
                )
                if boot_code != 0 and not dry_run:
                    print(
                        f"  ❌ Quá trình bootstrap thất bại với mã lỗi {boot_code}.",
                        file=sys.stderr,
                    )
                    return boot_code
            except Exception as e:
                print(f"  ⚠️ Lỗi khi thực hiện bootstrap: {e}", file=sys.stderr)
                if not dry_run:
                    return 1
        else:
            cat_recs = SharedSdkInspector(
                spoke_root, hub_root, project_type, archetype=archetype
            ).get_categorized_recommendations()
            if cat_recs:
                print("\n💡 Gợi ý Shared SDKs cho Spoke Python (ADR 0044):")
                for cat_title, cmds in cat_recs.items():
                    print(f"   [{cat_title}]:")
                    for cmd in cmds:
                        print(f"   -> {cmd}")
                print(
                    "   💡 Mẹo: Chạy 'python scripts/sync_spoke.py --bootstrap' để tự động cài đặt 1-chạm."
                )

        LegalKnowledgeSyncOrchestrator(
            spoke_root, hub_root, project_type, archetype=archetype
        ).sync_or_advise(dry_run=dry_run, pull_assets=pull_assets)
        return 0

    def _sync_full_bundle(
        self,
        spoke_root: Path,
        hub_root: Path,
        catalog: dict[str, Any],
        project_type: str,
        project_name: str,
        dry_run: bool = False,
        additional_bundles: list[str] | None = None,
        bootstrap: bool = False,
        force: bool = False,
        archetype: str = "",
        pull_assets: bool = False,
    ) -> int:
        """Full synchronization with Non-Destructive Selective Merge."""
        canonical_type, req_bundles = self._resolve_required_bundles(
            project_type, catalog.get("bundles", {}), additional_bundles, dry_run
        )
        if not canonical_type:
            return 1
        agents_dir = spoke_root / ".agents"
        skills, wfs = self._collect_sync_targets(catalog, hub_root, req_bundles)
        synced_folders, actions = self._sync_skills_phase(
            spoke_root, agents_dir / "skills", skills, dry_run
        )
        actions.extend(
            self._sync_workflows_phase(
                spoke_root, agents_dir / "workflows", wfs, synced_folders, dry_run
            )
        )
        actions.extend(
            self._sync_constitution_and_rules_phase(
                spoke_root, hub_root, canonical_type, dry_run, force
            )
        )
        self._refresh_telemetry_and_register(
            spoke_root, hub_root, project_name, canonical_type, archetype, dry_run
        )
        self._print_sync_summary_report(actions, dry_run)
        boot_res = self._run_bootstrap_and_legal_sync(
            spoke_root, hub_root, canonical_type, archetype, bootstrap, dry_run, force, pull_assets
        )
        if boot_res == 0:
            print(
                "\n[DRY-RUN] Quá trình mô phỏng hoàn tất. 0 tệp tin nào bị sửa đổi trên đĩa."
                if dry_run
                else "\n=== Sync Completed Successfully ==="
            )
        return boot_res

    def _check_git_working_tree_guard(self, dry_run: bool, check_git: bool, force: bool) -> bool:
        """Verify Spoke .agents/ working tree is clean when required."""
        if dry_run or not check_git or force:
            return True
        is_clean, dirty_details = GitWorkingTreeGuard(self.spoke_root).check_clean_working_tree()
        if is_clean:
            return True
        print("\n" + "!" * 80, file=sys.stderr)
        print(
            "[Sync] ⚠️  CẢNH BÁO: Phát hiện uncommitted changes trong thư mục .agents/:",
            file=sys.stderr,
        )
        for line in dirty_details.splitlines():
            print(f"  {line}", file=sys.stderr)
        print(
            "  Để tránh ghi đè dữ liệu ngoài ý muốn, vui lòng commit hoặc stash các thay đổi.",
            file=sys.stderr,
        )
        print(
            "  Hoặc truyền cờ '--force' / '--ignore-dirty' nếu muốn bỏ qua cảnh báo này.",
            file=sys.stderr,
        )
        print("!" * 80 + "\n", file=sys.stderr)
        return False

    def _extract_project_type_and_archetype(self, context: dict[str, Any]) -> tuple[str, str]:
        """Extract and cross-fill project_type and archetype from workspace context."""
        proj_dict = context.get("project") if isinstance(context.get("project"), dict) else {}
        raw_archetype = context.get("archetype") or proj_dict.get("archetype")
        spoke_archetype = str(raw_archetype).strip() if raw_archetype else ""

        raw_type = (
            context.get("project_type") or proj_dict.get("type") or proj_dict.get("project_type")
        )
        project_type = str(raw_type).strip() if raw_type else ""

        if not project_type and spoke_archetype:
            archetype_to_project_type = {
                "knowledge_corpus": "Tác vụ Admin",
                "enterprise_governance": "Tác vụ Admin",
                "project_delivery": "Thẩm tra thiết kế",
                "specialized_extension": "Phần mềm",
                "platform_hub": "Phần mềm",
            }
            project_type = archetype_to_project_type.get(spoke_archetype, "")

        if not spoke_archetype and project_type:
            from scripts.spoke.spoke_bootstrap import PROJECT_TYPE_TO_ARCHETYPE

            spoke_archetype = PROJECT_TYPE_TO_ARCHETYPE.get(project_type.lower(), "")
        return project_type, spoke_archetype

    def _load_spoke_workspace_metadata(
        self,
    ) -> tuple[dict[str, Any], Path, str, str, str, list[str]] | None:
        """Load workspace_context.yaml and extract project metadata."""
        context_file = self.spoke_root / ".agents" / "workspace_context.yaml"
        if not context_file.exists():
            context_file = self.spoke_root / ".md" / "workspace_context.yaml"
        if not context_file.exists():
            print(
                f"[Sync] Error: Could not find workspace_context.yaml in {self.spoke_root}/.agents/ or {self.spoke_root}/.md/",
                file=sys.stderr,
            )
            print(
                "[Sync] Please run 'init spoke' first in the target project folder.",
                file=sys.stderr,
            )
            return None

        context = load_yaml(context_file)
        proj_dict = context.get("project") if isinstance(context.get("project"), dict) else {}
        raw_name = context.get("project_name") or proj_dict.get("name")
        project_name = str(raw_name).strip() if raw_name else self.spoke_root.name
        project_type, spoke_archetype = self._extract_project_type_and_archetype(context)

        raw_add = context.get("additional_bundles") or proj_dict.get("additional_bundles")
        additional_bundles: list[str] = []
        if isinstance(raw_add, list):
            additional_bundles = [str(b).strip() for b in raw_add if str(b).strip()]
        elif isinstance(raw_add, str) and raw_add.strip():
            additional_bundles = [raw_add.strip()]

        return (
            context,
            context_file,
            project_name,
            project_type,
            spoke_archetype,
            additional_bundles,
        )

    def _try_pull_hub_repo(self, hub_root: Path, dry_run: bool, pull_hub: bool) -> None:
        """Attempt git pull on Hub repository when unlocked and enabled."""
        git_dir = hub_root / ".git"
        if not git_dir.exists() or dry_run:
            return
        index_lock = git_dir / "index.lock" if git_dir.is_dir() else None
        if index_lock is not None and index_lock.exists():
            print(
                "[Sync] Notice: Hub git lock (.git/index.lock) detected. "
                "Skipping git pull to prevent contention and continuing with local cache...",
                file=sys.stderr,
            )
            return
        if not pull_hub or os.environ.get("CCBA_SKIP_GIT_PULL") == "1":
            return

        print("[Sync] Hub is a Git repository. Attempting to pull latest changes from GitHub...")
        try:
            result = subprocess.run(
                ["git", "pull"],
                cwd=str(hub_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            if result.returncode == 0:
                print("[Sync] Git pull completed successfully.")
                if result.stdout.strip():
                    print(f"  {result.stdout.strip()}")
            else:
                print(
                    f"[Sync] Warning: Git pull failed with code {result.returncode}.",
                    file=sys.stderr,
                )
                if result.stderr.strip():
                    print(f"  {result.stderr.strip()}", file=sys.stderr)
                print("[Sync] Continuing with local offline cache...", file=sys.stderr)
        except Exception as e:
            print(f"[Sync] Warning: Could not execute git pull: {e}", file=sys.stderr)
            print("[Sync] Continuing with local offline cache...", file=sys.stderr)

    def _prepare_hub_and_backup(
        self,
        context: dict[str, Any],
        context_file: Path,
        dry_run: bool,
        backup: bool,
        pull_hub: bool,
    ) -> Path | None:
        """Discover Hub root, create Spoke snapshot backup if requested, and pull Hub repo."""
        if self.hub_root and self.hub_root.exists():
            hub_root = self.hub_root
        else:
            try:
                hub_root = HubDiscoverer(self.spoke_root, context, context_file).discover()
            except HubNotFoundError as e:
                print(str(e), file=sys.stderr)
                return None

        print(f"Hub Location: {hub_root}")
        if not dry_run and backup:
            snapshot_dir = SpokeBackupManager(self.spoke_root).create_backup()
            if snapshot_dir:
                try:
                    rel_backup = snapshot_dir.relative_to(self.spoke_root)
                except ValueError:
                    rel_backup = snapshot_dir
                print(f"[Sync] 🛡️  Đã tạo snapshot sao lưu an toàn: {rel_backup}")

        self._try_pull_hub_repo(hub_root, dry_run, pull_hub)
        return hub_root

    def _load_verified_catalog(
        self, hub_root: Path, dry_run: bool, allow_stale_catalog: bool
    ) -> dict[str, Any] | None:
        """Verify catalog.yaml exists and passes freshness gate before loading."""
        catalog_file = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
        if not catalog_file.exists():
            print(f"[Sync] Error: Could not find catalog.yaml at {catalog_file}", file=sys.stderr)
            return None
        self._halt_reason = (
            assess_catalog_freshness(
                hub_root, self.spoke_root, dry_run=dry_run, allow_stale_catalog=allow_stale_catalog
            )
            or ""
        )
        if self._halt_reason == "catalog_stale":
            return None
        return load_yaml(catalog_file)

    def sync_spoke_bundle(
        self,
        sync_item: str | None = None,
        dry_run: bool = False,
        force: bool = False,
        backup: bool = True,
        check_git: bool = True,
        only: str | None = None,
        bootstrap: bool = False,
        verify: bool = False,
        pull_hub: bool = True,
        pull_assets: bool = False,
        allow_stale_catalog: bool = False,
    ) -> int:
        """Main entrypoint for Spoke synchronization."""
        print(f"\n=== CCBA Spoke Synchronization{' [DRY-RUN]' if dry_run else ''} ===")
        print(f"Target Spoke: {self.spoke_root}")
        if not self._check_git_working_tree_guard(dry_run, check_git, force):
            return 1
        meta = self._load_spoke_workspace_metadata()
        if meta is None:
            return 1
        ctx, ctx_file, proj_name, proj_type, arch, add_bundles = meta
        hub_root = self._prepare_hub_and_backup(ctx, ctx_file, dry_run, backup, pull_hub)
        if not hub_root:
            return 1
        catalog = self._load_verified_catalog(hub_root, dry_run, allow_stale_catalog)
        if catalog is None:
            return 1
        item = sync_item or only
        args = (self.spoke_root, hub_root, catalog)
        b_opts = (dry_run, add_bundles, bootstrap, force, arch, pull_assets)
        res = (
            self._sync_single_item(*args, item, dry_run=dry_run)
            if item
            else self._sync_full_bundle(*args, proj_type, proj_name, *b_opts)
        )
        return (
            self.verify_spoke(hub_root=hub_root) if (res == 0 and not dry_run and verify) else res
        )

    def _discover_spoke_test_dirs(self) -> list[Path]:
        """Locate configured or standard pytest directories in Spoke workspace."""
        target_test_dirs: list[Path] = []
        ctx_file = self.spoke_root / ".agents" / "workspace_context.yaml"
        if not ctx_file.exists():
            ctx_file = self.spoke_root / ".md" / "workspace_context.yaml"
        ctx = load_yaml(ctx_file) if ctx_file.exists() else {}
        custom_test_paths = (
            ctx.get("verification", {}).get("test_path") if isinstance(ctx, dict) else None
        )
        if custom_test_paths:
            if isinstance(custom_test_paths, str):
                custom_test_paths = [custom_test_paths]
            for p in custom_test_paths:
                resolved_p = self.spoke_root / p
                if resolved_p.exists() and resolved_p not in target_test_dirs:
                    target_test_dirs.append(resolved_p)

        if not target_test_dirs:
            for rel in ("tests", "scripts/tests", "src/tests"):
                c_dir = self.spoke_root / rel
                if (
                    c_dir.exists()
                    and any(c_dir.rglob("test_*.py"))
                    and c_dir not in target_test_dirs
                ):
                    target_test_dirs.append(c_dir)
        return target_test_dirs

    def _resolve_spoke_test_command(self, resolved_hub: Path) -> str | None:
        """Build pytest command string for Spoke test suite if test directories exist."""
        from scripts.spoke.spoke_bootstrap import SpokeBootstrapper

        bootstrapper = SpokeBootstrapper(self.spoke_root, resolved_hub)
        venv_dir = bootstrapper.find_venv()
        spoke_python = bootstrapper.get_python_exec(venv_dir) if venv_dir else Path(sys.executable)
        test_runtime = spoke_python
        try:
            check_res = subprocess.run(
                [str(spoke_python), "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if check_res.returncode != 0:
                test_runtime = Path(sys.executable)
        except Exception:
            test_runtime = Path(sys.executable)

        target_test_dirs = self._discover_spoke_test_dirs()
        if not target_test_dirs:
            return None
        dirs_str = " ".join(f'"{d.as_posix()}"' for d in target_test_dirs)
        return f'"{test_runtime.as_posix()}" -m pytest {dirs_str} -q'

    def _execute_verification_commands(self, cmds: list[str]) -> int:
        """Execute post-sync verification commands via ccba_harness verifier."""
        try:
            from ccba_harness.verifier import verify_patch_execution

            res = verify_patch_execution(commands=cmds, cwd=self.spoke_root, fail_fast=True)
            if res.all_passed:
                print("✅ SUCCESS: Spoke post-sync verification passed 100% deterministically.")
                return 0
            first_failed = next((r for r in res.results if not r.passed), None)
            exit_code: int = first_failed.exit_code if first_failed else 1
            print(
                f"❌ FAILED: Spoke post-sync verification failed with exit code {exit_code}.",
                file=sys.stderr,
            )
            return exit_code
        except Exception as e:
            print(f"  ❌ Lỗi khi thực hiện post-sync verification: {e}", file=sys.stderr)
            return 1

    def verify_spoke(self, hub_root: Path | None = None) -> int:
        """Run deterministic ADR-0058 verification on synced spoke."""
        resolved_hub = hub_root or self.hub_root or Path(__file__).resolve().parents[3]
        cleanliness_script = resolved_hub / "scripts" / "spoke" / "check_spoke_cleanliness.py"
        import_depth_script = resolved_hub / "scripts" / "spoke" / "check_hub_import_depth.py"

        print("\n" + "=" * 85)
        print(" 🛡️  CCBA SPOKE DETERMINISTIC POST-SYNC VERIFICATION (ADR-0058)")
        print(f" Target Spoke: {self.spoke_root}")
        print("=" * 85)

        link_errors = audit_spoke_markdown_links(self.spoke_root, apply_fixes=False)
        if link_errors:
            print(
                "❌ FAILED: Spoke markdown link parity audit detected broken links:",
                file=sys.stderr,
            )
            for err in link_errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

        cmds: list[str] = []
        if cleanliness_script.exists():
            cmds.append(
                f'"{sys.executable}" "{cleanliness_script.as_posix()}" --path "{self.spoke_root.as_posix()}"'
            )
        if import_depth_script.exists():
            cmds.append(
                f'"{sys.executable}" "{import_depth_script.as_posix()}" --path "{self.spoke_root.as_posix()}"'
            )

        pytest_cmd = self._resolve_spoke_test_command(resolved_hub)
        if pytest_cmd:
            cmds.append(pytest_cmd)

        if not cmds:
            print("[Verify] Không có lệnh kiểm tra nào cần thực thi.")
            return 0
        return self._execute_verification_commands(cmds)

    def sync(
        self,
        sync_item: str | None = None,
        dry_run: bool = False,
        force: bool = False,
        backup: bool = True,
        check_git: bool = True,
        only: str | None = None,
        bootstrap: bool = False,
        verify: bool = False,
        pull_hub: bool = True,
        pull_assets: bool = False,
        allow_stale_catalog: bool = False,
    ) -> int:
        """Deep Seam entry point for syncing spoke bundle."""
        return self.sync_spoke_bundle(
            sync_item=sync_item or only,
            dry_run=dry_run,
            force=force,
            backup=backup,
            check_git=check_git,
            only=only,
            bootstrap=bootstrap,
            verify=verify,
            pull_hub=pull_hub,
            pull_assets=pull_assets,
            allow_stale_catalog=allow_stale_catalog,
        )

    def rollback(self, backup_path: Path | None = None) -> bool:
        """Restore .agents/ from latest snapshot or specified backup path."""
        return SpokeBackupManager(self.spoke_root).restore_backup(backup_path)

    def list_backups(self) -> list[Path]:
        """List available snapshots for this spoke."""
        return SpokeBackupManager(self.spoke_root).list_backups()


SpokeSyncEngine = SpokeSynchronizer


def _get_synchronizer_cls() -> type[SpokeSynchronizer]:
    """Helper to dynamically resolve SpokeSynchronizer class, supporting monkeypatching on facade."""
    spoke_sync_mod = sys.modules.get("scripts.spoke.spoke_synchronizer")
    if spoke_sync_mod and hasattr(spoke_sync_mod, "SpokeSynchronizer"):
        cls = spoke_sync_mod.SpokeSynchronizer
        if isinstance(cls, type):
            return cls
    return SpokeSynchronizer


def sync_project(
    spoke_path: str | Path = ".",
    sync_item: str | None = None,
    dry_run: bool = False,
    force: bool = False,
    backup: bool = True,
    check_git: bool = True,
    bootstrap: bool = False,
    verify: bool = False,
    pull_hub: bool = True,
    pull_assets: bool = False,
    allow_stale_catalog: bool = False,
) -> int:
    """Helper procedural delegate for spoke synchronization."""
    engine = _get_synchronizer_cls()(str(spoke_path))
    return engine.sync(
        sync_item=sync_item,
        dry_run=dry_run,
        force=force,
        backup=backup,
        check_git=check_git,
        bootstrap=bootstrap,
        verify=verify,
        pull_hub=pull_hub,
        pull_assets=pull_assets,
        allow_stale_catalog=allow_stale_catalog,
    )


def rollback_project(
    spoke_path: str | Path = ".",
    backup_path: Path | None = None,
) -> bool:
    """Helper procedural delegate for spoke rollback from snapshot."""
    engine = _get_synchronizer_cls()(str(spoke_path))
    return engine.rollback(backup_path=backup_path)


def list_project_backups(spoke_path: str | Path = ".") -> list[Path]:
    """Helper procedural delegate to list spoke backup snapshots."""
    engine = _get_synchronizer_cls()(str(spoke_path))
    return engine.list_backups()


def _sync_registered_spoke_entry(
    sp: dict[str, Any],
    idx: int,
    total: int,
    sync_cls: type[SpokeSynchronizer],
    sync_kwargs: dict[str, Any],
) -> tuple[dict[str, Any], int, bool]:
    """Synchronize a single registered Spoke entry during batch sync."""
    sp_name = sp.get("name", "Unknown")
    sp_path = sp.get("path", "")
    sp_type = sp.get("project_type", "Unknown")

    print(f"\n[{idx}/{total}] 🔄 Đang xử lý Spoke: '{sp_name}' ({sp_type})")
    print(f"  Đường dẫn: {sp_path}")

    if not os.path.exists(sp_path):
        print("  ⚠️ Cảnh báo: Spoke không tồn tại vật lý trên ổ đĩa. Bỏ qua.")
        return {"name": sp_name, "path": sp_path, "status": "MISSING", "code": 1}, 0, False

    try:
        engine = sync_cls(sp_path)
        res = engine.sync(pull_hub=(idx == 1), **sync_kwargs)
        status = "SUCCESS" if res == 0 else "FAILED"
        record = {"name": sp_name, "path": sp_path, "status": status, "code": res}
        if res != 0:
            if getattr(engine, "_halt_reason", "") == "catalog_stale":
                print(
                    "[BatchSync] Stopping: Hub catalog.yaml is stale. "
                    "Remaining Spokes were not synced.",
                    file=sys.stderr,
                )
                return record, 1, True
            return record, 1, False
        return record, 0, False
    except Exception as e:
        print(f"  ❌ Lỗi khi đồng bộ Spoke '{sp_name}': {e}", file=sys.stderr)
        return {"name": sp_name, "path": sp_path, "status": f"ERROR: {e}", "code": 1}, 1, False


def _print_batch_sync_summary(results: list[dict[str, Any]], mode_str: str) -> None:
    """Print summary table for multi-spoke batch synchronization."""
    print("\n" + "=" * 90)
    print(f" BÁO CÁO TỔNG KẾT BATCH SYNC{mode_str}")
    print("=" * 90)
    print(f"{'Tên Spoke':<25} | {'Trạng Thái':<14} | {'Đường Dẫn Vật Lý'}")
    print("-" * 90)
    for r in results:
        status_icon = (
            "✅ SUCCESS"
            if r["status"] == "SUCCESS"
            else ("⚠️ MISSING" if r["status"] == "MISSING" else f"❌ {r['status']}")
        )
        print(f"{r['name']:<25} | {status_icon:<14} | {r['path']}")
    print("=" * 90)


def _run_batch_spoke_loop(
    spokes: list[dict[str, Any]],
    sync_cls: type[SpokeSynchronizer],
    sync_kwargs: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    """Iterate through registered Spokes and collect batch sync results."""
    results: list[dict[str, Any]] = []
    total_exit_code = 0
    for idx, sp in enumerate(spokes, 1):
        rec, err_code, should_halt = _sync_registered_spoke_entry(
            sp, idx, len(spokes), sync_cls, sync_kwargs
        )
        results.append(rec)
        if err_code != 0:
            total_exit_code = 1
        if should_halt:
            break
    return results, total_exit_code


def sync_all_spokes(
    hub_root: Path | None = None,
    sync_item: str | None = None,
    dry_run: bool = False,
    force: bool = False,
    backup: bool = True,
    check_git: bool = True,
    include_sandboxes: bool = False,
    bootstrap: bool = False,
    verify: bool = False,
    pull_assets: bool = False,
    allow_stale_catalog: bool = False,
) -> int:
    """Batch synchronize all registered active Spokes found in Hub Registry."""
    root = hub_root or Path(__file__).resolve().parents[3]
    from scripts.spoke.decrypt_spoke_registry import get_registered_spokes

    spokes = get_registered_spokes(hub_root=root)
    if not include_sandboxes:
        spokes = [s for s in spokes if not s.get("is_sandbox", False)]
    if not spokes:
        print("[BatchSync] Warning: No registered Spokes found in Hub Registry.", file=sys.stderr)
        return 1
    mode_str = " [DRY-RUN SIMULATION]" if dry_run else ""
    print(
        f"\n{'=' * 90}\n CCBA MULTI-SPOKE BATCH SYNCHRONIZATION{mode_str}\n"
        f" Tìm thấy {len(spokes)} Spoke(s) trong Hub Registry.\n{'=' * 90}"
    )
    sync_kwargs = {
        "sync_item": sync_item,
        "dry_run": dry_run,
        "force": force,
        "backup": backup,
        "check_git": check_git,
        "bootstrap": bootstrap,
        "verify": verify,
        "pull_assets": pull_assets,
        "allow_stale_catalog": allow_stale_catalog,
    }
    results, total_exit_code = _run_batch_spoke_loop(spokes, _get_synchronizer_cls(), sync_kwargs)
    _print_batch_sync_summary(results, mode_str)
    return total_exit_code

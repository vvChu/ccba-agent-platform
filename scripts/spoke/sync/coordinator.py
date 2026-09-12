"""coordinator.py - Coordinator & Orchestration Engine for Spoke Synchronization.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import difflib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .backup import GitWorkingTreeGuard, SpokeBackupManager
from .base import HubNotFoundError, are_dirs_identical, are_files_identical, load_yaml, safe_remove
from .discovery import HubDiscoverer
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


def merge_agents_constitution(hub_text: str, spoke_text: str) -> str:
    """Merge Hub constitution into Spoke AGENTS.md while preserving custom Spoke sections.

    Args:
        hub_text: Content of Hub's AGENTS.md (canonical constitution).
        spoke_text: Content of Spoke's existing AGENTS.md.

    Returns:
        Merged content containing Hub's updated constitution and preserving any
        custom sections (e.g., '## Agent skills', '## Custom Rules') present in Spoke.
    """
    if not spoke_text.strip():
        return hub_text
    if not hub_text.strip():
        return spoke_text

    def split_into_sections(text: str) -> list[tuple[str, str]]:
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
            else:
                current_lines.append(line)

        if current_lines or current_heading:
            sections.append((current_heading, "".join(current_lines)))

        return sections

    hub_sections = split_into_sections(hub_text)
    spoke_sections = split_into_sections(spoke_text)

    hub_headings = {h for h, _ in hub_sections if h}

    # Find custom spoke sections not present in hub
    custom_spoke_sections: list[str] = []
    for heading, content in spoke_sections:
        if heading and heading not in hub_headings:
            custom_spoke_sections.append(content.rstrip())

    # Build merged output
    base_merged = hub_text.rstrip()
    if custom_spoke_sections:
        custom_block = "\n\n".join(custom_spoke_sections)
        return f"{base_merged}\n\n{custom_block}\n"

    return f"{base_merged}\n"


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
        spoke_skills_dir = spoke_agents_dir / "skills"
        spoke_workflows_dir = spoke_agents_dir / "workflows"

        found = False

        # Search Skills
        for skill_entry in catalog.get("skills", []):
            if skill_entry.get("name") == sync_item:
                skill_path_rel = skill_entry.get("skill_path")
                src = hub_root / Path(skill_path_rel).parent
                dest_name = Path(skill_path_rel).parent.name
                dest = spoke_skills_dir / dest_name

                if src.exists():
                    if src.resolve() == dest.resolve():
                        found = True
                        break
                    if dry_run:
                        print(
                            f"[Sync] [DRY-RUN] Would copy skill [{sync_item}] -> {dest.relative_to(spoke_root)}"
                        )
                    else:
                        print(
                            f"[Sync] Copying skill [{sync_item}] -> {dest.relative_to(spoke_root)}"
                        )
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        safe_remove(dest)
                        shutil.copytree(src, dest)
                    found = True
                    break
                else:
                    print(f"[Sync] Error: Skill source path not found at {src}", file=sys.stderr)
                    return 1

        # Search Workflows
        if not found:
            for wf_entry in catalog.get("workflows", []):
                if wf_entry.get("name") == sync_item:
                    wf_path_rel = wf_entry.get("workflow_path")
                    src = hub_root / wf_path_rel
                    filename = Path(wf_path_rel).name
                    dest = spoke_workflows_dir / filename

                    if src.exists():
                        if src.resolve() == dest.resolve():
                            found = True
                            break
                        if dry_run:
                            print(
                                f"[Sync] [DRY-RUN] Would copy workflow [{sync_item}] -> {dest.relative_to(spoke_root)}"
                            )
                        else:
                            print(
                                f"[Sync] Copying workflow [{sync_item}] -> {dest.relative_to(spoke_root)}"
                            )
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            if dest.exists():
                                dest.unlink()
                            shutil.copy2(src, dest)
                        found = True
                        break
                    else:
                        print(
                            f"[Sync] Error: Workflow source file not found at {src}",
                            file=sys.stderr,
                        )
                        return 1

        if not found:
            print(
                f"[Sync] Error: Item '{sync_item}' not found in Hub catalog.yaml.", file=sys.stderr
            )
            return 1

        # Merge constitution AGENTS.md
        hub_agents_md = hub_root / ".agents" / "AGENTS.md"
        spoke_agents_md = spoke_agents_dir / "AGENTS.md"
        if hub_agents_md.exists() and hub_agents_md.resolve() != spoke_agents_md.resolve():
            hub_content = hub_agents_md.read_text(encoding="utf-8")
            if spoke_agents_md.exists():
                spoke_content = spoke_agents_md.read_text(encoding="utf-8")
                merged_content = merge_agents_constitution(hub_content, spoke_content)
            else:
                merged_content = hub_content

            if dry_run:
                print(
                    f"[Sync] [DRY-RUN] Would sync constitutional rules -> {spoke_agents_md.relative_to(spoke_root)}"
                )
            else:
                spoke_agents_dir.mkdir(parents=True, exist_ok=True)
                spoke_agents_md.write_text(merged_content, encoding="utf-8")

        if dry_run:
            print("\n=== [DRY-RUN] On-Demand Sync Simulation Completed ===")
        else:
            print("\n=== Sync Completed Successfully ===")
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
    ) -> int:
        """Full synchronization with Non-Destructive Selective Merge."""
        if not project_type:
            print(
                "[Sync] Error: 'project_type' is not defined in workspace_context.yaml.",
                file=sys.stderr,
            )
            return 1

        bundle_defs = catalog.get("bundles", {})
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
            return 1

        if note:
            print(f"[Sync] ℹ️  {note}")

        project_type = canonical_type
        mode_banner = " [DRY-RUN MODE]" if dry_run else ""
        print(f"Project Type: {project_type}{mode_banner}")

        required_bundles = list(bundle_defs[project_type])
        if additional_bundles:
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

            print(f"Additional Bundles: {additional_bundles}")

        print(f"Required Bundles: {required_bundles}")

        spoke_agents_dir = spoke_root / ".agents"
        spoke_skills_dir = spoke_agents_dir / "skills"
        spoke_workflows_dir = spoke_agents_dir / "workflows"

        skills_to_sync = []
        wfs_to_sync = []

        # Filter Skills
        for skill_entry in catalog.get("skills", []):
            skill_name = skill_entry.get("name")
            skill_bundle = skill_entry.get("bundle")
            skill_path_rel = skill_entry.get("skill_path")

            if skill_bundle in required_bundles or skill_bundle == "_core":
                skills_to_sync.append(
                    {
                        "name": skill_name,
                        "src_dir": hub_root / Path(skill_path_rel).parent,
                        "dest_name": Path(skill_path_rel).parent.name,
                    }
                )

        # Filter Workflows
        for wf_entry in catalog.get("workflows", []):
            wf_name = wf_entry.get("name")
            wf_bundle = wf_entry.get("bundle")
            wf_path_rel = wf_entry.get("workflow_path")

            if wf_bundle in required_bundles or wf_bundle == "_core":
                wfs_to_sync.append(
                    {
                        "name": wf_name,
                        "src_file": hub_root / wf_path_rel,
                        "filename": Path(wf_path_rel).name,
                    }
                )

        # Status tracking
        actions: list[dict[str, Any]] = []

        # 1. Process Skills (Selective Merge)
        if not dry_run:
            spoke_skills_dir.mkdir(parents=True, exist_ok=True)

        synced_skill_folders = {sk["dest_name"] for sk in skills_to_sync}
        if spoke_skills_dir.exists():
            for existing_skill in spoke_skills_dir.iterdir():
                if existing_skill.is_dir() and existing_skill.name not in synced_skill_folders:
                    replacement = SKILL_DEPRECATION_ALIASES.get(existing_skill.name)
                    if replacement and replacement in synced_skill_folders:
                        actions.append(
                            {
                                "type": "Skill",
                                "name": existing_skill.name,
                                "status": "DEPRECATED_REPLACED",
                                "path": str(existing_skill.relative_to(spoke_root)),
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
                                "path": str(existing_skill.relative_to(spoke_root)),
                            }
                        )

        for sk in skills_to_sync:
            src = sk["src_dir"]
            dest = spoke_skills_dir / sk["dest_name"]
            if not src.exists():
                print(f"  - [Warning] Skill source path not found: {src}", file=sys.stderr)
                continue

            if src.resolve() == dest.resolve():
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                continue

            if not dest.exists():
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "NEW",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(src, dest, dirs_exist_ok=True)
            elif are_dirs_identical(src, dest):
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
            else:
                actions.append(
                    {
                        "type": "Skill",
                        "name": sk["name"],
                        "status": "UPDATED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    safe_remove(dest)
                    shutil.copytree(src, dest, dirs_exist_ok=True)

        # 2. Process Workflows (Non-Destructive Selective Merge)
        if not dry_run and wfs_to_sync:
            spoke_workflows_dir.mkdir(parents=True, exist_ok=True)

        synced_wf_filenames = {wf["filename"] for wf in wfs_to_sync}
        if spoke_workflows_dir.exists():
            for existing_wf in spoke_workflows_dir.iterdir():
                if existing_wf.is_file() and existing_wf.name not in synced_wf_filenames:
                    stem = existing_wf.stem
                    clean_name = stem.replace("ccba-", "")
                    replacement = (
                        SKILL_DEPRECATION_ALIASES.get(stem)
                        or SKILL_DEPRECATION_ALIASES.get(clean_name)
                        or (
                            f"ccba-{clean_name}"
                            if f"ccba-{clean_name}" in synced_skill_folders
                            else None
                        )
                        or (stem if stem in synced_skill_folders else None)
                    )
                    if (
                        existing_wf.suffix == ".md"
                        and replacement
                        and replacement in synced_skill_folders
                    ):
                        actions.append(
                            {
                                "type": "Workflow",
                                "name": existing_wf.stem,
                                "status": "DEPRECATED_MIGRATED_TO_SKILL",
                                "path": str(existing_wf.relative_to(spoke_root)),
                            }
                        )
                        if not dry_run:
                            bak_path = existing_wf.with_suffix(".md.bak")
                            if bak_path.exists():
                                safe_remove(bak_path)
                            existing_wf.rename(bak_path)
                    else:
                        actions.append(
                            {
                                "type": "Workflow",
                                "name": existing_wf.stem,
                                "status": "PRESERVED",
                                "path": str(existing_wf.relative_to(spoke_root)),
                            }
                        )

        for wf in wfs_to_sync:
            src = wf["src_file"]
            dest = spoke_workflows_dir / wf["filename"]
            if not src.exists():
                print(f"  - [Warning] Workflow source file not found: {src}", file=sys.stderr)
                continue

            if src.resolve() == dest.resolve():
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                continue

            if not dest.exists():
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "NEW",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
            elif are_files_identical(src, dest):
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "UNCHANGED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
            else:
                actions.append(
                    {
                        "type": "Workflow",
                        "name": wf["name"],
                        "status": "UPDATED",
                        "path": str(dest.relative_to(spoke_root)),
                    }
                )
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)

        # 3. Non-Destructive Merge AGENTS.md
        hub_agents_md = hub_root / ".agents" / "AGENTS.md"
        spoke_agents_md = spoke_agents_dir / "AGENTS.md"
        if hub_agents_md.exists() and hub_agents_md.resolve() != spoke_agents_md.resolve():
            hub_content = hub_agents_md.read_text(encoding="utf-8")
            if not spoke_agents_md.exists():
                rule_status = "NEW"
                merged_content = hub_content
            else:
                spoke_content = spoke_agents_md.read_text(encoding="utf-8")
                merged_content = merge_agents_constitution(hub_content, spoke_content)
                if merged_content == spoke_content:
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
                spoke_agents_md.write_text(merged_content, encoding="utf-8")

        # 4. Test guardrails
        guardrail_actions = TestGuardrailCopier(spoke_root, hub_root, project_type).copy_if_needed(
            dry_run=dry_run
        )
        actions.extend(guardrail_actions)

        # 5. Spoke telemetry refresh & registration (ADR-0046)
        if not dry_run:
            try:
                import json

                from ccba_harness.fleet import scan_spoke_telemetry

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

        SpokeRegistrar().register(spoke_root, hub_root, project_name, project_type, dry_run=dry_run)

        # 6. Print Structured Output & Summary Table
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
        for act in actions:
            status_symbol = {
                "NEW": "🟢 NEW",
                "UPDATED": "🔄 UPDATED",
                "UNCHANGED": "⚪ UNCHANGED",
                "PRESERVED": "🛡️ PRESERVED",
                "DEPRECATED_REPLACED": "🗑️ DEPRECATED",
            }.get(act["status"], act["status"])
            print(f"{act['type']:<10} | {act['name']:<30} | {status_symbol:<12} | {act['path']}")
        print("-" * 90)
        print(
            f"Tổng kết: {new_count} mới, {updated_count} cập nhật, {unchanged_count} không đổi, {deprecated_count} dọn dẹp cũ, {preserved_count} giữ nguyên nội bộ."
        )

        # 7. Zero-Latency Shared Python SDKs Inspection & 1-Click Bootstrap
        if bootstrap:
            try:
                from scripts.spoke.spoke_bootstrap import SpokeBootstrapper

                print("\n🚀 [1-Click Bootstrap] Tự động liên kết Hub Packages (ADR 0044):")
                bootstrapper = SpokeBootstrapper(spoke_root, hub_root)
                boot_code = bootstrapper.bootstrap(dry_run=dry_run, force=force)
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
            sdk_inspector = SharedSdkInspector(spoke_root, hub_root, project_type)
            sdk_recs = sdk_inspector.get_recommendations()
            if sdk_recs:
                print("\n💡 Gợi ý Shared SDKs cho Spoke Python:")
                print("   Để sử dụng AI Gateway hoặc Office Processing dùng chung từ Hub:")
                for cmd in sdk_recs:
                    print(f"   -> {cmd}")
                print(
                    "   💡 Mẹo: Chạy 'python scripts/sync_spoke.py --bootstrap' để tự động cài đặt 1-chạm."
                )

        # 8. Automatic Legal Knowledge Sync & Zero-Bloat Advisory (ADR 0050)
        LegalKnowledgeSyncOrchestrator(spoke_root, hub_root, project_type).sync_or_advise(
            dry_run=dry_run
        )

        if dry_run:
            print("\n[DRY-RUN] Quá trình mô phỏng hoàn tất. 0 tệp tin nào bị sửa đổi trên đĩa.")
        else:
            print("\n=== Sync Completed Successfully ===")
        return 0

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
    ) -> int:
        """Main entrypoint for Spoke synchronization."""
        mode_str = " [DRY-RUN]" if dry_run else ""
        print(f"\n=== CCBA Spoke Synchronization{mode_str} ===")
        print(f"Target Spoke: {self.spoke_root}")

        # Git Working Tree Guard (Execution mode only)
        if not dry_run and check_git and not force:
            guard = GitWorkingTreeGuard(self.spoke_root)
            is_clean, dirty_details = guard.check_clean_working_tree()
            if not is_clean:
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
                return 1

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
            return 1

        context = load_yaml(context_file)

        project_name_val = context.get("project_name")
        if not project_name_val:
            proj_dict = context.get("project")
            if isinstance(proj_dict, dict):
                project_name_val = proj_dict.get("name")
        if not project_name_val:
            project_name = self.spoke_root.name
        else:
            project_name = str(project_name_val).strip()

        project_type_val = context.get("project_type") or context.get("archetype")
        if not project_type_val:
            proj_dict = context.get("project")
            if isinstance(proj_dict, dict):
                project_type_val = proj_dict.get("type") or proj_dict.get("archetype")
        if not project_type_val:
            project_type = ""
        else:
            project_type = str(project_type_val).strip()

        # Extract additional_bundles
        raw_add_bundles = context.get("additional_bundles")
        if not raw_add_bundles:
            proj_dict = context.get("project")
            if isinstance(proj_dict, dict):
                raw_add_bundles = proj_dict.get("additional_bundles")

        additional_bundles: list[str] = []
        if isinstance(raw_add_bundles, list):
            additional_bundles = [str(b).strip() for b in raw_add_bundles if str(b).strip()]
        elif isinstance(raw_add_bundles, str) and raw_add_bundles.strip():
            additional_bundles = [raw_add_bundles.strip()]

        if self.hub_root and self.hub_root.exists():
            hub_root = self.hub_root
        else:
            try:
                discoverer = HubDiscoverer(self.spoke_root, context, context_file)
                hub_root = discoverer.discover()
            except HubNotFoundError as e:
                print(str(e), file=sys.stderr)
                return 1

        print(f"Hub Location: {hub_root}")

        # Snapshot Backup before actual modification
        if not dry_run and backup:
            backup_mgr = SpokeBackupManager(self.spoke_root)
            snapshot_dir = backup_mgr.create_backup()
            if snapshot_dir:
                try:
                    rel_backup = snapshot_dir.relative_to(self.spoke_root)
                except ValueError:
                    rel_backup = snapshot_dir
                print(f"[Sync] 🛡️  Đã tạo snapshot sao lưu an toàn: {rel_backup}")

        # Auto git pull Hub if git repo (only when not dry_run and pull_hub enabled)
        git_dir = hub_root / ".git"
        index_lock = git_dir / "index.lock" if git_dir.is_dir() else None
        skip_pull = (
            not pull_hub
            or os.environ.get("CCBA_SKIP_GIT_PULL") == "1"
            or (index_lock is not None and index_lock.exists())
        )

        if git_dir.exists() and not dry_run:
            if index_lock is not None and index_lock.exists():
                print(
                    "[Sync] Notice: Hub git lock (.git/index.lock) detected. "
                    "Skipping git pull to prevent contention and continuing with local cache...",
                    file=sys.stderr,
                )
            elif not skip_pull:
                print(
                    "[Sync] Hub is a Git repository. Attempting to pull latest changes from GitHub..."
                )
                try:
                    result = subprocess.run(
                        ["git", "pull"],
                        cwd=str(hub_root),
                        capture_output=True,
                        text=True,
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

        catalog_file = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
        if not catalog_file.exists():
            print(f"[Sync] Error: Could not find catalog.yaml at {catalog_file}", file=sys.stderr)
            return 1

        catalog = load_yaml(catalog_file)

        target_item = sync_item or only
        if target_item:
            res_code = self._sync_single_item(
                self.spoke_root, hub_root, catalog, target_item, dry_run=dry_run
            )
        else:
            res_code = self._sync_full_bundle(
                self.spoke_root,
                hub_root,
                catalog,
                project_type,
                project_name,
                dry_run=dry_run,
                additional_bundles=additional_bundles,
                bootstrap=bootstrap,
                force=force,
            )

        if res_code != 0:
            return res_code

        if not dry_run and verify:
            verify_code = self.verify_spoke(hub_root=hub_root)
            if verify_code != 0:
                return verify_code

        return 0

    def verify_spoke(self, hub_root: Path | None = None) -> int:
        """Run deterministic ADR-0058 verification on synced spoke."""
        resolved_hub = hub_root or self.hub_root or Path(__file__).resolve().parents[3]
        cleanliness_script = resolved_hub / "scripts" / "spoke" / "check_spoke_cleanliness.py"
        import_depth_script = resolved_hub / "scripts" / "spoke" / "check_hub_import_depth.py"

        print("\n" + "=" * 85)
        print(" 🛡️  CCBA SPOKE DETERMINISTIC POST-SYNC VERIFICATION (ADR-0058)")
        print(f" Target Spoke: {self.spoke_root}")
        print("=" * 85)

        cmds: list[str] = []
        if cleanliness_script.exists():
            cmds.append(
                f"{sys.executable} {cleanliness_script.as_posix()} --path {self.spoke_root.as_posix()}"
            )
        if import_depth_script.exists():
            cmds.append(
                f"{sys.executable} {import_depth_script.as_posix()} --path {self.spoke_root.as_posix()}"
            )

        spoke_tests = self.spoke_root / "tests"
        if spoke_tests.exists() and any(spoke_tests.glob("test_*.py")):
            cmds.append(f"{sys.executable} -m pytest {spoke_tests.as_posix()} -q")

        if not cmds:
            print("[Verify] Không có lệnh kiểm tra nào cần thực thi.")
            return 0

        try:
            from ccba_harness.verifier import verify_patch_execution

            res = verify_patch_execution(commands=cmds, cwd=self.spoke_root, fail_fast=True)
            if res.all_passed:
                print("✅ SUCCESS: Spoke post-sync verification passed 100% deterministically.")
                return 0
            else:
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
        )

    def rollback(self, backup_path: Path | None = None) -> bool:
        """Restore .agents/ from latest snapshot or specified backup path."""
        return SpokeBackupManager(self.spoke_root).restore_backup(backup_path)

    def list_backups(self) -> list[Path]:
        """List available snapshots for this spoke."""
        return SpokeBackupManager(self.spoke_root).list_backups()


# Deep Seam Alias
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
    print("\n" + "=" * 90)
    print(f" CCBA MULTI-SPOKE BATCH SYNCHRONIZATION{mode_str}")
    print(f" Tìm thấy {len(spokes)} Spoke(s) trong Hub Registry.")
    print("=" * 90)

    results: list[dict[str, Any]] = []
    total_exit_code = 0
    sync_cls = _get_synchronizer_cls()

    for idx, sp in enumerate(spokes, 1):
        sp_name = sp.get("name", "Unknown")
        sp_path = sp.get("path", "")
        sp_type = sp.get("project_type", "Unknown")

        print(f"\n[{idx}/{len(spokes)}] 🔄 Đang xử lý Spoke: '{sp_name}' ({sp_type})")
        print(f"  Đường dẫn: {sp_path}")

        if not os.path.exists(sp_path):
            print("  ⚠️ Cảnh báo: Spoke không tồn tại vật lý trên ổ đĩa. Bỏ qua.")
            results.append({"name": sp_name, "path": sp_path, "status": "MISSING", "code": 1})
            continue

        try:
            engine = sync_cls(sp_path)
            res = engine.sync(
                sync_item=sync_item,
                dry_run=dry_run,
                force=force,
                backup=backup,
                check_git=check_git,
                bootstrap=bootstrap,
                verify=verify,
                pull_hub=(idx == 1),
            )
            status = "SUCCESS" if res == 0 else "FAILED"
            results.append({"name": sp_name, "path": sp_path, "status": status, "code": res})
            if res != 0:
                total_exit_code = 1
        except Exception as e:
            print(f"  ❌ Lỗi khi đồng bộ Spoke '{sp_name}': {e}", file=sys.stderr)
            results.append({"name": sp_name, "path": sp_path, "status": f"ERROR: {e}", "code": 1})
            total_exit_code = 1

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

    return total_exit_code

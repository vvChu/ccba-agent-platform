"""doc_auditor.py - Unified Facade for Document, Skill & Governance Auditing.

Thin Facade and backward-compatible entry point delegating to `scripts.governance`.
Sub-auditors live in `scripts/governance/`:
- `link_auditor.py`      — Markdown link validation, code symbols, and auto-fixer
- `skill_auditor.py`     — Agent skills, workflows & step completion criteria
- `registry_auditor.py`  — Legal registry maps & orphan file scanner
- `env_auditor.py`       — Environment variables parity (.env.example)
- `drift_auditor.py`     — Architecture drift & git change tracker
- `cli.py`               — CLI runner & console formatter

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure scripts directory is importable
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from governance import (
    CODE_REF_RE,
    ENV_VAR_RE,
    EXCLUSION_HEADERS,
    FRONTMATTER_RE,
    IGNORE_CODE_REFS,
    IGNORE_ENV_PREFIXES,
    IGNORE_ENV_VARS,
    LINK_RE,
    STEP_LINE_RE,
    WORKFLOW_HEADERS,
    AuditIssue,
    AuditReport,
    BaseAuditor,
    DocumentAuditor,
    DriftAuditor,
    EnvAuditor,
    LinkAuditor,
    RegistryAuditor,
    SkillAuditor,
    run_docs_validation_cli,
    run_skills_validation_cli,
)

# ---------------------------------------------------------------------------
# Backward-compatible standalone function aliases
# ---------------------------------------------------------------------------

_default_auditor = DocumentAuditor()


def parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str]:
    """Parse YAML frontmatter from document content (standalone alias)."""
    return _default_auditor.parse_frontmatter(content)


def extract_code_references(content: str) -> list[tuple[int, str]]:
    """Extract code symbol references (standalone alias)."""
    return _default_auditor.extract_code_references(content)


def extract_internal_links(content: str) -> list[tuple[int, str, str]]:
    """Extract relative internal Markdown links (standalone alias)."""
    return _default_auditor.extract_internal_links(content)


def extract_env_variables(content: str) -> list[tuple[int, str]]:
    """Extract documented environment variables (standalone alias)."""
    return _default_auditor.extract_env_variables(content)


def search_codebase_for_symbol(symbol: str, search_dirs: list[Path] | None = None) -> bool:
    """Check if symbol declaration exists in codebase (standalone alias)."""
    return _default_auditor.search_codebase_for_symbol(symbol, search_dirs)


def load_env_example(project_root: Path) -> set[str]:
    """Load declared env variable names from .env.example (standalone alias)."""
    auditor = DocumentAuditor(project_root)
    return auditor.load_env_example()


def load_legal_registry(project_root: Path) -> dict[str, Any]:
    """Load legal document registry (standalone alias)."""
    auditor = DocumentAuditor(project_root)
    return auditor.load_legal_registry()


def build_markdown_to_doc_map(
    registry: dict[str, Any], project_root: Path
) -> dict[Path, dict[str, Any]]:
    """Build map from path to legal doc definition (standalone alias)."""
    auditor = DocumentAuditor(project_root)
    return auditor.build_markdown_to_doc_map(registry)


def scan_orphan_files(bundle_root: Path, project_root: Path) -> list[Path]:
    """Scan orphan files in legal bundle (standalone alias)."""
    auditor = DocumentAuditor(project_root)
    return auditor.scan_orphan_files(bundle_root)


def validate_markdown_file(
    filepath: Path,
    search_dirs: list[Path],
    env_example_vars: set[str],
    project_root: Path,
    fix: bool = False,
    registry_map: dict[Path, dict[str, Any]] | None = None,
) -> dict[str, list[Any]]:
    """Validate a single markdown file (standalone alias)."""
    auditor = DocumentAuditor(project_root)
    return auditor.validate_markdown_file(
        filepath, search_dirs, env_example_vars, fix=fix, registry_map=registry_map
    )


def get_modified_files(project_root: Path) -> set[Path]:
    """Get modified files (standalone alias)."""
    auditor = DocumentAuditor(project_root)
    return auditor.get_modified_files()


def check_architecture_drift(project_root: Path) -> list[str]:
    """Check architecture drift (standalone alias)."""
    auditor = DocumentAuditor(project_root)
    return auditor.check_architecture_drift()


__all__ = [
    "AuditIssue",
    "AuditReport",
    "BaseAuditor",
    "DocumentAuditor",
    "DriftAuditor",
    "EnvAuditor",
    "LinkAuditor",
    "RegistryAuditor",
    "SkillAuditor",
    "run_docs_validation_cli",
    "run_skills_validation_cli",
    "parse_frontmatter",
    "extract_code_references",
    "extract_internal_links",
    "extract_env_variables",
    "search_codebase_for_symbol",
    "load_env_example",
    "load_legal_registry",
    "build_markdown_to_doc_map",
    "scan_orphan_files",
    "validate_markdown_file",
    "get_modified_files",
    "check_architecture_drift",
    "FRONTMATTER_RE",
    "CODE_REF_RE",
    "LINK_RE",
    "ENV_VAR_RE",
    "STEP_LINE_RE",
    "IGNORE_CODE_REFS",
    "IGNORE_ENV_PREFIXES",
    "IGNORE_ENV_VARS",
    "WORKFLOW_HEADERS",
    "EXCLUSION_HEADERS",
]

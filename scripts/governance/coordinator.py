"""coordinator.py - Unified Coordinator Deep Module for Governance & Document Auditing.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import AuditIssue, BaseAuditor, GovernanceAuditReport
from .cli import run_docs_validation_cli, run_skills_validation_cli
from .drift_auditor import DriftAuditor
from .duplication_auditor import DuplicationAuditor
from .env_auditor import EnvAuditor
from .link_auditor import LinkAuditor
from .registry_auditor import RegistryAuditor
from .skill_auditor import SkillAuditor
from .wiki_health_linter import WikiHealthLinter


class DocumentAuditor(BaseAuditor):
    """Deep Coordinator Module for Document, Skill & Governance Auditing.

    Coordinates 7 domain sub-auditors:
    - LinkAuditor: Markdown links, code symbol declarations & auto-fixing
    - SkillAuditor: Skill frontmatter, character limits & step completion criteria
    - RegistryAuditor: Legal registry mapping & orphan file detection
    - EnvAuditor: Environment variable documentation & .env.example parity
    - DriftAuditor: Git change tracking & Architecture drift detection
    - DuplicationAuditor: Anti-duplication SSOT guardrail for Hub-Spoke
    - WikiHealthLinter: LLM-Wiki index, mutation log & orphan note detection
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize DocumentAuditor with workspace root path."""
        if project_root is None:
            project_root = Path(__file__).resolve().parent.parent.parent
        self._project_root: Path = project_root
        self.link_auditor = LinkAuditor(self._project_root)
        self.skill_auditor = SkillAuditor(self._project_root)
        self.registry_auditor = RegistryAuditor(self._project_root)
        self.env_auditor = EnvAuditor(self._project_root)
        self.drift_auditor = DriftAuditor(self._project_root)
        self.duplication_auditor = DuplicationAuditor(self._project_root)
        self.wiki_linter = WikiHealthLinter(self._project_root)

    @property
    def project_root(self) -> Path:
        """Get the current project workspace root."""
        return self._project_root

    @project_root.setter
    def project_root(self, new_root: Path) -> None:
        """Set project root and propagate to all sub-auditors."""
        self._project_root = new_root
        if hasattr(self, "link_auditor"):
            self.link_auditor.project_root = new_root
        if hasattr(self, "skill_auditor"):
            self.skill_auditor.project_root = new_root
        if hasattr(self, "registry_auditor"):
            self.registry_auditor.project_root = new_root
        if hasattr(self, "env_auditor"):
            self.env_auditor.project_root = new_root
        if hasattr(self, "drift_auditor"):
            self.drift_auditor.project_root = new_root
        if hasattr(self, "duplication_auditor"):
            self.duplication_auditor.project_root = new_root
        if hasattr(self, "wiki_linter"):
            self.wiki_linter.project_root = new_root

    # ---------------------------------------------------------------------------
    # Delegation methods for LinkAuditor
    # ---------------------------------------------------------------------------

    def parse_frontmatter(self, content: str) -> tuple[dict[str, Any] | None, str]:
        """Parse YAML frontmatter from document content."""
        return self.link_auditor.parse_frontmatter(content)

    def extract_code_references(self, content: str) -> list[tuple[int, str]]:
        """Extract code symbol references like `my_func()` or `MyClass`."""
        return self.link_auditor.extract_code_references(content)

    def extract_internal_links(self, content: str) -> list[tuple[int, str, str]]:
        """Extract relative internal Markdown links."""
        return self.link_auditor.extract_internal_links(content)

    def search_codebase_for_symbol(
        self, symbol: str, search_dirs: list[Path] | None = None
    ) -> bool:
        """Check if symbol declaration exists in codebase source files."""
        return self.link_auditor.search_codebase_for_symbol(symbol, search_dirs)

    def validate_markdown_file(
        self,
        filepath: Path,
        search_dirs: list[Path] | None = None,
        env_example_vars: set[str] | None = None,
        fix: bool = False,
        registry_map: dict[Path, dict[str, Any]] | None = None,
    ) -> dict[str, list[Any]]:
        """Validate a single markdown file for inconsistencies, broken links, and hallucinations."""
        return self.link_auditor.validate_markdown_file(
            filepath,
            search_dirs=search_dirs,
            env_example_vars=env_example_vars,
            fix=fix,
            registry_map=registry_map,
        )

    # ---------------------------------------------------------------------------
    # Delegation methods for SkillAuditor
    # ---------------------------------------------------------------------------

    def audit_skill(
        self,
        file_path: Path,
        check_shallow: bool = False,
        enforce_gpi: bool = False,
    ) -> list[AuditIssue]:
        """Audit a single SKILL.md file for CCBA compliance."""
        return self.skill_auditor.audit_skill(
            file_path, check_shallow=check_shallow, enforce_gpi=enforce_gpi
        )

    def audit_workspace_gates(self, skills_dir: Path | None = None) -> list[AuditIssue]:
        """Perform workspace-level Hard CI Gate checks across all skills (ADR-0040)."""
        return self.skill_auditor.audit_workspace_gates(skills_dir)

    def analyze_steps_completion_criteria(self, body: str) -> list[tuple[int, str]]:
        """Helper to scan workflow steps for Completion Criteria."""
        return self.skill_auditor.analyze_steps_completion_criteria(body)

    _analyze_steps_completion_criteria = analyze_steps_completion_criteria

    def audit_workspace(self) -> dict[str, Any]:
        """Audit all documentation and skills in workspace."""
        return self.skill_auditor.audit_workspace()

    # ---------------------------------------------------------------------------
    # Delegation methods for RegistryAuditor
    # ---------------------------------------------------------------------------

    def load_legal_registry(self) -> dict[str, Any]:
        """Load legal document registry from workspace YAML."""
        return self.registry_auditor.load_legal_registry()

    def build_markdown_to_doc_map(
        self, registry: dict[str, Any] | None = None
    ) -> dict[Path, dict[str, Any]]:
        """Map resolved markdown file paths to document definitions in legal registry."""
        return self.registry_auditor.build_markdown_to_doc_map(registry)

    def scan_orphan_files(self, bundle_root: Path) -> list[Path]:
        """Scan for unreferenced markdown files under a bundle directory."""
        return self.registry_auditor.scan_orphan_files(bundle_root)

    # ---------------------------------------------------------------------------
    # Delegation methods for EnvAuditor
    # ---------------------------------------------------------------------------

    def load_env_example(self) -> set[str]:
        """Load declared environment variable names from .env.example."""
        return self.env_auditor.load_env_example()

    def extract_env_variables(self, content: str) -> list[tuple[int, str]]:
        """Extract documented environment variables."""
        return self.env_auditor.extract_env_variables(content)

    # ---------------------------------------------------------------------------
    # Delegation methods for DriftAuditor
    # ---------------------------------------------------------------------------

    def get_modified_files(self) -> set[Path]:
        """Get set of modified files in the current git workspace or branch."""
        return self.drift_auditor.get_modified_files()

    def check_marker_drift(self, docs: list[Path] | None = None) -> list[str]:
        """Check invariant marker drift delegating to DriftAuditor."""
        return self.drift_auditor.check_marker_drift(docs=docs)

    def check_structural_git_drift(self) -> list[str]:
        """Check structural git drift delegating to DriftAuditor."""
        return self.drift_auditor.check_structural_git_drift()

    def check_architecture_drift(self) -> list[str]:
        """Check if structural files or markers drifted without updating architecture docs."""
        return self.drift_auditor.check_architecture_drift()

    # ---------------------------------------------------------------------------
    # Coordinator Higher-Level APIs
    # ---------------------------------------------------------------------------

    def audit_documents(
        self,
        docs_dir: Path | str = "docs",
        src_dirs: list[Path] | None = None,
        fix: bool = False,
        changed_only: bool = False,
    ) -> GovernanceAuditReport:
        """Audit documentation files and return a structured GovernanceAuditReport."""
        target_dir = Path(docs_dir)
        if not target_dir.is_absolute():
            target_dir = self.project_root / target_dir

        if src_dirs is None:
            src_dirs = [
                self.project_root / "scripts",
                self.project_root / "packages",
                self.project_root,
            ]

        if not target_dir.exists():
            return GovernanceAuditReport(
                issues=[
                    AuditIssue(0, str(target_dir), "Directory does not exist", category="docs")
                ],
                total_issues=1,
                has_hard_errors=True,
                scanned_files=0,
            )

        exclude_dirs = {
            ".git",
            "node_modules",
            ".venv",
            "venv",
            "claudekit-engineer",
            "claudekit-marketing",
            ".pytest_cache",
            "extracted_docs",
            ".md",
            "CDE",
        }
        md_files = []

        if target_dir.is_file():
            if target_dir.suffix == ".md" and not target_dir.name.endswith("_compiled.md"):
                md_files.append(target_dir)
        else:
            for p in target_dir.rglob("*.md"):
                if p.is_file():
                    if p.name.endswith("_compiled.md"):
                        continue
                    if "legal_docs" in p.parts:
                        other_excludes = exclude_dirs - {".md"}
                        if any(ex in p.parts for ex in other_excludes):
                            continue
                    else:
                        if any(ex in p.parts for ex in exclude_dirs):
                            continue
                    if ".agents" in p.parts:
                        idx = p.parts.index(".agents")
                        if len(p.parts) > idx + 1:
                            subfolder = p.parts[idx + 1]
                            if subfolder not in {"skills", "workflows"}:
                                continue
                    md_files.append(p)

        for root_file in ["README.md", "PLATFORM.md", "CONTRIBUTING.md", "SECURITY.md"]:
            root_path = self.project_root / root_file
            if root_path.exists() and root_path not in md_files:
                md_files.append(root_path)

        env_vars = self.load_env_example()
        modified_files = self.get_modified_files()

        if changed_only:
            md_files = [f for f in md_files if f.resolve() in modified_files]

        registry = self.load_legal_registry()
        registry_map = self.build_markdown_to_doc_map(registry)

        issues_list: list[AuditIssue] = []
        has_hard_errors = False

        for filepath in md_files:
            file_issues = self.validate_markdown_file(
                filepath,
                src_dirs,
                env_vars,
                fix=fix,
                registry_map=registry_map,
            )

            str_path = str(
                filepath.relative_to(self.project_root)
                if filepath.is_relative_to(self.project_root)
                else filepath
            )

            for cat, items in file_issues.items():
                for line, subj, msg in items:
                    issues_list.append(
                        AuditIssue(
                            line_number=line,
                            subject=subj,
                            message=msg,
                            category=cat,
                            file_path=str_path,
                        )
                    )
                    if "Error" in msg or "Broken" in msg or "does not exist" in msg:
                        has_hard_errors = True

        arch_drift = self.check_architecture_drift()
        for err in arch_drift:
            issues_list.append(
                AuditIssue(
                    line_number=0,
                    subject="Architecture Drift",
                    message=err,
                    category="architecture_drift",
                    file_path="README.md",
                )
            )
            has_hard_errors = True

        dup_issues = self.duplication_auditor.audit()
        for issue in dup_issues:
            issues_list.append(issue)
            has_hard_errors = True

        wiki_issues = self.wiki_linter.audit()
        for issue in wiki_issues:
            issues_list.append(issue)
            has_hard_errors = True

        return GovernanceAuditReport(
            issues=issues_list,
            total_issues=len(issues_list),
            has_hard_errors=has_hard_errors,
            scanned_files=len(md_files),
        )

    def audit(self, target: Any = None) -> list[AuditIssue]:
        """Polymorphic audit entry point returning list of issues."""
        report = self.audit_documents()
        return report.issues

    def run_docs_validation_cli(self, args_list: list[str] | None = None) -> int:
        """CLI entry point for validate_docs.py."""
        return run_docs_validation_cli(self, args_list)

    def run_skills_validation_cli(self, args_list: list[str] | None = None) -> int:
        """CLI entry point for validate_skills.py."""
        return run_skills_validation_cli(self, args_list)

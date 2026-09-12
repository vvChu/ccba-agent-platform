"""Governance Module for CCBA Agent Platform.

Unified Deep Facade exporting Sub-Auditors, Common Regexes, and Constitution Cross-Reference Validator.
"""

from .audit_skills_hygiene import (
    SkillAuditResult,
    audit_all_skills,
    check_skills_hygiene,
)
from .audit_skills_hygiene import (
    audit_skill as audit_skill_hygiene,
)
from .audit_skills_hygiene import (
    generate_report as generate_hygiene_report,
)
from .base import (
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
    GovernanceAuditReport,
    is_exclusion_header,
)
from .cli import (
    run_docs_validation_cli,
    run_skills_validation_cli,
)
from .coordinator import DocumentAuditor
from .cross_ref_validator import (
    CrossRefIssue,
    CrossRefValidationReport,
    CrossRefValidator,
    extract_markdown_headings,
    find_closest_heading,
    validate_cross_references,
)
from .drift_auditor import DriftAuditor
from .duplication_auditor import (
    FORBIDDEN_DIRECTORIES,
    FORBIDDEN_RAW_SCRAPE_PATTERNS,
    DuplicationAuditor,
)
from .env_auditor import EnvAuditor
from .link_auditor import LinkAuditor
from .registry_auditor import RegistryAuditor
from .sandbox_auditor import SandboxAuditor
from .skill_auditor import SkillAuditor
from .wiki_health_linter import WikiHealthLinter

__all__ = [
    "AuditIssue",
    "AuditReport",
    "GovernanceAuditReport",
    "BaseAuditor",
    "DocumentAuditor",
    "DriftAuditor",
    "DuplicationAuditor",
    "EnvAuditor",
    "LinkAuditor",
    "RegistryAuditor",
    "SandboxAuditor",
    "SkillAuditor",
    "SkillAuditResult",
    "audit_all_skills",
    "audit_skill_hygiene",
    "check_skills_hygiene",
    "generate_hygiene_report",
    "WikiHealthLinter",
    "run_docs_validation_cli",
    "run_skills_validation_cli",
    "CODE_REF_RE",
    "ENV_VAR_RE",
    "EXCLUSION_HEADERS",
    "FRONTMATTER_RE",
    "IGNORE_CODE_REFS",
    "IGNORE_ENV_PREFIXES",
    "IGNORE_ENV_VARS",
    "LINK_RE",
    "STEP_LINE_RE",
    "WORKFLOW_HEADERS",
    "is_exclusion_header",
    "CrossRefIssue",
    "CrossRefValidationReport",
    "CrossRefValidator",
    "extract_markdown_headings",
    "find_closest_heading",
    "validate_cross_references",
    "FORBIDDEN_DIRECTORIES",
    "FORBIDDEN_RAW_SCRAPE_PATTERNS",
]

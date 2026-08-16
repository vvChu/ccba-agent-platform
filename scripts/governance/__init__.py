"""Governance Module for CCBA Agent Platform.

Unified Deep Facade exporting Sub-Auditors, Common Regexes, and Constitution Cross-Reference Validator.
"""

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
from .skill_auditor import SkillAuditor
from .wiki_health_linter import WikiHealthLinter

__all__ = [
    "AuditIssue",
    "AuditReport",
    "BaseAuditor",
    "DocumentAuditor",
    "DriftAuditor",
    "DuplicationAuditor",
    "EnvAuditor",
    "LinkAuditor",
    "RegistryAuditor",
    "SkillAuditor",
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
    "CrossRefIssue",
    "CrossRefValidationReport",
    "CrossRefValidator",
    "extract_markdown_headings",
    "find_closest_heading",
    "validate_cross_references",
    "FORBIDDEN_DIRECTORIES",
    "FORBIDDEN_RAW_SCRAPE_PATTERNS",
]

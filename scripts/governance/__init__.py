"""Governance Module for CCBA Agent Platform.

Unified Deep Facade exporting Sub-Auditors, Common Regexes, and Constitution Cross-Reference Validator.
"""

from scripts.governance.base import (
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
from scripts.governance.cli import (
    run_docs_validation_cli,
    run_skills_validation_cli,
)
from scripts.governance.coordinator import DocumentAuditor
from scripts.governance.cross_ref_validator import (
    CrossRefIssue,
    CrossRefValidationReport,
    CrossRefValidator,
    extract_markdown_headings,
    find_closest_heading,
    validate_cross_references,
)
from scripts.governance.drift_auditor import DriftAuditor
from scripts.governance.env_auditor import EnvAuditor
from scripts.governance.link_auditor import LinkAuditor
from scripts.governance.registry_auditor import RegistryAuditor
from scripts.governance.skill_auditor import SkillAuditor

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
]

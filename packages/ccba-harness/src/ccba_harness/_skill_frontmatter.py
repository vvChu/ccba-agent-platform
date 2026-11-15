"""_skill_frontmatter.py - Frontmatter parsing, taxonomy loading, and metadata validation.

Internal decomposition module for `ccba_harness.skill_validator`.
Not a standalone package boundary for external callers unless explicitly re-exported.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

try:
    import yaml as _DEFAULT_YAML
except ImportError:
    _DEFAULT_YAML = None

FRONTMATTER_PATTERN = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
FRONTMATTER_RE = FRONTMATTER_PATTERN
DEFAULT_VALID_BUNDLES: set[str] = set("_core _software _qc _consulting _bim _governance".split())
SHALLOW_SKILL_MIN_LINES = 35
MAX_MODEL_INVOKED_PER_BUNDLE = 10

_CATALOG_RELATIVE_PATHS = (
    Path(".agents") / "skills" / "platform-loader" / "catalog.yaml",
    Path("catalog.yaml"),
    Path(".agents") / "catalog.yaml",
)
_YAML_UNSET: Any = object()


@dataclass(frozen=True)
class SkillFrontmatterSpec:
    """Structured result of parsing a Markdown file's leading YAML frontmatter block."""

    raw_block: str
    metadata: dict[str, Any]
    body: str
    raw_yaml: str
    has_frontmatter: bool
    error: str | None = None


def _issue(fp: str, msg: str, category: str) -> SkillAuditIssue:
    """Build a line-1 SkillAuditIssue record concisely."""
    return SkillAuditIssue(1, fp, msg, category, fp)


class SkillAuditIssue(NamedTuple):
    """Container for a single skill or workflow audit issue."""

    line_number: int
    subject: str
    message: str
    category: str = ""
    file_path: str = ""


class AuditIssueString(str):
    """String subclass representing an audit issue with structured metadata."""

    line_number: int
    subject: str
    message: str
    category: str
    file_path: str

    def __new__(
        cls,
        message: str,
        line_number: int = 1,
        subject: str = "",
        category: str = "",
        file_path: str = "",
    ) -> AuditIssueString:
        obj = super().__new__(cls, message)
        obj.line_number = line_number
        obj.subject = subject
        obj.message = message
        obj.category = category
        obj.file_path = file_path
        return obj

    def to_audit_issue(self) -> SkillAuditIssue:
        """Convert to SkillAuditIssue NamedTuple."""
        return SkillAuditIssue(
            line_number=self.line_number,
            subject=self.subject,
            message=self.message,
            category=self.category,
            file_path=self.file_path,
        )


def resolve_yaml_module(yaml_module: Any = _YAML_UNSET) -> Any:
    """Resolve PyYAML module, honoring monkeypatched `skill_validator.yaml`."""
    if yaml_module is not _YAML_UNSET:
        return yaml_module
    facade = sys.modules.get("ccba_harness.skill_validator")
    if facade is not None and hasattr(facade, "yaml"):
        return facade.yaml
    return _DEFAULT_YAML


def normalize_bool_flag(value: Any) -> Any:
    """Normalize string boolean representations while preserving non-string types."""
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")
    return value


def load_catalog_dict(project_root: Path, yaml_module: Any = _YAML_UNSET) -> dict[str, Any] | None:
    """Load first readable catalog.yaml mapping beneath project_root."""
    yaml_mod = resolve_yaml_module(yaml_module)
    if yaml_mod is None:
        return None
    for rel_path in _CATALOG_RELATIVE_PATHS:
        cat_path = project_root / rel_path
        if not cat_path.exists():
            continue
        try:
            loaded = yaml_mod.safe_load(cat_path.read_text(encoding="utf-8")) or {}
            if isinstance(loaded, dict):
                return loaded
        except Exception:
            continue
    return None


def load_valid_bundles(project_root: Path, yaml_module: Any = _YAML_UNSET) -> set[str]:
    """Load valid bundle names from catalog.yaml with DEFAULT_VALID_BUNDLES fallback."""
    valid: set[str] = set(DEFAULT_VALID_BUNDLES)
    data = load_catalog_dict(project_root, yaml_module=yaml_module)
    if data is None:
        return valid

    bundles_map = data.get("bundles", {})
    if isinstance(bundles_map, dict):
        for b_list in bundles_map.values():
            if isinstance(b_list, list):
                valid.update(str(b) for b in b_list)

    notebook_ids = data.get("notebook_ids", {})
    if isinstance(notebook_ids, dict):
        valid.update(str(nb_key) for nb_key in notebook_ids.keys())
    return valid


def load_registered_commands(
    project_root: Path,
    extra_commands: set[str],
    yaml_module: Any = _YAML_UNSET,
) -> set[str]:
    """Retrieve canonical slash commands and aliases from catalog.yaml plus host commands."""
    commands: set[str] = set()
    data = load_catalog_dict(project_root, yaml_module=yaml_module)
    if data is not None:
        for item in data.get("skills", []):
            if isinstance(item, dict) and item.get("command"):
                cmd = str(item["command"]).strip()
                commands.add(cmd)
                if cmd.startswith("/ccba-"):
                    commands.add("/" + cmd[6:])
                elif cmd.startswith("/bigbim-"):
                    commands.add("/" + cmd[8:])
        for item in data.get("workflows", []):
            if isinstance(item, dict) and item.get("command"):
                commands.add(str(item["command"]).strip())

    commands.update(extra_commands)
    return commands


def parse_markdown_frontmatter(
    content: str, *, yaml_module: Any = _YAML_UNSET
) -> SkillFrontmatterSpec:
    """Parse leading YAML frontmatter block while preserving raw bytes and YAML errors."""
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return SkillFrontmatterSpec("", {}, content, "", False, None)
    raw_block = match.group(0).rstrip("\r\n")
    raw_yaml = match.group(1)
    body = content[match.end() :]
    yaml_mod = resolve_yaml_module(yaml_module)
    if yaml_mod is None:
        return SkillFrontmatterSpec(raw_block, {}, body, raw_yaml, True, "YAML_PACKAGE_MISSING")
    try:
        meta = yaml_mod.safe_load(raw_yaml)
    except Exception as exc:
        return SkillFrontmatterSpec(raw_block, {}, body, raw_yaml, True, f"YAML_PARSE_ERROR: {exc}")
    if not isinstance(meta, dict):
        return SkillFrontmatterSpec(raw_block, {}, body, raw_yaml, True, "NON_MAPPING_FRONTMATTER")
    return SkillFrontmatterSpec(raw_block, meta, body, raw_yaml, True, None)


def parse_frontmatter_dict(
    fp: str,
    content: str,
    yaml_module: Any = _YAML_UNSET,
    missing_yaml_msg: str = "PyYAML package is required to parse skill frontmatter. Run: pip install pyyaml",
) -> tuple[re.Match[str] | None, dict[str, Any] | None, list[SkillAuditIssue]]:
    """Extract regex match and parse YAML frontmatter dictionary with fail-closed issues."""
    match = FRONTMATTER_PATTERN.match(content)
    spec = parse_markdown_frontmatter(content, yaml_module=yaml_module)
    if not spec.has_frontmatter:
        return None, None, [_issue(fp, "Missing YAML frontmatter '---'", "MALFORMED_FRONTMATTER")]
    if spec.error == "YAML_PACKAGE_MISSING":
        return match, None, [_issue(fp, missing_yaml_msg, "YAML_PACKAGE_MISSING")]
    if spec.error and spec.error.startswith("YAML_PARSE_ERROR: "):
        msg = f"Failed to parse frontmatter YAML: {spec.error.removeprefix('YAML_PARSE_ERROR: ')}"
        return match, None, [_issue(fp, msg, "YAML_PARSE_ERROR")]
    if spec.error is not None:
        return (
            match,
            None,
            [_issue(fp, "Frontmatter YAML is not a valid dictionary", "MALFORMED_FRONTMATTER")],
        )
    return match, spec.metadata, []


def check_shallow_skill_content(
    file_path: Path,
    content: str | None = None,
    yaml_module: Any = _YAML_UNSET,
) -> list[SkillAuditIssue]:
    """Verify that a skill has at least SHALLOW_SKILL_MIN_LINES non-empty lines (ADR-0040)."""
    if content is None:
        if not file_path.exists():
            return []
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return []

    line_count = len([line for line in content.splitlines() if line.strip()])
    if line_count >= SHALLOW_SKILL_MIN_LINES:
        return []

    spec = parse_markdown_frontmatter(content, yaml_module=yaml_module)
    skill_name = str(spec.metadata.get("name") or file_path.parent.name)
    msg = (
        f"Skill '{skill_name}' is too shallow ({line_count} content lines < "
        f"{SHALLOW_SKILL_MIN_LINES} lines minimum per ADR-0040). "
        "Provide detailed workflow instructions and complete step criteria."
    )
    return [_issue(str(file_path), msg, "SHALLOW_SKILL_WARNING")]


def validate_skill_name_field(fp: str, meta: dict[str, Any]) -> list[SkillAuditIssue]:
    """Validate skill `name` presence and ADR-0056 namespace contract."""
    name = meta.get("name")
    if not name or not isinstance(name, str):
        return [
            SkillAuditIssue(1, fp, "Missing or invalid 'name' in frontmatter", "MISSING_NAME", fp)
        ]

    is_verify_cat = str(meta.get("category", "")).strip() == "verification"
    is_valid_namespace = (
        name.startswith(("ccba-", "bigbim-"))
        or name == "platform-loader"
        or (name.startswith("verify-") and is_verify_cat)
    )
    if is_valid_namespace:
        return []

    return [
        SkillAuditIssue(
            1,
            fp,
            f"Skill name '{name}' violates ADR-0056 namespace rules. "
            "Must start with 'ccba-' (or 'bigbim-', 'verify-' with category: verification, or 'platform-loader')",
            category="INVALID_NAMESPACE",
            file_path=fp,
        )
    ]


def validate_skill_description_field(
    fp: str,
    meta: dict[str, Any],
    disable_model_inv: Any,
) -> list[SkillAuditIssue]:
    """Validate `description` presence and <= 180 char ceiling for model-invoked skills."""
    description = meta.get("description")
    if not description or not isinstance(description, str):
        return [
            SkillAuditIssue(
                1, fp, "Missing or invalid 'description' in frontmatter", "MISSING_DESCRIPTION", fp
            )
        ]
    if not disable_model_inv and len(description) > 180:
        return [
            SkillAuditIssue(
                1,
                fp,
                f"Description length ({len(description)}) exceeds 180 character limit "
                "for model-invoked skill",
                category="DESCRIPTION_TOO_LONG",
                file_path=fp,
            )
        ]
    return []


def validate_skill_bundle_field(
    fp: str,
    meta: dict[str, Any],
    valid_bundles: set[str],
) -> list[SkillAuditIssue]:
    """Validate required `bundle` field against loaded taxonomy (ADR-0041 / ADR-0044)."""
    bundle = meta.get("bundle")
    if not bundle or not isinstance(bundle, str):
        return [
            SkillAuditIssue(
                1,
                fp,
                "Skill is missing required 'bundle' field in frontmatter",
                "MISSING_BUNDLE_FIELD",
                fp,
            )
        ]
    if bundle not in valid_bundles:
        return [
            SkillAuditIssue(
                1,
                fp,
                f"Skill bundle '{bundle}' is invalid. Must be one of: {sorted(valid_bundles)}",
                category="INVALID_BUNDLE_FIELD",
                file_path=fp,
            )
        ]
    return []


def _check_command_prefix(fp: str, name: str, command: Any) -> list[SkillAuditIssue]:
    """Check whether declared command matches canonical skill name slash prefixes."""
    cmd_base = str(command).strip().split()[0]
    expected_cmd = f"/{name}"
    allowed_prefixes = (
        expected_cmd,
        f"/{name.replace('ccba-', '')}",
        f"/workflow_{name.replace('ccba-', '').replace('-', '_')}",
    )
    if any(cmd_base == prefix for prefix in allowed_prefixes):
        return []
    return [
        SkillAuditIssue(
            1,
            fp,
            f"Skill '{name}' command '{command}' does not match expected Slash Command name '{expected_cmd}'",
            category="INVALID_COMMAND_FIELD",
            file_path=fp,
        )
    ]


def validate_skill_command_contracts(
    fp: str,
    content: str,
    meta: dict[str, Any],
) -> list[SkillAuditIssue]:
    """Validate ADR-0056 slash command contract and ADR-0066 hub/spoke command distribution."""
    issues: list[SkillAuditIssue] = []
    name = meta.get("name")
    name_str = name if isinstance(name, str) and name else ""
    user_invocable = normalize_bool_flag(meta.get("user-invocable", False))
    command = meta.get("command")

    if user_invocable:
        if not command:
            expected_cmd = f"/{name}" if name else ""
            issues.append(
                SkillAuditIssue(
                    1,
                    fp,
                    f"Skill '{name}' has 'user-invocable: true' but is missing "
                    f"'command: {expected_cmd}' in frontmatter (ADR-0056 Slash Command contract)",
                    category="MISSING_COMMAND_FIELD",
                    file_path=fp,
                )
            )
        elif name_str:
            issues.extend(_check_command_prefix(fp, name_str, command))
    elif command and name_str:
        issues.extend(_check_command_prefix(fp, name_str, command))

    dist_invocable = normalize_bool_flag(
        meta.get("user-invocable", meta.get("user_invocable", False))
    )
    bundle = meta.get("bundle")
    if command and dist_invocable and bundle == "_governance":
        scope = str(meta.get("scope", "")).strip().lower()
        if scope != "hub" and "# ccba:allow-hub-only-command" not in content:
            issues.append(
                SkillAuditIssue(
                    1,
                    fp,
                    f"Skill '{name}' declares interactive command '{command}' with 'bundle: _governance' "
                    "without 'scope: hub' (ADR-0066). Spoke developers will not get IDE slash command "
                    "autocomplete. Either promote to 'bundle: _core' or declare 'scope: hub' if Hub-only.",
                    category="INVALID_COMMAND_DISTRIBUTION",
                    file_path=fp,
                )
            )
    return issues


def validate_skill_frontmatter_metadata(
    fp: str,
    content: str,
    meta: dict[str, Any],
    valid_bundles: set[str],
) -> list[SkillAuditIssue]:
    """Validate skill frontmatter fields (name, description, bundle, slash commands)."""
    disable_model_inv = normalize_bool_flag(meta.get("disable-model-invocation", False))
    issues: list[SkillAuditIssue] = []
    issues.extend(validate_skill_name_field(fp, meta))
    issues.extend(validate_skill_description_field(fp, meta, disable_model_inv))
    issues.extend(validate_skill_bundle_field(fp, meta, valid_bundles))
    issues.extend(validate_skill_command_contracts(fp, content, meta))
    return issues

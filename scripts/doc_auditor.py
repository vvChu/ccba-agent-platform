"""doc_auditor.py - Unified Deep Module for Document, Skill & Governance Auditing.

Deep module hiding frontmatter parsing, line-scanning regexes, symbol lookups,
link validation, legal registry mapping, orphan scanning, architecture drift checks,
and skill step verification behind clean entry points:
- `audit_skill(path)`
- `audit_document(path, ...)`
- `audit_workspace()`
- `run_docs_validation_cli()`
- `run_skills_validation_cli()`

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple

import yaml

# Core Regex Patterns
FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
CODE_REF_RE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]*(?:\(\))?)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
ENV_VAR_RE = re.compile(r"`([A-Z][A-Z0-9_]{2,})`|\$([A-Z][A-Z0-9_]{2,})")
STEP_LINE_RE = re.compile(r"^\s*([0-9]+)\.\s+(.*)$")

# Common Keywords to Ignore in Code Symbol Audit
IGNORE_CODE_REFS: set[str] = {
    "true",
    "false",
    "null",
    "undefined",
    "string",
    "number",
    "boolean",
    "object",
    "array",
    "function",
    "async",
    "await",
    "const",
    "let",
    "var",
    "if",
    "else",
    "for",
    "while",
    "return",
    "import",
    "export",
    "default",
    "npm",
    "npx",
    "node",
    "yarn",
    "pnpm",
    "git",
    "bash",
    "sh",
    "zsh",
    "get",
    "post",
    "put",
    "delete",
    "patch",
    "head",
    "options",
    "json",
    "xml",
    "html",
    "css",
    "sql",
    "api",
    "url",
    "uri",
    "http",
    "https",
    "ok",
    "error",
    "warning",
    "info",
    "debug",
    "trace",
    "readme",
    "license",
    "changelog",
    "todo",
    "fixme",
    "note",
    "hack",
    "dev",
    "prod",
    "test",
    "staging",
    "production",
    "development",
    "src",
    "lib",
    "dist",
    "build",
    "docs",
    "tests",
    "config",
    "index",
    "main",
    "app",
    "server",
    "client",
    "utils",
    "helpers",
}

IGNORE_ENV_PREFIXES: list[str] = ["NODE_", "PATH", "HOME", "USER", "SHELL", "TERM", "PWD", "CI"]
IGNORE_ENV_VARS: set[str] = {"ARGUMENTS"}

WORKFLOW_HEADERS: set[str] = {
    "workflow",
    "quy trình",
    "các bước",
    "steps",
    "hành động",
    "chuyển đổi",
    "tiến hành",
    "thực hiện",
}

EXCLUSION_HEADERS: set[str] = {
    "lưu ý",
    "chú ý",
    "notes",
    "yêu cầu",
    "rules",
    "quy tắc",
    "tham chiếu",
    "reference",
    "giới thiệu",
    "introduction",
    "tổng quan",
    "overview",
    "chuẩn bị",
    "setup",
}


class AuditIssue(NamedTuple):
    """Container for a single audit issue."""

    line_number: int
    subject: str
    message: str


class DocumentAuditor:
    """Deep module for auditing CCBA Agent markdown documentation, skills, and governance rules.

    Hides internal line-scanning, symbol searches, legal registry maps, link validations,
    and frontmatter parsing logic behind a simplified interface.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize DocumentAuditor with workspace root path."""
        if project_root is None:
            project_root = Path(__file__).parent.parent.resolve()
        self.project_root = project_root

    def parse_frontmatter(self, content: str) -> tuple[dict[str, Any] | None, str]:
        """Parse YAML frontmatter from document content."""
        stripped = content.strip()
        if not stripped.startswith("---"):
            return None, content
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                if isinstance(frontmatter, dict):
                    return frontmatter, parts[2]
            except Exception:
                pass
        return None, content

    def extract_code_references(self, content: str) -> list[tuple[int, str]]:
        """Extract code symbol references like `my_func()` or `MyClass`."""
        references = []
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if line.strip().startswith("```"):
                continue
            matches = CODE_REF_RE.findall(line)
            for ref in matches:
                clean_ref = ref.replace("()", "")
                if clean_ref.lower() in IGNORE_CODE_REFS:
                    continue
                if ref.endswith("()") or (
                    clean_ref and clean_ref[0].isupper() and any(c.islower() for c in clean_ref)
                ):
                    references.append((idx + 1, ref))
        return references

    def extract_internal_links(self, content: str) -> list[tuple[int, str, str]]:
        """Extract relative internal Markdown links."""
        links = []
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            matches = LINK_RE.findall(line)
            for text, href in matches:
                if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
                    continue
                links.append((idx + 1, text, href))
        return links

    def extract_env_variables(self, content: str) -> list[tuple[int, str]]:
        """Extract documented environment variables."""
        env_vars = []
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if line.strip().startswith("```"):
                continue
            matches = ENV_VAR_RE.findall(line)
            for var1, var2 in matches:
                var = var1 or var2
                if not var:
                    continue
                if any(var.startswith(prefix) for prefix in IGNORE_ENV_PREFIXES):
                    continue
                if var in IGNORE_ENV_VARS:
                    continue
                env_vars.append((idx + 1, var))
        return env_vars

    def search_codebase_for_symbol(
        self, symbol: str, search_dirs: list[Path] | None = None
    ) -> bool:
        """Check if symbol declaration exists in codebase source files."""
        if search_dirs is None:
            search_dirs = [
                self.project_root / "src",
                self.project_root / "packages",
                self.project_root / "scripts",
            ]

        clean_sym = symbol.replace("()", "")
        patterns = [
            re.compile(r"\bdef\s+" + re.escape(clean_sym) + r"\b"),
            re.compile(r"\bclass\s+" + re.escape(clean_sym) + r"\b"),
            re.compile(r"\bfunction\s+" + re.escape(clean_sym) + r"\b"),
            re.compile(r"\bconst\s+" + re.escape(clean_sym) + r"\s*="),
            re.compile(r"\blet\s+" + re.escape(clean_sym) + r"\s*="),
        ]

        for sdir in search_dirs:
            if not sdir.exists():
                continue
            for ext in ["*.py", "*.js", "*.cjs", "*.ts", "*.go", "*.sh"]:
                for filepath in sdir.rglob(ext):
                    if any(
                        p in filepath.parts
                        for p in ["tests", "venv", ".venv", "node_modules", "dist", "build"]
                    ):
                        continue
                    try:
                        with open(filepath, encoding="utf-8", errors="ignore") as f:
                            file_content = f.read()
                            if any(pat.search(file_content) for pat in patterns):
                                return True
                    except Exception:
                        continue
        return False

    def load_env_example(self) -> set[str]:
        """Load declared environment variable names from .env.example."""
        env_path = self.project_root / ".env.example"
        if not env_path.exists():
            return set()
        env_vars = set()
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    match = re.match(r"^([A-Z0-9_]+)=", line)
                    if match:
                        env_vars.add(match.group(1))
        except Exception:
            pass
        return env_vars

    def load_legal_registry(self) -> dict:
        """Load legal document registry from workspace YAML."""
        registry_path = self.project_root / ".md" / "data" / "legal_registry.yaml"
        if not registry_path.exists():
            return {}
        try:
            with open(registry_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def build_markdown_to_doc_map(self, registry: dict | None = None) -> dict[Path, dict]:
        """Map resolved markdown file paths to document definitions in legal registry."""
        if registry is None:
            registry = self.load_legal_registry()
        mapping = {}
        for _cat, docs in registry.items():
            if not isinstance(docs, list):
                continue
            for doc in docs:
                if not isinstance(doc, dict):
                    continue
                potential_paths = []

                if "markdown_path" in doc:
                    potential_paths.append(self.project_root / doc["markdown_path"])

                if "file_path" in doc:
                    fp = self.project_root / doc["file_path"]
                    potential_paths.append(fp.with_suffix(".md"))
                    potential_paths.append(fp.parent / "full_text.md")

                doc_id = doc.get("id", "")
                if doc_id:
                    slug = doc_id.lower().replace("-", "_")
                    legal_docs_dir = self.project_root / ".md" / "legal_docs"
                    if legal_docs_dir.exists():
                        for p in legal_docs_dir.rglob("*.md"):
                            if p.name == "full_text.md" and slug in p.parent.name.lower():
                                potential_paths.append(p)
                            if p.stem.lower() == slug:
                                potential_paths.append(p)

                for p in potential_paths:
                    try:
                        resolved = p.resolve()
                        if resolved.exists():
                            mapping[resolved] = doc
                    except Exception:
                        pass
        return mapping

    def scan_orphan_files(self, bundle_root: Path) -> list[Path]:
        """Scan for unreferenced markdown files under a bundle directory."""
        exclude_dirs = {".git", "node_modules", ".venv", "venv", ".pytest_cache"}
        all_files = []
        for p in bundle_root.rglob("*.md"):
            if p.is_file() and not any(ex in p.parts for ex in exclude_dirs):
                all_files.append(p.resolve())

        if not all_files:
            return []

        referenced = set()
        for filepath in all_files:
            try:
                with open(filepath, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            links = self.extract_internal_links(content)
            for _line_num, _text, href in links:
                base_href = href.split("#")[0]
                if not base_href:
                    continue
                if base_href.startswith("/"):
                    resolved = (bundle_root / base_href.lstrip("/")).resolve()
                else:
                    resolved = (filepath.parent / base_href).resolve()
                referenced.add(resolved)

            frontmatter, _ = self.parse_frontmatter(content)
            if frontmatter and isinstance(frontmatter, dict):
                parent_doc = frontmatter.get("parent_document")
                if parent_doc and isinstance(parent_doc, str):
                    if parent_doc.startswith("/"):
                        parent_path = (bundle_root / parent_doc.lstrip("/")).resolve()
                    else:
                        parent_path = (filepath.parent / parent_doc).resolve()

                    if parent_path.exists() and parent_path.is_file():
                        try:
                            is_inside = parent_path.is_relative_to(bundle_root)
                        except ValueError:
                            is_inside = False
                        if is_inside:
                            referenced.add(filepath)

        orphans = []
        for filepath in all_files:
            if filepath.name in ("index.md", "full_text.md"):
                continue
            if filepath not in referenced:
                orphans.append(filepath)

        return orphans

    def get_modified_files(self) -> set[Path]:
        """Get set of modified files in the current git workspace or branch."""
        modified = set()
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if len(line) > 3:
                        filepath = (self.project_root / line[3:].strip()).resolve()
                        modified.add(filepath)

            res = subprocess.run(
                ["git", "diff", "--name-only", "origin/main...HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if line.strip():
                        filepath = (self.project_root / line.strip()).resolve()
                        modified.add(filepath)
        except Exception:
            pass
        return modified

    def check_architecture_drift(self) -> list[str]:
        """Check if structural files were added/deleted without updating architecture docs."""
        drift_errors = []
        try:
            res = subprocess.run(
                ["git", "diff", "--name-status", "origin/main...HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                res = subprocess.run(
                    ["git", "diff", "--name-status", "HEAD~1"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )

            changes = res.stdout.splitlines()
            res2 = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            changes.extend(res2.stdout.splitlines())

            structural_change = False
            arch_doc_updated = False
            arch_docs = {"README.md", "PLATFORM.md", ".agents/skills/architecture-sync/SKILL.md"}
            tracked_prefixes = ("packages/", "scripts/", ".agents/skills/", ".agents/workflows/")

            for line in changes:
                if not line.strip():
                    continue
                parts = line.split()
                status = parts[0]
                filepath = parts[-1].strip().replace("\\", "/")

                if filepath in arch_docs or (status.startswith("M") and filepath in arch_docs):
                    arch_doc_updated = True

                if (
                    status.startswith("A")
                    or status.startswith("D")
                    or status.startswith("R")
                    or status == "??"
                ):
                    if filepath == "pyproject.toml" or filepath.startswith(tracked_prefixes):
                        structural_change = True

            if structural_change and not arch_doc_updated:
                drift_errors.append(
                    "Structural drift detected: You added/deleted/renamed files in core directories (packages, scripts, skills, workflows) but did not update Architecture Docs (README.md, PLATFORM.md, architecture-sync). Run 'python scripts/update_arch_stats.py' and commit."
                )
        except Exception:
            pass
        return drift_errors

    def validate_markdown_file(
        self,
        filepath: Path,
        search_dirs: list[Path] | None = None,
        env_example_vars: set[str] | None = None,
        fix: bool = False,
        registry_map: dict[Path, dict] | None = None,
    ) -> dict[str, list[tuple[int, str, str]]]:
        """Validate a single markdown file for inconsistencies, broken links, and hallucinations."""
        if search_dirs is None:
            search_dirs = [
                self.project_root / "scripts",
                self.project_root / "packages",
                self.project_root,
            ]
        if env_example_vars is None:
            env_example_vars = self.load_env_example()
        if registry_map is None:
            registry_map = self.build_markdown_to_doc_map()

        issues = {
            "code_refs": [],
            "links": [],
            "env_vars": [],
            "okf_frontmatter": [],
            "okf_links": [],
            "okf_conflicts": [],
        }

        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            issues["links"].append((0, "Error reading file", str(e)))
            return issues

        is_okf = False
        bundle_root = None
        parts = filepath.resolve().parts
        if "legal_docs" in parts:
            idx = parts.index("legal_docs")
            if idx + 1 < len(parts):
                is_okf = True
                bundle_root = Path(*parts[: idx + 2])

        frontmatter = None
        if content.strip().startswith("---"):
            frontmatter, _ = self.parse_frontmatter(content)
            if frontmatter and isinstance(frontmatter, dict):
                okf_fields = {
                    "type",
                    "resource",
                    "status",
                    "document_number",
                    "timestamp",
                    "parent_document",
                    "uniclass",
                }
                if any(field in frontmatter for field in okf_fields):
                    is_okf = True
                    if not bundle_root:
                        bundle_root = filepath.parent

        if is_okf:
            if frontmatter is None:
                issues["okf_frontmatter"].append(
                    (1, "frontmatter", "Missing YAML frontmatter for OKF Bundle file")
                )
            else:
                if "type" not in frontmatter:
                    issues["okf_frontmatter"].append(
                        (1, "type", "Missing required field: 'type'")
                    )
                else:
                    okf_keywords = {
                        "Law",
                        "Decree",
                        "Circular",
                        "Standard",
                        "Appendix",
                        "Section",
                        "Consolidated Document",
                        "Guiding Document",
                    }
                    if frontmatter["type"] not in okf_keywords:
                        issues["okf_frontmatter"].append(
                            (
                                1,
                                "type",
                                f"Invalid type: '{frontmatter['type']}'. Must be one of {sorted(okf_keywords)}",
                            )
                        )

                if "resource" not in frontmatter:
                    issues["okf_frontmatter"].append(
                        (1, "resource", "Missing required field: 'resource'")
                    )

                if "status" not in frontmatter and "document_number" not in frontmatter:
                    issues["okf_frontmatter"].append(
                        (
                            1,
                            "status/document_number",
                            "Missing required field: 'status' or 'document_number'",
                        )
                    )

                if "timestamp" not in frontmatter:
                    issues["okf_frontmatter"].append(
                        (1, "timestamp", "Missing required field: 'timestamp'")
                    )

        # 1. Code symbol references
        code_refs = self.extract_code_references(content)
        for line_num, ref in code_refs:
            if not self.search_codebase_for_symbol(ref, search_dirs):
                issues["code_refs"].append((line_num, ref, "Symbol is not defined in codebase"))

        # 2. Links validation
        links = self.extract_internal_links(content)
        fixed_content = content
        file_modified = False
        lines = content.splitlines()

        for line_num, _text, href in links:
            base_href = href.split("#")[0]
            anchor = href.split("#", 1)[1] if "#" in href else ""
            target_path = None

            if base_href:
                if is_okf and href.startswith("/"):
                    target_path = (bundle_root / base_href.lstrip("/")).resolve()
                    if not target_path.exists():
                        issues["okf_links"].append(
                            (line_num, href, f"Resolved file does not exist: {target_path}")
                        )
                elif base_href.startswith("file:") or bool(re.match(r"^[a-zA-Z]:", base_href)):
                    clean_path = base_href.replace("file:///", "").replace("file://", "")
                    has_win_drive = bool(re.match(r"^[a-zA-Z]:", clean_path))

                    if has_win_drive and sys.platform != "win32":
                        workspace_name = self.project_root.name
                        if workspace_name in clean_path:
                            parts_link = clean_path.split(workspace_name + "/", 1)
                            rel_path_guess = (
                                f"../../{parts_link[1]}" if len(parts_link) > 1 else "relative path"
                            )
                            if len(parts_link) > 1:
                                try:
                                    depth_to_root = os.path.relpath(
                                        self.project_root, filepath.parent
                                    ).replace(os.sep, "/")
                                    rel_path_guess = f"{depth_to_root}/{parts_link[1]}"
                                    rel_path_guess = os.path.normpath(rel_path_guess).replace(
                                        os.sep, "/"
                                    )
                                except ValueError:
                                    pass

                            if fix:
                                fixed_href = (
                                    f"{rel_path_guess}#{anchor}" if anchor else rel_path_guess
                                )
                                fixed_content = fixed_content.replace(
                                    f"]({href})", f"]({fixed_href})"
                                )
                                file_modified = True
                                issues["links"].append(
                                    (
                                        line_num,
                                        href,
                                        f"[AUTO-FIXED] Absolute file link inside workspace on Linux. Fixed to: '{fixed_href}'",
                                    )
                                )
                            else:
                                issues["links"].append(
                                    (
                                        line_num,
                                        href,
                                        f"[WARNING] Absolute file link inside workspace. Recommend relative link: '{rel_path_guess}'",
                                    )
                                )
                        continue

                    target_path = Path(clean_path).resolve()
                    try:
                        is_internal = target_path.is_relative_to(self.project_root)
                    except ValueError:
                        is_internal = False

                    try:
                        is_sibling = target_path.is_relative_to(self.project_root.parent)
                    except ValueError:
                        is_sibling = False

                    if is_internal:
                        if not target_path.exists():
                            issues["links"].append(
                                (line_num, href, f"File does not exist: {clean_path}")
                            )
                        else:
                            try:
                                rel_to_workspace = os.path.relpath(
                                    target_path, filepath.parent
                                ).replace(os.sep, "/")
                                if fix:
                                    fixed_href = (
                                        f"{rel_to_workspace}#{anchor}"
                                        if anchor
                                        else rel_to_workspace
                                    )
                                    fixed_content = fixed_content.replace(
                                        f"]({href})", f"]({fixed_href})"
                                    )
                                    file_modified = True
                                    issues["links"].append(
                                        (
                                            line_num,
                                            href,
                                            f"[AUTO-FIXED] Absolute file link inside workspace. Fixed to: '{fixed_href}'",
                                        )
                                    )
                                else:
                                    issues["links"].append(
                                        (
                                            line_num,
                                            href,
                                            f"[WARNING] Absolute file link inside workspace. Recommend relative link: '{rel_to_workspace}'",
                                        )
                                    )
                            except ValueError:
                                issues["links"].append(
                                    (
                                        line_num,
                                        href,
                                        f"[WARNING] Absolute file link inside workspace on different drive: '{clean_path}'",
                                    )
                                )
                    elif is_sibling:
                        if target_path.exists():
                            try:
                                rel_to_parent = os.path.relpath(
                                    target_path, filepath.parent
                                ).replace(os.sep, "/")
                                if fix:
                                    fixed_href = (
                                        f"{rel_to_parent}#{anchor}" if anchor else rel_to_parent
                                    )
                                    fixed_content = fixed_content.replace(
                                        f"]({href})", f"]({fixed_href})"
                                    )
                                    file_modified = True
                                    issues["links"].append(
                                        (
                                            line_num,
                                            href,
                                            f"[AUTO-FIXED] Sibling repository link. Fixed to: '{fixed_href}'",
                                        )
                                    )
                                else:
                                    issues["links"].append(
                                        (
                                            line_num,
                                            href,
                                            f"[WARNING] Sibling repository absolute link. Recommend relative link: '{rel_to_parent}'",
                                        )
                                    )
                            except ValueError:
                                pass
                    else:
                        continue
                else:
                    target_path = (filepath.parent / base_href).resolve()
                    if is_okf:
                        try:
                            is_inside = target_path.is_relative_to(bundle_root)
                        except ValueError:
                            is_inside = False
                        if is_inside:
                            issues["okf_links"].append(
                                (
                                    line_num,
                                    href,
                                    "Cross-link inside bundle must start with '/' (absolute path relative to bundle root)",
                                )
                            )
                    if not target_path.exists():
                        issues["links"].append(
                            (line_num, href, f"File does not exist: {base_href}")
                        )
            else:
                target_path = filepath.resolve()

            # Cross-Validity conflicts
            if anchor and registry_map and target_path:
                doc = registry_map.get(target_path)
                if doc:
                    clauses = doc.get("clauses", {})
                    if anchor in clauses:
                        clause = clauses[anchor]
                        status = clause.get("status")
                        if status in ("amended", "superseded"):
                            idx = line_num - 1
                            start = max(0, idx - 3)
                            end = min(len(lines), idx + 4)
                            accompanied = False
                            for i in range(start, end):
                                if "> [!WARNING]" in lines[i]:
                                    accompanied = True
                                    break
                            if not accompanied:
                                issues["okf_conflicts"].append(
                                    (
                                        line_num,
                                        href,
                                        f"Link points to {status} clause '{anchor}' in '{doc.get('id')}' but is not accompanied by a > [!WARNING] block",
                                    )
                                )

        if fix and file_modified:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(fixed_content)
            except Exception as e:
                issues["links"].append((0, "Error writing fixed file", str(e)))

        # 3. Environment variables check
        env_vars = self.extract_env_variables(content)
        for line_num, var in env_vars:
            if env_example_vars and var not in env_example_vars:
                issues["env_vars"].append((line_num, var, "Variable is missing in .env.example"))

        # 4. Superseded legal doc check
        superseded_docs_patterns = [
            (r"Nghị định 06/2021", "NĐ 06/2021 đã bị thay thế bởi NĐ 105/2025/NĐ-CP"),
            (r"Nghị định 15/2021", "NĐ 15/2021 đã bị thay thế bởi NĐ 105/2025/NĐ-CP"),
            (
                r"Luật Xây dựng 2014",
                "Luật XD 2014 đã bị thay thế bởi Luật Xây dựng 2025 (135/2025/QH15)",
            ),
        ]
        for line_idx, line_str in enumerate(lines, 1):
            for pattern, note in superseded_docs_patterns:
                if re.search(pattern, line_str, re.IGNORECASE):
                    if not re.search(
                        r"(thay thế|superseded|105/2025|135/2025)", line_str, re.IGNORECASE
                    ):
                        issues["okf_conflicts"].append(
                            (
                                line_idx,
                                line_str.strip()[:60],
                                f"[WARNING] Tham chiếu văn bản hết hiệu lực: '{pattern}'. {note}",
                            )
                        )

        return issues

    def audit_skill(self, file_path: Path) -> list[AuditIssue]:
        """Audit a single SKILL.md file for CCBA compliance."""
        issues: list[AuditIssue] = []
        if not file_path.exists():
            return [AuditIssue(1, str(file_path), "File does not exist")]

        content = file_path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(content)
        if not match:
            return [AuditIssue(1, str(file_path), "Missing YAML frontmatter '---'")]

        try:
            meta = yaml.safe_load(match.group(1))
        except Exception as e:
            return [AuditIssue(1, str(file_path), f"Failed to parse frontmatter YAML: {e}")]

        if not isinstance(meta, dict):
            return [AuditIssue(1, str(file_path), "Frontmatter YAML is not a valid dictionary")]

        name = meta.get("name")
        description = meta.get("description")
        disable_model_inv = meta.get("disable-model-invocation", False)

        if not name or not isinstance(name, str):
            issues.append(AuditIssue(1, str(file_path), "Missing or invalid 'name' in frontmatter"))
        if not description or not isinstance(description, str):
            issues.append(
                AuditIssue(1, str(file_path), "Missing or invalid 'description' in frontmatter")
            )

        if description and isinstance(description, str) and not disable_model_inv:
            if len(description) > 180:
                issues.append(
                    AuditIssue(
                        1,
                        str(file_path),
                        f"Description length ({len(description)}) exceeds 180 character limit for model-invoked skill",
                    )
                )

        frontmatter_lines = len(match.group(0).splitlines())
        body = content[match.end() :]

        step_errors = self._analyze_steps_completion_criteria(body)
        for line_offset, err_msg in step_errors:
            abs_line = line_offset + frontmatter_lines
            issues.append(AuditIssue(abs_line, str(file_path), err_msg))

        return issues

    def _analyze_steps_completion_criteria(self, body: str) -> list[tuple[int, str]]:
        """Helper to scan workflow steps for Completion Criteria."""
        errors = []
        lines = body.splitlines()
        in_workflow_section = False
        workflow_trigger_level = None
        header_stack: list[tuple[int, str, bool]] = []
        in_code_block = False
        current_step_line = None
        current_step_num = None
        current_step_content: list[str] = []

        for idx, line in enumerate(lines):
            line_strip = line.strip()
            if line_strip.startswith("```"):
                in_code_block = not in_code_block
                if current_step_line is not None:
                    current_step_content.append(line)
                continue

            if in_code_block:
                if current_step_line is not None:
                    current_step_content.append(line)
                continue

            if line_strip.startswith("#"):
                if current_step_line is not None:
                    step_body = "\n".join(current_step_content)
                    if not (
                        "**Completion Criterion:**" in step_body
                        or "**Tiêu chí hoàn thành:**" in step_body
                    ):
                        errors.append(
                            (
                                current_step_line,
                                f"Step {current_step_num} is missing a Completion Criterion ('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                            )
                        )
                    current_step_line = None
                    current_step_num = None
                    current_step_content = []

                level = len(line_strip) - len(line_strip.lstrip("#"))
                header_text = line_strip.lstrip("#").strip().lower()

                while header_stack and header_stack[-1][0] >= level:
                    header_stack.pop()

                is_exclusion = any(kw in header_text for kw in EXCLUSION_HEADERS)
                is_workflow_keyword = any(kw in header_text for kw in WORKFLOW_HEADERS)

                if is_workflow_keyword and not is_exclusion:
                    is_workflow = True
                elif is_exclusion:
                    is_workflow = False
                else:
                    is_workflow = header_stack[-1][2] if header_stack else False

                header_stack.append((level, header_text, is_workflow))
                in_workflow_section = is_workflow
                if in_workflow_section:
                    if workflow_trigger_level is None:
                        workflow_trigger_level = level
                else:
                    workflow_trigger_level = None
                continue

            if not in_workflow_section:
                continue

            current_level = header_stack[-1][0] if header_stack else 0
            if current_level != workflow_trigger_level:
                continue

            step_match = STEP_LINE_RE.match(line)
            if step_match:
                if current_step_line is not None:
                    step_body = "\n".join(current_step_content)
                    if not (
                        "**Completion Criterion:**" in step_body
                        or "**Tiêu chí hoàn thành:**" in step_body
                    ):
                        errors.append(
                            (
                                current_step_line,
                                f"Step {current_step_num} is missing a Completion Criterion ('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                            )
                        )

                current_step_line = idx + 1
                current_step_num = step_match.group(1)
                current_step_content = [line]
            elif current_step_line is not None:
                current_step_content.append(line)

        if current_step_line is not None:
            step_body = "\n".join(current_step_content)
            if not (
                "**Completion Criterion:**" in step_body or "**Tiêu chí hoàn thành:**" in step_body
            ):
                errors.append(
                    (
                        current_step_line,
                        f"Step {current_step_num} is missing a Completion Criterion ('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                    )
                )

        return errors

    def audit_workspace(self) -> dict[str, Any]:
        """Audit all documentation and skills in workspace."""
        skill_issues: list[AuditIssue] = []
        skills_dir = self.project_root / ".agents" / "skills"

        if skills_dir.exists():
            for skill_path in skills_dir.rglob("SKILL.md"):
                skill_issues.extend(self.audit_skill(skill_path))

        return {
            "skills": skill_issues,
            "total_skill_issues": len(skill_issues),
        }

    def run_docs_validation_cli(self, args_list: list[str] | None = None) -> int:
        """CLI entry point for validate_docs.py."""
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

        parser = argparse.ArgumentParser(description="Validate documentation accuracy.")
        parser.add_argument(
            "docs_dir",
            nargs="?",
            default="docs",
            help="Directory containing markdown files (default: docs)",
        )
        parser.add_argument(
            "--src",
            default="scripts,packages",
            help="Comma-separated directories to search for code definitions",
        )
        parser.add_argument("--root", default=".", help="Project workspace root directory")
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Automatically convert absolute workspace links to relative links",
        )
        parser.add_argument(
            "--changed", action="store_true", help="Only validate markdown files changed in git"
        )

        args = parser.parse_args(args_list)

        self.project_root = Path(args.root).resolve()
        docs_dir = Path(args.docs_dir)
        if not docs_dir.is_absolute():
            docs_dir = self.project_root / docs_dir

        src_paths = [Path(p.strip()) for p in args.src.split(",")]
        resolved_src_paths = []
        for p in src_paths:
            if not p.is_absolute():
                resolved_src_paths.append(self.project_root / p)
            else:
                resolved_src_paths.append(p)
        resolved_src_paths.append(self.project_root)

        if not docs_dir.exists():
            print(f"\x1b[31mError:\x1b[0m Docs directory '{docs_dir}' does not exist.")
            return 1

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

        if docs_dir.is_file():
            if docs_dir.suffix == ".md" and not docs_dir.name.endswith("_compiled.md"):
                md_files.append(docs_dir)
        else:
            for p in docs_dir.rglob("*.md"):
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

        if not md_files:
            print("No markdown files found to validate.")
            return 0

        env_vars = self.load_env_example()
        modified_files = self.get_modified_files()

        if args.changed:
            md_files = [f for f in md_files if f.resolve() in modified_files]

        registry = self.load_legal_registry()
        registry_map = self.build_markdown_to_doc_map(registry)

        print(f"Scanned {len(md_files)} markdown file(s).")
        print(
            f"Searching code declarations in: {', '.join(str(p.relative_to(self.project_root)) for p in resolved_src_paths if p.exists())}"
        )
        print("-" * 60)

        total_issues = 0
        broken_links_count = 0
        hard_errors_count = 0
        bundle_roots = set()

        for filepath in md_files:
            relative_path = (
                filepath.relative_to(self.project_root)
                if filepath.is_relative_to(self.project_root)
                else filepath
            )
            issues = self.validate_markdown_file(
                filepath,
                resolved_src_paths,
                env_vars,
                fix=args.fix,
                registry_map=registry_map,
            )

            parts = filepath.resolve().parts
            if "legal_docs" in parts:
                idx = parts.index("legal_docs")
                if idx + 1 < len(parts):
                    bundle_roots.add(Path(*parts[: idx + 2]))

            file_has_issues = any(issues.values())
            if file_has_issues:
                print(f"\n\x1b[4mFile: {relative_path}\x1b[0m")
                is_modified = filepath.resolve() in modified_files
                if not modified_files:
                    if os.getenv("GITHUB_ACTIONS") == "true":
                        is_modified = False
                    else:
                        is_modified = True

                is_hard_error = is_modified or ("legal_docs" in docs_dir.parts)

                for line, field, err in issues.get("okf_frontmatter", []):
                    if is_hard_error:
                        print(
                            f"  [L{line}] \x1b[31mOKF Frontmatter Error:\x1b[0m field `{field}` - {err}"
                        )
                        total_issues += 1
                        hard_errors_count += 1
                    else:
                        print(
                            f"  [L{line}] \x1b[33mOKF Frontmatter Warning:\x1b[0m field `{field}` - {err}"
                        )
                        total_issues += 1

                for line, symbol, err in issues["code_refs"]:
                    print(f"  [L{line}] \x1b[33mCode Ref Warning:\x1b[0m `{symbol}` - {err}")
                    total_issues += 1

                for line, link, err in issues.get("okf_links", []):
                    if is_hard_error:
                        print(f"  [L{line}] \x1b[31mOKF Link Error:\x1b[0m ({link}) - {err}")
                        total_issues += 1
                        hard_errors_count += 1
                    else:
                        print(f"  [L{line}] \x1b[33mOKF Link Warning:\x1b[0m ({link}) - {err}")
                        total_issues += 1

                for line, link, err in sorted(issues["links"]):
                    if "[AUTO-FIXED]" in err:
                        print(f"  [L{line}] \x1b[32mLink Fixed:\x1b[0m ({link}) - {err}")
                    elif "[WARNING]" in err:
                        print(f"  [L{line}] \x1b[33mLink Warning:\x1b[0m ({link}) - {err}")
                        total_issues += 1
                    else:
                        if is_hard_error:
                            print(
                                f"  [L{line}] \x1b[31mBroken Link Error:\x1b[0m ({link}) - {err}"
                            )
                            total_issues += 1
                            broken_links_count += 1
                        else:
                            print(
                                f"  [L{line}] \x1b[33mLink Warning (Old File):\x1b[0m ({link}) - [SOFT-WARN] {err}"
                            )
                            total_issues += 1

                for line, link, err in issues.get("okf_conflicts", []):
                    if is_hard_error:
                        print(f"  [L{line}] \x1b[31mOKF Conflict Error:\x1b[0m ({link}) - {err}")
                        total_issues += 1
                        hard_errors_count += 1
                    else:
                        print(
                            f"  [L{line}] \x1b[33mOKF Conflict Warning:\x1b[0m ({link}) - {err}"
                        )
                        total_issues += 1

                for line, var, err in issues["env_vars"]:
                    print(f"  [L{line}] \x1b[33mEnv Var Warning:\x1b[0m `{var}` - {err}")
                    total_issues += 1

        orphan_issues_count = 0
        for root in sorted(bundle_roots):
            orphans = self.scan_orphan_files(root)
            if orphans:
                print(f"\n\x1b[4mBundle: {root.relative_to(self.project_root)}\x1b[0m")
                for o in sorted(orphans):
                    rel_o = o.relative_to(self.project_root)
                    bundle_has_mod = any(f.is_relative_to(root) for f in modified_files)
                    is_hard = bundle_has_mod or ("legal_docs" in docs_dir.parts)

                    if is_hard:
                        print(
                            f"  \x1b[31mOrphan File Error:\x1b[0m {rel_o} is not referenced by any other markdown file in the bundle."
                        )
                        total_issues += 1
                        orphan_issues_count += 1
                    else:
                        print(
                            f"  \x1b[33mOrphan File Warning:\x1b[0m {rel_o} is not referenced by any other markdown file in the bundle."
                        )
                        total_issues += 1

        arch_drift_issues = self.check_architecture_drift()
        if arch_drift_issues:
            print("\n\x1b[4mArchitecture Drift Check\x1b[0m")
            for err in arch_drift_issues:
                print(f"  \x1b[31mDrift Error:\x1b[0m {err}")
                total_issues += 1
                hard_errors_count += 1

        print("-" * 60)
        if total_issues > 0:
            print(f"Completed with {total_issues} issue(s) detected.")
            if broken_links_count > 0 or hard_errors_count > 0 or orphan_issues_count > 0:
                print(
                    "\x1b[31m[ERROR] Detected hard errors/broken links. Blocking commit/build.\x1b[0m"
                )
                return 1
            else:
                print(
                    "\x1b[33m[WARN] Warnings/Old file broken links detected. Committing/building is allowed.\x1b[0m"
                )
                return 0
        else:
            print(
                "\x1b[32mDocumentation validation completed successfully! No issues detected.\x1b[0m"
            )
            return 0

    def run_skills_validation_cli(self, args_list: list[str] | None = None) -> int:
        """CLI entry point for validate_skills.py."""
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

        parser = argparse.ArgumentParser(description="Validate CCBA Agent Skills.")
        parser.add_argument(
            "skills_dir",
            nargs="?",
            default=".agents/skills",
            help="Directory containing skills (default: .agents/skills)",
        )
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Validate a specific SKILL.md file instead of the whole directory",
        )
        args = parser.parse_args(args_list)

        if args.file:
            target_path = Path(args.file)
            if not target_path.is_absolute():
                target_path = self.project_root / target_path
            skills_files = [target_path] if target_path.exists() else []
        else:
            search_path = Path(args.skills_dir)
            if not search_path.is_absolute():
                search_path = self.project_root / search_path
            skills_files = list(search_path.rglob("SKILL.md")) if search_path.exists() else []

        if not skills_files:
            print("No SKILL.md files found for validation.")
            return 0

        total_errors = 0
        for skill_path in skills_files:
            issues = self.audit_skill(skill_path)
            if issues:
                rel_path = (
                    skill_path.relative_to(self.project_root)
                    if skill_path.is_relative_to(self.project_root)
                    else skill_path
                )
                print(f"\n\x1b[31m[ERROR]\x1b[0m {rel_path}:")
                for line, _subject, msg in issues:
                    print(f"  Line {line}: {msg}")
                    total_errors += 1

        if total_errors > 0:
            print(f"\nValidation failed with {total_errors} error(s).")
            return 1

        print(f"\x1b[32mSuccessfully validated {len(skills_files)} SKILL.md file(s).\x1b[0m")
        return 0


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


def search_codebase_for_symbol(
    symbol: str, search_dirs: list[Path] | None = None
) -> bool:
    """Check if symbol declaration exists in codebase (standalone alias)."""
    return _default_auditor.search_codebase_for_symbol(symbol, search_dirs)


def load_env_example(project_root: Path) -> set[str]:
    """Load declared env variable names from .env.example (standalone alias)."""
    auditor = DocumentAuditor(project_root)
    return auditor.load_env_example()


def load_legal_registry(project_root: Path) -> dict:
    """Load legal document registry (standalone alias)."""
    auditor = DocumentAuditor(project_root)
    return auditor.load_legal_registry()


def build_markdown_to_doc_map(registry: dict, project_root: Path) -> dict[Path, dict]:
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
    registry_map: dict[Path, dict] = None,
) -> dict[str, list[tuple[int, str, str]]]:
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

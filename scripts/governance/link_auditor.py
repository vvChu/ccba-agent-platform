"""link_auditor.py - Markdown internal link, code symbol reference validation & auto-fixer.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from .base import (
    CODE_REF_RE,
    ENV_VAR_RE,
    IGNORE_CODE_REFS,
    IGNORE_ENV_PREFIXES,
    IGNORE_ENV_VARS,
    LINK_RE,
    AuditIssue,
    BaseAuditor,
)


class LinkAuditor(BaseAuditor):
    """Deep Sub-Auditor for Markdown links, code symbols, and auto-fixing non-portable paths."""

    def __init__(self, project_root: Path | None = None) -> None:
        super().__init__(project_root)
        self._symbol_cache: dict[tuple[str, tuple[str, ...]], bool] = {}
        self._file_list_cache: dict[tuple[str, ...], list[Path]] = {}

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
        in_code_block = False
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
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
        in_code_block = False
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # Loại bỏ inline code spans (ví dụ `[link](url)`) để không bắt nhầm link ví dụ
            line_no_inline_code = re.sub(r"`[^`]+`", "", line)
            matches = LINK_RE.findall(line_no_inline_code)
            for text, href in matches:
                if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
                    continue
                links.append((idx + 1, text, href))
        return links

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

        dirs_key = tuple(str(d.resolve()) for d in search_dirs)
        cache_key = (symbol, dirs_key)
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]

        clean_sym = symbol.replace("()", "")
        patterns = [
            re.compile(r"\bdef\s+" + re.escape(clean_sym) + r"\b"),
            re.compile(r"\bclass\s+" + re.escape(clean_sym) + r"\b"),
            re.compile(r"\bfunction\s+" + re.escape(clean_sym) + r"\b"),
            re.compile(r"\bconst\s+" + re.escape(clean_sym) + r"\s*="),
            re.compile(r"\blet\s+" + re.escape(clean_sym) + r"\s*="),
        ]

        if dirs_key not in self._file_list_cache:
            files: list[Path] = []
            excludes = [
                "tests",
                "venv",
                ".venv",
                "node_modules",
                "dist",
                "build",
                ".md",
                ".git",
                "__pycache__",
            ]
            for sdir in search_dirs:
                if not sdir.exists():
                    continue
                for ext in ["*.py", "*.js", "*.cjs", "*.ts", "*.go", "*.sh"]:
                    for filepath in sdir.rglob(ext):
                        if any(p in filepath.parts for p in excludes):
                            continue
                        files.append(filepath)
            self._file_list_cache[dirs_key] = files

        file_list = self._file_list_cache[dirs_key]
        for filepath in file_list:
            try:
                with open(filepath, encoding="utf-8", errors="ignore") as f:
                    file_content = f.read()
                    if any(pat.search(file_content) for pat in patterns):
                        self._symbol_cache[cache_key] = True
                        return True
            except Exception:
                continue

        self._symbol_cache[cache_key] = False
        return False

    def validate_markdown_file(
        self,
        filepath: Path,
        search_dirs: list[Path] | None = None,
        env_example_vars: set[str] | None = None,
        fix: bool = False,
        registry_map: dict[Path, dict[str, Any]] | None = None,
    ) -> dict[str, list[Any]]:
        """Validate a single markdown file for inconsistencies, broken links, and hallucinations."""
        if search_dirs is None:
            search_dirs = [
                self.project_root / "src",
                self.project_root / "packages",
                self.project_root / "scripts",
            ]
            # Dynamic Skill Scope: nạp thêm scripts của skill nếu đang audit file trong skill đó
            resolved_path = filepath.resolve()
            parts = resolved_path.parts
            if ".agents" in parts and "skills" in parts:
                try:
                    idx = parts.index("skills")
                    if idx + 1 < len(parts):
                        skill_root = Path(*parts[: idx + 2])
                        skill_scripts = skill_root / "scripts"
                        if skill_scripts.exists() and skill_scripts.is_dir():
                            search_dirs = list(search_dirs) + [skill_scripts]
                except Exception:
                    pass

        issues: dict[str, list[Any]] = {
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
                    issues["okf_frontmatter"].append((1, "type", "Missing required field: 'type'"))
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
                if is_okf and bundle_root and href.startswith("/"):
                    target_path = (bundle_root / base_href.lstrip("/")).resolve()
                    if not target_path.exists():
                        issues["okf_links"].append(
                            (line_num, href, f"Resolved file does not exist: {target_path}")
                        )
                elif base_href.startswith("file:") or bool(re.match(r"^[a-zA-Z]:", base_href)):
                    clean_path = (
                        base_href.replace("file:///", "").replace("file://", "").replace("\\", "/")
                    )
                    workspace_name = self.project_root.name
                    rel_path_guess = None

                    # 1. Thử resolve đường dẫn tuyệt đối trực tiếp
                    try:
                        target_path = Path(clean_path).resolve()
                        if target_path.is_relative_to(self.project_root):
                            rel_path_guess = os.path.relpath(target_path, filepath.parent).replace(
                                os.sep, "/"
                            )
                        elif target_path.is_relative_to(self.project_root.parent):
                            rel_path_guess = os.path.relpath(target_path, filepath.parent).replace(
                                os.sep, "/"
                            )
                    except (ValueError, Exception):
                        pass

                    # 2. Nếu không resolve được (ví dụ chạy trên Linux nhưng link có D:/workspace), tách theo tên workspace
                    if not rel_path_guess and workspace_name in clean_path:
                        parts_link = clean_path.split(workspace_name + "/", 1)
                        if len(parts_link) > 1:
                            target_in_root = self.project_root / parts_link[1]
                            try:
                                rel_path_guess = os.path.relpath(
                                    target_in_root, filepath.parent
                                ).replace(os.sep, "/")
                            except ValueError:
                                pass

                    if rel_path_guess:
                        rel_path_guess = os.path.normpath(rel_path_guess).replace(os.sep, "/")
                        fixed_href = f"{rel_path_guess}#{anchor}" if anchor else rel_path_guess
                        if fix:
                            fixed_content = fixed_content.replace(f"]({href})", f"]({fixed_href})")
                            file_modified = True
                            issues["links"].append(
                                (
                                    line_num,
                                    href,
                                    f"[AUTO-FIXED] Non-portable absolute file link. Fixed to: '{fixed_href}'",
                                )
                            )
                        else:
                            issues["links"].append(
                                (
                                    line_num,
                                    href,
                                    f"Non-portable absolute file link. Must use repo-relative link: '{fixed_href}'",
                                )
                            )
                    else:
                        issues["links"].append(
                            (
                                line_num,
                                href,
                                f"Non-portable absolute file link cannot be resolved to workspace: '{clean_path}'",
                            )
                        )
                    continue

                else:
                    target_path = (filepath.parent / base_href).resolve()
                    if is_okf and bundle_root:
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
        env_vars = []
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

    def fix_relative_links(self, filepath: Path) -> tuple[bool, list[AuditIssue]]:
        """Auto-fix absolute or file:// links in a markdown file to repo-relative links."""
        issues_dict = self.validate_markdown_file(filepath, fix=True)
        res_issues: list[AuditIssue] = []
        str_path = str(
            filepath.relative_to(self.project_root)
            if filepath.is_relative_to(self.project_root)
            else filepath
        )
        for cat, items in issues_dict.items():
            for line, subj, msg in items:
                res_issues.append(
                    AuditIssue(
                        line_number=line,
                        subject=subj,
                        message=msg,
                        category=cat,
                        file_path=str_path,
                    )
                )
        file_modified = any("[AUTO-FIXED]" in issue.message for issue in res_issues)
        return file_modified, res_issues

    def audit(self, target: Path) -> list[AuditIssue]:
        """Audit a single markdown file and return standard AuditIssue list."""
        issues_dict = self.validate_markdown_file(target)
        res: list[AuditIssue] = []
        str_path = str(
            target.relative_to(self.project_root)
            if target.is_relative_to(self.project_root)
            else target
        )
        for cat, items in issues_dict.items():
            for line, subj, msg in items:
                res.append(
                    AuditIssue(
                        line_number=line,
                        subject=subj,
                        message=msg,
                        category=cat,
                        file_path=str_path,
                    )
                )
        return res

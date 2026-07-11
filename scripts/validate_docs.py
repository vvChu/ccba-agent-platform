#!/usr/bin/env python3
"""validate_docs.py - CLI tool for validating documentation accuracy.

Scans markdown documentation for potential hallucinations:
- Invented code symbols (functions, classes) not present in source code.
- Broken relative links.
- Documented environment variables missing from .env.example.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

# Import core utilities
from doc_core import (
    extract_code_references,
    extract_env_variables,
    extract_internal_links,
    load_env_example,
    parse_frontmatter,
    search_codebase_for_symbol,
)


def load_legal_registry(project_root: Path) -> dict:
    """Load the legal document registry from YAML.

    Args:
        project_root: Path to workspace root directory.

    Returns:
        Registry dict.
    """
    registry_path = project_root / ".md" / "data" / "legal_registry.yaml"
    if not registry_path.exists():
        return {}
    try:
        with open(registry_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def build_markdown_to_doc_map(registry: dict, project_root: Path) -> dict[Path, dict]:
    """Map resolved markdown file paths to their document definitions in the registry.

    Args:
        registry: The parsed legal registry dict.
        project_root: Path to workspace root directory.

    Returns:
        Dict mapping Path to document definition dict.
    """
    mapping = {}
    for _cat, docs in registry.items():
        if not isinstance(docs, list):
            continue
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            potential_paths = []

            # 1. Check markdown_path
            if "markdown_path" in doc:
                potential_paths.append(project_root / doc["markdown_path"])

            # 2. Check file_path
            if "file_path" in doc:
                fp = project_root / doc["file_path"]
                potential_paths.append(fp.with_suffix(".md"))
                potential_paths.append(fp.parent / "full_text.md")

            # 3. Fallback matching doc ID to slug
            doc_id = doc.get("id", "")
            if doc_id:
                slug = doc_id.lower().replace("-", "_")
                legal_docs_dir = project_root / ".md" / "legal_docs"
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


def scan_orphan_files(bundle_root: Path, project_root: Path) -> list[Path]:
    """Scan for markdown files under the bundle directory that are not referenced.

    Args:
        bundle_root: Absolute path to the bundle directory.
        project_root: Absolute path to workspace root.

    Returns:
        List of absolute paths to orphan markdown files.
    """
    EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", ".pytest_cache"}

    all_files = []
    for p in bundle_root.rglob("*.md"):
        if p.is_file():
            # Filter exclusions
            if any(ex in p.parts for ex in EXCLUDE_DIRS):
                continue
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

        links = extract_internal_links(content)
        for _line_num, _text, href in links:
            base_href = href.split("#")[0]
            if not base_href:
                continue

            if base_href.startswith("/"):
                # Absolute bundle path
                resolved = (bundle_root / base_href.lstrip("/")).resolve()
            else:
                # Relative path
                resolved = (filepath.parent / base_href).resolve()

            referenced.add(resolved)

        # Parse parent_document from frontmatter
        frontmatter, _ = parse_frontmatter(content)
        if frontmatter and isinstance(frontmatter, dict):
            parent_doc = frontmatter.get("parent_document")
            if parent_doc and isinstance(parent_doc, str):
                if parent_doc.startswith("/"):
                    parent_path = (bundle_root / parent_doc.lstrip("/")).resolve()
                else:
                    parent_path = (filepath.parent / parent_doc).resolve()

                # If parent exists in the bundle, this file is not an orphan
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


# Extraction and helper functions migrated to doc_core.py


def validate_markdown_file(
    filepath: Path,
    search_dirs: list[Path],
    env_example_vars: set[str],
    project_root: Path,
    fix: bool = False,
    registry_map: dict[Path, dict] = None,
) -> dict[str, list[tuple[int, str, str]]]:
    """Validate a single markdown file for inconsistencies and hallucinations.

    Args:
        filepath: Markdown file path.
        search_dirs: Code source directories.
        env_example_vars: Valid environment variables.
        project_root: Workspace root path.
        fix: Automatically fix absolute workspace file links.
        registry_map: Optional mapping from resolved Path to registry document.

    Returns:
        Dict of found issues categorized.
    """
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

    # Identify if file belongs to an OKF Bundle
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
        frontmatter, _ = parse_frontmatter(content)
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

    # Validate OKF Frontmatter
    if is_okf:
        if frontmatter is None:
            issues["okf_frontmatter"].append(
                (1, "frontmatter", "Missing YAML frontmatter for OKF Bundle file")
            )
        else:
            # Check type
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

            # Check resource
            if "resource" not in frontmatter:
                issues["okf_frontmatter"].append(
                    (1, "resource", "Missing required field: 'resource'")
                )

            # Check status or document_number
            if "status" not in frontmatter and "document_number" not in frontmatter:
                issues["okf_frontmatter"].append(
                    (
                        1,
                        "status/document_number",
                        "Missing required field: 'status' or 'document_number'",
                    )
                )

            # Check timestamp
            if "timestamp" not in frontmatter:
                issues["okf_frontmatter"].append(
                    (1, "timestamp", "Missing required field: 'timestamp'")
                )

    # 1. Validate Code References
    code_refs = extract_code_references(content)
    for line_num, ref in code_refs:
        if not search_codebase_for_symbol(ref, search_dirs):
            issues["code_refs"].append((line_num, ref, "Symbol is not defined in codebase"))

    # 2. Validate Relative Links / OKF Cross-Links / Validity Conflicts
    links = extract_internal_links(content)
    fixed_content = content
    file_modified = False
    lines = content.splitlines()

    for line_num, _text, href in links:
        base_href = href.split("#")[0]
        anchor = href.split("#", 1)[1] if "#" in href else ""

        target_path = None
        if base_href:
            if is_okf and href.startswith("/"):
                # Absolute bundle cross-link
                target_path = (bundle_root / base_href.lstrip("/")).resolve()
                if not target_path.exists():
                    issues["okf_links"].append(
                        (line_num, href, f"Resolved file does not exist: {target_path}")
                    )
            elif base_href.startswith("file:") or bool(re.match(r"^[a-zA-Z]:", base_href)):
                # Handle absolute links
                clean_path = base_href.replace("file:///", "").replace("file://", "")
                has_win_drive = bool(re.match(r"^[a-zA-Z]:", clean_path))

                if has_win_drive and sys.platform != "win32":
                    workspace_name = project_root.name
                    if workspace_name in clean_path:
                        parts = clean_path.split(workspace_name + "/", 1)
                        rel_path_guess = f"../../{parts[1]}" if len(parts) > 1 else "relative path"
                        if len(parts) > 1:
                            try:
                                depth_to_root = os.path.relpath(
                                    project_root, filepath.parent
                                ).replace(os.sep, "/")
                                rel_path_guess = f"{depth_to_root}/{parts[1]}"
                                rel_path_guess = os.path.normpath(rel_path_guess).replace(
                                    os.sep, "/"
                                )
                            except ValueError:
                                pass

                        if fix:
                            fixed_href = f"{rel_path_guess}#{anchor}" if anchor else rel_path_guess
                            fixed_content = fixed_content.replace(f"]({href})", f"]({fixed_href})")
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
                    is_internal = target_path.is_relative_to(project_root)
                except ValueError:
                    is_internal = False

                try:
                    is_sibling = target_path.is_relative_to(project_root.parent)
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
                                    f"{rel_to_workspace}#{anchor}" if anchor else rel_to_workspace
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
                            rel_to_parent = os.path.relpath(target_path, filepath.parent).replace(
                                os.sep, "/"
                            )
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
                # Normal relative path link
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
                    issues["links"].append((line_num, href, f"File does not exist: {base_href}"))
        else:
            # Self-link (anchor-only)
            target_path = filepath.resolve()

        # Validate Cross-Validity Conflicts
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

    # 3. Validate Environment Variables
    env_vars = extract_env_variables(content)
    for line_num, var in env_vars:
        if env_example_vars and var not in env_example_vars:
            issues["env_vars"].append((line_num, var, "Variable is missing in .env.example"))

    return issues


def get_modified_files(project_root: Path) -> set[Path]:
    """Get the set of files modified in the current branch or locally."""
    modified = set()
    try:
        # Check local changes (staged + unstaged + untracked)
        res = subprocess.run(
            ["git", "status", "--porcelain"], cwd=project_root, capture_output=True, text=True
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if len(line) > 3:
                    filepath = (project_root / line[3:].strip()).resolve()
                    modified.add(filepath)

        # Check commits in current branch relative to origin/main (CI PR check)
        res = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if line.strip():
                    filepath = (project_root / line.strip()).resolve()
                    modified.add(filepath)

        # Check commits in current branch relative to HEAD~1 as fallback
        res = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if line.strip():
                    filepath = (project_root / line.strip()).resolve()
                    modified.add(filepath)
    except Exception:
        pass
    return modified


def main():
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

    args = parser.parse_args()

    project_root = Path(args.root).resolve()
    docs_dir = Path(args.docs_dir)
    if not docs_dir.is_absolute():
        docs_dir = project_root / docs_dir

    src_paths = [Path(p.strip()) for p in args.src.split(",")]
    resolved_src_paths = []
    for p in src_paths:
        if not p.is_absolute():
            resolved_src_paths.append(project_root / p)
        else:
            resolved_src_paths.append(p)

    # Include project root as source path search fallback
    resolved_src_paths.append(project_root)

    if not docs_dir.exists():
        print(f"\x1b[31mError:\x1b[0m Docs directory '{docs_dir}' does not exist.")
        sys.exit(1)

    # Find all md files recursively, excluding node_modules, .venv, git, and external sub-repos
    EXCLUDE_DIRS = {
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
                    other_excludes = EXCLUDE_DIRS - {".md"}
                    if any(ex in p.parts for ex in other_excludes):
                        continue
                else:
                    if any(ex in p.parts for ex in EXCLUDE_DIRS):
                        continue
                # Exclude temporary worker/session folders in .agents (only keep skills/, workflows/ and top-level md files)
                if ".agents" in p.parts:
                    idx = p.parts.index(".agents")
                    if len(p.parts) > idx + 1:
                        subfolder = p.parts[idx + 1]
                        if subfolder not in {"skills", "workflows"}:
                            continue
                md_files.append(p)

    # Also check README.md, PLATFORM.md, CONTRIBUTING.md in root if they exist
    for root_file in ["README.md", "PLATFORM.md", "CONTRIBUTING.md", "SECURITY.md"]:
        root_path = project_root / root_file
        if root_path.exists() and root_path not in md_files:
            md_files.append(root_path)

    if not md_files:
        print("No markdown files found to validate.")
        sys.exit(0)

    # Load Env configurations
    env_vars = load_env_example(project_root)

    # Get modified files to distinguish hard blocks from soft warnings
    modified_files = get_modified_files(project_root)

    if args.changed:
        md_files = [f for f in md_files if f.resolve() in modified_files]

    # Load Legal Registry
    registry = load_legal_registry(project_root)
    registry_map = build_markdown_to_doc_map(registry, project_root)

    print(f"Scanned {len(md_files)} markdown file(s).")
    print(
        f"Searching code declarations in: {', '.join(str(p.relative_to(project_root)) for p in resolved_src_paths if p.exists())}"
    )
    print("-" * 60)

    total_issues = 0
    broken_links_count = 0
    hard_errors_count = 0
    bundle_roots = set()

    for filepath in md_files:
        relative_path = (
            filepath.relative_to(project_root)
            if filepath.is_relative_to(project_root)
            else filepath
        )
        issues = validate_markdown_file(
            filepath,
            resolved_src_paths,
            env_vars,
            project_root,
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

            # Print OKF Frontmatter Issues
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

            # Print Code Symbol Issues
            for line, symbol, err in issues["code_refs"]:
                print(f"  [L{line}] \x1b[33mCode Ref Warning:\x1b[0m `{symbol}` - {err}")
                total_issues += 1

            # Print OKF Link Issues
            for line, link, err in issues.get("okf_links", []):
                if is_hard_error:
                    print(f"  [L{line}] \x1b[31mOKF Link Error:\x1b[0m ({link}) - {err}")
                    total_issues += 1
                    hard_errors_count += 1
                else:
                    print(f"  [L{line}] \x1b[33mOKF Link Warning:\x1b[0m ({link}) - {err}")
                    total_issues += 1

            # Print Link Issues
            for line, link, err in sorted(issues["links"]):
                if "[AUTO-FIXED]" in err:
                    print(f"  [L{line}] \x1b[32mLink Fixed:\x1b[0m ({link}) - {err}")
                elif "[WARNING]" in err:
                    print(f"  [L{line}] \x1b[33mLink Warning:\x1b[0m ({link}) - {err}")
                    total_issues += 1
                else:
                    if is_hard_error:
                        print(f"  [L{line}] \x1b[31mBroken Link Error:\x1b[0m ({link}) - {err}")
                        total_issues += 1
                        broken_links_count += 1
                    else:
                        print(
                            f"  [L{line}] \x1b[33mLink Warning (Old File):\x1b[0m ({link}) - [SOFT-WARN] {err}"
                        )
                        total_issues += 1

            # Print OKF Conflict Issues
            for line, link, err in issues.get("okf_conflicts", []):
                if is_hard_error:
                    print(f"  [L{line}] \x1b[31mOKF Conflict Error:\x1b[0m ({link}) - {err}")
                    total_issues += 1
                    hard_errors_count += 1
                else:
                    print(f"  [L{line}] \x1b[33mOKF Conflict Warning:\x1b[0m ({link}) - {err}")
                    total_issues += 1

            # Print Env Issues
            for line, var, err in issues["env_vars"]:
                print(f"  [L{line}] \x1b[33mEnv Var Warning:\x1b[0m `{var}` - {err}")
                total_issues += 1

    # Scan for Orphan Files
    orphan_issues_count = 0
    for root in sorted(bundle_roots):
        orphans = scan_orphan_files(root, project_root)
        if orphans:
            print(f"\n\x1b[4mBundle: {root.relative_to(project_root)}\x1b[0m")
            for o in sorted(orphans):
                rel_o = o.relative_to(project_root)
                # Check if this bundle has any modified files
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

    print("-" * 60)
    if total_issues > 0:
        print(f"Completed with {total_issues} issue(s) detected.")
        if broken_links_count > 0 or hard_errors_count > 0 or orphan_issues_count > 0:
            print(
                "\x1b[31m[ERROR] Detected hard errors/broken links. Blocking commit/build.\x1b[0m"
            )
            sys.exit(1)  # Hard Block
        else:
            print(
                "\x1b[33m[WARN] Warnings/Old file broken links detected. Committing/building is allowed.\x1b[0m"
            )
            sys.exit(0)  # Soft Warn
    else:
        print("\x1b[32mDocumentation validation completed successfully! No issues detected.\x1b[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()

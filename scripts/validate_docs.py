#!/usr/bin/env python3
"""validate_docs.py - CLI tool for validating documentation accuracy.

Scans markdown documentation for potential hallucinations:
- Invented code symbols (functions, classes) not present in source code.
- Broken relative links.
- Documented environment variables missing from .env.example.
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

# Regex Patterns
CODE_REF_RE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]*(?:\(\))?)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
ENV_VAR_RE = re.compile(r"`([A-Z][A-Z0-9_]{2,})`|\$([A-Z][A-Z0-9_]{2,})")

# System/Common keywords to ignore (not actual project code references)
IGNORE_CODE_REFS: Set[str] = {
    "true", "false", "null", "undefined", "string", "number", "boolean",
    "object", "array", "function", "async", "await", "const", "let", "var",
    "if", "else", "for", "while", "return", "import", "export", "default",
    "npm", "npx", "node", "yarn", "pnpm", "git", "bash", "sh", "zsh",
    "get", "post", "put", "delete", "patch", "head", "options",
    "json", "xml", "html", "css", "sql", "api", "url", "uri", "http", "https",
    "ok", "error", "warning", "info", "debug", "trace",
    "readme", "license", "changelog", "todo", "fixme", "note", "hack",
    "dev", "prod", "test", "staging", "production", "development",
    "src", "lib", "dist", "build", "docs", "tests", "config",
    "index", "main", "app", "server", "client", "utils", "helpers"
}

IGNORE_ENV_PREFIXES: List[str] = ["NODE_", "PATH", "HOME", "USER", "SHELL", "TERM", "PWD", "CI"]
IGNORE_ENV_VARS: Set[str] = {"ARGUMENTS"}


def extract_code_references(content: str) -> List[Tuple[int, str]]:
    """Scan file lines for code references like `my_func()` or `MyClass`.

    Args:
        content: File contents.

    Returns:
        List of tuples containing (line_number, reference_string).
    """
    references = []
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        # Skip markdown code blocks
        if line.strip().startswith("```"):
            continue
        
        matches = CODE_REF_RE.findall(line)
        for ref in matches:
            clean_ref = ref.replace("()", "")
            if clean_ref.lower() in IGNORE_CODE_REFS:
                continue
            
            # Match only function calls (ends with ()) or PascalCase classes
            if ref.endswith("()") or (clean_ref and clean_ref[0].isupper() and any(c.islower() for c in clean_ref)):
                references.append((idx + 1, ref))
                
    return references


def extract_internal_links(content: str) -> List[Tuple[int, str, str]]:
    """Scan file lines for relative internal links.

    Args:
        content: File contents.

    Returns:
        List of tuples containing (line_number, link_text, href_url).
    """
    links = []
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        matches = LINK_RE.findall(line)
        for text, href in matches:
            # Skip web URLs, anchors, mailto links
            if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
                continue
            links.append((idx + 1, text, href))
    return links


def extract_env_variables(content: str) -> List[Tuple[int, str]]:
    """Scan file lines for environment variables (capitalized with underscores).

    Args:
        content: File contents.

    Returns:
        List of tuples containing (line_number, variable_name).
    """
    env_vars = []
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        # Skip markdown code blocks
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


def search_codebase_for_symbol(symbol: str, search_dirs: List[Path]) -> bool:
    """Check if the given class or function symbol is declared in source dirs.

    Args:
        symbol: The symbol to find (e.g. "my_func" or "MyClass").
        search_dirs: Directories containing source code.

    Returns:
        True if symbol declaration is found.
    """
    clean_sym = symbol.replace("()", "")
    
    # Declarations patterns (Python, JavaScript, Go, etc.)
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
        # Scan source files
        for ext in ["*.py", "*.js", "*.cjs", "*.ts", "*.go", "*.sh"]:
            for filepath in sdir.rglob(ext):
                # Ignore test folders or build target folders
                if any(p in filepath.parts for p in ["tests", "venv", ".venv", "node_modules", "dist", "build"]):
                    continue
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()
                        if any(pat.search(file_content) for pat in patterns):
                            return True
                except Exception:
                    continue
    return False


def load_env_example(project_root: Path) -> Set[str]:
    """Parse .env.example file to extract declared env variable names.

    Args:
        project_root: Path to workspace root directory.

    Returns:
        Set of defined env variable keys.
    """
    env_path = project_root / ".env.example"
    if not env_path.exists():
        return set()
        
    env_vars = set()
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip comments or empty lines
                if not line or line.startswith("#"):
                    continue
                match = re.match(r"^([A-Z0-9_]+)=", line)
                if match:
                    env_vars.add(match.group(1))
    except Exception:
        pass
    return env_vars


def validate_markdown_file(
    filepath: Path,
    search_dirs: List[Path],
    env_example_vars: Set[str]
) -> Dict[str, List[Tuple[int, str, str]]]:
    """Validate a single markdown file for inconsistencies and hallucinations.

    Args:
        filepath: Markdown file path.
        search_dirs: Code source directories.
        env_example_vars: Valid environment variables.

    Returns:
        Dict of found issues categorized.
    """
    issues = {
        "code_refs": [],
        "links": [],
        "env_vars": []
    }
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        issues["links"].append((0, "Error reading file", str(e)))
        return issues

    # 1. Validate Code References
    code_refs = extract_code_references(content)
    for line_num, ref in code_refs:
        if not search_codebase_for_symbol(ref, search_dirs):
            issues["code_refs"].append((line_num, ref, "Symbol is not defined in codebase"))

    # 2. Validate Relative Links
    links = extract_internal_links(content)
    for line_num, text, href in links:
        # Strip anchor if present (e.g. "./doc.md#section" -> "./doc.md")
        base_href = href.split("#")[0]
        if not base_href:
            continue
            
        target_path = (filepath.parent / base_href).resolve()
        if not target_path.exists():
            issues["links"].append((line_num, href, f"File does not exist: {base_href}"))

    # 3. Validate Environment Variables
    env_vars = extract_env_variables(content)
    for line_num, var in env_vars:
        if env_example_vars and var not in env_example_vars:
            issues["env_vars"].append((line_num, var, "Variable is missing in .env.example"))
            
    return issues


def main():
    parser = argparse.ArgumentParser(description="Validate documentation accuracy.")
    parser.add_argument("docs_dir", nargs="?", default="docs", help="Directory containing markdown files (default: docs)")
    parser.add_argument("--src", default="scripts,packages", help="Comma-separated directories to search for code definitions")
    parser.add_argument("--root", default=".", help="Project workspace root directory")
    
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
    EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", "claudekit-engineer", "claudekit-marketing", ".pytest_cache", "extracted_docs"}
    md_files = []
    
    if docs_dir.is_file():
        if docs_dir.suffix == ".md":
            md_files.append(docs_dir)
    else:
        for p in docs_dir.rglob("*.md"):
            if any(ex in p.parts for ex in EXCLUDE_DIRS):
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
    
    print(f"Scanned {len(md_files)} markdown file(s).")
    print(f"Searching code declarations in: {', '.join(str(p.relative_to(project_root)) for p in resolved_src_paths if p.exists())}")
    print("-" * 60)
    
    total_issues = 0
    broken_links_count = 0
    
    for filepath in md_files:
        relative_path = filepath.relative_to(project_root) if filepath.is_relative_to(project_root) else filepath
        issues = validate_markdown_file(filepath, resolved_src_paths, env_vars)
        
        file_has_issues = any(issues.values())
        if file_has_issues:
            print(f"\n\x1b[4mFile: {relative_path}\x1b[0m")
            
            # Print Code Symbol Issues
            for line, symbol, err in issues["code_refs"]:
                print(f"  [L{line}] \x1b[33mCode Ref Warning:\x1b[0m `{symbol}` - {err}")
                total_issues += 1
                
            # Print Link Issues
            for line, link, err in issues["links"]:
                print(f"  [L{line}] \x1b[31mBroken Link Error:\x1b[0m ({link}) - {err}")
                total_issues += 1
                broken_links_count += 1
                
            # Print Env Issues
            for line, var, err in issues["env_vars"]:
                print(f"  [L{line}] \x1b[33mEnv Var Warning:\x1b[0m `{var}` - {err}")
                total_issues += 1
                
    print("-" * 60)
    if total_issues > 0:
        print(f"Completed with {total_issues} issue(s) detected.")
        if broken_links_count > 0:
            print(f"\x1b[31m[ERROR] Detected {broken_links_count} broken relative link(s). Blocking commit/build.\x1b[0m")
            sys.exit(1)  # Hard Block
        else:
            print("\x1b[33m[WARN] Warnings detected (Code Refs / Env Vars). Committing/building is allowed.\x1b[0m")
            sys.exit(0)  # Soft Warn
    else:
        print("\x1b[32mDocumentation validation completed successfully! No issues detected.\x1b[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()

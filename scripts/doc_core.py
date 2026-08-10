"""doc_core.py - Core utilities for parsing and validating CCBA Agent documentation.

Provides reusable helpers for frontmatter parsing, link extraction, code symbol detection,
and environment variables lookup.
"""

import re
from pathlib import Path
from typing import Any

import yaml

# Regex Patterns
FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
CODE_REF_RE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]*(?:\(\))?)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
ENV_VAR_RE = re.compile(r"`([A-Z][A-Z0-9_]{2,})`|\$([A-Z][A-Z0-9_]{2,})")

# System/Common keywords to ignore (not actual project code references)
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


def parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str]:
    """Parse YAML frontmatter if present at the start of the content.

    Args:
        content: The text content of the markdown file.

    Returns:
        A tuple of (parsed_frontmatter_dict or None, remaining_content).
    """
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


def extract_code_references(content: str) -> list[tuple[int, str]]:
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
            if ref.endswith("()") or (
                clean_ref and clean_ref[0].isupper() and any(c.islower() for c in clean_ref)
            ):
                references.append((idx + 1, ref))

    return references


def extract_internal_links(content: str) -> list[tuple[int, str, str]]:
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


def extract_env_variables(content: str) -> list[tuple[int, str]]:
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


_CODEBASE_FILE_CACHE: dict[Path, list[tuple[Path, str]]] = {}


def search_codebase_for_symbol(symbol: str, search_dirs: list[Path]) -> bool:
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
        if sdir not in _CODEBASE_FILE_CACHE:
            files = []
            for ext in ["*.py", "*.js", "*.cjs", "*.ts", "*.go", "*.sh"]:
                for filepath in sdir.rglob(ext):
                    if any(
                        p in filepath.parts
                        for p in ["tests", "venv", ".venv", "node_modules", "dist", "build", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".agents", "scratch", "input_documents", "CDE", ".md", "assets"]
                    ):
                        continue
                    try:
                        with open(filepath, encoding="utf-8", errors="ignore") as f:
                            files.append((filepath, f.read()))
                    except Exception:
                        continue
            _CODEBASE_FILE_CACHE[sdir] = files

        for filepath, file_content in _CODEBASE_FILE_CACHE[sdir]:
            if any(pat.search(file_content) for pat in patterns):
                return True
    return False


def load_env_example(project_root: Path) -> set[str]:
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
        with open(env_path, encoding="utf-8") as f:
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

"""ccba_harness.blast_radius - Cross-Boundary Blast Radius Analyzer (ADR-0009).

Scans codebase AST and config files to identify modules, services, and test suites
impacted by modifications in shared packages, skills, or platform seams.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RiskLevel = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"]

CORE_PIPELINE_KEYWORDS = (
    "retrieval",
    "ingestion",
    "api",
    "scoring",
    "evals",
    "parser",
)

OPERATIONAL_KEYWORDS = (
    "chatops",
    "watchdog",
    "mcp_server",
    "telemetry",
    "forensics",
    "daemon",
)


class BlastRadiusReport(BaseModel):
    """Structured report detailing blast radius across affected files."""

    model_config = ConfigDict(extra="forbid")

    targets: list[str]
    risk_level: RiskLevel
    affected_file_count: int
    affected_files: list[str]
    recommended_tests: list[str]
    details: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


def _match_import_node(node: ast.AST, targets: set[str]) -> list[dict[str, Any]]:
    """Extracts reference hits from Import and ImportFrom AST nodes."""
    hits: list[dict[str, Any]] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            for target in targets:
                if target in alias.name:
                    hits.append(
                        {
                            "line": node.lineno,
                            "target": target,
                            "type": "import",
                            "name": alias.name,
                        }
                    )
    elif isinstance(node, ast.ImportFrom):
        mod = node.module or ""
        for target in targets:
            if target in mod:
                hits.append(
                    {"line": node.lineno, "target": target, "type": "import_from", "module": mod}
                )
        for alias in node.names:
            for target in targets:
                if target == alias.name:
                    hits.append(
                        {
                            "line": node.lineno,
                            "target": target,
                            "type": "import_name",
                            "name": alias.name,
                        }
                    )
    return hits


def _match_value_node(node: ast.AST, targets: set[str]) -> list[dict[str, Any]]:
    """Extracts reference hits from Name and Constant AST nodes."""
    hits: list[dict[str, Any]] = []
    if isinstance(node, ast.Name) and node.id in targets:
        hits.append({"line": node.lineno, "target": node.id, "type": "name_ref"})
    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
        for target in targets:
            if target in node.value and len(target) > 3:
                hits.append({"line": node.lineno, "target": target, "type": "string_literal"})
    return hits


def extract_ast_references(file_path: Path, targets: set[str]) -> list[dict[str, Any]]:
    """Extracts line numbers and matching symbols from a python file using AST.

    Args:
        file_path: Python file to parse.
        targets: Target symbol or package names to search for.

    Returns:
        List of matching hit dictionaries.
    """
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except Exception:
        return []

    hits: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        hits.extend(_match_import_node(node, targets))
        hits.extend(_match_value_node(node, targets))
    return hits


def calculate_risk(affected_files: list[str]) -> RiskLevel:
    """Calculates cumulative risk level based on affected service domains.

    Args:
        affected_files: List of file paths impacted by targets.

    Returns:
        Categorical RiskLevel value.
    """
    if not affected_files:
        return "NONE"

    has_core = any(any(kw in f.lower() for kw in CORE_PIPELINE_KEYWORDS) for f in affected_files)
    if has_core:
        return "CRITICAL"

    has_ops = any(any(kw in f.lower() for kw in OPERATIONAL_KEYWORDS) for f in affected_files)
    if has_ops:
        return "HIGH"

    if len(affected_files) >= 5:
        return "MEDIUM"

    return "LOW"


def recommend_tests(affected_files: list[str], root_dir: Path) -> list[str]:
    """Recommends specific pytest targets based on impacted files.

    Args:
        affected_files: Relative paths of impacted files.
        root_dir: Workspace root directory.

    Returns:
        Sorted list of recommended test paths.
    """
    tests: set[str] = set()
    for rel_path in affected_files:
        stem = Path(rel_path).stem
        # Look for direct unit test matching test_<stem>.py
        direct_test = root_dir / "tests" / f"test_{stem}.py"
        if direct_test.exists():
            tests.add(str(direct_test.relative_to(root_dir)))

        pkg_test = root_dir / "packages" / "ccba-harness" / "tests" / f"test_{stem}.py"
        if pkg_test.exists():
            tests.add(str(pkg_test.relative_to(root_dir)))

    if not tests:
        # Fallback to general test suites if present
        for candidate in ("tests", "packages/ccba-harness/tests"):
            if (root_dir / candidate).exists():
                tests.add(candidate)
                break

    return sorted(tests)


def scan_workspace_for_targets(
    targets: set[str], root_dir: Path
) -> dict[str, list[dict[str, Any]]]:
    """Scans all python and config files in workspace for target symbol references.

    Args:
        targets: Target symbols/module names.
        root_dir: Root path to begin filesystem walk.

    Returns:
        Dictionary mapping relative file paths to lists of hit dictionaries.
    """
    results: dict[str, list[dict[str, Any]]] = {}
    scan_extensions = {".py", ".sh", ".yaml", ".yml"}

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = sorted(
            [
                d
                for d in dirs
                if d not in {".git", ".venv", "venv", "__pycache__", "node_modules", "exports"}
            ]
        )
        for file_name in sorted(files):
            file_path = Path(root) / file_name
            if file_path.suffix not in scan_extensions:
                continue

            rel_path = str(file_path.relative_to(root_dir))
            if file_path.suffix == ".py":
                hits = extract_ast_references(file_path, targets)
            else:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    hits = [
                        {"line": idx + 1, "target": t, "type": "text_match"}
                        for idx, line in enumerate(content.splitlines())
                        for t in targets
                        if t in line
                    ]
                except Exception:
                    hits = []

            if hits:
                results[rel_path] = hits
    return results


def analyze_blast_radius(targets: set[str], root_dir: Path) -> BlastRadiusReport:
    """Performs end-to-end blast radius analysis over the given root directory.

    Args:
        targets: Set of module, symbol, or skill names changed.
        root_dir: Workspace or spoke directory to analyze.

    Returns:
        BlastRadiusReport instance.
    """
    scan_results = scan_workspace_for_targets(targets, root_dir)
    affected_files = sorted(scan_results.keys())
    risk = calculate_risk(affected_files)
    recommended = recommend_tests(affected_files, root_dir)

    return BlastRadiusReport(
        targets=sorted(targets),
        risk_level=risk,
        affected_file_count=len(affected_files),
        affected_files=affected_files,
        recommended_tests=recommended,
        details=scan_results,
    )

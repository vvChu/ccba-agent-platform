#!/usr/bin/env python3
"""check_hardcoded_parameters.py - AST Hardcoded Parameter & KISS Linter.

Inspects Python source code for anti-pattern hardcoded parameters:
1. Raw LLM model names ('gemini-*', 'gpt-*', 'claude-*', 'llama-*', etc.)
   - Must use `ccba_ai.routing.ModelArchetype` or `choose_model()`.
   - Exemption: `# ccba:allow-raw-model`.
2. Hardcoded network IP addresses (e.g., '100.83.192.30')
   - Must read from environment variables (e.g., `AI_GATEWAY_URL`).
   - Exemption: `# ccba:allow-raw-ip`.
3. Hardcoded machine drive paths ('C:\\...', 'D:\\...')
   - Must use platform-agnostic relative paths or environment variables.
   - Exemption: `# ccba:allow-machine-path`.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

# Regex patterns for hardcoded parameter detection
MODEL_PATTERN = re.compile(
    r"^(?:gemini[-/]|gpt[-/]|claude[-/]|llama[-/]|mistral[-/]|qwen[-/]|deepseek[-/]|text-embedding[-/])[a-zA-Z0-9_\-\.]+$",
    re.IGNORECASE,
)
IP_PATTERN = re.compile(r"\b(?!(?:127\.0\.0\.1|0\.0\.0\.0)\b)(?:[1-9]\d{0,2}\.){3}[1-9]\d{0,2}\b")
WIN_PATH_PATTERN = re.compile(r"^[a-zA-Z]:[\\/][a-zA-Z0-9_\-\.\\/]+")

# Files explicitly exempt from model name inspection (SSOT providers and mock infrastructure)
EXEMPT_FILES = {
    "routing.py",
    "fallback.py",
    "mock_provider.py",
    "copilot_provider.py",
}


@dataclass
class ParameterViolation:
    """Represents a hardcoded parameter violation."""

    file_path: Path
    line_number: int
    rule_name: str
    message: str


def is_whitelisted_file(path: Path) -> bool:
    """Check if file is exempt from parameter inspection.

    Args:
        path: Path to the target file.

    Returns:
        True if the file should be skipped, False otherwise.
    """
    path_str = str(path).replace("\\", "/")

    # Exclude tests, fixtures, and scenario verifications
    if "/tests/" in path_str or path.name.startswith("test_") or path.name.startswith("verify_"):
        return True

    # Exclude virtualenvs, build dirs, internal docs, and archives
    if any(
        p in path_str for p in ["/.venv/", "/build/", "/dist/", "/.git/", "/.md/", "/archive/"]
    ) or path_str.startswith(".md/"):
        return True

    # Exclude SSOT routing definitions and CLI secret credential locators
    if path.name in EXEMPT_FILES and "ccba_ai" in path_str:
        return True
    if "ccba_maskara" in path_str and "_locator.py" in path_str:
        return True

    return False


class HardcodedParameterASTVisitor(ast.NodeVisitor):
    """AST Visitor that detects raw model names, IPs, and machine paths."""

    def __init__(
        self,
        current_file: Path,
        raw_lines: list[str] | None = None,
    ) -> None:
        self.current_file = current_file
        self.raw_lines = raw_lines or []
        self.violations: list[ParameterViolation] = []

    def _has_exemption(self, line_number: int, end_line_number: int | None, tag: str) -> bool:
        """Check if any line in span contains the exemption tag."""
        if not self.raw_lines:
            return False
        end_line = end_line_number if end_line_number is not None else line_number
        start_idx = max(0, line_number - 1)
        end_idx = min(len(self.raw_lines), end_line)
        for idx in range(start_idx, end_idx):
            line = self.raw_lines[idx]
            if tag in line or "noqa" in line:
                return True
        return False

    def visit_Constant(self, node: ast.Constant) -> None:
        """Inspect string constants for hardcoded values."""
        if isinstance(node.value, str):
            val = node.value.strip()
            end_lineno = getattr(node, "end_lineno", node.lineno)

            # Check 1: Raw LLM Model Strings
            if MODEL_PATTERN.match(val):
                if not self._has_exemption(node.lineno, end_lineno, "ccba:allow-raw-model"):
                    self.violations.append(
                        ParameterViolation(
                            file_path=self.current_file,
                            line_number=node.lineno,
                            rule_name="RawModelStringViolation",
                            message=(
                                f"Raw model string '{val}' hardcoded. Platform-Aware KISS requires "
                                "using 'ccba_ai.routing.ModelArchetype' or 'choose_model()'."
                            ),
                        )
                    )

            # Check 2: Hardcoded Network IPs
            elif IP_PATTERN.search(val):
                if not self._has_exemption(node.lineno, end_lineno, "ccba:allow-raw-ip"):
                    ip_match = IP_PATTERN.search(val)
                    matched_ip = ip_match.group(0) if ip_match else val
                    self.violations.append(
                        ParameterViolation(
                            file_path=self.current_file,
                            line_number=node.lineno,
                            rule_name="HardcodedNetworkIPViolation",
                            message=(
                                f"Hardcoded network IP '{matched_ip}' detected. Must read endpoint from "
                                "environment variables (e.g. AI_GATEWAY_URL)."
                            ),
                        )
                    )

            # Check 3: Hardcoded Windows Machine Drive Paths
            elif WIN_PATH_PATTERN.match(val):
                if not self._has_exemption(node.lineno, end_lineno, "ccba:allow-machine-path"):
                    self.violations.append(
                        ParameterViolation(
                            file_path=self.current_file,
                            line_number=node.lineno,
                            rule_name="HardcodedMachinePathViolation",
                            message=(
                                f"Hardcoded Windows machine path '{val}' detected. Must use dynamic path "
                                "resolution or annotate with '# ccba:allow-machine-path'."
                            ),
                        )
                    )

        self.generic_visit(node)


def check_file_content(file_path: Path, content: str) -> list[ParameterViolation]:
    """Parse and check file content for parameter violations.

    Args:
        file_path: Target path for reporting.
        content: Python source code as string.

    Returns:
        List of detected ParameterViolations.
    """
    if is_whitelisted_file(file_path):
        return []

    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        return []

    lines = content.splitlines()
    visitor = HardcodedParameterASTVisitor(file_path, raw_lines=lines)
    visitor.visit(tree)
    return visitor.violations


def check_file(file_path: Path) -> list[ParameterViolation]:
    """Read and inspect a single Python file."""
    if is_whitelisted_file(file_path):
        return []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as err:
        return [
            ParameterViolation(
                file_path=file_path,
                line_number=1,
                rule_name="FileReadError",
                message=f"Failed to read file: {err}",
            )
        ]
    return check_file_content(file_path, content)


def scan_directory(root_dir: Path) -> list[ParameterViolation]:
    """Recursively scan directory for Python parameter violations."""
    all_violations: list[ParameterViolation] = []
    for path in sorted(root_dir.rglob("*.py")):
        if not is_whitelisted_file(path):
            all_violations.extend(check_file(path))
    return all_violations


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for AST hardcoded parameter linter."""
    parser = argparse.ArgumentParser(
        description="AST Linter for Hardcoded Parameters & Dynamic Scalability."
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Check a single Python file.",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("."),
        help="Root directory to scan (default: repo root).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=True,
        help="Exit with non-zero code if any violations are found.",
    )

    args = parser.parse_args(argv)

    if args.file:
        violations = check_file(args.file)
    else:
        violations = scan_directory(args.dir)

    if not violations:
        print("✅ [check_hardcoded_parameters] 0 violations found. All parameters compliant.")
        return 0

    print(f"❌ [check_hardcoded_parameters] Found {len(violations)} violation(s):")
    for v in violations:
        rel_path = v.file_path.as_posix()
        print(f"  {rel_path}:{v.line_number} [{v.rule_name}]: {v.message}")

    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())

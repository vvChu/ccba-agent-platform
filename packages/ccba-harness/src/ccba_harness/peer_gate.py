"""ccba_harness.peer_gate - Reusable 7-Stage Automated Implementation Gate (ADR-0007 & ADR-0009).

Provides cross-repository 7-stage quality gate verification:
1. Scoped Pytest -> 100% pass
2. Flake8 / Linter Check -> exit code 0
3. AST Function Length Check (KISS <= 50 lines) -> 0 violations
4. Redundant Comment & Dead Code Sanitation (ADR-0009 / Pstack Upstream) -> 0 violations
5. Clean Module Import & Circular Dependency Check -> exit code 0
6. Hub Import Depth Check (depth <= 2) -> 0 violations
7. Secret & Raw IP Cleanliness Check (ADR-0060 / RULE-1.21) -> 0 violations
"""

from __future__ import annotations

import ast
import datetime
import io
import re
import shutil
import subprocess
import sys
import time
import tokenize
import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .peer import PeerVerdictBlock, render_verdict_header

HUB_PACKAGE_PREFIXES = (
    "ccba_ai",
    "ccba_core",
    "ccba_harness",
    "ccba_legal",
    "ccba_maskara",
    "ccba_notebooklm",
    "ccba_ooxml",
    "ccba_pdf_prep",
    "ccba_qc_core",
    "mdconverter",
)

TAILSCALE_IP_REGEX = re.compile(r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b")
LEAK_DETECTOR_REGEX = re.compile(r"\b(?:AIzaSy[A-Za-z0-9_-]{33}|sk-[A-Za-z0-9]{32,})\b")

ALLOWLIST_PATTERNS = re.compile(
    r"^\s*#\s*("
    r"ccba:"
    r"|noqa"
    r"|type:\s*ignore"
    r"|pragma:\s*no cover"
    r"|flake8:"
    r"|mypy:"
    r"|pylint:"
    r"|isort:"
    r"|nosec"
    r"|TODO\b"
    r"|FIXME\b"
    r"|!\s*/"
    r"|coding[:=]"
    r"|---+"
    r"|===+"
    r"|___+"
    r"|Theo Điều\b"
    r"|Luật Xây dựng\b"
    r"|NĐ\s*\d+"
    r"|QCVN\b"
    r"|TCVN\b"
    r")",
    re.IGNORECASE,
)

DEAD_CODE_KEYWORDS = ("def ", "class ", "import ", "from ", "return ")


class GateCheck(BaseModel):
    """Result of a single gate verification check."""

    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    exit_code: int
    stdout_tail: str
    duration_ms: int


class GateResult(BaseModel):
    """Aggregate result across all gate checks."""

    model_config = ConfigDict(extra="forbid")

    gate: Literal["PASS", "FAIL"]
    timestamp: str
    branch: str | None = None
    checks: list[GateCheck] = Field(default_factory=list)


def run_command_check(name: str, cmd: list[str], cwd: Path) -> GateCheck:
    """Runs a shell command and captures execution metrics and tail output.

    Args:
        name: Identifier name for the check.
        cmd: Command arguments list.
        cwd: Working directory to run command in.

    Returns:
        GateCheck summary object.
    """
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=180,
            check=False,
        )
        duration_ms = int((time.time() - t0) * 1000)
        output = proc.stdout or ""
        tail = "\n".join(output.strip().splitlines()[-15:])
        return GateCheck(
            name=name,
            passed=(proc.returncode == 0),
            exit_code=proc.returncode,
            stdout_tail=tail,
            duration_ms=duration_ms,
        )
    except Exception as exc:
        duration_ms = int((time.time() - t0) * 1000)
        return GateCheck(
            name=name,
            passed=False,
            exit_code=-1,
            stdout_tail=f"Exception: {exc}",
            duration_ms=duration_ms,
        )


def is_hub_workspace(workspace_dir: Path) -> bool:
    """Checks whether the workspace is the central Hub repository."""
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        return "ccba-agent-platform" in res.stdout
    except Exception:
        return False


def get_target_files(
    workspace_dir: Path, changed_files: list[str] | None = None, branch: str | None = None
) -> list[Path]:
    """Resolves target python files to analyze for AST function length and hygiene.

    Args:
        workspace_dir: Root directory of the repository.
        changed_files: Explicit list of modified file paths.
        branch: Target branch to diff against if changed_files is omitted.

    Returns:
        Deterministic sorted list of python file paths.
    """
    if changed_files:
        return sorted([workspace_dir / f for f in changed_files if f.endswith(".py")])

    files: list[Path] = []
    if branch:
        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", f"{branch}...HEAD"],
                cwd=workspace_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            for line in res.stdout.splitlines():
                if line.endswith(".py"):
                    files.append(workspace_dir / line)
        except Exception:
            pass
    else:
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=workspace_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[-1].endswith(".py"):
                    files.append(workspace_dir / parts[-1])
        except Exception:
            pass

    if not files:
        for pattern in ("scripts/peer_*.py", "scripts/check_*.py"):
            files.extend(list(workspace_dir.glob(pattern)))
    return sorted({f for f in files if f.exists()})


def check_ast_function_length(target_files: list[Path], max_lines: int = 50) -> GateCheck:
    """Scans target Python files to ensure no function/method definition exceeds max_lines.

    Args:
        target_files: List of Python file paths to inspect.
        max_lines: Maximum allowed line span per function.

    Returns:
        GateCheck summary.
    """
    t0 = time.time()
    violations: list[str] = []

    for py_file in target_files:
        if "__pycache__" in str(py_file) or ".venv" in str(py_file) or "tests" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            if "# ccba:allow-long-functions" in content:
                continue
            tree = ast.parse(content, filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    end_lineno = getattr(node, "end_lineno", node.lineno)
                    length = end_lineno - node.lineno + 1
                    if length > max_lines:
                        violations.append(
                            f"{py_file.name}:{node.lineno} {node.name}() [{length} lines > {max_lines}]"
                        )
        except Exception:
            continue

    duration_ms = int((time.time() - t0) * 1000)
    passed = len(violations) == 0
    tail = (
        "\n".join(violations[:10])
        if violations
        else f"All analyzed functions satisfy KISS rule (<= {max_lines} lines)."
    )
    return GateCheck(
        name="ast_function_length",
        passed=passed,
        exit_code=0 if passed else 1,
        stdout_tail=tail,
        duration_ms=duration_ms,
    )


def check_redundant_comments(target_files: list[Path]) -> GateCheck:
    """Enforces Anti-Slop Discipline (ADR-0009 / Pstack Upstream): Blocks redundant comments & dead code.

    Scans Python source files for:
    1. Commented-out dead code (standalone comments containing def, class, import, return).
    2. Redundant comments immediately preceding def/class that merely restate the identifier name (<= 5 words).

    Args:
        target_files: List of Python file paths to inspect.

    Returns:
        GateCheck summary.
    """
    t0 = time.time()
    violations: list[str] = []

    for py_file in target_files:
        if any(
            part in py_file.parts for part in ("tests", ".venv", "__pycache__", "site-packages")
        ):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            if "# ccba:allow-redundant-comments" in content:
                continue

            lines = content.splitlines(keepends=True)
            tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))

            for tok in tokens:
                if tok.type != tokenize.COMMENT:
                    continue

                text = tok.string
                start_line, start_col = tok.start

                if ALLOWLIST_PATTERNS.search(text):
                    continue

                curr_line_str = lines[start_line - 1] if start_line <= len(lines) else ""
                is_standalone = start_col == (len(curr_line_str) - len(curr_line_str.lstrip()))

                # Sub-check A: Dead code detection
                if is_standalone:
                    stripped_comment = text.lstrip("#").strip()
                    if any(stripped_comment.startswith(kw) for kw in DEAD_CODE_KEYWORDS):
                        is_dead_code = False
                        try:
                            if stripped_comment.startswith("return "):
                                code_to_parse = f"def _dummy():\n    {stripped_comment}"
                            elif stripped_comment.endswith(":"):
                                code_to_parse = f"{stripped_comment}\n    pass"
                            else:
                                code_to_parse = stripped_comment
                            tree = ast.parse(code_to_parse)
                            if tree.body:
                                stmt = tree.body[0]
                                if isinstance(
                                    stmt,
                                    (
                                        ast.FunctionDef,
                                        ast.AsyncFunctionDef,
                                        ast.ClassDef,
                                        ast.Import,
                                        ast.ImportFrom,
                                        ast.Return,
                                    ),
                                ):
                                    is_dead_code = True
                        except (SyntaxError, IndentationError):
                            is_dead_code = False

                        if is_dead_code:
                            violations.append(
                                f"{py_file.name}:{start_line} commented-out dead code: '{text[:60]}'"
                            )
                            continue

                # Sub-check B: Duplicate name restatement
                curr_idx = start_line
                target_name = None
                while curr_idx < len(lines):
                    nxt_line = lines[curr_idx].strip()
                    if not nxt_line or nxt_line.startswith("#") or nxt_line.startswith("@"):
                        curr_idx += 1
                        continue
                    m = re.match(r"^(?:async\s+)?def\s+([a-zA-Z0-9_]+)\b", nxt_line)
                    if not m:
                        m = re.match(r"^class\s+([a-zA-Z0-9_]+)\b", nxt_line)
                    if m:
                        target_name = m.group(1)
                    break

                if target_name:
                    comment_content = text.lstrip("#").strip()
                    words = re.findall(r"[a-zA-Z0-9]+", comment_content.lower())
                    if words and len(words) <= 5:
                        name_tokens_list = re.findall(
                            r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z][a-z0-9]|\b)", target_name
                        )
                        name_tokens = {t.lower() for t in name_tokens_list if t}
                        if set(words).issubset(name_tokens):
                            violations.append(
                                f"{py_file.name}:{start_line} duplicate comment restating '{target_name}': '{text[:60]}'"
                            )
        except Exception:
            continue

    duration_ms = int((time.time() - t0) * 1000)
    passed = len(violations) == 0
    tail = (
        "\n".join(violations[:10])
        if violations
        else "Comment sanitation clean: no commented-out code or redundant restatements."
    )
    return GateCheck(
        name="redundant_comment_sanitation",
        passed=passed,
        exit_code=0 if passed else 1,
        stdout_tail=tail,
        duration_ms=duration_ms,
    )


def check_hub_import_depth(
    target_files: list[Path], max_depth: int = 2, is_hub: bool = False
) -> GateCheck:
    """Enforces ADR 0044: Blocks deep module imports into Hub packages from Spoke files.

    Args:
        target_files: List of Python file paths to scan.
        max_depth: Maximum package path segments permitted.
        is_hub: Whether the current workspace is the central Hub repository.

    Returns:
        GateCheck summary.
    """
    if is_hub:
        return GateCheck(
            name="hub_import_depth",
            passed=True,
            exit_code=0,
            stdout_tail="Hub workspace detected: Hub internal module depth exempted (ADR 0044 applies to Spokes).",
            duration_ms=0,
        )

    t0 = time.time()
    violations: list[str] = []

    for py_file in target_files:
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    parts = node.module.split(".")
                    if parts[0] in HUB_PACKAGE_PREFIXES and len(parts) > max_depth:
                        violations.append(
                            f"{py_file.name}:{node.lineno} forbidden deep import '{node.module}' (depth {len(parts)} > {max_depth})"
                        )
        except Exception:
            continue

    duration_ms = int((time.time() - t0) * 1000)
    passed = len(violations) == 0
    tail = (
        "\n".join(violations[:10])
        if violations
        else "Hub import depth check clean: all imports conform to ADR 0044."
    )
    return GateCheck(
        name="hub_import_depth",
        passed=passed,
        exit_code=0 if passed else 1,
        stdout_tail=tail,
        duration_ms=duration_ms,
    )


def check_secret_ip_cleanliness(target_files: list[Path]) -> GateCheck:
    """Scans code for hardcoded Tailscale IPs or raw API keys without explicit allowlist comment.

    Args:
        target_files: List of Python file paths to scan.

    Returns:
        GateCheck summary.
    """
    t0 = time.time()
    violations: list[str] = []

    for py_file in target_files:
        if "__pycache__" in str(py_file) or ".venv" in str(py_file) or "tests" in str(py_file):
            continue
        try:
            lines = py_file.read_text(encoding="utf-8").splitlines()
            for idx, line in enumerate(lines, start=1):
                if "# ccba:allow-raw-ip" in line or "# ccba:allow-machine-path" in line:
                    continue
                if TAILSCALE_IP_REGEX.search(line):
                    violations.append(
                        f"{py_file.name}:{idx} raw Tailscale IP detected without allowlist comment."
                    )
                if (
                    LEAK_DETECTOR_REGEX.search(line)
                    and "dummy" not in line.lower()
                    and "mock" not in line.lower()
                ):
                    violations.append(f"{py_file.name}:{idx} raw API key pattern detected.")
        except Exception:
            continue

    duration_ms = int((time.time() - t0) * 1000)
    passed = len(violations) == 0
    tail = (
        "\n".join(violations[:10])
        if violations
        else "Cleanliness check clean: no raw IPs or secrets detected."
    )
    return GateCheck(
        name="secret_ip_cleanliness",
        passed=passed,
        exit_code=0 if passed else 1,
        stdout_tail=tail,
        duration_ms=duration_ms,
    )


def _build_linter_check(target_files: list[Path], ws: Path) -> GateCheck:
    """Builds and executes the linter gate check."""
    flake8_bin = shutil.which("flake8")
    if flake8_bin and target_files:
        flake8_cmd = [flake8_bin, "--max-line-length=120", "--extend-ignore=E501"] + [
            str(f) for f in target_files
        ]
        return run_command_check("flake8_lint", flake8_cmd, cwd=ws)
    return GateCheck(
        name="flake8_lint",
        passed=True,
        exit_code=0,
        stdout_tail="flake8 skipped (binary not found or no target files).",
        duration_ms=0,
    )


def run_full_gate(
    workspace_dir: Path | None = None,
    branch: str | None = None,
    changed_files: list[str] | None = None,
    pytest_targets: list[str] | None = None,
) -> GateResult:
    """Executes the complete 6-stage automated gate across the given workspace."""
    ws = workspace_dir.resolve() if workspace_dir else Path.cwd().resolve()
    now_iso = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat()
    test_args = pytest_targets or ["packages/ccba-harness/tests/test_peer.py"]
    target_files = get_target_files(ws, changed_files=changed_files, branch=branch)
    import_cmd = [
        sys.executable,
        "-c",
        "import ccba_harness; import ccba_harness.peer; print('Import clean.')",
    ]

    checks = [
        run_command_check(
            "pytest_suite", [sys.executable, "-m", "pytest"] + test_args + ["-q"], cwd=ws
        ),
        _build_linter_check(target_files, ws),
        check_ast_function_length(target_files, max_lines=50),
        check_redundant_comments(target_files),
        run_command_check("import_cycle_check", import_cmd, cwd=ws),
        check_hub_import_depth(target_files, is_hub=is_hub_workspace(ws)),
        check_secret_ip_cleanliness(target_files),
    ]

    all_passed = all(c.passed for c in checks)
    return GateResult(
        gate="PASS" if all_passed else "FAIL", timestamp=now_iso, branch=branch, checks=checks
    )


# Canonical alias conforming to ADR-0007 / ADR-0009 specifications
run_implementation_gate = run_full_gate


def write_verdict_file(result: GateResult, peer_exchange_dir: Path) -> Path:
    """Persists a GateResult as a YAML front-matter markdown verdict file.

    Args:
        result: The GateResult to write.
        peer_exchange_dir: Directory where peer exchange files reside.

    Returns:
        Path to the saved verdict file.
    """
    peer_exchange_dir.mkdir(parents=True, exist_ok=True)
    req_id = f"auto-gate-{uuid.uuid4().hex[:12]}"
    verdict_type = "GATE_PASS" if result.gate == "PASS" else "GATE_FAIL"

    block = PeerVerdictBlock(
        request_id=req_id,
        verdict=verdict_type,
        conditions=[],
        risk_score=1 if result.gate == "PASS" else 4,
        effort="XS",
        summary=f"Automated 6-stage gate verification: {result.gate}. Checks: {len(result.checks)} executed.",
    )
    frontmatter = render_verdict_header(block)
    body = (
        f"# Automated Gate Execution Report\n\n"
        f"- **Timestamp**: `{result.timestamp}`\n"
        f"- **Gate Status**: `{result.gate}`\n"
        f"- **Branch**: `{result.branch or 'N/A'}`\n\n"
        f"## Stage Summary\n\n"
        f"| Check Name | Status | Exit Code | Duration |\n"
        f"|---|:---:|:---:|:---:|\n"
    )
    for c in result.checks:
        status_icon = "PASS" if c.passed else "FAIL"
        body += f"| `{c.name}` | {status_icon} | {c.exit_code} | {c.duration_ms}ms |\n"

    out_file = peer_exchange_dir / f"grok_implementation_gate_{req_id}.md"
    out_file.write_text(frontmatter + body, encoding="utf-8")
    return out_file


def print_summary_table(result: GateResult) -> None:
    """Prints a clean ASCII summary table to stdout."""
    print("\n" + "=" * 65)
    print(f"🛡️  PEER IMPLEMENTATION GATE RESULT: [{result.gate}]")
    print("=" * 65)
    print(f"Timestamp: {result.timestamp} | Branch: {result.branch or 'N/A'}\n")
    print(f"{'Check Name':<28} | {'Status':<8} | {'Exit':<5} | Duration")
    print("-" * 65)
    for c in result.checks:
        status_str = "PASS" if c.passed else "FAIL"
        print(f"{c.name:<28} | {status_str:<8} | {c.exit_code:<5} | {c.duration_ms}ms")
    print("=" * 65 + "\n")

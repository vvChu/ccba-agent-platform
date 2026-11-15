"""Pure-stdlib scanner seam for raw models, hardcoded IPs, and machine paths.

Zero intra-package or third-party imports so this module can also run as a
standalone Tier-0 guardrail synced into Spoke ``scripts/_guardrails/``.
"""

from __future__ import annotations

import ast
import ipaddress
import os
import re
from collections.abc import Iterable, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from pathlib import Path

_APPROVED_MODEL_ALIASES: frozenset[str] = frozenset(
    (
        "ocr-primary ocr-fallback ocr-tier4 ocr-proxy rag-core rag-light "
        "local-coder local-instruct fast-realtime text-auto text-gemma "
        "text-gemma-12b text-gemma-4b text-light-gemma text-light-auto auto "
        "reasoning-gemma reasoning-fallback qwen-local qwen-local-primary "  # ccba:allow-raw-model
        "gemini-flash-latest gemini-reasoning-latest embedding-default "  # ccba:allow-raw-model
        "audio-primary whisper-primary whisper-local "
        "tier-reasoning tier-fast tier-ocr tier-local"
    ).split()
)

_DEPRECATED_MODEL_PREFIXES: tuple[str, ...] = tuple(
    (
        "gemini-2.5- gemini-3.5-flash- gemini-3.6- gemini-3.7- "  # ccba:allow-raw-model
        "qwen-3.5-35b qwen3.5-35b gemma-3-27b "  # ccba:allow-raw-model
        "smart-brain smartest-brain ocr-tier3"
    ).split()
)

_RAW_MODEL_PREFIXES: tuple[str, ...] = tuple(
    (
        "gemini- claude- gpt- llama- mistral- qwen- deepseek- gemma- grok- "
        "text-embedding- openai/ anthropic/ gemini/"
    ).split()
)

_MODEL_PATTERN = re.compile(
    r"^(?:gemini[-/]|gpt[-/]|claude[-/]|llama[-/]|mistral[-/]|qwen[-/]|deepseek[-/]|"
    r"gemma[-/]|grok[-/]|openai/|anthropic/|text-embedding[-/])[a-zA-Z0-9_\-\.]+$",
    re.IGNORECASE,
)

_IPV4_CANDIDATE_RE = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")
_STANDARD_PUBLIC_DNS: frozenset[str] = frozenset(
    "8.8.8.8 8.8.4.4 1.1.1.1 1.0.0.1 255.255.255.255".split()  # ccba:allow-raw-ip
)

_STATUTORY_CLAUSE_REF_RE = re.compile(
    r"""(?:"""
    r"""(?:["']{3}|^\s*#{1,6})\s*"""
    r"""|(?:\b(?:tại|điểm|khoản|mục|điều|chương|phụ\s+lục|qcvn|tcvn|như|bảng|hình|"""
    r"""chú\s+thích(?:\s+tại)?|tuân\s+thủ|quy\s+định\s+tại|nêu\s+tại|theo)\s+)"""
    r""")"""
    r"""(\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2})(?=\s{2,}|[\s.,);:"']|$)""",
    re.IGNORECASE,
)

_WIN_PATH_RE = re.compile(
    r"""(?:[rR]?["'][A-Za-z]:(?:[\\/]+[^"'\n]*|[\\/]*["'])|"""
    r"""[=:]\s*[A-Za-z]:[\\/]+[A-Za-z0-9_.\-\\/]+)"""
)
_POSIX_HOME_RE = re.compile(r"""(?:["']|[=:]\s*)/home/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+""")
_SHAREPOINT_TOKEN_RE = re.compile(r"/?:[a-z]:/[grs]/", re.IGNORECASE)

_PRUNED_DIR_NAMES: frozenset[str] = frozenset(
    (
        ".venv venv .git .md build dist archive legacy_scripts tests "
        "__pycache__ node_modules .mypy_cache .pytest_cache .ruff_cache"
    ).split()
)

_DEFAULT_EXEMPT_MODEL_FILES: frozenset[str] = frozenset(
    (
        "routing.py fallback.py mock_provider.py copilot_provider.py "
        "litellm_config.yaml custom_callbacks.py "
        "check_spoke_cleanliness.py _parameter_cleanliness.py"
    ).split()
)

_COMMENT_PREFIXES: tuple[str, ...] = ("#", "//", "/*", "*", '"""', "'''")
_PATH_NOISE_TOKENS: tuple[str, ...] = ("path/to", "example", "dummy")
_VALID_RULES: frozenset[str] = frozenset({"raw_model", "raw_ip", "machine_path"})


@dataclass(frozen=True)
class ParameterViolation:
    """Structured finding emitted by stdlib cleanliness scanners."""

    file_path: Path
    line_number: int
    rule_name: str
    message: str


def is_statutory_clause_match(line: str, match: re.Match[str]) -> bool:
    """Return True when a 4-part dotted number is a statutory clause citation."""
    has_group = bool(match.lastindex and match.lastindex >= 1)
    ip_str = match.group(1) if has_group else match.group(0)
    span_start, span_end = match.span(1) if has_group else match.span(0)
    parts = ip_str.split(".")
    if len(parts) != 4 or any(int(part) > 30 for part in parts):
        return False
    prefix = line[:span_end]
    for clause_match in _STATUTORY_CLAUSE_REF_RE.finditer(line):
        if clause_match.start(1) == span_start and clause_match.end(1) == span_end:
            return True
    return prefix.lstrip().startswith(f"{ip_str}  ")


def _collect_docstring_lines(tree: ast.AST) -> set[int]:
    """Collect 1-indexed line numbers belonging to Python AST docstrings."""
    doc_lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            continue
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            start_ln = getattr(node.body[0], "lineno", 0)
            end_ln = getattr(node.body[0], "end_lineno", start_ln)
            doc_lines.update(range(start_ln, end_ln + 1))
    return doc_lines


def _resolve_py_context(
    filepath: Path,
    content: str,
) -> tuple[bool, ast.AST | None, set[int], list[str]]:
    """Parse Python AST safely and return docstring lines and splitlines."""
    lines = content.splitlines()
    if filepath.suffix.lower() != ".py":
        return False, None, set(), lines
    try:
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError:
        return False, None, set(), lines
    return True, tree, _collect_docstring_lines(tree), lines


def _collect_exempt_stmt_lines(tree: ast.AST | None, lines: list[str], tag: str) -> set[int]:
    """Return all line numbers spanned by statements containing the exemption tag."""
    if tree is None:
        return set()
    exempt_lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.stmt):
            continue
        start = getattr(node, "lineno", 0)
        end = getattr(node, "end_lineno", start) or start
        span = lines[max(0, start - 1) : min(len(lines), end)]
        if any(tag in sl or "noqa" in sl for sl in span):
            exempt_lines.update(range(start, end + 1))
    return exempt_lines


def _is_whitelisted_path(path: Path) -> bool:
    """Return True when path lies inside pruned folders or exempt filename patterns."""
    if any(part in _PRUNED_DIR_NAMES for part in path.parts):
        return True
    if path.name.startswith(("test_", "verify_")):
        return True
    normalized = path.as_posix()
    if "ccba_maskara" in normalized and "_locator.py" in normalized:
        return True
    if path.name in _DEFAULT_EXEMPT_MODEL_FILES and (
        "ccba_ai" in normalized or path.name == "_parameter_cleanliness.py"
    ):
        return True
    return False


def _iter_walk_py_files(root_dir: Path, pruned_dirs: AbstractSet[str]) -> list[Path]:
    """Walk directory tree sorting subdirectories and pruning ignored trees in-place."""
    collected: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = sorted(d for d in dirnames if d not in pruned_dirs)
        base = Path(dirpath)
        for fname in sorted(filenames):
            if fname.endswith(".py"):
                cand = base / fname
                if not _is_whitelisted_path(cand):
                    collected.append(cand)
    return sorted(collected, key=lambda p: p.as_posix())


class _ParameterCleanlinessScanner:
    """Stateful helper executing unified stdlib AST + regex cleanliness rules."""

    def __init__(
        self,
        *,
        rules: AbstractSet[str],
        allowed_model_aliases: AbstractSet[str],
        exempt_model_files: AbstractSet[str],
        check_posix_home: bool,
    ) -> None:
        self._rules = rules
        self._aliases = frozenset(a.lower() for a in allowed_model_aliases)
        self._exempt_model_files = exempt_model_files
        self._check_posix_home = check_posix_home

    def scan_file(self, filepath: Path, content: str) -> list[ParameterViolation]:
        """Run enabled rules on a single in-memory file payload."""
        is_py, tree, doc_lines, lines = _resolve_py_context(filepath, content)
        violations: list[ParameterViolation] = []
        if "raw_model" in self._rules and is_py and tree is not None:
            violations.extend(self._scan_models(filepath, tree, doc_lines, lines))
        if "raw_ip" in self._rules:
            violations.extend(self._scan_ips(filepath, is_py, tree, doc_lines, lines))
        if "machine_path" in self._rules:
            violations.extend(self._scan_machine_paths(filepath, is_py, tree, doc_lines, lines))
        violations.sort(key=lambda v: (v.file_path.as_posix(), v.line_number, v.rule_name))
        return violations

    def _scan_models(
        self,
        filepath: Path,
        tree: ast.AST,
        doc_lines: set[int],
        lines: list[str],
    ) -> list[ParameterViolation]:
        """Detect unapproved raw LLM model literals via AST inspection."""
        if filepath.name in self._exempt_model_files:
            return []
        if any("ccba:allow-raw-model-file" in line for line in lines[:5]):
            return []
        exempt_lines = _collect_exempt_stmt_lines(tree, lines, "ccba:allow-raw-model")
        findings: list[ParameterViolation] = []
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            lineno = getattr(node, "lineno", 0)
            end_lineno = getattr(node, "end_lineno", lineno) or lineno
            if lineno in doc_lines or lineno in exempt_lines or not (0 < lineno <= len(lines)):
                continue
            span_lines = lines[max(0, lineno - 1) : min(len(lines), end_lineno)]
            if any("ccba:allow-raw-model" in sl or "noqa" in sl for sl in span_lines):
                continue
            if self._is_raw_model_literal(node.value):
                findings.append(
                    ParameterViolation(
                        file_path=filepath,
                        line_number=lineno,
                        rule_name="RawModelStringViolation",
                        message=(
                            f"Raw model string '{node.value}' detected. "
                            "Use ccba_ai.routing or alias, or annotate '# ccba:allow-raw-model'."
                        ),
                    )
                )
        return findings

    def _is_raw_model_literal(self, raw_value: str) -> bool:
        """Return True when string matches a raw provider model or deprecated prefix."""
        val = raw_value.strip().lower()
        if not val or " " in val or len(val) >= 60 or val in self._aliases:
            return False
        if _MODEL_PATTERN.match(val):
            return True
        return any(val.startswith(pfx) for pfx in _RAW_MODEL_PREFIXES + _DEPRECATED_MODEL_PREFIXES)

    @staticmethod
    def _iter_active_lines(
        is_py: bool,
        tree: ast.AST | None,
        doc_lines: set[int],
        lines: list[str],
        marker: str,
    ) -> Iterable[tuple[int, str, str]]:
        """Yield non-comment, non-docstring, non-exempt lines as (line_num, line, stripped)."""
        exempt_lines = _collect_exempt_stmt_lines(tree, lines, marker)
        in_docstring = False
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            was_in = in_docstring
            if not is_py and (stripped.count('"""') % 2 == 1 or stripped.count("'''") % 2 == 1):
                in_docstring = not in_docstring
            skip_doc = (
                line_num in doc_lines or line_num in exempt_lines
                if is_py
                else (was_in or in_docstring)
            )
            if (
                skip_doc
                or stripped.startswith(_COMMENT_PREFIXES)
                or marker in stripped
                or "noqa" in stripped
            ):
                continue
            yield line_num, line, stripped

    def _scan_ips(
        self,
        filepath: Path,
        is_py: bool,
        tree: ast.AST | None,
        doc_lines: set[int],
        lines: list[str],
    ) -> list[ParameterViolation]:
        """Detect hardcoded non-exempt IPv4 literals while honoring statutory citations."""
        findings: list[ParameterViolation] = []
        for line_num, line, _ in self._iter_active_lines(
            is_py, tree, doc_lines, lines, "ccba:allow-raw-ip"
        ):
            for match in _IPV4_CANDIDATE_RE.finditer(line):
                ip_str = match.group(1)
                if self._is_exempt_ipv4(line, match, ip_str):
                    continue
                findings.append(
                    ParameterViolation(
                        file_path=filepath,
                        line_number=line_num,
                        rule_name="HardcodedNetworkIPViolation",
                        message=(
                            f"Hardcoded IP address '{ip_str}' detected. "
                            "Use env vars (e.g. GATEWAY_PROXY_URL) or annotate '# ccba:allow-raw-ip'."
                        ),
                    )
                )
                break
        return findings

    @staticmethod
    def _is_exempt_ipv4(line: str, match: re.Match[str], ip_str: str) -> bool:
        """Return True when candidate IPv4 is loopback, unspecified, DNS, version, or statutory."""
        try:
            ip = ipaddress.IPv4Address(ip_str)
        except ValueError:
            return True
        if ip.is_loopback or ip.is_unspecified or ip.is_multicast or ip_str in _STANDARD_PUBLIC_DNS:
            return True
        if ip_str.endswith(".0") and "version" in line[: match.start()].lower():
            return True
        return is_statutory_clause_match(line, match)

    def _scan_machine_paths(
        self,
        filepath: Path,
        is_py: bool,
        tree: ast.AST | None,
        doc_lines: set[int],
        lines: list[str],
    ) -> list[ParameterViolation]:
        """Detect hardcoded Windows drive paths (including spaces) and optional POSIX home paths."""
        findings: list[ParameterViolation] = []
        for line_num, _line, stripped in self._iter_active_lines(
            is_py, tree, doc_lines, lines, "ccba:allow-machine-path"
        ):
            if any(tok in stripped for tok in _PATH_NOISE_TOKENS):
                continue
            desc = self._match_machine_path_desc(_SHAREPOINT_TOKEN_RE.sub("", stripped))
            if desc is not None:
                findings.append(
                    ParameterViolation(
                        file_path=filepath,
                        line_number=line_num,
                        rule_name="HardcodedMachinePathViolation",
                        message=(
                            f"{desc} detected. Use env vars (e.g. CCBA_HUB_PATH) "
                            "or annotate with '# ccba:allow-machine-path'."
                        ),
                    )
                )
        return findings

    def _match_machine_path_desc(self, sanitized_line: str) -> str | None:
        """Match Windows drive path or POSIX home path patterns on a sanitized line."""
        if _WIN_PATH_RE.search(sanitized_line):
            return "Hardcoded Windows drive path"
        if self._check_posix_home and _POSIX_HOME_RE.search(sanitized_line):
            return "Hardcoded POSIX user home path"
        return None


def _expand_targets(
    targets: Path | Sequence[Path],
    pruned_dirs: AbstractSet[str],
    respect_whitelist: bool,
) -> list[Path]:
    """Expand files/directories into sorted list of concrete paths to scan."""
    target_seq: Iterable[Path] = (targets,) if isinstance(targets, Path) else targets
    by_key: dict[str, Path] = {}
    for item in target_seq:
        if item.is_dir():
            for child in _iter_walk_py_files(item, pruned_dirs):
                by_key.setdefault(child.as_posix(), child)
        elif not (respect_whitelist and _is_whitelisted_path(item)):
            by_key.setdefault(item.as_posix(), item)
    return sorted(by_key.values(), key=lambda p: p.as_posix())


def scan_parameter_cleanliness(
    targets: Path | Sequence[Path],
    *,
    content: str | None = None,
    rules: Sequence[str] | None = None,
    allowed_model_aliases: AbstractSet[str] | None = None,
    exempt_model_files: AbstractSet[str] | None = None,
    check_posix_home: bool = False,
    pruned_dirs: AbstractSet[str] | None = None,
    respect_whitelist: bool = True,
) -> list[ParameterViolation]:
    """Scan Python or config targets for raw models, IPs, and hardcoded machine paths."""
    active_rules = _VALID_RULES if rules is None else frozenset(rules) & _VALID_RULES
    extra_aliases = frozenset(allowed_model_aliases) if allowed_model_aliases else frozenset()
    extra_exempt = frozenset(exempt_model_files) if exempt_model_files else frozenset()
    scanner = _ParameterCleanlinessScanner(
        rules=active_rules,
        allowed_model_aliases=_APPROVED_MODEL_ALIASES | extra_aliases,
        exempt_model_files=_DEFAULT_EXEMPT_MODEL_FILES | extra_exempt,
        check_posix_home=check_posix_home,
    )
    if content is not None and isinstance(targets, Path):
        if respect_whitelist and _is_whitelisted_path(targets):
            return []
        return scanner.scan_file(targets, content)

    effective_pruned = _PRUNED_DIR_NAMES if pruned_dirs is None else pruned_dirs
    files = _expand_targets(targets, effective_pruned, respect_whitelist)
    all_violations: list[ParameterViolation] = []
    for filepath in files:
        try:
            text = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        all_violations.extend(scanner.scan_file(filepath, text))
    all_violations.sort(key=lambda v: (v.file_path.as_posix(), v.line_number, v.rule_name))
    return all_violations

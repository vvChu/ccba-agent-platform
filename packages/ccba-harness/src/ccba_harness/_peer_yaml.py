"""_peer_yaml.py - Strict-first YAML frontmatter loader with bounded LLM ScannerError recovery."""

from __future__ import annotations

import json
import re
from typing import Any

import yaml

_BLOCK_SCALAR_MAP_RE = re.compile(
    r"^(\s*(?:-\s+)?)[A-Za-z_][A-Za-z0-9_-]*:[ \t]*[|>](?:[+-]\d*|\d*[+-]?)?[ \t]*$"
)
_BLOCK_SCALAR_SEQ_RE = re.compile(r"^(\s*)-\s+[|>](?:[+-]\d*|\d*[+-]?)?[ \t]*$")
_UNQUOTED_KV_RE = re.compile(r"^(\s*(?:-\s+)?)([A-Za-z_][A-Za-z0-9_-]*):[ \t]+(.+?)\s*$")
_DOUBLE_QUOTED_LINE_RE = re.compile(r'^(\s*(?:-\s+|[A-Za-z_][A-Za-z0-9_-]*:[ \t]+))"(.*)"[ \t]*$')
_SKIP_PLAIN_PREFIXES: tuple[str, ...] = ("'", '"', "[", "{", "|", ">", "&", "*", "!", "?", "%")
_VALID_YAML_ESCAPES: frozenset[str] = frozenset('0abtnvfre "/\\N_LPxuU')


def _block_header_parent_indent(line: str) -> int | None:
    """Returns the parent indentation column if line opens a YAML literal/folded block scalar."""
    map_match = _BLOCK_SCALAR_MAP_RE.match(line)
    if map_match:
        return len(map_match.group(1))
    seq_match = _BLOCK_SCALAR_SEQ_RE.match(line)
    if seq_match:
        return len(seq_match.group(1))
    return None


def _next_nonempty_indent(lines: list[str], start_idx: int) -> int | None:
    """Returns leading-space count of the next non-blank line after start_idx, or None."""
    for idx in range(start_idx, len(lines)):
        if lines[idx].strip():
            return len(lines[idx]) - len(lines[idx].lstrip(" "))
    return None


def _repair_single_line(line: str, next_indent: int | None) -> str:
    """Repairs known single-line LLM YAML quoting/escape defects while keeping malformed YAML fail-closed."""
    dq_match = _DOUBLE_QUOTED_LINE_RE.match(line)
    if dq_match:
        prefix, inner = dq_match.group(1), dq_match.group(2)
        fixed = re.sub(
            r"\\(.)",
            lambda m: m.group(0) if m.group(1) in _VALID_YAML_ESCAPES else f"\\\\{m.group(1)}",
            inner,
        )
        return f'{prefix}"{fixed}"'

    kv_match = _UNQUOTED_KV_RE.match(line)
    if kv_match:
        prefix, key, val = kv_match.group(1), kv_match.group(2), kv_match.group(3)
        if (
            val
            and not val.startswith(_SKIP_PLAIN_PREFIXES)
            and (": " in val or val.endswith(":"))
            and (next_indent is None or next_indent <= len(prefix))
        ):
            return f"{prefix}{key}: {json.dumps(val, ensure_ascii=False)}"
    return line


def _repair_frontmatter_yaml_lines(raw_yaml: str) -> str:
    """Applies line-level recovery while skipping interior lines of literal/folded block scalars."""
    lines = raw_yaml.splitlines()
    repaired: list[str] = []
    block_parent_indent: int | None = None

    for idx, line in enumerate(lines):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if block_parent_indent is not None:
            if not stripped or indent > block_parent_indent:
                repaired.append(line)
                continue
            block_parent_indent = None

        header_indent = _block_header_parent_indent(line)
        if header_indent is not None:
            block_parent_indent = header_indent
            repaired.append(line)
            continue

        repaired.append(_repair_single_line(line, _next_nonempty_indent(lines, idx + 1)))

    suffix = "\n" if raw_yaml.endswith("\n") else ""
    return "\n".join(repaired) + suffix


def safe_load_frontmatter_yaml(raw_yaml: str) -> Any:
    """Parses YAML frontmatter strictly first, recovering only proven LLM ScannerError shapes.

    Args:
        raw_yaml: Raw YAML text extracted between frontmatter fences.

    Returns:
        Parsed YAML object on success, or None when strict and bounded recovery both fail.
    """
    try:
        return yaml.safe_load(raw_yaml)
    except yaml.YAMLError:
        pass
    repaired = _repair_frontmatter_yaml_lines(raw_yaml)
    if repaired == raw_yaml:
        return None
    try:
        return yaml.safe_load(repaired)
    except yaml.YAMLError:
        return None

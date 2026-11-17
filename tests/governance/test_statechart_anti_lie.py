"""Automated CI Gate: Statechart Anti-Lie & Bug-Path Parity Verification (Pstack v0.15.42).

Enforces the 5 Pstack Anti-Lie invariants for ``stateDiagram-v2`` blocks plus
fail-closed transition parsing (including inline ``:::className`` suffixes),
multi-line ``note ... end note`` skipping, and static parity between ``bug_path``
declarations and diagram transitions.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import yaml

HUB_ROOT = Path(__file__).resolve().parents[2]

VALID_MERMAID_HEADERS = (
    "flowchart",
    "graph",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram",
    "stateDiagram-v2",
    "erDiagram",
    "gantt",
    "pie",
    "gitGraph",
    "mindmap",
    "timeline",
    "quadrantChart",
    "xychart-beta",
    "sankey-beta",
    "block-beta",
    "packet-beta",
    "kanban",
    "architecture-beta",
    "C4Context",
    "C4Container",
    "C4Component",
    "C4Dynamic",
    "C4Deployment",
    "journey",
    "requirementDiagram",
    "zenuml",
)
RE_MERMAID_BLOCK = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
RE_YAML_BLOCK = re.compile(r"```ya?ml\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
RE_INLINE_JSON_LIST = re.compile(r"`(\[\s*\{[^`]*?\"from\"[^`]*?\}\s*\])`")
RE_COMPOSITE_START = re.compile(r'^state\s+(?:"[^"]+"\s+as\s+)?([A-Za-z0-9_]+)\s*\{$')
RE_STATE_DECL = re.compile(
    r'^(?:state\s+(?:"[^"]+"\s+as\s+)?([A-Za-z0-9_]+)|([A-Za-z0-9_]+)\s*:\s*.*)$'
)
RE_CLASS_ASSIGN = re.compile(r"^class\s+([A-Za-z0-9_,\s]+)\s+[A-Za-z0-9_]+\s*;?$")
RE_STATE_EDGE = re.compile(
    r"^(?P<src>\[\*\]|[A-Za-z0-9_]+)(?:[:]{3}(?P<src_cls>[A-Za-z0-9_]+))?"
    r"\s*-->\s*"
    r"(?P<dst>\[\*\]|[A-Za-z0-9_]+)(?:[:]{3}(?P<dst_cls>[A-Za-z0-9_]+))?"
    r"(?:\s*:.*)?$"
)


@dataclass
class _ParsedStatechart:
    """Internal representation of a parsed ``stateDiagram-v2`` block."""

    edges: list[tuple[str, str]] = field(default_factory=list)
    composite_states: set[str] = field(default_factory=set)
    classed_states: set[str] = field(default_factory=set)
    parent_of: dict[str, str] = field(default_factory=dict)
    initial_children: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    region_of: dict[str, tuple[str, int]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def _record_node_scope(
    node: str,
    scope_stack: list[list[Any]],
    declared_outside: set[str],
    parsed: _ParsedStatechart,
) -> None:
    """Bind a node to its composite/region only when not already declared outside."""
    if node == "[*]":
        return
    if not scope_stack:
        declared_outside.add(node)
        return
    if node not in declared_outside:
        comp_id, region_idx = str(scope_stack[-1][0]), int(scope_stack[-1][1])
        parsed.parent_of.setdefault(node, comp_id)
        parsed.region_of.setdefault(node, (comp_id, region_idx))


def _analyze_statechart(lines: list[str]) -> _ParsedStatechart:
    """Parse ``stateDiagram-v2`` body into structured edges, scopes, and syntax errors."""
    parsed = _ParsedStatechart()
    scope_stack: list[list[Any]] = []
    declared_outside: set[str] = set()
    in_note = False
    for raw_line in lines[1:]:
        line = raw_line.strip()
        if in_note:
            if line == "end note":
                in_note = False
            continue
        if not line or line.startswith("%%"):
            continue
        if line == "note" or line.startswith("note "):
            if ":" not in line:
                in_note = True
            continue
        if m_comp := RE_COMPOSITE_START.match(line):
            comp_id = m_comp.group(1)
            _record_node_scope(comp_id, scope_stack, declared_outside, parsed)
            parsed.composite_states.add(comp_id)
            scope_stack.append([comp_id, 0])
        elif line == "}":
            if scope_stack:
                scope_stack.pop()
        elif line == "--":
            if not scope_stack:
                parsed.errors.append("root-level '--' parallel separator outside composite state")
            else:
                scope_stack[-1][1] += 1
        elif m_cls := RE_CLASS_ASSIGN.match(line):
            parsed.classed_states.update(s.strip() for s in m_cls.group(1).split(",") if s.strip())
        elif m_edge := RE_STATE_EDGE.match(line):
            _consume_edge_match(m_edge, scope_stack, declared_outside, parsed)
        elif "-->" in line:
            parsed.errors.append(f"unparseable statechart transition line: '{line}'")
        elif m_decl := RE_STATE_DECL.match(line):
            st_id = m_decl.group(1) or m_decl.group(2)
            _record_node_scope(st_id, scope_stack, declared_outside, parsed)
    return parsed


def _consume_edge_match(
    match: re.Match[str],
    scope_stack: list[list[Any]],
    declared_outside: set[str],
    parsed: _ParsedStatechart,
) -> None:
    """Record a matched edge, any inline ``:::className``, and composite scope."""
    src, src_cls, dst, dst_cls = match.group("src", "src_cls", "dst", "dst_cls")
    if src_cls and src != "[*]":
        parsed.classed_states.add(src)
    if dst_cls and dst != "[*]":
        parsed.classed_states.add(dst)
    for node in (src, dst):
        _record_node_scope(node, scope_stack, declared_outside, parsed)
    if src == "[*]" and scope_stack:
        parent_id = str(scope_stack[-1][0])
        if dst != "[*]":
            parsed.initial_children[parent_id].add(dst)
        eff_src = parent_id
    else:
        eff_src = src
    parsed.edges.append((eff_src, dst))


def _parse_statechart_lines(
    lines: list[str],
) -> tuple[list[tuple[str, str]], set[str], set[str], dict[str, str], list[str]]:
    """Parse stateDiagram-v2 lines into edges, composites, classed, parents, and errors."""
    parsed = _analyze_statechart(lines)
    return (
        parsed.edges,
        parsed.composite_states,
        parsed.classed_states,
        parsed.parent_of,
        parsed.errors,
    )


def verify_statechart_anti_lie(lines: list[str]) -> list[str]:
    """Validate a stateDiagram-v2 block against the 5 Pstack Anti-Lie invariants."""
    parsed = _analyze_statechart(lines)
    errors = list(parsed.errors)
    if len(parsed.edges) > 20:
        errors.append(f"edge count {len(parsed.edges)} exceeds Anti-Lie budget (<= 20)")
    for bad_cls in sorted(parsed.composite_states & parsed.classed_states):
        errors.append(f"class applied to composite state '{bad_cls}'")
    adj: dict[str, set[str]] = defaultdict(set)
    non_self_out: dict[str, set[str]] = defaultdict(set)
    all_states: set[str] = set()
    for src, dst in parsed.edges:
        adj[src].add(dst)
        if src != dst:
            non_self_out[src].add(dst)
        if src != "[*]":
            all_states.add(src)
        if dst != "[*]":
            all_states.add(dst)
    visited = _bfs_reachable(adj)
    for st in sorted(all_states - visited):
        errors.append(f"unreachable state '{st}' from [*]")
    comp_exits = {
        c
        for c in parsed.composite_states
        if any(d != c and parsed.parent_of.get(d) != c for d in non_self_out.get(c, ()))
    }
    for st in sorted(all_states & visited):
        if not non_self_out.get(st) and not _has_lifted_exit(st, parsed.parent_of, comp_exits):
            errors.append(f"deadlock/inescapable state '{st}' has no exit transition")
    return errors


def _bfs_reachable(adj: dict[str, set[str]]) -> set[str]:
    """Return all state IDs reachable from ``[*]`` via BFS."""
    visited: set[str] = {"[*]"}
    queue: deque[str] = deque(["[*]"])
    while queue:
        curr = queue.popleft()
        for nxt in adj.get(curr, ()):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return visited


def _has_lifted_exit(state: str, parent_of: dict[str, str], comp_exits: set[str]) -> bool:
    """Return True if any composite ancestor of ``state`` owns a lifted external exit."""
    anc = parent_of.get(state)
    while anc:
        if anc in comp_exits:
            return True
        anc = parent_of.get(anc)
    return False


def _is_descendant(node: str, ancestor: str, parent_of: dict[str, str]) -> bool:
    """Return True if ``node`` lies inside ``ancestor`` along ``parent_of``."""
    curr = parent_of.get(node)
    while curr:
        if curr == ancestor:
            return True
        curr = parent_of.get(curr)
    return False


def _extract_bug_path_pairs(tail: str) -> list[tuple[str, str]]:
    """Extract ordered ``(from, to)`` step pairs from inline JSON and YAML ``bug_path`` blocks."""
    pairs: list[tuple[str, str]] = []
    for m_json in RE_INLINE_JSON_LIST.finditer(tail):
        try:
            items = json.loads(m_json.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(items, list):
            for entry in items:
                if isinstance(entry, dict) and "from" in entry and "to" in entry:
                    pairs.append((str(entry["from"]), str(entry["to"])))
    for m_yaml in RE_YAML_BLOCK.finditer(tail):
        try:
            data = yaml.safe_load(m_yaml.group(1))
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict) or "bug_path" not in data:
            continue
        bp = data["bug_path"]
        if isinstance(bp, list):
            for entry in bp:
                if isinstance(entry, dict) and "from" in entry and "to" in entry:
                    pairs.append((str(entry["from"]), str(entry["to"])))
        elif isinstance(bp, dict) and isinstance(bp.get("trace"), list):
            trace = [str(x) for x in bp["trace"]]
            pairs.extend((trace[i], trace[i + 1]) for i in range(len(trace) - 1))
    return pairs


def _step_matches_chart(
    u: str, v: str, parsed: _ParsedStatechart, edge_set: set[tuple[str, str]]
) -> bool:
    """Verify ``(u, v)`` via direct edge, Single-Way-In 2-hop, or Composite Exit Lifting."""
    if (u, v) in edge_set:
        return True
    for comp in parsed.composite_states:
        if (u, comp) in edge_set and v in parsed.initial_children.get(comp, ()):
            return True
    anc = parsed.parent_of.get(u)
    while anc:
        if (anc, v) in edge_set and v != anc and not _is_descendant(v, anc, parsed.parent_of):
            return True
        anc = parsed.parent_of.get(anc)
    return False


def verify_bug_path_matches_statechart(md_content: str) -> list[str]:
    """Ensure every declared ``bug_path`` step after a statechart matches its transitions."""
    if "stateDiagram" not in md_content or "bug_path" not in md_content:
        return []
    blocks: list[tuple[re.Match[str], list[str]]] = []
    for match in RE_MERMAID_BLOCK.finditer(md_content):
        lines = [
            ln.strip()
            for ln in match.group(1).splitlines()
            if ln.strip() and not ln.strip().startswith("%%")
        ]
        if lines and lines[0].startswith("stateDiagram"):
            blocks.append((match, lines))
    errors: list[str] = []
    for idx, (match, lines) in enumerate(blocks):
        tail_end = blocks[idx + 1][0].start() if idx + 1 < len(blocks) else len(md_content)
        tail = md_content[match.end() : tail_end]
        pairs = _extract_bug_path_pairs(tail)
        if not pairs:
            continue
        parsed = _analyze_statechart(lines)
        edge_set = set(parsed.edges)
        for u, v in pairs:
            if not _step_matches_chart(u, v, parsed, edge_set):
                errors.append(f"bug_path step '{u} -> {v}' does not match stateDiagram transitions")
    return errors


def test_verify_statechart_anti_lie_catches_violations() -> None:
    """Verify verify_statechart_anti_lie catches Anti-Lie violations and inline :::class."""
    bad_lines = [
        "stateDiagram-v2",
        "--",
        "[*] --> Idle",
        "Idle --> Running",
        "state Running {",
        "  [*] --> Stuck",
        "  Stuck --> Stuck",
        "}",
        "Orphan:::bugPath --> [*]",
        "class Running breaks",
    ]
    errors = verify_statechart_anti_lie(bad_lines)
    assert any("root-level '--'" in e for e in errors)
    assert any("composite state 'Running'" in e for e in errors)
    assert any("unreachable state 'Orphan'" in e for e in errors)
    assert any("deadlock/inescapable state 'Stuck'" in e for e in errors)
    inline_comp = [
        "stateDiagram-v2",
        "[*] --> Box",
        "state Box {",
        "  [*] --> Inner",
        "}",
        "Box:::breaks --> [*]",
    ]
    assert any("composite state 'Box'" in e for e in verify_statechart_anti_lie(inline_comp))
    unparseable = ["stateDiagram-v2", "[*] --> Idle", "Bad Node --> [*]", "Idle --> [*]"]
    assert any(
        "unparseable statechart transition" in e for e in verify_statechart_anti_lie(unparseable)
    )
    note_ok = [
        "stateDiagram-v2",
        "[*] --> Idle",
        "note right of Idle",
        "  explanatory a --> b",
        "end note",
        "Idle --> [*]",
    ]
    assert verify_statechart_anti_lie(note_ok) == []
    over_budget = (
        ["stateDiagram-v2", "[*] --> S0"]
        + [f"S{i} --> S{i + 1}" for i in range(20)]
        + ["S20 --> [*]"]
    )
    assert any("exceeds Anti-Lie budget" in e for e in verify_statechart_anti_lie(over_budget))
    lifted_ok = [
        "stateDiagram-v2",
        "[*] --> Idle",
        "Idle --> Active",
        "state Active {",
        "  [*] --> Step1",
        "  Step1 --> Step2",
        "}",
        "Active --> Done",
        "Done --> [*]",
    ]
    assert verify_statechart_anti_lie(lifted_ok) == []
    assert any(
        "Idle -> Ghost" in e
        for e in verify_bug_path_matches_statechart(
            "```mermaid\nstateDiagram-v2\n[*] --> Idle\nIdle --> [*]\n```\n"
            '- `bug_path`: `[{"from": "Idle", "to": "Ghost"}]`\n'
        )
    )
    assert (
        verify_bug_path_matches_statechart(
            "```mermaid\nstateDiagram-v2\n[*] --> Idle\nIdle --> [*]\n```\n"
            '- `[{"from": "Idle", "to": "Ghost"}]`\n'
        )
        == []
    )


@pytest.mark.fast
def test_all_repo_statecharts_and_bug_paths_pass_strict_gate() -> None:
    """Scan all skills, rules, docs, and verify-ccba-* suites for statechart + bug_path errors."""
    roots = (
        HUB_ROOT / ".agents" / "skills",
        HUB_ROOT / ".agents" / "rules",
        HUB_ROOT / "docs",
        HUB_ROOT / "packages" / "ccba-harness" / ".agents" / "skills",
    )
    violations: list[str] = []
    for root in roots:
        for md_file in sorted(root.rglob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            rel = md_file.relative_to(HUB_ROOT)
            for match in RE_MERMAID_BLOCK.finditer(content):
                lines = [
                    ln.strip()
                    for ln in match.group(1).splitlines()
                    if ln.strip() and not ln.strip().startswith("%%")
                ]
                if lines and lines[0].startswith("stateDiagram"):
                    for err in verify_statechart_anti_lie(lines):
                        violations.append(f"{rel}: {err}")
            for err in verify_bug_path_matches_statechart(content):
                violations.append(f"{rel}: {err}")
    assert not violations, "Statechart / bug_path violations:\n" + "\n".join(violations)


def test_verify_bug_path_matches_live_fixtures_and_rejects_cross_region() -> None:
    """Verify bug_path parity on live fixtures and rejection of invalid cross-region steps."""
    for rel in (
        "packages/ccba-harness/.agents/skills/verify-ccba-ai/SKILL.md",
        ".agents/skills/ccba-mermaid-diagram/references/statechart_verification_guide.md",
        ".agents/skills/ccba-sharepoint-iac/SKILL.md",
    ):
        text = (HUB_ROOT / rel).read_text(encoding="utf-8")
        assert verify_bug_path_matches_statechart(text) == [], f"Unexpected parity error in {rel}"

    guide = (
        HUB_ROOT / ".agents/skills/ccba-mermaid-diagram/references/statechart_verification_guide.md"
    ).read_text(encoding="utf-8")
    forged = guide + '\n- forged: `[{"from": "Compute", "to": "Halted", "when": "cross_region"}]`\n'
    errs = verify_bug_path_matches_statechart(forged)
    assert any("Compute -> Halted" in e for e in errs)

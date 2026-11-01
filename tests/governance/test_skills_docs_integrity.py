"""Automated CI Gate: Skills Documentation & Public Catalog Portal Integrity (ADR-0058).

Verifies that:
1. All 73 active skills are classified into docs/skills/portals.yaml with zero duplicates or orphans.
2. docs/skills/*.md files conform strictly to the 5-section standardized structure.
3. Central index (docs/skills/INDEX.md), FAQ, llms.txt, llms-full.txt, and docs/index.html exist and are 100% in sync.
4. check_skills_docs_in_sync passes without error.
"""

import re
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import pytest
import yaml

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.governance.compile_skills_docs import (
    HUB_ROOT,
    PIPELINE_MAP,
    check_skills_docs_in_sync,
    load_portals,
)

SKILLS_DIR = HUB_ROOT / ".agents" / "skills"
DOCS_DIR = HUB_ROOT / "docs"
DOCS_SKILLS_DIR = DOCS_DIR / "skills"
PORTALS_YAML_PATH = DOCS_SKILLS_DIR / "portals.yaml"

EXPECTED_SECTIONS = [
    "## 1. Action Header & Kích Hoạt Nhanh",
    "## 2. Mục Đích & Rào Chắn Bất Biến (Defining Constraints)",
    "## 3. Khi Nào Sử Dụng & Kích Hoạt (Triggers)",
    "## 4. Vị Trí Trong Chuỗi Giá Trị (The Pipeline Trail)",
    "## 5. Khóa Cứng Kỷ Luật & Tiêu Chí Hoàn Thành (ADR-0058)",
]


@pytest.fixture(scope="module")
def active_skill_names() -> set[str]:
    """Extract names of all active skills in .agents/skills/."""
    skills = set()
    for sf in SKILLS_DIR.glob("**/SKILL.md"):
        content = sf.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = yaml.safe_load(parts[1]) or {}
                name = fm.get("name") or sf.parent.name
                skills.add(str(name).strip())
        else:
            skills.add(sf.parent.name)
    return skills


@pytest.fixture(scope="module")
def portal_skill_names() -> tuple[list[dict[str, Any]], set[str]]:
    """Extract skills declared across all portals in portals.yaml."""
    assert PORTALS_YAML_PATH.exists(), f"portals.yaml not found at {PORTALS_YAML_PATH}"
    portals = load_portals(PORTALS_YAML_PATH)
    all_skills: list[str] = []
    for p in portals:
        all_skills.extend(p.get("skills", []))
    return portals, set(all_skills)


def test_portals_yaml_has_five_standard_portals(
    portal_skill_names: tuple[list[dict[str, Any]], set[str]],
) -> None:
    """Verify portals.yaml defines exactly the 5 agreed portals."""
    portals, _ = portal_skill_names
    portal_ids = {p.get("id") for p in portals}
    expected_ids = {
        "init_navigation",
        "core_engineering",
        "bim_aiqc",
        "legal_compliance",
        "governance_upkeep",
    }
    assert portal_ids == expected_ids, f"Portals mismatch: {portal_ids ^ expected_ids}"


def test_all_active_skills_in_portals_yaml_exactly_match(
    active_skill_names: set[str],
    portal_skill_names: tuple[list[dict[str, Any]], set[str]],
) -> None:
    """Ensure 100% 1-to-1 match between active skills and portals.yaml."""
    _, portal_skills = portal_skill_names
    missing_in_portals = active_skill_names - portal_skills
    orphans_in_portals = portal_skills - active_skill_names

    assert not missing_in_portals, f"Active skills missing from portals.yaml: {missing_in_portals}"
    assert not orphans_in_portals, f"Skills in portals.yaml not found on disk: {orphans_in_portals}"
    assert len(active_skill_names) == 76, (
        f"Expected exactly 76 active skills, found {len(active_skill_names)}"
    )


def test_zero_duplicate_skills_across_portals(
    portal_skill_names: tuple[list[dict[str, Any]], set[str]],
) -> None:
    """Ensure no skill is declared in multiple portals."""
    portals, _ = portal_skill_names
    seen = set()
    duplicates = set()
    for p in portals:
        for s in p.get("skills", []):
            if s in seen:
                duplicates.add(s)
            seen.add(s)
    assert not duplicates, f"Found skills assigned to multiple portals: {duplicates}"


def test_skills_documentation_in_sync_deterministic_gate() -> None:
    """Ensure check_skills_docs_in_sync returns True (100% in-sync)."""
    in_sync, msg = check_skills_docs_in_sync(HUB_ROOT)
    assert in_sync, f"Documentation out of sync:\n{msg}"


def test_all_markdown_docs_have_five_standard_sections(active_skill_names: set[str]) -> None:
    """Verify every skill doc has all 5 required section headings."""
    for name in active_skill_names:
        doc_path = DOCS_SKILLS_DIR / f"{name}.md"
        assert doc_path.exists(), f"Doc file missing: {doc_path}"
        content = doc_path.read_text(encoding="utf-8")
        for heading in EXPECTED_SECTIONS:
            assert heading in content, f"Missing section '{heading}' in {doc_path.name}"


def test_docs_artifacts_integrity() -> None:
    """Verify INDEX.md, FAQ.md, llms.txt, llms-full.txt, and index.html exist and are substantial."""
    artifacts = [
        DOCS_SKILLS_DIR / "INDEX.md",
        DOCS_SKILLS_DIR / "FAQ.md",
        DOCS_DIR / "llms.txt",
        DOCS_DIR / "llms-full.txt",
        DOCS_DIR / "index.html",
    ]
    for art in artifacts:
        assert art.exists(), f"Artifact missing: {art}"
        content = art.read_text(encoding="utf-8")
        assert len(content.strip()) > 200, (
            f"Artifact suspiciously small ({len(content)} bytes): {art}"
        )


def test_all_active_skills_have_pipeline_trail_mapping(active_skill_names: set[str]) -> None:
    """Verify every active skill has an explicit pipeline trail mapping in compile_skills_docs."""
    missing = active_skill_names - set(PIPELINE_MAP.keys())
    assert not missing, f"Skills missing pipeline trail mapping: {missing}"


def test_validate_skills_cli_check_flag() -> None:
    """Ensure run_skills_validation_cli handles the --check flag without error."""
    from scripts.doc_auditor import DocumentAuditor

    auditor = DocumentAuditor()
    exit_code = auditor.run_skills_validation_cli(["--check"])
    assert exit_code == 0, (
        f"run_skills_validation_cli(['--check']) failed with exit code {exit_code}"
    )


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
RE_COMPOSITE_START = re.compile(r'^state\s+(?:"[^"]+"\s+as\s+)?([A-Za-z0-9_]+)\s*\{$')
RE_CLASS_ASSIGN = re.compile(r"^class\s+([A-Za-z0-9_,\s]+)\s+[A-Za-z0-9_]+\s*;?$")
RE_STATE_EDGE = re.compile(r"^(\[\*\]|[A-Za-z0-9_]+)\s*-->\s*(\[\*\]|[A-Za-z0-9_]+)(?:\s*:.*)?$")


def _parse_statechart_lines(
    lines: list[str],
) -> tuple[list[tuple[str, str]], set[str], set[str], list[str]]:
    """Parse stateDiagram-v2 lines into edges, composite states, classed states, and syntax errors."""
    edges: list[tuple[str, str]] = []
    composite_states: set[str] = set()
    classed_states: set[str] = set()
    errors: list[str] = []
    scope_stack: list[str] = []
    for raw_line in lines[1:]:
        line = raw_line.strip()
        if m_comp := RE_COMPOSITE_START.match(line):
            comp_id = m_comp.group(1)
            composite_states.add(comp_id)
            scope_stack.append(comp_id)
        elif line == "}":
            if scope_stack:
                scope_stack.pop()
        elif line == "--":
            if not scope_stack:
                errors.append("root-level '--' parallel separator outside composite state")
        elif m_cls := RE_CLASS_ASSIGN.match(line):
            classed_states.update(s.strip() for s in m_cls.group(1).split(",") if s.strip())
        elif m_edge := RE_STATE_EDGE.match(line):
            src, dst = m_edge.group(1), m_edge.group(2)
            eff_src = scope_stack[-1] if (src == "[*]" and scope_stack) else src
            edges.append((eff_src, dst))
    return edges, composite_states, classed_states, errors


def verify_statechart_anti_lie(lines: list[str]) -> list[str]:
    """Validate a stateDiagram-v2 block against the 5 Pstack Anti-Lie invariants."""
    edges, composite_states, classed_states, errors = _parse_statechart_lines(lines)
    if len(edges) > 20:
        errors.append(f"edge count {len(edges)} exceeds Anti-Lie budget (<= 20)")
    for bad_cls in sorted(composite_states & classed_states):
        errors.append(f"class applied to composite state '{bad_cls}'")
    adj: dict[str, set[str]] = defaultdict(set)
    non_self_out: dict[str, set[str]] = defaultdict(set)
    all_states: set[str] = set()
    for src, dst in edges:
        adj[src].add(dst)
        if src != dst:
            non_self_out[src].add(dst)
        if src != "[*]":
            all_states.add(src)
        if dst != "[*]":
            all_states.add(dst)
    visited: set[str] = {"[*]"}
    queue: deque[str] = deque(["[*]"])
    while queue:
        curr = queue.popleft()
        for nxt in adj.get(curr, ()):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    for st in sorted(all_states - visited):
        errors.append(f"unreachable state '{st}' from [*]")
    for st in sorted(all_states & visited):
        if not non_self_out.get(st):
            errors.append(f"deadlock/inescapable state '{st}' has no exit transition")
    return errors


def test_all_mermaid_blocks_have_valid_diagram_headers() -> None:
    """Ensure every ```mermaid block in skills, rules, and docs has a valid header and body."""
    search_roots = (SKILLS_DIR, HUB_ROOT / ".agents" / "rules", DOCS_DIR)
    violations: list[str] = []
    for root in search_roots:
        for md_file in sorted(root.rglob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            for match in RE_MERMAID_BLOCK.finditer(content):
                lines = [
                    ln.strip()
                    for ln in match.group(1).splitlines()
                    if ln.strip() and not ln.strip().startswith("%%")
                ]
                lineno = content[: match.start()].count("\n") + 1
                rel_path = md_file.relative_to(HUB_ROOT)
                if not lines:
                    violations.append(f"{rel_path}:{lineno}: empty mermaid diagram body")
                elif not any(lines[0].startswith(h) for h in VALID_MERMAID_HEADERS):
                    violations.append(f"{rel_path}:{lineno}: invalid header '{lines[0]}'")
                elif lines[0].startswith("stateDiagram"):
                    for err in verify_statechart_anti_lie(lines):
                        violations.append(f"{rel_path}:{lineno}: {err}")
    assert not violations, "Invalid ```mermaid blocks found:\n" + "\n".join(violations)


def test_verify_statechart_anti_lie_catches_violations() -> None:
    """Verify verify_statechart_anti_lie detects all 5 Anti-Lie statechart violations."""
    bad_lines = [
        "stateDiagram-v2",
        "--",
        "[*] --> Idle",
        "Idle --> Running",
        "state Running {",
        "  [*] --> Stuck",
        "  Stuck --> Stuck",
        "}",
        "Orphan --> [*]",
        "class Running breaks",
    ]
    errors = verify_statechart_anti_lie(bad_lines)
    assert any("root-level '--'" in e for e in errors)
    assert any("composite state 'Running'" in e for e in errors)
    assert any("unreachable state 'Orphan'" in e for e in errors)
    assert any("deadlock/inescapable state 'Stuck'" in e for e in errors)
    over_budget = (
        ["stateDiagram-v2", "[*] --> S0"]
        + [f"S{i} --> S{i + 1}" for i in range(20)]
        + ["S20 --> [*]"]
    )
    assert any("exceeds Anti-Lie budget" in e for e in verify_statechart_anti_lie(over_budget))

"""Automated CI Gate: Skills Documentation & Public Catalog Portal Integrity (ADR-0058).

Verifies that:
1. All 76 active skills are classified into docs/skills/portals.yaml with zero duplicates or orphans.
2. docs/skills/*.md files conform strictly to the 5-section standardized structure.
3. Central index (docs/skills/INDEX.md), FAQ, llms.txt, llms-full.txt, and docs/index.html exist and are 100% in sync.
4. check_skills_docs_in_sync, portal map fields, guide paths, seam contracts, AST budgets, and WCAG contrast pass.
"""

import ast
import json
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
    TEMPLATE_HTML_PATH,
    check_skills_docs_in_sync,
    load_portals,
    load_seam_contract_cards,
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


def test_portal_map_fields_and_spine_order(
    portal_skill_names: tuple[list[dict[str, Any]], set[str]],
) -> None:
    """Verify step, question, start_with, and spine_order in portals.yaml (COND-MAP-FIELDS)."""
    portals, _ = portal_skill_names
    steps: set[str] = set()
    all_spine: list[str] = []
    for p in portals:
        pid = p.get("id")
        step = str(p.get("step") or "")
        question = str(p.get("question") or "").strip()
        start_with = str(p.get("start_with") or "").strip()
        p_skills = [str(s) for s in p.get("skills", [])]
        spine = [str(s) for s in p.get("spine_order", [])]

        assert step in {"01", "02", "03", "04", "05"}, f"Invalid step {step!r} in {pid}"
        steps.add(step)
        assert question, f"Empty question in portal {pid}"
        assert start_with in p_skills, f"start_with {start_with!r} not in {pid} skills"
        assert spine, f"Empty spine_order in portal {pid}"
        assert len(spine) == len(set(spine)), f"Duplicate spine_order items in {pid}"
        assert set(spine) <= set(p_skills), f"spine_order not subset of skills in {pid}"
        all_spine.extend(spine)
    assert steps == {"01", "02", "03", "04", "05"}, f"Expected 5 unique steps, got {steps}"
    assert len(all_spine) == len(set(all_spine)), "Overlapping spine_order skills across portals"


def test_portal_guide_paths_resolve_inside_docs(
    portal_skill_names: tuple[list[dict[str, Any]], set[str]],
) -> None:
    """Verify every portal guide path resolves cleanly inside docs/ (COND-GUIDE-PATH)."""
    portals, _ = portal_skill_names
    docs_root = DOCS_DIR.resolve()
    for p in portals:
        pid = p.get("id")
        guides = p.get("guides") or []
        assert guides, f"Portal {pid} must declare at least one guide"
        for g in guides:
            rel_path = str(g.get("path") or "")
            assert rel_path and not rel_path.startswith("/"), f"Leading slash in {pid}: {rel_path}"
            assert not rel_path.startswith("docs/"), f"Redundant docs/ prefix in {pid}: {rel_path}"
            assert ".." not in rel_path and "\\" not in rel_path, (
                f"Unsafe path in {pid}: {rel_path}"
            )
            target = (DOCS_DIR / rel_path).resolve()
            assert target.is_relative_to(docs_root), f"Path escapes docs/ in {pid}: {rel_path}"
            assert target.is_file(), f"Missing guide file for {pid}: {target}"


def test_index_html_embedded_json_parity() -> None:
    """Verify embedded JSON payloads in docs/index.html match YAML sources (COND-CARD-SHAPE)."""
    html = (DOCS_DIR / "index.html").read_text(encoding="utf-8")
    payloads: dict[str, Any] = {}
    for var_name in ("SKILLS", "PORTALS", "PACKAGE_SEAMS", "SEAM_CONTRACTS"):
        m = re.search(rf"const\s+{var_name}\s*=\s*(\[.*?\]);\s*$", html, re.MULTILINE)
        assert m is not None, f"Embedded const {var_name} not found in docs/index.html"
        payloads[var_name] = json.loads(m.group(1))

    assert len(payloads["SKILLS"]) == 76
    assert len(payloads["PORTALS"]) == 5
    assert len(payloads["PACKAGE_SEAMS"]) == 10
    expected_cards = load_seam_contract_cards(HUB_ROOT)
    assert len(payloads["SEAM_CONTRACTS"]) == len(expected_cards)
    assert {c["seam_id"] for c in payloads["SEAM_CONTRACTS"]} == {
        c["seam_id"] for c in expected_cards
    }
    for card in payloads["SEAM_CONTRACTS"]:
        assert card["kind"] in {"package", "skill"}
        assert isinstance(card["in"], list) and isinstance(card["out"], list)
        assert isinstance(card["hardware"], list)
        assert isinstance(card["forbidden_substitute_imports"], list)


def test_compiler_ast_size_budget() -> None:
    """Verify compile_skills_docs.py obeys module and function LOC budgets via stdlib ast (COND-PAGES-AST)."""
    compiler_path = HUB_ROOT / "scripts" / "governance" / "compile_skills_docs.py"
    source = compiler_path.read_text(encoding="utf-8")
    total_lines = len(source.splitlines())
    assert total_lines <= 800, f"compile_skills_docs.py has {total_lines} lines (> 800)"
    tree = ast.parse(source, filename=str(compiler_path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = getattr(node, "end_lineno", node.lineno)
            func_len = end_line - node.lineno + 1
            assert func_len <= 50, f"Function {node.name} is {func_len} lines (> 50)"
            if node.name == "main":
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) and getattr(sub.func, "attr", "") == "parse_args":
                        parse_line = getattr(sub, "end_lineno", sub.lineno)
                        post_lines = end_line - parse_line + 1
                        assert post_lines <= 40, (
                            f"main post-parse_args is {post_lines} lines (> 40)"
                        )


def _relative_luminance(hex_color: str) -> float:
    """Calculate WCAG 2.x relative luminance from a 6-digit hex color."""
    h = hex_color.lstrip("#")
    assert len(h) == 6, f"Expected 6-digit hex color, got {hex_color!r}"
    channels: list[float] = []
    for i in (0, 2, 4):
        c = int(h[i : i + 2], 16) / 255.0
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    """Calculate WCAG contrast ratio between two 6-digit hex colors."""
    lum_a, lum_b = _relative_luminance(hex_a), _relative_luminance(hex_b)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def test_portal_template_css_tokens_and_wcag_contrast() -> None:
    """Verify --ccba-* tokens, split grid rules, and WCAG 2.2 AA contrast >= 4.5:1 (COND-CONTRAST-PAIRS & COND-ROOT-STAYS-DARK)."""
    css_html = TEMPLATE_HTML_PATH.read_text(encoding="utf-8")
    assert "--ah-" not in css_html, "Found unprefixed --ah- token in skills_portal.html"
    assert "minmax(0, 0.9fr) minmax(0, 1.1fr)" in css_html
    assert "var(--ccba-line)" in css_html

    for selector in (r":root", r'\[data-theme="light"\]'):
        m_block = re.search(rf"{selector}\s*\{{(.*?)\}}", css_html, re.DOTALL)
        assert m_block is not None, f"Missing CSS block for {selector}"
        assert "--ccba-nav-height: 62px" in m_block.group(1)
        tokens = dict(
            re.findall(r"(--ccba-[a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6})\b", m_block.group(1))
        )
        if selector == r":root":
            assert tokens.get("--ccba-bg") == "#0e0e0d"
            assert tokens.get("--ccba-fg-body") == "#f4f3f1"
            assert tokens.get("--ccba-fg-muted") == "#b5b8c0"
        else:
            assert tokens.get("--ccba-bg") == "#fbfbfc"
            assert tokens.get("--ccba-bg-sidebar") == "#f5f6f8"
            assert tokens.get("--ccba-gold") == "#9a6700"
        pairs = (
            ("--ccba-bg", "--ccba-fg-body"),
            ("--ccba-bg", "--ccba-fg-muted"),
            ("--ccba-bg", "--ccba-gold"),
            ("--ccba-bg-sidebar", "--ccba-fg-body"),
            ("--ccba-bg-sidebar", "--ccba-fg-muted"),
            ("--ccba-bg-sidebar", "--ccba-gold"),
            ("--ccba-cta-bg", "--ccba-cta-fg"),
            ("--ccba-bg", "--ccba-fg-subtle"),
            ("--ccba-bg", "--ccba-fg-faint"),
            ("--ccba-bg", "--ccba-primary"),
            ("--ccba-bg-card", "--ccba-fg-subtle"),
            ("--ccba-bg-card", "--ccba-fg-faint"),
            ("--ccba-bg-card", "--ccba-primary"),
            ("--ccba-bg-sidebar", "--ccba-fg-subtle"),
            ("--ccba-bg-sidebar", "--ccba-fg-faint"),
            ("--ccba-bg-sidebar", "--ccba-primary"),
            ("--ccba-code-bg", "--ccba-fg-subtle"),
            ("--ccba-code-bg", "--ccba-fg-faint"),
            ("--ccba-code-bg", "--ccba-primary"),
        )
        for k_a, k_b in pairs:
            c_a, c_b = tokens.get(k_a, ""), tokens.get(k_b, "")
            assert c_a and c_b, f"Missing token pair ({k_a}, {k_b}) in {selector}"
            assert _contrast_ratio(c_a, c_b) >= 4.5, f"Low contrast ({k_a}, {k_b}) in {selector}"


def test_portal_template_escapes_portal_icon_and_count() -> None:
    """Verify that p.icon, p.count, p.id, and s.portal_icon are HTML-escaped via escapeHtml()."""
    html_text = TEMPLATE_HTML_PATH.read_text(encoding="utf-8")
    for raw_expr in ("${p.icon}", "${p.count}", "goal-${p.id}", "${s.portal_icon}"):
        assert raw_expr not in html_text, f"Unescaped expression {raw_expr} in skills_portal.html"
    assert "${escapeHtml(p.icon)}" in html_text
    assert "${escapeHtml(p.count)}" in html_text
    assert "goal-${escapeHtml(p.id)}" in html_text
    assert "${escapeHtml(s.portal_icon)}" in html_text


REQUIRED_SHELL_SNIPPETS = (
    '<html lang="vi" data-theme="light">',
    'const savedTheme = localStorage.getItem("ccba_theme") || "light";',
    'document.documentElement.setAttribute("data-theme", savedTheme);',
    "--ccba-nav-height: 62px;",
    "flex-wrap: nowrap;",
    "top: var(--ccba-nav-height);",
    'id="mobileMenuBtn"',
    'aria-controls="appSidebar"',
    'aria-expanded="false"',
    "openSearchFromHeader()",
    "searchInput.focus()",
    'class="header-cta-btn"',
    'data-slot="sidebar-wrapper"',
    'data-slot="sidebar"',
    'aria-label="Learning navigation"',
    "width: 264px;",
    "height: calc(100vh - var(--ccba-nav-height));",
    "@media (min-width: 1024px)",
    "z-index: 55;",
    "background: var(--ccba-fg-body);",
    "color: var(--ccba-bg);",
    'class="app-main"',
    "min-width: 0;",
    'class="app-main-inner"',
    "function renderSidebar()",
    'data-slot="sidebar-group-label">Explore</div>',
    'data-slot="sidebar-group-label">Guides</div>',
    'data-slot="sidebar-group-label">What\'s New</div>',
    'data-slot="sidebar-group-label">Topics</div>',
    "${SKILLS.length}",
    "${PACKAGE_SEAMS.length}",
    "PORTALS.map(p => p.start_with)",
    "seenGuides.has(g.path)",
    "jumpToTopic(",
    'class="inline-advisor-banner"',
    '<button type="button" class="do-this-card"',
    '<button type="button" class="media-card"',
    'class="media-thumb"',
    "width: 132px;",
    "height: 78px;",
    'class="media-card-arrow"',
    "width: 34px;",
    "height: 34px;",
)


def test_aihero_app_shell_sidebar_and_obligations() -> None:
    """Verify OBL-SHELL-SIDEBAR, OBL-HEADER-MINIMAL, OBL-LIGHT-DEFAULT, OBL-MEDIA-CARDS, and 4 Grok conditions."""
    for target_path in (TEMPLATE_HTML_PATH, DOCS_DIR / "index.html"):
        html_text = target_path.read_text(encoding="utf-8")
        assert "--ah-" not in html_text, f"Forbidden --ah- token in {target_path.name}"
        assert "top: 53px" not in html_text, f"Stale top: 53px found in {target_path.name}"
        assert "minmax(0, 0.9fr) minmax(0, 1.1fr)" in html_text
        assert html_text.index("</header>") < html_text.index('data-slot="sidebar-wrapper"'), (
            f".app-shell must appear after </header> in {target_path.name}"
        )
        for snippet in REQUIRED_SHELL_SNIPPETS:
            assert snippet in html_text, f"Missing {snippet!r} in {target_path.name}"


PHASE3_REQUIRED_SNIPPETS = (
    "do-this-card",
    "media-card-list",
    "SPINE #",
    "header .view-tabs { display: none; }",
    "@media (max-width: 1279px)",
    ".header-aux-link { display: none !important; }",
    'class="nav-doc-btn header-aux-link"',
    'id="tabMap"',
    'id="tabSkills"',
    'id="tabSeams"',
    "<span>🗺️ Map</span>",
    "<span>🧩 Seams</span>",
    "const HASH_SLUG_RE = /^[a-z0-9-]+$/;",
    "decodeURIComponent",
    "window.history.replaceState",
    "window.applyHashRoute = function(rawHash)",
    "window.closeSkillModal = function()",
    'window.addEventListener("hashchange"',
    ".media-thumb--orchestrator { border-color: var(--ccba-gold); }",
    ".media-thumb--kernel { border-color: var(--ccba-primary); }",
    ".media-thumb--guide { border-color: var(--ccba-accent); }",
)


def test_phase3_map_a2_scoped_header_and_safe_hash_router() -> None:
    """Verify Phase 3 Grok conditions: COND-MAP-A2, COND-HEADER-CSS, COND-HASH-SAFE, and E."""
    for target_path in (TEMPLATE_HTML_PATH, DOCS_DIR / "index.html"):
        html_text = target_path.read_text(encoding="utf-8")
        for forbidden in (
            ".spine-chain",
            ".spine-node",
            ".spine-sep",
            ".guides-row",
            ".guide-pill",
            "scrollWidth",
        ):
            assert forbidden not in html_text, f"Forbidden {forbidden!r} in {target_path.name}"
        m_desktop = re.search(
            r"@media\s*\(min-width:\s*1024px\)\s*\{(.*?)\n\s*\}", html_text, re.DOTALL
        )
        assert m_desktop is not None, f"Missing @media (min-width: 1024px) in {target_path.name}"
        assert "header .view-tabs { display: none; }" in m_desktop.group(1)
        for snippet in PHASE3_REQUIRED_SNIPPETS:
            assert snippet in html_text, f"Missing Phase 3 {snippet!r} in {target_path.name}"


PHASE4_OPERATE_MODE_SNIPPETS = (
    '"Be Vietnam Pro"',
    '"JetBrains Mono"',
    "font-variant-numeric: tabular-nums;",
    ":focus-visible {",
    "overscroll-behavior: contain;",
    "content-visibility: auto;",
    'role="dialog" aria-modal="true" aria-labelledby="modalTitle"',
    'aria-label="Đóng hộp thoại"',
    "function normalizeVi(str)",
    "function buildSkillsHash()",
    "function buildSeamsHash()",
    "window.resetSkillsFilter = function()",
    "window.clearSeamFilter = function()",
    'id="skillsEmptyState"',
    'id="seamSearchInput"',
)


def test_phase4_operate_mode_and_ccba_design_compliance() -> None:
    """Verify Phase 4 ccba-design v2.3.0 Operate-Mode, WCAG 2.2, and Surgical Refactor invariants."""
    for target_path in (TEMPLATE_HTML_PATH, DOCS_DIR / "index.html"):
        html_text = target_path.read_text(encoding="utf-8")
        for snippet in PHASE4_OPERATE_MODE_SNIPPETS:
            assert snippet in html_text, f"Missing Phase 4 {snippet!r} in {target_path.name}"
        assert 'style="' not in html_text, f"Inline style attribute found in {target_path.name}"
        style_block = html_text.split("<style>", 1)[1].split("</style>", 1)[0]
        assert "#viewMap .hero" in style_block
        assert "@media (max-width: 959px)" in style_block
        assert "@media (max-width: 767px)" in style_block
        assert ".brand-title" in style_block
        assert ".nav-label-desktop" in style_block
        font_sizes = re.findall(r"font-size:\s*([^;]+);", style_block)
        assert font_sizes, f"No font-size declarations found in {target_path.name}"
        for fs in font_sizes:
            assert fs.strip().startswith("var(--ccba-text-"), (
                f"Un-tokenized font-size {fs!r} in {target_path.name}"
            )
        radii = re.findall(r"border-radius:\s*([^;]+);", style_block)
        assert radii, f"No border-radius declarations found in {target_path.name}"
        for br in radii:
            assert br.strip().startswith("var(--ccba-radius-"), (
                f"Un-tokenized border-radius {br!r} in {target_path.name}"
            )
        route_fn = html_text.split("window.applyHashRoute = function(rawHash)", 1)[1].split(
            "window.setSkillsDisplayMode", 1
        )[0]
        assert route_fn.index('indexOf("?")') < route_fn.index("decodeURIComponent("), (
            f"applyHashRoute must split '?' before decodeURIComponent in {target_path.name}"
        )


PHASE4C_AND_NOXON_SNIPPETS = (
    'id="seamsEmptyState"',
    'class="spine-stepper"',
    'class="do-this-row"',
    'class="do-this-copy-btn font-mono"',
    'class="goal-guides-drawer"',
    "Copy Brief cho Agent",
    "prefers-reduced-motion: reduce",
    "overflow-wrap: anywhere;",
    "minmax(min(100%, 330px), 1fr)",
    "min-width: min(100%, 240px);",
    "html:has(.modal-backdrop.open)",
    "html:has(.app-sidebar.mobile-open)",
    'aria-current="step"',
    "nav-label-mobile",
    "!skillModal.contains(document.activeElement)",
    ".jump-card:last-child:nth-child(odd) { grid-column: 1 / -1; }",
)


def test_phase4c_mobile_overflow_and_noxon_invariants() -> None:
    """Verify Phase 4C mobile cascade, overflow guards, chip contrast, and Noxon N1-N3 patterns."""
    for target_path in (TEMPLATE_HTML_PATH, DOCS_DIR / "index.html"):
        html_text = target_path.read_text(encoding="utf-8")
        for snippet in PHASE4C_AND_NOXON_SNIPPETS:
            assert snippet in html_text, f"Missing Phase 4C/Noxon {snippet!r} in {target_path.name}"
        style_block = html_text.split("<style>", 1)[1].split("</style>", 1)[0]
        base_chips_idx = style_block.index(".portal-chips {")
        late_mobile_idx = style_block.rindex("@media (max-width: 767px)")
        assert late_mobile_idx > base_chips_idx, (
            f"Late @media (max-width: 767px) must appear after .portal-chips in {target_path.name}"
        )
        chip_active_block = style_block.split(".chip.active {", 1)[1].split("}", 1)[0]
        assert "background: var(--ccba-fg-body);" in chip_active_block
        assert "color: var(--ccba-bg);" in chip_active_block

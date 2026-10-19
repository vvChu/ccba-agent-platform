#!/usr/bin/env python3
"""audit_skills_hygiene.py - Comprehensive Skill Hygiene & Governance Standards Auditor (HUB-ADR-0058).

Graduated official governance tool checking CCBA Hub skills against:
1. Frontmatter SSOT: metadata.version, metadata.author (mandatory), valid YAML.
2. Clean Dead Wood: strictly forbids ClaudeKit remnants (/ck:*, /ultrathink, git-manager, <tasks>, TaskCreate...).
3. ADR-0057 Directory Hygiene: forbids stray root .md files outside references/, forbids non-.md files in references/.
4. Level 3 Progressive Disclosure: enforces Level 3 Reference Index table and 100% coverage via direct links or router INDEX.md.
5. Windows PowerShell Compatibility: detects bashisms (export VAR=, sudo apt, bare grep, 2>/dev/null, xargs, $(...)).
6. Safe Headless Process Invocation: Start-Process requires try/catch fallback blocks.
7. Relative Link Integrity: forbids broken relative links in references/ ([SKILL.md](SKILL.md)).

Zero external dependencies outside Python stdlib and PyYAML.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = HUB_ROOT / ".agents" / "skills"
PORTALS_FILE = HUB_ROOT / "docs" / "skills" / "portals.yaml"
DEFAULT_REPORT_MD = HUB_ROOT / ".md" / "scratch" / "skills_audit_report.md"

RE_DEAD_WOOD: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"/ck:[a-zA-Z0-9_\-]+"), "ClaudeKit Command (/ck:*)"),
    (re.compile(r"/ultrathink\b"), "ClaudeKit Command (/ultrathink)"),
    (re.compile(r"\bgit-manager\b"), "ClaudeKit Tool (git-manager)"),
    (re.compile(r"</?tasks\b[^>]*>"), "Claude Tasks XML tag (<tasks>)"),
    (
        re.compile(r"\b(TaskCreate|TaskUpdate|TaskList|TaskGet|TaskComplete|TaskDelete)\b"),
        "Claude Native Tasks (TaskCreate/Update/List)",
    ),
    (re.compile(r"\bAskUserQuestion\b"), "Claude Tool (AskUserQuestion)"),
    (re.compile(r"\bcode-reviewer\.md\b"), "Missing ClaudeKit Template (code-reviewer.md)"),
    (re.compile(r"\bcodebase-summary\.md\b"), "Missing ClaudeKit File (codebase-summary.md)"),
    (
        re.compile(r"<!--\s*Ratchet Optimization Refinement"),
        "Ratchet Optimization Junk Comment (ADR-0058)",
    ),
]

RE_BASHISMS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bexport\s+[A-Za-z_][A-Za-z0-9_]*="),
        "Bashism environment export (export VAR=...)",
    ),
    (re.compile(r"\bsudo\s+apt(?:-get)?\b"), "Linux package manager invocation (sudo apt/apt-get)"),
    (re.compile(r"(?<!git\s)(?<!git-)(?<!--)\bgrep\s+-[a-zA-Z]"), "Bashism grep flag (grep -*)"),
    (
        re.compile(
            r"(?<!git\s)(?<!git-)(?<!--)(?:\|\s*grep\b|(?<!\w)grep\s+(?:-[a-zA-Z0-9]+\s+)*[\"']?[a-zA-Z0-9_\-*+^$]+)"
        ),
        "Bashism bare grep invocation",
    ),
    (re.compile(r"\bawk\s+['\"]"), "Bashism awk execution"),
    (re.compile(r"\bhead\s+-[0-9n]"), "Bashism head command"),
    (re.compile(r"2>/dev/null"), "Bashism error redirection (2>/dev/null)"),
    (re.compile(r"\bxargs\b"), "Bashism xargs invocation (xargs)"),
    (re.compile(r"\$\([^)\r\n]+\)"), "Bashism command substitution $(...)"),
]

RE_START_PROCESS = re.compile(r"\bStart-Process\b")
RE_BROKEN_SKILL_LINK = re.compile(r"\[([^\]]+)\]\((SKILL\.md)\)")
RE_LEVEL3_HEADER = re.compile(
    r"##\s+(?:Progressive Disclosure|Reference Index|Tài liệu Tham Chiếu|Bảng Tham Chiếu)",
    re.IGNORECASE,
)

BENIGN_GREP_PATTERNS = (
    "git grep",
    "--grep",
    "grep_search",
    "semgrep",
    "Semgrep",
    "ripgrep",
    "Ripgrep",
    "(Select-String / grep)",
    "single grep",
    "`grep` the prefix",
    "`grep`/`view_file`",
    "Grep tham chiếu",
    "Grep nhân vật",
    "grep for",
    "grep +",
)

PORTALS_ORDER = (
    "init_navigation",
    "core_engineering",
    "bim_aiqc",
    "legal_compliance",
    "governance_upkeep",
)


def is_start_process_protected(text: str, match_start: int, match_end: int) -> bool:
    """Check if a Start-Process invocation is wrapped inside a safe try { ... } catch block."""
    before = text[:match_start]
    try_matches = list(re.finditer(r"\btry\s*\{", before))
    if not try_matches:
        return False
    between_try = text[try_matches[-1].end() : match_start]
    if between_try.count("{") < between_try.count("}"):
        return False
    after = text[match_end:]
    catch_match = re.search(r"\}\s*catch\b", after)
    if not catch_match:
        return False
    between_catch = after[: catch_match.start()]
    net_open = between_try.count("{") - between_try.count("}")
    net_close = between_catch.count("}") - between_catch.count("{")
    return net_open == net_close


def _seed_direct_reference_coverage(
    l3_text: str, ref_dir: Path, ref_files: list[Path]
) -> tuple[set[Path], set[Path]]:
    """Identifies directly referenced files and top-level INDEX.md routers in Level 3 section."""
    covered_files: set[Path] = set()
    covered_routers: set[Path] = set()
    for rf in ref_files:
        rel_to_ref = rf.relative_to(ref_dir).as_posix()
        is_direct = (rel_to_ref in l3_text) or (f"references/{rel_to_ref}" in l3_text)
        if not is_direct and rf.name == "INDEX.md":
            parent_rel = rf.parent.relative_to(ref_dir).as_posix()
            if parent_rel != ".":
                tokens = (
                    parent_rel,
                    f"{parent_rel}/",
                    f"references/{parent_rel}",
                    f"references/{parent_rel}/",
                )
                is_direct = any(tok in l3_text for tok in tokens)
            elif "references/" in l3_text or "references/INDEX.md" in l3_text:
                is_direct = True
        if is_direct:
            covered_files.add(rf)
            if rf.name == "INDEX.md":
                covered_routers.add(rf)
    return covered_files, covered_routers


def resolve_uncovered_references(
    skill_content: str, ref_dir: Path, ref_files: list[Path]
) -> list[str]:
    """Resolve full coverage of reference files via Level 3 index and deep router INDEX.md files."""
    l3_match = RE_LEVEL3_HEADER.search(skill_content)
    l3_text = skill_content[l3_match.start() :] if l3_match is not None else skill_content
    covered_files, covered_routers = _seed_direct_reference_coverage(l3_text, ref_dir, ref_files)

    changed = True
    while changed:
        changed = False
        for router in list(covered_routers):
            try:
                router_text = router.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for rf in ref_files:
                if rf not in covered_files and rf != router:
                    try:
                        rf_rel = rf.relative_to(router.parent).as_posix()
                    except ValueError:
                        continue
                    if rf_rel in router_text or rf.name in router_text:
                        covered_files.add(rf)
                        changed = True
                        if rf.name == "INDEX.md":
                            covered_routers.add(rf)

    return sorted(rf.relative_to(ref_dir).as_posix() for rf in ref_files if rf not in covered_files)


@dataclass
class Issue:
    """Represents a detected governance or hygiene violation."""

    severity: str
    category: str
    file_rel: str
    line_no: int
    detail: str


@dataclass
class SkillAuditResult:
    """Audit result for an individual agent skill."""

    name: str
    portal_id: str
    portal_name: str
    version: str = "N/A"
    author: str = "N/A"
    tier: str = "N/A"
    bundle: str = "N/A"
    num_references: int = 0
    has_level3_index: bool = False
    issues: list[Issue] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Calculate overall status: RED if critical issues, YELLOW if warnings, else GREEN."""
        if any(i.severity == "RED" for i in self.issues):
            return "RED"
        if any(i.severity == "YELLOW" for i in self.issues):
            return "YELLOW"
        return "GREEN"


def load_portals(
    portals_path: Path | None = None,
) -> tuple[dict[str, tuple[str, str]], dict[str, str]]:
    """Load portal navigation taxonomy from portals.yaml."""
    path = portals_path or PORTALS_FILE
    skill_to_portal: dict[str, tuple[str, str]] = {}
    portal_names: dict[str, str] = {}
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for p in data.get("portals", []):
                pid = p["id"]
                pname = p.get("name", pid)
                portal_names[pid] = pname
                for sname in p.get("skills", []):
                    skill_to_portal[sname] = (pid, pname)
        except Exception:
            pass
    return skill_to_portal, portal_names


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from document header."""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) >= 3:
        try:
            parsed = yaml.safe_load(parts[1])
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _check_directory_hygiene(
    skill_dir: Path, sname: str, ref_dir: Path, result: SkillAuditResult
) -> None:
    """Validates ADR-0057 directory hygiene (no stray root .md, no non-.md in references/)."""
    try:
        dir_items = sorted(skill_dir.iterdir(), key=lambda p: p.name.lower())
    except Exception:
        dir_items = []
    for item in dir_items:
        if item.is_file() and item.suffix.lower() == ".md" and item.name != "SKILL.md":
            result.issues.append(
                Issue(
                    "RED",
                    "Directory Hygiene (ADR-0057)",
                    f"{sname}/{item.name}",
                    1,
                    f"Stray markdown file at skill root: {item.name}. Must be moved to references/.",
                )
            )
    if ref_dir.is_dir():
        for item in sorted(ref_dir.rglob("*"), key=lambda p: p.as_posix()):
            if item.is_file() and item.suffix.lower() != ".md":
                rel_ref = item.relative_to(skill_dir).as_posix()
                result.issues.append(
                    Issue(
                        "RED",
                        "Directory Hygiene (ADR-0057)",
                        f"{sname}/{rel_ref}",
                        1,
                        f"Non-markdown file in references/: {item.name}. Must be moved to resources/ or scripts/.",
                    )
                )


def _check_frontmatter_metadata(skill_content: str, sname: str, result: SkillAuditResult) -> None:
    """Validates SKILL.md YAML frontmatter and mandatory metadata.version / metadata.author."""
    rel = f"{sname}/SKILL.md"
    if not skill_content.startswith("---"):
        result.issues.append(
            Issue("RED", "Governance Metadata", rel, 1, "Missing YAML frontmatter in SKILL.md")
        )
        fm: dict[str, Any] = {}
    else:
        fm = parse_frontmatter(skill_content)
        if not fm:
            result.issues.append(
                Issue(
                    "RED",
                    "Governance Metadata",
                    rel,
                    1,
                    "Invalid or empty YAML frontmatter in SKILL.md",
                )
            )

    meta = fm.get("metadata", {})
    if isinstance(meta, dict):
        result.version = str(meta.get("version", "N/A"))
        result.author = str(meta.get("author", "N/A"))
    result.tier = str(fm.get("tier", "N/A"))
    result.bundle = str(fm.get("bundle", "N/A"))

    if result.version in ("N/A", "None", ""):
        result.issues.append(
            Issue(
                "YELLOW",
                "Governance Metadata",
                rel,
                1,
                "Missing metadata.version in frontmatter",
            )
        )
    if result.author in ("N/A", "None", ""):
        result.issues.append(
            Issue(
                "RED",
                "Governance Metadata",
                rel,
                1,
                "Missing or empty metadata.author in frontmatter (mandatory)",
            )
        )


def _check_level3_index(
    skill_content: str,
    sname: str,
    ref_dir: Path,
    ref_files: list[Path],
    result: SkillAuditResult,
) -> None:
    """Checks Level 3 Reference Index presence and full reference coverage."""
    if result.num_references == 0:
        return
    has_index = bool(
        RE_LEVEL3_HEADER.search(skill_content)
        or ("references/" in skill_content and "| :---" in skill_content)
    )
    result.has_level3_index = has_index
    rel = f"{sname}/SKILL.md"
    last_line = len(skill_content.splitlines())
    if not has_index:
        result.issues.append(
            Issue(
                "YELLOW",
                "Progressive Disclosure",
                rel,
                last_line,
                f"Has {result.num_references} reference files but lacks Level 3 Reference Index in SKILL.md",
            )
        )
        return
    uncovered = resolve_uncovered_references(skill_content, ref_dir, ref_files)
    if uncovered:
        suffix = f" (+{len(uncovered) - 3} more)" if len(uncovered) > 3 else ""
        result.issues.append(
            Issue(
                "YELLOW",
                "Progressive Disclosure",
                rel,
                last_line,
                f"Reference files not indexed in Level 3 table: {', '.join(uncovered[:3])}{suffix}",
            )
        )


def _scan_bashisms_in_lines(lines: list[str], rel_path: str, result: SkillAuditResult) -> None:
    """Scans markdown lines for Windows PowerShell incompatible bashisms outside Linux code fences."""
    in_code_fence = False
    is_linux_fence = False
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code_fence:
                in_code_fence, is_linux_fence = False, False
            else:
                in_code_fence = True
                lang = stripped[3:].strip().lower()
                is_linux_fence = any(
                    k in lang for k in ("linux", "ubuntu", "bash (linux)", "sh (linux)")
                )
            continue
        if in_code_fence and is_linux_fence:
            continue
        is_table_row = stripped.startswith("|") and stripped.endswith("|")
        for pattern, label in RE_BASHISMS:
            if "grep" in label.lower():
                if any(benign in line for benign in BENIGN_GREP_PATTERNS):
                    continue
                if is_table_row and "`grep" not in stripped:
                    continue
            if pattern.search(line):
                result.issues.append(
                    Issue(
                        "RED",
                        "Windows Bashism",
                        rel_path,
                        idx,
                        f"Found {label}: `{stripped[:60]}`",
                    )
                )


def _scan_markdown_file(
    md_file: Path, sname: str, skill_dir: Path, result: SkillAuditResult
) -> None:
    """Scans a single markdown file for broken links, dead wood, bashisms, and unsafe Start-Process."""
    rel_path = f"{sname}/{md_file.relative_to(skill_dir).as_posix()}"
    text = md_file.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    if "references" in md_file.parts:
        for idx, line in enumerate(lines, start=1):
            if RE_BROKEN_SKILL_LINK.search(line):
                result.issues.append(
                    Issue(
                        "RED",
                        "Relative Link Broken",
                        rel_path,
                        idx,
                        "Broken link [SKILL.md](SKILL.md) in references/. Must be [SKILL.md](../SKILL.md).",
                    )
                )

    for pattern, label in RE_DEAD_WOOD:
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                result.issues.append(
                    Issue(
                        "RED",
                        "Dead Wood Remnant",
                        rel_path,
                        idx,
                        f"Found {label}: `{line.strip()[:60]}`",
                    )
                )

    _scan_bashisms_in_lines(lines, rel_path, result)

    for match in RE_START_PROCESS.finditer(text):
        if not is_start_process_protected(text, match.start(), match.end()):
            line_no = text[: match.start()].count("\n") + 1
            result.issues.append(
                Issue(
                    "RED",
                    "Safe Headless Process",
                    rel_path,
                    line_no,
                    "Start-Process without try/catch fallback block. May fail in headless/CI environment.",
                )
            )


def audit_skill(
    skill_dir: Path,
    skill_to_portal: dict[str, tuple[str, str]] | None = None,
    hub_root: Path | None = None,
) -> SkillAuditResult:
    """Audit a single skill directory against full CCBA hygiene standards."""
    _ = hub_root
    sname = skill_dir.name
    portal_map = skill_to_portal if skill_to_portal is not None else {}
    portal_id, portal_name = portal_map.get(sname, ("unknown", "Chưa phân loại"))
    result = SkillAuditResult(name=sname, portal_id=portal_id, portal_name=portal_name)

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        result.issues.append(
            Issue("RED", "Directory Hygiene (ADR-0057)", sname, 0, "Missing SKILL.md")
        )
        return result

    ref_dir = skill_dir / "references"
    ref_files = (
        sorted(ref_dir.glob("**/*.md"), key=lambda p: p.as_posix()) if ref_dir.is_dir() else []
    )
    result.num_references = len(ref_files)

    _check_directory_hygiene(skill_dir, sname, ref_dir, result)
    skill_content = skill_md.read_text(encoding="utf-8", errors="replace")
    _check_frontmatter_metadata(skill_content, sname, result)
    _check_level3_index(skill_content, sname, ref_dir, ref_files, result)

    for md_file in sorted(skill_dir.rglob("*.md"), key=lambda p: p.as_posix()):
        _scan_markdown_file(md_file, sname, skill_dir, result)

    return result


def audit_all_skills(
    hub_root: Path | None = None,
    skills_dir: Path | None = None,
) -> list[SkillAuditResult]:
    """Audit all active skills in the repository."""
    root = hub_root or HUB_ROOT
    s_dir = skills_dir or (root / ".agents" / "skills")
    skill_to_portal, _ = load_portals(root / "docs" / "skills" / "portals.yaml")
    if not s_dir.exists():
        return []
    skill_dirs = sorted(
        [d for d in s_dir.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))],
        key=lambda p: p.name,
    )
    return [audit_skill(d, skill_to_portal, hub_root=root) for d in skill_dirs]


def _render_portal_rows(results: list[SkillAuditResult], p_names: dict[str, str]) -> list[str]:
    """Renders Markdown table rows for the 5 portals breakdown."""
    rows: list[str] = []
    for pid in PORTALS_ORDER:
        pname = p_names.get(pid, pid)
        p_skills = [r for r in results if r.portal_id == pid]
        p_green = sum(1 for r in p_skills if r.status == "GREEN")
        p_yellow = sum(1 for r in p_skills if r.status == "YELLOW")
        p_red = sum(1 for r in p_skills if r.status == "RED")
        priority = (
            "🔴 Cần nâng cấp"
            if p_red > 0
            else ("🟡 Hoàn thiện index" if p_yellow > 0 else "🟢 Rất tốt")
        )
        rows.append(
            f"| **{pname}** (`{pid}`) | {len(p_skills)} | {p_green} | {p_yellow} | {p_red} | {priority} |"
        )
    return rows


def _render_red_and_yellow_sections(
    red_skills: list[SkillAuditResult], yellow_skills: list[SkillAuditResult]
) -> list[str]:
    """Renders Markdown sections 3 (RED skills) and 4 (YELLOW skills)."""
    lines = ["", "---", "", "## 3. Danh Sách Chi Tiết Các Kỹ Năng Nhóm Đỏ (🔴 Cần Nâng Cấp)", ""]
    if not red_skills:
        lines.append("🎉 *Không có kỹ năng nào thuộc Nhóm Đỏ!*")
    for r in red_skills:
        lines.extend(
            [
                f"### 🔴 `{r.name}` (Cổng: {r.portal_name} | v{r.version})",
                f"- **Vị trí:** `.agents/skills/{r.name}/` | **Số file references:** {r.num_references}",
                "- **Các vấn đề phát hiện:**",
                *[
                    f"  - {'❌' if i.severity == 'RED' else '⚠️'} `[{i.category}]` {i.file_rel}:{i.line_no} $\\rightarrow$ {i.detail}"
                    for i in r.issues
                ],
                "",
            ]
        )
    lines.extend(
        ["", "---", "", "## 4. Danh Sách Chi Tiết Các Kỹ Năng Nhóm Vàng (🟡 Cần Hoàn Thiện)", ""]
    )
    if not yellow_skills:
        lines.append("🎉 *Không có kỹ năng nào thuộc Nhóm Vàng!*")
    else:
        lines.extend(
            [
                "| Tên Kỹ Năng | Cổng Điều Hướng | Phiên Bản | References | Vấn Đề Cần Hoàn Thiện |",
                "| :--- | :--- | :---: | :---: | :--- |",
                *[
                    f"| `{r.name}` | {r.portal_name} | v{r.version} | {r.num_references} | {'; '.join(i.detail for i in r.issues)} |"
                    for r in yellow_skills
                ],
            ]
        )
    return lines


def generate_report(
    results: list[SkillAuditResult], portal_names: dict[str, str] | None = None
) -> str:
    """Generate comprehensive Markdown audit report."""
    total = len(results)
    reds = [r for r in results if r.status == "RED"]
    yellows = [r for r in results if r.status == "YELLOW"]
    greens = [r for r in results if r.status == "GREEN"]
    g_pct, y_pct, r_pct = (
        (len(greens) * 100 / total if total else 0.0),
        (len(yellows) * 100 / total if total else 0.0),
        (len(reds) * 100 / total if total else 0.0),
    )
    today = datetime.date.today().isoformat()
    lines = [
        f"# 📊 Báo Cáo Khảo Sát Toàn Diện {total} Skills Nền Tảng CCBA Hub\n",
        f"> **Thời điểm khảo sát:** {today} | **Tổng số kỹ năng active:** {total}",
        "> **Tiêu chuẩn kiểm định:** Clean Dead Wood (KISS), Windows PowerShell Compatibility, ADR-0057 Directory Hygiene, Level 3 Progressive Disclosure, Safe Headless Fallback.\n\n---\n",
        "## 1. Tóm Tắt Tình Trạng Toàn Nền Tảng (Executive Summary)\n",
        "| Phân Nhóm Đánh Giá | Số Lượng Kỹ Năng | Tỷ Lệ | Đánh Giá Tác Động & Trạng Thái |",
        "| :--- | :---: | :---: | :--- |",
        f"| 🟢 **Xanh (Đạt Chuẩn Hoàn Toàn)** | **{len(greens)}** / {total} | {g_pct:.1f}% | 100% tuân thủ ADR-0057, không tàn dư ngoại lai, an toàn Windows PowerShell |",
        f"| 🟡 **Vàng (Cần Hoàn Thiện)** | **{len(yellows)}** / {total} | {y_pct:.1f}% | Thiếu bảng Level 3 Reference Index hoặc thiếu metadata version trong frontmatter |",
        f"| 🔴 **Đỏ (Ưu Tiên Nâng Cấp Ngay)** | **{len(reds)}** / {total} | {r_pct:.1f}% | Chứa tàn dư ClaudeKit, lệnh bash không chạy được trên Windows, hoặc sai cấu trúc thư mục |\n\n---\n",
        "## 2. Thống Kê Theo 5 Cổng Điều Hướng (5 Portals Breakdown)\n",
        "| Cổng Điều Hướng | Tổng Số Skills | 🟢 Xanh | 🟡 Vàng | 🔴 Đỏ | Trạng Thái Ưu Tiên |",
        "| :--- | :---: | :---: | :---: | :---: | :--- |",
        *_render_portal_rows(results, portal_names or {}),
        *_render_red_and_yellow_sections(reds, yellows),
        "\n---\n\n## 5. Danh Sách Các Kỹ Năng Đạt Chuẩn Hoàn Toàn (🟢 Nhóm Xanh)\n",
        "| Tên Kỹ Năng | Cổng Điều Hướng | Phiên Bản | Tier / Bundle | References | Level 3 Index |",
        "| :--- | :--- | :---: | :---: | :---: | :---: |",
        *[
            f"| `{r.name}` | {r.portal_name} | v{r.version} | `{r.tier}` / `{r.bundle}` | {r.num_references} | {'✅ Đã có' if r.has_level3_index or r.num_references == 0 else 'N/A'} |"
            for r in greens
        ],
        "\n---\n*Báo cáo được tạo tự động bởi CCBA Platform Quality Auditor*",
    ]
    return "\n".join(lines)


def _resolve_target_skill_dir(target_path: Path | str, root: Path) -> tuple[bool, Path]:
    """Resolves a file or directory path to its enclosing skill directory, detecting workflows."""
    target = Path(target_path).resolve()
    if "workflows" in target.parts:
        return True, target
    if not target.is_file():
        return False, target
    if target.name.lower() == "skill.md":
        return False, target.parent
    curr = target.parent
    while curr != curr.parent and curr != root:
        if (curr / "SKILL.md").exists():
            return False, curr
        curr = curr.parent
    return False, target.parent


def check_skills_hygiene(
    hub_root: Path | None = None,
    target_path: Path | str | None = None,
) -> tuple[bool, str]:
    """Check skills hygiene across repository or for a single target skill."""
    root = hub_root or HUB_ROOT
    skill_to_portal, _ = load_portals(root / "docs" / "skills" / "portals.yaml")

    if target_path:
        is_wf, skill_dir = _resolve_target_skill_dir(target_path, root)
        if is_wf:
            return True, f"Target '{target_path}' is a workflow; skipped from skill hygiene check."
        if not skill_dir.exists():
            return False, f"Skill target directory does not exist: {skill_dir}"
        result = audit_skill(skill_dir, skill_to_portal, hub_root=root)
        if result.status == "GREEN":
            return True, f"Skill '{result.name}' is 100% compliant with hygiene standards."
        details = [
            f"  - [{i.severity}] [{i.category}] {i.file_rel}:{i.line_no} -> {i.detail}"
            for i in result.issues
        ]
        return (
            False,
            f"Skill '{result.name}' failed hygiene audit ({result.status}):\n" + "\n".join(details),
        )

    results = audit_all_skills(hub_root=root)
    reds = [r for r in results if r.status == "RED"]
    yellows = [r for r in results if r.status == "YELLOW"]
    if not reds and not yellows:
        return (
            True,
            f"All {len(results)} active skill(s) are 100% compliant with hygiene standards.",
        )

    msg_lines = [
        f"Detected {len(reds)} RED and {len(yellows)} YELLOW skill(s) out of {len(results)} total:"
    ]
    for r in (reds + yellows)[:10]:
        msg_lines.append(f"  * {r.name} ({r.status}):")
        for i in r.issues[:3]:
            msg_lines.append(
                f"    - [{i.severity}] [{i.category}] {i.file_rel}:{i.line_no} -> {i.detail}"
            )
    if len(reds) + len(yellows) > 10:
        msg_lines.append(f"  ... and {len(reds) + len(yellows) - 10} more skills with issues.")
    return False, "\n".join(msg_lines)


def _configure_win32_utf8() -> None:
    """Reconfigures stdout and stderr to UTF-8 on Windows platforms."""
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8")
                except Exception:
                    pass


def _build_arg_parser() -> argparse.ArgumentParser:
    """Constructs the CLI argument parser for audit_skills_hygiene."""
    parser = argparse.ArgumentParser(
        description="CCBA Skills Hygiene & Standards Auditor (HUB-ADR-0058)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run audit and return exit code 0 if 100% GREEN, 1 if any RED or YELLOW issues.",
    )
    parser.add_argument(
        "--file", "-f", type=str, default=None, help="Audit a specific skill directory or SKILL.md."
    )
    parser.add_argument(
        "--report", type=str, default=None, help="Path to write detailed markdown report file."
    )
    parser.add_argument(
        "--json", action="store_true", help="Output audit summary and results as JSON to stdout."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print detailed violations for each skill."
    )
    return parser


def _emit_cli_output(
    results: list[SkillAuditResult],
    portal_names: dict[str, str],
    args: argparse.Namespace,
) -> int:
    """Formats and prints CLI output (report file, JSON, or human summary) and returns exit code."""
    if args.report:
        report_path = Path(args.report).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(generate_report(results, portal_names), encoding="utf-8")
        if not args.json:
            print(f"[OK] Markdown report saved to: {report_path}")

    red_count = sum(1 for r in results if r.status == "RED")
    yellow_count = sum(1 for r in results if r.status == "YELLOW")
    green_count = sum(1 for r in results if r.status == "GREEN")
    passed = red_count == 0 and yellow_count == 0

    if args.json:
        summary_data: dict[str, Any] = {
            "total": len(results),
            "red_count": red_count,
            "yellow_count": yellow_count,
            "green_count": green_count,
            "status": "PASS" if passed else "FAIL",
            "skills": [asdict(r) for r in results],
        }
        print(json.dumps(summary_data, indent=2, ensure_ascii=False))
    else:
        print(f"[OK] Audit completed for {len(results)} skill(s).")
        print(f"     [GREEN]  Fully Compliant: {green_count}")
        print(f"     [YELLOW] Need Improvement: {yellow_count}")
        print(f"     [RED]    Critical Upgrades Needed: {red_count}")
        if args.verbose or not passed:
            for r in results:
                if r.status != "GREEN" or args.verbose:
                    icon = "🟢" if r.status == "GREEN" else ("🟡" if r.status == "YELLOW" else "🔴")
                    print(f"\n{icon} Skill: {r.name} (v{r.version}, {r.portal_name})")
                    for i in r.issues:
                        sev = "❌" if i.severity == "RED" else "⚠️"
                        print(f"  {sev} [{i.category}] {i.file_rel}:{i.line_no} -> {i.detail}")

    return (0 if passed else 1) if args.check else 0


def main(argv: list[str] | None = None) -> int:
    """CLI runner for skill hygiene audit tool."""
    _configure_win32_utf8()
    args = _build_arg_parser().parse_args(argv)
    skill_to_portal, portal_names = load_portals()

    if args.file:
        is_wf, skill_dir = _resolve_target_skill_dir(args.file, HUB_ROOT)
        if is_wf:
            if args.json:
                print(
                    json.dumps(
                        {"status": "PASS", "total": 0, "message": "Workflows excluded from audit"}
                    )
                )
            else:
                print(f"[INFO] '{args.file}' is a workflow; excluded from skill hygiene audit.")
            return 0
        if not skill_dir.exists():
            print(f"[ERROR] Target skill directory not found: {skill_dir}", file=sys.stderr)
            return 1
        results = [audit_skill(skill_dir, skill_to_portal)]
    else:
        results = audit_all_skills()

    return _emit_cli_output(results, portal_names, args)


if __name__ == "__main__":
    sys.exit(main())

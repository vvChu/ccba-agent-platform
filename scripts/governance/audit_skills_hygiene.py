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

# ---------------------------------------------------------------------------
# Governance Audit Regex Patterns
# ---------------------------------------------------------------------------

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


def is_start_process_protected(text: str, match_start: int, match_end: int) -> bool:
    """Check if a Start-Process invocation is wrapped inside a safe try { ... } catch block."""
    before = text[:match_start]
    try_matches = list(re.finditer(r"\btry\s*\{", before))
    if not try_matches:
        return False
    last_try = try_matches[-1]
    between_try = text[last_try.end() : match_start]
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


def resolve_uncovered_references(
    skill_content: str,
    ref_dir: Path,
    ref_files: list[Path],
) -> list[str]:
    """Resolve full coverage of reference files via Level 3 index and deep router INDEX.md files.

    Returns:
        list of relative paths (to ref_dir) for any reference files not covered.
    """
    l3_match = RE_LEVEL3_HEADER.search(skill_content)
    l3_text = skill_content[l3_match.start() :] if l3_match is not None else skill_content

    covered_files: set[Path] = set()
    covered_routers: set[Path] = set()

    for rf in ref_files:
        rel_to_ref = rf.relative_to(ref_dir).as_posix()
        is_direct = (rel_to_ref in l3_text) or (f"references/{rel_to_ref}" in l3_text)
        if not is_direct and rf.name == "INDEX.md":
            parent_rel = rf.parent.relative_to(ref_dir).as_posix()
            if parent_rel != ".":
                if (
                    parent_rel in l3_text
                    or f"{parent_rel}/" in l3_text
                    or f"references/{parent_rel}" in l3_text
                    or f"references/{parent_rel}/" in l3_text
                ):
                    is_direct = True
            elif "references/" in l3_text or "references/INDEX.md" in l3_text:
                is_direct = True

        if is_direct:
            covered_files.add(rf)
            if rf.name == "INDEX.md":
                covered_routers.add(rf)

    changed = True
    while changed:
        changed = False
        for router in list(covered_routers):
            try:
                router_text = router.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            router_dir = router.parent
            for rf in ref_files:
                if rf not in covered_files and rf != router:
                    try:
                        rf_rel = rf.relative_to(router_dir).as_posix()
                    except ValueError:
                        continue
                    if rf_rel in router_text or rf.name in router_text:
                        covered_files.add(rf)
                        changed = True
                        if rf.name == "INDEX.md":
                            covered_routers.add(rf)

    return sorted(rf.relative_to(ref_dir).as_posix() for rf in ref_files if rf not in covered_files)


# ---------------------------------------------------------------------------
# Data Transfer Objects
# ---------------------------------------------------------------------------


@dataclass
class Issue:
    """Represents a detected governance or hygiene violation."""

    severity: str  # RED, YELLOW
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


# ---------------------------------------------------------------------------
# Portal & Frontmatter Loaders
# ---------------------------------------------------------------------------


def load_portals(
    portals_path: Path | None = None,
) -> tuple[dict[str, tuple[str, str]], dict[str, str]]:
    """Load portal navigation taxonomy from portals.yaml.

    Returns:
        tuple[skill_to_portal_map, portal_names_map]
    """
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


# ---------------------------------------------------------------------------
# Skill Audit Logic
# ---------------------------------------------------------------------------


def audit_skill(
    skill_dir: Path,
    skill_to_portal: dict[str, tuple[str, str]] | None = None,
    hub_root: Path | None = None,
) -> SkillAuditResult:
    """Audit a single skill directory against full CCBA hygiene standards."""
    sname = skill_dir.name
    portal_map = skill_to_portal if skill_to_portal is not None else {}
    portal_id, portal_name = portal_map.get(sname, ("unknown", "Chưa phân loại"))
    result = SkillAuditResult(name=sname, portal_id=portal_id, portal_name=portal_name)

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        result.issues.append(
            Issue(
                severity="RED",
                category="Directory Hygiene (ADR-0057)",
                file_rel=sname,
                line_no=0,
                detail="Missing SKILL.md",
            )
        )
        return result

    # Check 1: Root stray markdown files
    try:
        dir_items = sorted(skill_dir.iterdir(), key=lambda p: p.name.lower())
    except Exception:
        dir_items = []

    for item in dir_items:
        if item.is_file() and item.suffix.lower() == ".md" and item.name != "SKILL.md":
            result.issues.append(
                Issue(
                    severity="RED",
                    category="Directory Hygiene (ADR-0057)",
                    file_rel=f"{sname}/{item.name}",
                    line_no=1,
                    detail=f"Stray markdown file at skill root: {item.name}. Must be moved to references/.",
                )
            )

    # Count references & Check 2: Non-markdown files inside references/
    ref_dir = skill_dir / "references"
    ref_files = (
        sorted(ref_dir.glob("**/*.md"), key=lambda p: p.as_posix()) if ref_dir.is_dir() else []
    )
    result.num_references = len(ref_files)

    if ref_dir.is_dir():
        for item in sorted(ref_dir.rglob("*"), key=lambda p: p.as_posix()):
            if item.is_file() and item.suffix.lower() != ".md":
                rel_ref_item = item.relative_to(skill_dir).as_posix()
                result.issues.append(
                    Issue(
                        severity="RED",
                        category="Directory Hygiene (ADR-0057)",
                        file_rel=f"{sname}/{rel_ref_item}",
                        line_no=1,
                        detail=f"Non-markdown file in references/: {item.name}. Must be moved to resources/ or scripts/.",
                    )
                )

    # Read SKILL.md and parse frontmatter
    skill_content = skill_md.read_text(encoding="utf-8", errors="replace")
    if not skill_content.startswith("---"):
        result.issues.append(
            Issue(
                severity="RED",
                category="Governance Metadata",
                file_rel=f"{sname}/SKILL.md",
                line_no=1,
                detail="Missing YAML frontmatter in SKILL.md",
            )
        )
        fm = {}
    else:
        fm = parse_frontmatter(skill_content)
        if not fm:
            result.issues.append(
                Issue(
                    severity="RED",
                    category="Governance Metadata",
                    file_rel=f"{sname}/SKILL.md",
                    line_no=1,
                    detail="Invalid or empty YAML frontmatter in SKILL.md",
                )
            )

    meta = fm.get("metadata", {})
    if isinstance(meta, dict):
        result.version = str(meta.get("version", "N/A"))
        result.author = str(meta.get("author", "N/A"))
    result.tier = str(fm.get("tier", "N/A"))
    result.bundle = str(fm.get("bundle", "N/A"))

    # Validate metadata version & author
    if result.version in ("N/A", "None", ""):
        result.issues.append(
            Issue(
                severity="YELLOW",
                category="Governance Metadata",
                file_rel=f"{sname}/SKILL.md",
                line_no=1,
                detail="Missing metadata.version in frontmatter",
            )
        )
    if result.author in ("N/A", "None", ""):
        result.issues.append(
            Issue(
                severity="RED",
                category="Governance Metadata",
                file_rel=f"{sname}/SKILL.md",
                line_no=1,
                detail="Missing or empty metadata.author in frontmatter (mandatory)",
            )
        )

    # Check 3: Level 3 Reference Index & Full Coverage
    if result.num_references > 0:
        has_index = bool(
            RE_LEVEL3_HEADER.search(skill_content)
            or ("references/" in skill_content and "| :---" in skill_content)
        )
        result.has_level3_index = has_index
        if not has_index:
            result.issues.append(
                Issue(
                    severity="YELLOW",
                    category="Progressive Disclosure",
                    file_rel=f"{sname}/SKILL.md",
                    line_no=len(skill_content.splitlines()),
                    detail=f"Has {result.num_references} reference files but lacks Level 3 Reference Index in SKILL.md",
                )
            )
        else:
            uncovered = resolve_uncovered_references(skill_content, ref_dir, ref_files)
            if uncovered:
                result.issues.append(
                    Issue(
                        severity="YELLOW",
                        category="Progressive Disclosure",
                        file_rel=f"{sname}/SKILL.md",
                        line_no=len(skill_content.splitlines()),
                        detail=f"Reference files not indexed in Level 3 table: {', '.join(uncovered[:3])}"
                        + (f" (+{len(uncovered) - 3} more)" if len(uncovered) > 3 else ""),
                    )
                )

    # Scan all markdown files in skill for Dead Wood, Bashisms, Start-Process
    all_md_files = sorted(skill_dir.rglob("*.md"), key=lambda p: p.as_posix())
    for md_file in all_md_files:
        rel_path = f"{sname}/{md_file.relative_to(skill_dir).as_posix()}"
        text = md_file.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()

        # Check 4: Broken links in references/
        if "references" in md_file.parts:
            for idx, line in enumerate(lines, start=1):
                if RE_BROKEN_SKILL_LINK.search(line):
                    result.issues.append(
                        Issue(
                            severity="RED",
                            category="Relative Link Broken",
                            file_rel=rel_path,
                            line_no=idx,
                            detail="Broken link [SKILL.md](SKILL.md) in references/. Must be [SKILL.md](../SKILL.md).",
                        )
                    )

        # Check 5: Clean Dead Wood
        for pattern, label in RE_DEAD_WOOD:
            for idx, line in enumerate(lines, start=1):
                if pattern.search(line):
                    result.issues.append(
                        Issue(
                            severity="RED",
                            category="Dead Wood Remnant",
                            file_rel=rel_path,
                            line_no=idx,
                            detail=f"Found {label}: `{line.strip()[:60]}`",
                        )
                    )

        # Check 6: Windows PowerShell Compatibility (Bashisms)
        in_code_fence = False
        is_linux_fence = False
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                if in_code_fence:
                    in_code_fence = False
                    is_linux_fence = False
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
                            severity="RED",
                            category="Windows Bashism",
                            file_rel=rel_path,
                            line_no=idx,
                            detail=f"Found {label}: `{line.strip()[:60]}`",
                        )
                    )

        # Check 7: Headless Start-Process without try/catch
        for match in RE_START_PROCESS.finditer(text):
            if not is_start_process_protected(text, match.start(), match.end()):
                line_no = text[: match.start()].count("\n") + 1
                result.issues.append(
                    Issue(
                        severity="RED",
                        category="Safe Headless Process",
                        file_rel=rel_path,
                        line_no=line_no,
                        detail="Start-Process without try/catch fallback block. May fail in headless/CI environment.",
                    )
                )

    return result


def audit_all_skills(
    hub_root: Path | None = None,
    skills_dir: Path | None = None,
) -> list[SkillAuditResult]:
    """Audit all active skills in the repository."""
    root = hub_root or HUB_ROOT
    s_dir = skills_dir or (root / ".agents" / "skills")
    portals_path = root / "docs" / "skills" / "portals.yaml"
    skill_to_portal, _ = load_portals(portals_path)

    if not s_dir.exists():
        return []

    skill_dirs = sorted(
        [d for d in s_dir.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))],
        key=lambda p: p.name,
    )

    return [audit_skill(d, skill_to_portal, hub_root=root) for d in skill_dirs]


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------


def generate_report(
    results: list[SkillAuditResult],
    portal_names: dict[str, str] | None = None,
) -> str:
    """Generate comprehensive Markdown audit report."""
    total_skills = len(results)
    red_skills = [r for r in results if r.status == "RED"]
    yellow_skills = [r for r in results if r.status == "YELLOW"]
    green_skills = [r for r in results if r.status == "GREEN"]
    p_names = portal_names or {}

    green_pct = (len(green_skills) * 100 / total_skills) if total_skills else 0.0
    yellow_pct = (len(yellow_skills) * 100 / total_skills) if total_skills else 0.0
    red_pct = (len(red_skills) * 100 / total_skills) if total_skills else 0.0

    lines: list[str] = [
        f"# 📊 Báo Cáo Khảo Sát Toàn Diện {total_skills} Skills Nền Tảng CCBA Hub",
        "",
        f"> **Thời điểm khảo sát:** 2026-09-12 | **Tổng số kỹ năng active:** {total_skills}",
        "> **Tiêu chuẩn kiểm định:** Clean Dead Wood (KISS), Windows PowerShell Compatibility, ADR-0057 Directory Hygiene, Level 3 Progressive Disclosure, Safe Headless Fallback.",
        "",
        "---",
        "",
        "## 1. Tóm Tắt Tình Trạng Toàn Nền Tảng (Executive Summary)",
        "",
        "| Phân Nhóm Đánh Giá | Số Lượng Kỹ Năng | Tỷ Lệ | Đánh Giá Tác Động & Trạng Thái |",
        "| :--- | :---: | :---: | :--- |",
        f"| 🟢 **Xanh (Đạt Chuẩn Hoàn Toàn)** | **{len(green_skills)}** / {total_skills} | {green_pct:.1f}% | 100% tuân thủ ADR-0057, không tàn dư ngoại lai, an toàn Windows PowerShell |",
        f"| 🟡 **Vàng (Cần Hoàn Thiện)** | **{len(yellow_skills)}** / {total_skills} | {yellow_pct:.1f}% | Thiếu bảng Level 3 Reference Index hoặc thiếu metadata version trong frontmatter |",
        f"| 🔴 **Đỏ (Ưu Tiên Nâng Cấp Ngay)** | **{len(red_skills)}** / {total_skills} | {red_pct:.1f}% | Chứa tàn dư ClaudeKit, lệnh bash không chạy được trên Windows, hoặc sai cấu trúc thư mục |",
        "",
        "---",
        "",
        "## 2. Thống Kê Theo 5 Cổng Điều Hướng (5 Portals Breakdown)",
        "",
        "| Cổng Điều Hướng | Tổng Số Skills | 🟢 Xanh | 🟡 Vàng | 🔴 Đỏ | Trạng Thái Ưu Tiên |",
        "| :--- | :---: | :---: | :---: | :---: | :--- |",
    ]

    portals_order = [
        "init_navigation",
        "core_engineering",
        "bim_aiqc",
        "legal_compliance",
        "governance_upkeep",
    ]
    for pid in portals_order:
        pname = p_names.get(pid, pid)
        p_skills = [r for r in results if r.portal_id == pid]
        p_total = len(p_skills)
        p_green = sum(1 for r in p_skills if r.status == "GREEN")
        p_yellow = sum(1 for r in p_skills if r.status == "YELLOW")
        p_red = sum(1 for r in p_skills if r.status == "RED")
        priority = (
            "🔴 Cần nâng cấp"
            if p_red > 0
            else ("🟡 Hoàn thiện index" if p_yellow > 0 else "🟢 Rất tốt")
        )
        lines.append(
            f"| **{pname}** (`{pid}`) | {p_total} | {p_green} | {p_yellow} | {p_red} | {priority} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Danh Sách Chi Tiết Các Kỹ Năng Nhóm Đỏ (🔴 Cần Nâng Cấp)",
            "",
        ]
    )

    if not red_skills:
        lines.append("🎉 *Không có kỹ năng nào thuộc Nhóm Đỏ!*")
    else:
        for r in red_skills:
            lines.append(f"### 🔴 `{r.name}` (Cổng: {r.portal_name} | v{r.version})")
            lines.append(
                f"- **Vị trí:** `.agents/skills/{r.name}/` | **Số file references:** {r.num_references}"
            )
            lines.append("- **Các vấn đề phát hiện:**")
            for issue in r.issues:
                prefix = "❌" if issue.severity == "RED" else "⚠️"
                lines.append(
                    f"  - {prefix} `[{issue.category}]` {issue.file_rel}:{issue.line_no} $\\rightarrow$ {issue.detail}"
                )
            lines.append("")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 4. Danh Sách Chi Tiết Các Kỹ Năng Nhóm Vàng (🟡 Cần Hoàn Thiện)",
            "",
        ]
    )

    if not yellow_skills:
        lines.append("🎉 *Không có kỹ năng nào thuộc Nhóm Vàng!*")
    else:
        lines.append(
            "| Tên Kỹ Năng | Cổng Điều Hướng | Phiên Bản | References | Vấn Đề Cần Hoàn Thiện |"
        )
        lines.append("| :--- | :--- | :---: | :---: | :--- |")
        for r in yellow_skills:
            issues_str = "; ".join(f"{i.detail}" for i in r.issues)
            lines.append(
                f"| `{r.name}` | {r.portal_name} | v{r.version} | {r.num_references} | {issues_str} |"
            )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 5. Danh Sách Các Kỹ Năng Đạt Chuẩn Hoàn Toàn (🟢 Nhóm Xanh)",
            "",
            "| Tên Kỹ Năng | Cổng Điều Hướng | Phiên Bản | Tier / Bundle | References | Level 3 Index |",
            "| :--- | :--- | :---: | :---: | :---: | :---: |",
        ]
    )

    for r in green_skills:
        l3_str = "✅ Đã có" if r.has_level3_index or r.num_references == 0 else "N/A"
        lines.append(
            f"| `{r.name}` | {r.portal_name} | v{r.version} | `{r.tier}` / `{r.bundle}` | {r.num_references} | {l3_str} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 6. Lộ Trình Nâng Cấp Khuyến Nghị (Batch Refactoring Plan)",
            "",
            "Thay vì cập nhật toàn bộ cùng lúc gây vi phạm `simplify_gate` và race condition:",
            "1. **Đợt 1 — Xử lý Nhóm Đỏ (Cụm Kỹ Nghệ & Quản trị):** Xử lý dứt điểm các tàn dư ClaudeKit, bashisms và file root sai vị trí.",
            "2. **Đợt 2 — Bổ sung Level 3 Reference Index cho Nhóm Vàng:** Chèn bảng chỉ mục tham chiếu chi tiết và chuẩn hóa metadata.",
            "3. **Mỗi đợt tuân thủ nghiêm ngặt:** Chạy Recompilation Gate (`compile_catalog.py`, `compile_skills_docs.py --write`), đạt `verify-patch --preset skill` và commit riêng rẽ.",
            "",
            "---",
            "*Báo cáo được tạo tự động bởi CCBA Platform Quality Auditor*",
        ]
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Integrated Governance Hook
# ---------------------------------------------------------------------------


def check_skills_hygiene(
    hub_root: Path | None = None,
    target_path: Path | str | None = None,
) -> tuple[bool, str]:
    """Check skills hygiene across repository or for a single target skill.

    Returns:
        tuple[bool, str]: (is_clean, diagnostic_summary)
    """
    root = hub_root or HUB_ROOT
    portals_path = root / "docs" / "skills" / "portals.yaml"
    skill_to_portal, _ = load_portals(portals_path)

    if target_path:
        target = Path(target_path).resolve()
        if "workflows" in target.parts:
            return True, f"Target '{target_path}' is a workflow; skipped from skill hygiene check."

        if target.is_file():
            if target.name.lower() == "skill.md":
                skill_dir = target.parent
            else:
                curr = target.parent
                found = None
                while curr != curr.parent and curr != root:
                    if (curr / "SKILL.md").exists():
                        found = curr
                        break
                    curr = curr.parent
                skill_dir = found if found else target.parent
        else:
            skill_dir = target

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

    # Workspace-wide audit
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


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI runner for skill hygiene audit tool."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass
        if hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(
        description="CCBA Skills Hygiene & Standards Auditor (HUB-ADR-0058)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run audit and return exit code 0 if 100% GREEN, 1 if any RED or YELLOW issues (default: True).",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        default=None,
        help="Audit a specific skill directory or SKILL.md file path.",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Path to write detailed markdown report file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output audit summary and results as JSON to stdout.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed violations for each skill.",
    )

    args = parser.parse_args(argv)

    skill_to_portal, portal_names = load_portals()

    if args.file:
        target = Path(args.file).resolve()
        if "workflows" in target.parts:
            if args.json:
                print(
                    json.dumps(
                        {"status": "PASS", "total": 0, "message": "Workflows excluded from audit"}
                    )
                )
            else:
                print(f"[INFO] '{args.file}' is a workflow; excluded from skill hygiene audit.")
            return 0

        if target.is_file():
            if target.name.lower() == "skill.md":
                skill_dir = target.parent
            else:
                curr = target.parent
                found = None
                while curr != curr.parent and curr != HUB_ROOT:
                    if (curr / "SKILL.md").exists():
                        found = curr
                        break
                    curr = curr.parent
                skill_dir = found if found else target.parent
        else:
            skill_dir = target

        if not skill_dir.exists():
            print(f"[ERROR] Target skill directory not found: {skill_dir}", file=sys.stderr)
            return 1

        results = [audit_skill(skill_dir, skill_to_portal)]
    else:
        results = audit_all_skills()

    report_md = generate_report(results, portal_names)

    if args.report:
        report_path = Path(args.report).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_md, encoding="utf-8")
        if not args.json:
            print(f"[OK] Markdown report saved to: {report_path}")

    red_count = sum(1 for r in results if r.status == "RED")
    yellow_count = sum(1 for r in results if r.status == "YELLOW")
    green_count = sum(1 for r in results if r.status == "GREEN")

    summary_data: dict[str, Any] = {
        "total": len(results),
        "red_count": red_count,
        "yellow_count": yellow_count,
        "green_count": green_count,
        "status": "PASS" if all(r.status == "GREEN" for r in results) else "FAIL",
        "skills": [asdict(r) for r in results],
    }

    if args.json:
        print(json.dumps(summary_data, indent=2, ensure_ascii=False))
    else:
        print(f"[OK] Audit completed for {len(results)} skill(s).")
        print(f"     [GREEN]  Fully Compliant: {green_count}")
        print(f"     [YELLOW] Need Improvement: {yellow_count}")
        print(f"     [RED]    Critical Upgrades Needed: {red_count}")

        if args.verbose or red_count > 0 or yellow_count > 0:
            for r in results:
                if r.status != "GREEN" or args.verbose:
                    icon = "🟢" if r.status == "GREEN" else ("🟡" if r.status == "YELLOW" else "🔴")
                    print(f"\n{icon} Skill: {r.name} (v{r.version}, {r.portal_name})")
                    for issue in r.issues:
                        sev_icon = "❌" if issue.severity == "RED" else "⚠️"
                        print(
                            f"  {sev_icon} [{issue.category}] {issue.file_rel}:{issue.line_no} -> {issue.detail}"
                        )

    if args.check:
        return 0 if summary_data["status"] == "PASS" else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

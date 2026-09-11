"""sync_hub_adr_matrix.py - Hub ADR Matrix Compiler & Living Traceability Engine.

Two-Tier Architecture Matrix Engine:
- Tier 1: Platform Constitution (Hub ADRs)
- Tier 2: Domain-Specific Architecture Decisions (Spoke ADRs)
- Non-Destructive Section Preservation for custom Spoke notes & audits.
- Living Skill Radar & Cross-Reference Tracker across skills, workflows, and core docs.

Conforms to: ADR 0032, ADR 0037, ADR 0047, ADR 0051.
Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(line_buffering=True, encoding="utf-8")

HUB_REPO_URL = "https://github.com/vvChu/ccba-agent-platform"


def parse_adr_file(adr_path: Path) -> dict[str, Any]:
    """Extract metadata from an ADR markdown file supporting YAML frontmatter and H1 fallback.

    Args:
        adr_path: Path to the ADR markdown file.

    Returns:
        Dictionary containing num, num_str, title, filename, status, date, and path.
    """
    content = adr_path.read_text(encoding="utf-8")

    fm_data: dict[str, Any] = {}
    body_content = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                loaded = yaml.safe_load(parts[1])
                if isinstance(loaded, dict):
                    fm_data = loaded
                    body_content = parts[2]
            except Exception:
                pass

    # 1. Number extraction
    adr_num = 0
    if "id" in fm_data:
        m = re.search(r"0*([0-9]+)", str(fm_data["id"]))
        if m:
            adr_num = int(m.group(1))

    if adr_num == 0:
        h1_match = re.search(
            r"^#\s*(?:HUB-ADR|HUB_ADR|ADR)?[-\s]*0*([0-9]+)[:\s\.\-]+(.*)$",
            body_content,
            re.MULTILINE | re.IGNORECASE,
        )
        if h1_match:
            adr_num = int(h1_match.group(1))
        else:
            fname_match = re.match(
                r"^(?:HUB-ADR-)?0*([0-9]+)-(.*)\.md$", adr_path.name, re.IGNORECASE
            )
            if fname_match:
                adr_num = int(fname_match.group(1))

    # 2. Title extraction
    adr_title = ""
    if "title" in fm_data and fm_data["title"]:
        adr_title = str(fm_data["title"]).strip()
    else:
        h1_match = re.search(
            r"^#\s*(?:HUB-ADR|HUB_ADR|ADR)?[-\s]*(?:0*[0-9]+[:\s\.\-]+|[:\s\.\-]+)?(.*)$",
            body_content,
            re.MULTILINE | re.IGNORECASE,
        )
        if h1_match and h1_match.group(1).strip():
            adr_title = h1_match.group(1).strip()
        else:
            fname_match = re.match(
                r"^(?:HUB-ADR-)?0*([0-9]+)-(.*)\.md$", adr_path.name, re.IGNORECASE
            )
            if fname_match:
                adr_title = fname_match.group(2).replace("-", " ").title()
            else:
                adr_title = adr_path.stem

    # 3. Status extraction
    status = "ACCEPTED"
    if "status" in fm_data and fm_data["status"]:
        raw_status = str(fm_data["status"]).upper().strip()
        if "SUPERSEDED" in raw_status:
            status = "SUPERSEDED"
        elif "DEPRECATED" in raw_status:
            status = "DEPRECATED"
        elif "PROPOSED" in raw_status or "DRAFT" in raw_status:
            status = "PROPOSED"
        else:
            status = "ACCEPTED"
    else:
        # Check standard markdown patterns
        status_match = re.search(
            r"(?:##\s*(?:1\.\s*)?Trạng Thái\s*\(Status\)|\*?\s*\*\*\s*Status:\s*\*\*|\*?\s*\*\*\s*Trạng Thái\s*\(Status\)\s*\*\*|##\s*Status)\s*\n?\s*\*?\*?([A-Za-z_ ]+)",
            content,
            re.IGNORECASE,
        )
        if status_match:
            raw_s = status_match.group(1).upper().strip()
            if "SUPERSEDED" in raw_s:
                status = "SUPERSEDED"
            elif "DEPRECATED" in raw_s:
                status = "DEPRECATED"
            elif "PROPOSED" in raw_s or "DRAFT" in raw_s:
                status = "PROPOSED"
            else:
                status = "ACCEPTED"
        elif "DEPRECATED" in content[:600].upper():
            status = "DEPRECATED"
        elif "SUPERSEDED" in content[:600].upper():
            status = "SUPERSEDED"

    # 4. Date extraction
    date_str = ""
    if "date" in fm_data and fm_data["date"]:
        date_str = str(fm_data["date"]).strip()
    else:
        date_match = re.search(r"\b(202[0-9]-[0-1][0-9]-[0-3][0-9])\b", content)
        if date_match:
            date_str = date_match.group(1)

    return {
        "num": adr_num,
        "num_str": f"{adr_num:04d}",
        "title": adr_title,
        "filename": adr_path.name,
        "status": status,
        "date": date_str,
        "path": adr_path,
        "content": content,
    }


def scan_skill_radar(
    adr_list: list[dict[str, Any]],
    search_root: Path,
    extra_roots: list[Path] | None = None,
    is_hub: bool = True,
    strict_hub_prefix: bool = False,
) -> dict[str, list[dict[str, str]]]:
    """Scan all SKILL.md, AGENTS.md, CONTEXT.md, and docs to detect ADR references.

    Args:
        adr_list: List of ADR dictionaries.
        search_root: Primary directory to search.
        extra_roots: Optional additional directories to search.
        is_hub: Whether scanning for Hub platform ADRs (True) or Spoke domain ADRs (False).
        strict_hub_prefix: If True, only match HUB-ADR-XXXX / HUB_ADR-XXXX, ignoring bare ADR references (essential when scanning Spoke directories for Hub ADRs to avoid collision with Spoke domain ADRs).

    Returns:
        Mapping from ADR num_str to list of referencing files.
    """
    matrix: dict[str, list[dict[str, str]]] = {a["num_str"]: [] for a in adr_list}
    all_roots = [search_root]
    if extra_roots:
        all_roots.extend(extra_roots)

    target_paths: list[Path] = []
    for r in all_roots:
        if not r.exists():
            continue

        # 1. Skills
        skills_dir = r / ".agents" / "skills"
        if skills_dir.exists():
            target_paths.extend(sorted(skills_dir.glob("**/SKILL.md")))

        # 2. Workflows
        wf_dir = r / ".agents" / "workflows"
        if wf_dir.exists():
            target_paths.extend(sorted(wf_dir.glob("*.md")))

        # 3. Core markdown files
        for core_f in [
            "AGENTS.md",
            "CONTEXT.md",
            ".agents/AGENTS.md",
            ".md/knowledge/session_learnings.md",
        ]:
            p = r / core_f
            if p.exists() and p not in target_paths:
                target_paths.append(p)

        # 4. Monorepo packages AGENTS.md
        packages_dir = r / "packages"
        if packages_dir.exists():
            target_paths.extend(sorted(packages_dir.glob("*/AGENTS.md")))

    # Regex to match ADR references
    if not is_hub:
        # In Spoke mode scanning domain ADRs: strictly exclude HUB-ADR-XXXX
        ref_pattern = re.compile(r"(?<!HUB-)(?<!HUB_)\bADR[-\s]*0*([0-9]+)\b", re.IGNORECASE)
    elif strict_hub_prefix:
        # In Spoke context scanning Hub ADRs: strictly require HUB-ADR / HUB_ADR prefix to prevent collisions with bare ADRs
        ref_pattern = re.compile(r"\b(?:HUB-ADR|HUB_ADR)[-\s]*0*([0-9]+)\b", re.IGNORECASE)
    else:
        # In Hub repository: matches HUB-ADR-0010, HUB_ADR-0010, or legacy ADR-0010 for backward compatibility
        ref_pattern = re.compile(r"\b(?:HUB-ADR|HUB_ADR|ADR)[-\s]*0*([0-9]+)\b", re.IGNORECASE)

    for doc_path in target_paths:
        try:
            text = doc_path.read_text(encoding="utf-8")
        except Exception:
            continue

        # Relative path representation
        try:
            rel_path = str(doc_path.relative_to(search_root)).replace("\\", "/")
        except ValueError:
            rel_path = doc_path.name

        matches = ref_pattern.findall(text)
        for m in matches:
            try:
                num = int(m)
                num_str = f"{num:04d}"
                if num_str in matrix:
                    existing_files = [item["file"] for item in matrix[num_str]]
                    if rel_path not in existing_files:
                        matrix[num_str].append({"file": rel_path})
            except ValueError:
                continue

    return matrix


def extract_preserved_sections(existing_content: str) -> str:
    """Extract custom sections from existing TRACEABILITY_MATRIX.md to preserve them.

    Supports explicit marker <!-- CUSTOM_SECTIONS_START --> or auto-captures
    custom H2 sections outside auto-generated tables.

    Args:
        existing_content: Existing file content.

    Returns:
        String of preserved custom content.
    """
    if not existing_content.strip():
        return ""

    # 1. Explicit marker check
    marker_match = re.search(
        r"<!--\s*CUSTOM_SECTIONS_START\s*-->\s*(.*?)\s*<!--\s*CUSTOM_SECTIONS_END\s*-->",
        existing_content,
        re.DOTALL | re.IGNORECASE,
    )
    if marker_match:
        return marker_match.group(1).strip()

    # 2. Auto-capture heuristic: find H2s not belonging to generated tables
    generated_markers = [
        "Tier 1",
        "Tier 2",
        "Platform Constitution",
        "Domain-Specific",
        "Living Architecture",
        "Danh Mục",
        "CCBA Platform",
        "Architectural Decisions",
    ]
    lines = existing_content.splitlines()
    custom_lines: list[str] = []
    capture = False
    for line in lines:
        if line.startswith("## "):
            if any(marker in line for marker in generated_markers):
                capture = False
            else:
                capture = True
        if capture:
            custom_lines.append(line)

    return "\n".join(custom_lines).strip()


def compile_hub_adr_readme(adr_list: list[dict[str, Any]], target_file: Path) -> str:
    """Generate docs/adr/README.md for Hub."""
    if not adr_list:
        return ""

    first_num = adr_list[0]["num_str"]
    last_num = adr_list[-1]["num_str"]

    lines = [
        "# 🏛️ CCBA Agent Services Platform — Architectural Decision Records (ADRs)",
        "",
        "Tài liệu này lưu trữ toàn bộ các Quyết định Kiến trúc (ADRs) định hình nền tảng **CCBA Agent Services Platform (Hub)**, bao gồm Skills Framework, AI Gateway, Monorepo Packages, Governance, và Hub-Spoke Ecosystem.",
        "",
        "*(Tệp này được biên dịch tự động bởi `scripts/sync_hub_adr_matrix.py` — Không chỉnh sửa thủ công)*",
        "",
        "---",
        "",
        f"## 📑 Danh Mục Quyết Định Kiến Trúc ({first_num} — {last_num})",
        "",
        "| Mã ADR | Tiêu đề | Trạng thái |",
        "| :--- | :--- | :---: |",
    ]

    for adr in adr_list:
        status_icon = "✅ ACCEPTED" if adr["status"] == "ACCEPTED" else f"⚠️ {adr['status']}"
        lines.append(
            f"| [HUB-ADR {adr['num_str']}]({adr['filename']}) | {adr['title']} | {status_icon} |"
        )

    lines.append("")
    new_content = "\n".join(lines).strip() + "\n"
    if str(target_file) and str(target_file) != ".":
        target_file.write_text(new_content, encoding="utf-8")
    return new_content


def compile_hub_traceability_matrix(
    adr_list: list[dict[str, Any]],
    matrix: dict[str, list[dict[str, str]]],
    target_file: Path,
    preserved_content: str = "",
) -> str:
    """Generate docs/adr/TRACEABILITY_MATRIX.md for Hub.

    Args:
        adr_list: Hub Platform ADRs.
        matrix: Skill radar mapping.
        target_file: Output path.
        preserved_content: Custom preserved content.

    Returns:
        Generated content.
    """
    lines = [
        "# 🗺️ Living Architecture Traceability Matrix & Skill Radar",
        "",
        "> **Mục tiêu:** Ma trận tự động theo dõi mối quan hệ giữa các **Quyết định Kiến trúc (ADR)** và các **Kỹ năng (Skills) / Hiến pháp Vận hành**.",
        "",
        "*(Tệp này được biên dịch tự động bởi `scripts/sync_hub_adr_matrix.py` — Không chỉnh sửa thủ công)*",
        "",
        "---",
        "",
        "## 🏛️ CCBA Platform Architectural Decisions",
        "",
        "| Mã ADR | Tiêu đề Quyết Định | Trạng thái | Tài Liệu & Skills Đang Tuân Thủ / Viện Dẫn |",
        "| :--- | :--- | :---: | :--- |",
    ]

    for adr in adr_list:
        num_str = adr["num_str"]
        refs = matrix.get(num_str, [])
        status_icon = "✅ ACCEPTED" if adr["status"] == "ACCEPTED" else f"⚠️ {adr['status']}"
        if refs:
            ref_links = "<br>".join([f"`{r['file']}`" for r in refs])
        else:
            ref_links = "*Chưa có liên kết trực tiếp*"

        lines.append(
            f"| [HUB-ADR {num_str}]({adr['filename']}) | **{adr['title']}** | {status_icon} | {ref_links} |"
        )

    lines.append("")

    if preserved_content:
        lines.append("---")
        lines.append("")
        lines.append("<!-- CUSTOM_SECTIONS_START -->")
        lines.append(preserved_content)
        lines.append("<!-- CUSTOM_SECTIONS_END -->")
        lines.append("")

    new_content = "\n".join(lines).strip() + "\n"
    if str(target_file) and str(target_file) != ".":
        target_file.write_text(new_content, encoding="utf-8")
    return new_content


def compile_two_tier_adr_matrix(
    hub_adrs: list[dict[str, Any]],
    spoke_adrs: list[dict[str, Any]],
    hub_matrix: dict[str, list[dict[str, str]]],
    spoke_matrix: dict[str, list[dict[str, str]]],
    target_file: Path,
    preserved_content: str = "",
) -> str:
    """Generate docs/adr/TRACEABILITY_MATRIX.md for Spoke with Two-Tier Architecture.

    Tier 1: Platform Constitution (Hub ADRs)
    Tier 2: Domain-Specific Architecture Decisions (Spoke ADRs)
    Preserves any existing Spoke custom sections.

    Args:
        hub_adrs: Platform ADRs from Hub.
        spoke_adrs: Domain ADRs from Spoke.
        hub_matrix: Skill radar mapping for Hub ADRs.
        spoke_matrix: Skill radar mapping for Spoke ADRs.
        target_file: Output path.
        preserved_content: Custom content to preserve.

    Returns:
        Generated content.
    """
    lines = [
        "# 🗺️ Living Architecture Traceability Matrix & Skill Radar",
        "",
        "> **Mục tiêu:** Ma trận tự động theo dõi mối quan hệ giữa các **Quyết định Kiến trúc (ADR)** và các **Kỹ năng (Skills) / Hiến pháp Vận hành**.",
        "",
        "*(Tệp này được biên dịch tự động bởi `scripts/sync_hub_adr_matrix.py` — Cơ chế Two-Tier Preservation)*",
        "",
        "---",
        "",
        "## 🏛️ Tier 1 — Platform Constitution (Hub ADRs)",
        "",
        f"> Các quyết định kiến trúc nền tảng dùng chung được đồng bộ từ Central Hub ([{HUB_REPO_URL}]({HUB_REPO_URL})).",
        "",
        "| Mã ADR | Tiêu đề Quyết Định | Trạng thái | Tài Liệu & Skills Đang Tuân Thủ / Viện Dẫn |",
        "| :--- | :--- | :---: | :--- |",
    ]

    for adr in hub_adrs:
        num_str = adr["num_str"]
        refs = hub_matrix.get(num_str, [])
        status_icon = "✅ ACCEPTED" if adr["status"] == "ACCEPTED" else f"⚠️ {adr['status']}"
        if refs:
            ref_links = "<br>".join([f"`{r['file']}`" for r in refs])
        else:
            ref_links = "*Chưa có liên kết trực tiếp*"

        hub_adr_url = f"{HUB_REPO_URL}/blob/main/docs/adr/{adr['filename']}"
        lines.append(
            f"| [HUB-ADR {num_str}]({hub_adr_url}) | **{adr['title']}** | {status_icon} | {ref_links} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🌐 Tier 2 — Domain-Specific Architecture Decisions (Spoke ADRs)")
    lines.append("")
    lines.append(
        "> Các quyết định kiến trúc nghiệp vụ đặc thù được ban hành và quản trị độc lập tại Spoke."
    )
    lines.append("")
    lines.append(
        "| Mã ADR | Tiêu đề Quyết Định | Trạng thái | Tài Liệu & Skills Đang Tuân Thủ / Viện Dẫn |"
    )
    lines.append("| :--- | :--- | :---: | :--- |")

    for adr in spoke_adrs:
        num_str = adr["num_str"]
        refs = spoke_matrix.get(num_str, [])
        status_icon = "✅ ACCEPTED" if adr["status"] == "ACCEPTED" else f"⚠️ {adr['status']}"
        if refs:
            ref_links = "<br>".join([f"`{r['file']}`" for r in refs])
        else:
            ref_links = "*Chưa có liên kết trực tiếp*"

        lines.append(
            f"| [Domain ADR {num_str}]({adr['filename']}) | **{adr['title']}** | {status_icon} | {ref_links} |"
        )

    lines.append("")

    if preserved_content:
        lines.append("---")
        lines.append("")
        lines.append("<!-- CUSTOM_SECTIONS_START -->")
        lines.append(preserved_content)
        lines.append("<!-- CUSTOM_SECTIONS_END -->")
        lines.append("")

    new_content = "\n".join(lines).strip() + "\n"
    if str(target_file) and str(target_file) != ".":
        target_file.write_text(new_content, encoding="utf-8")
    return new_content


def detect_environment(root_dir: Path) -> tuple[str, Path, Path | None]:
    """Detect whether current root_dir is Hub or Spoke.

    Returns:
        Tuple of (mode: "hub" | "spoke", hub_path: Path, spoke_path: Path | None)
    """
    # 1. Primary Invariant (AGENTS.md): Identify via git remote get-url origin
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(root_dir),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and "ccba-agent-platform" in res.stdout:
            return "hub", root_dir, None
    except Exception:
        pass

    # 2. Check workspace_context.yaml
    ws_context = root_dir / ".md" / "workspace_context.yaml"
    if ws_context.exists():
        try:
            cfg = yaml.safe_load(ws_context.read_text(encoding="utf-8"))
            if isinstance(cfg, dict):
                if cfg.get("project", {}).get("name") == "ccba-agent-platform":
                    return "hub", root_dir, None
                if "hub_path" in cfg:
                    hub_val = Path(cfg["hub_path"])
                    if hub_val.resolve() != root_dir.resolve() and hub_val.exists():
                        return "spoke", hub_val.resolve(), root_dir
        except Exception:
            pass

    # 3. Check for core hub markers
    if (root_dir / "packages" / "ccba-ai").exists() and (
        root_dir / "scripts" / "sync_spoke.py"
    ).exists():
        return "hub", root_dir, None

    return "spoke", root_dir, root_dir


def load_adrs_from_dir(adr_dir: Path) -> list[dict[str, Any]]:
    """Load and parse all ADR markdown files in a directory."""
    if not adr_dir.exists():
        return []
    adr_files = sorted(
        [f for f in adr_dir.glob("*.md") if f.name not in ("README.md", "TRACEABILITY_MATRIX.md")]
    )
    adr_list = [parse_adr_file(f) for f in adr_files]
    adr_list = [a for a in adr_list if a["num"] > 0]
    adr_list.sort(key=lambda x: x["num"])
    return adr_list


def run_pipeline(
    hub_dir: Path,
    spoke_dir: Path | None = None,
    check_mode: bool = False,
    dry_run: bool = False,
) -> bool:
    """Run ADR Matrix compilation pipeline.

    Args:
        hub_dir: Path to Central Hub root.
        spoke_dir: Optional path to Spoke root.
        check_mode: If True, do not modify files, return False if changes detected.
        dry_run: If True, preview generated content without writing.

    Returns:
        True if successful / clean, False if check failed or error occurred.
    """
    is_spoke_mode = spoke_dir is not None and spoke_dir.resolve() != hub_dir.resolve()
    target_root = spoke_dir if is_spoke_mode and spoke_dir else hub_dir
    target_adr_dir = target_root / "docs" / "adr"

    if not target_adr_dir.exists():
        if dry_run or check_mode:
            print(f"[ERROR] Target ADR directory not found at: {target_adr_dir}")
            return False
        target_adr_dir.mkdir(parents=True, exist_ok=True)

    hub_adr_dir = hub_dir / "docs" / "adr"
    hub_adrs = load_adrs_from_dir(hub_adr_dir)

    all_in_sync = True

    if not is_spoke_mode:
        # =====================================================================
        # HUB MODE EXECUTION
        # =====================================================================
        print(f"[sync_hub_adr_matrix] Running in HUB mode ({len(hub_adrs)} ADRs found)")

        # 1. README.md
        readme_path = hub_adr_dir / "README.md"
        existing_readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
        first_num = hub_adrs[0]["num_str"] if hub_adrs else "0001"
        last_num = hub_adrs[-1]["num_str"] if hub_adrs else "0001"

        readme_lines = [
            "# 🏛️ CCBA Agent Services Platform — Architectural Decision Records (ADRs)",
            "",
            "Tài liệu này lưu trữ toàn bộ các Quyết định Kiến trúc (ADRs) định hình nền tảng **CCBA Agent Services Platform (Hub)**, bao gồm Skills Framework, AI Gateway, Monorepo Packages, Governance, và Hub-Spoke Ecosystem.",
            "",
            "*(Tệp này được biên dịch tự động bởi `scripts/sync_hub_adr_matrix.py` — Không chỉnh sửa thủ công)*",
            "",
            "---",
            "",
            f"## 📑 Danh Mục Quyết Định Kiến Trúc ({first_num} — {last_num})",
            "",
            "| Mã ADR | Tiêu đề | Trạng thái |",
            "| :--- | :--- | :---: |",
        ]
        for adr in hub_adrs:
            status_icon = "✅ ACCEPTED" if adr["status"] == "ACCEPTED" else f"⚠️ {adr['status']}"
            readme_lines.append(
                f"| [HUB-ADR {adr['num_str']}]({adr['filename']}) | {adr['title']} | {status_icon} |"
            )
        readme_lines.append("")
        new_readme = "\n".join(readme_lines).strip() + "\n"

        if check_mode:
            if existing_readme != new_readme:
                print(f"[FAIL] {readme_path} is out of sync!")
                diff = difflib.unified_diff(
                    existing_readme.splitlines(keepends=True),
                    new_readme.splitlines(keepends=True),
                    fromfile="existing",
                    tofile="expected",
                )
                sys.stdout.writelines(diff)
                all_in_sync = False
            else:
                print(f"[PASS] {readme_path} is in sync.")
        elif not dry_run:
            readme_path.write_text(new_readme, encoding="utf-8")
            print(f"[sync_hub_adr_matrix] Updated {readme_path}")
        else:
            print(f"[DRY-RUN] Would update {readme_path} ({len(hub_adrs)} ADRs)")

        # 2. TRACEABILITY_MATRIX.md
        matrix_path = hub_adr_dir / "TRACEABILITY_MATRIX.md"
        existing_matrix = matrix_path.read_text(encoding="utf-8") if matrix_path.exists() else ""
        preserved = extract_preserved_sections(existing_matrix)

        radar = scan_skill_radar(hub_adrs, hub_dir, is_hub=True)
        new_matrix = compile_hub_traceability_matrix(
            hub_adrs, radar, matrix_path if not (dry_run or check_mode) else Path(""), preserved
        )

        if check_mode:
            if existing_matrix != new_matrix:
                print(f"[FAIL] {matrix_path} is out of sync!")
                diff = difflib.unified_diff(
                    existing_matrix.splitlines(keepends=True),
                    new_matrix.splitlines(keepends=True),
                    fromfile="existing",
                    tofile="expected",
                )
                sys.stdout.writelines(diff)
                all_in_sync = False
            else:
                print(f"[PASS] {matrix_path} is in sync.")
        elif not dry_run:
            matrix_path.write_text(new_matrix, encoding="utf-8")
            print(f"[sync_hub_adr_matrix] Updated {matrix_path}")
        else:
            print(f"[DRY-RUN] Would update {matrix_path}")

    else:
        # =====================================================================
        # SPOKE MODE EXECUTION (Two-Tier Preservation)
        # =====================================================================
        assert spoke_dir is not None
        spoke_adr_dir = spoke_dir / "docs" / "adr"
        spoke_adrs = load_adrs_from_dir(spoke_adr_dir)

        print(
            f"[sync_hub_adr_matrix] Running in SPOKE mode (Hub: {len(hub_adrs)} ADRs, Spoke: {len(spoke_adrs)} Domain ADRs)"
        )

        matrix_path = spoke_adr_dir / "TRACEABILITY_MATRIX.md"
        existing_matrix = matrix_path.read_text(encoding="utf-8") if matrix_path.exists() else ""
        preserved = extract_preserved_sections(existing_matrix)

        # Radar scanning across Spoke and Hub
        spoke_radar = scan_skill_radar(spoke_adrs, spoke_dir, is_hub=False)
        hub_radar = scan_skill_radar(
            hub_adrs, spoke_dir, extra_roots=[hub_dir], is_hub=True, strict_hub_prefix=True
        )

        new_matrix = compile_two_tier_adr_matrix(
            hub_adrs,
            spoke_adrs,
            hub_radar,
            spoke_radar,
            matrix_path if not (dry_run or check_mode) else Path(""),
            preserved,
        )

        if check_mode:
            if existing_matrix != new_matrix:
                print(f"[FAIL] {matrix_path} is out of sync!")
                diff = difflib.unified_diff(
                    existing_matrix.splitlines(keepends=True),
                    new_matrix.splitlines(keepends=True),
                    fromfile="existing",
                    tofile="expected",
                )
                sys.stdout.writelines(diff)
                all_in_sync = False
            else:
                print(f"[PASS] {matrix_path} is in sync.")
        elif not dry_run:
            matrix_path.write_text(new_matrix, encoding="utf-8")
            print(f"[sync_hub_adr_matrix] Updated Spoke Two-Tier Matrix: {matrix_path}")
        else:
            print(f"[DRY-RUN] Would update Spoke Two-Tier Matrix: {matrix_path}")

    return all_in_sync


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CCBA ADR Matrix Compiler & Living Traceability Engine (ADR 0037, ADR 0051)"
    )
    parser.add_argument(
        "--hub-dir",
        type=Path,
        default=None,
        help="Path to Central Hub root directory.",
    )
    parser.add_argument(
        "--spoke-dir",
        type=Path,
        default=None,
        help="Path to Spoke root directory (enables Two-Tier Spoke mode).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI Gate mode: check if README and TRACEABILITY_MATRIX are in sync without writing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview generated files without modifying files on disk.",
    )

    args = parser.parse_args()

    root_dir = Path.cwd()
    detected_mode, detected_hub, detected_spoke = detect_environment(root_dir)

    hub_dir = args.hub_dir or detected_hub
    spoke_dir = args.spoke_dir or (detected_spoke if detected_mode == "spoke" else None)

    success = run_pipeline(
        hub_dir=hub_dir,
        spoke_dir=spoke_dir,
        check_mode=args.check,
        dry_run=args.dry_run,
    )

    if args.check and not success:
        sys.exit(1)


if __name__ == "__main__":
    main()

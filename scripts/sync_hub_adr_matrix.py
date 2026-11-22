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
import os
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


def _normalize_adr_status(raw_status: str) -> str:
    """Map raw status string to canonical ACCEPTED/SUPERSEDED/DEPRECATED/PROPOSED."""
    upper = raw_status.upper().strip()
    if "SUPERSEDED" in upper:
        return "SUPERSEDED"
    if "DEPRECATED" in upper:
        return "DEPRECATED"
    if "PROPOSED" in upper or "DRAFT" in upper:
        return "PROPOSED"
    return "ACCEPTED"


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

    fname_match = re.match(r"^(?:HUB-ADR-)?0*([0-9]+)-(.*)\.md$", adr_path.name, re.IGNORECASE)

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
        elif fname_match:
            adr_num = int(fname_match.group(1))

    # 2. Title extraction
    if "title" in fm_data and fm_data["title"]:
        adr_title = str(fm_data["title"]).strip()
    else:
        h1_title = re.search(
            r"^#\s*(?:HUB-ADR|HUB_ADR|ADR)?[-\s]*(?:0*[0-9]+[:\s\.\-]+|[:\s\.\-]+)?(.*)$",
            body_content,
            re.MULTILINE | re.IGNORECASE,
        )
        if h1_title and h1_title.group(1).strip():
            adr_title = h1_title.group(1).strip()
        elif fname_match:
            adr_title = fname_match.group(2).replace("-", " ").title()
        else:
            adr_title = adr_path.stem

    # 3. Status extraction
    status = "ACCEPTED"
    if "status" in fm_data and fm_data["status"]:
        status = _normalize_adr_status(str(fm_data["status"]))
    else:
        status_match = re.search(
            r"(?:##\s*(?:1\.\s*)?Trạng Thái\s*\(Status\)|\*?\s*\*\*\s*Status:\s*\*\*|\*?\s*\*\*\s*Trạng Thái\s*\(Status\)\s*\*\*|##\s*Status)\s*\n?\s*\*?\*?([A-Za-z_ ]+)",
            content,
            re.IGNORECASE,
        )
        if status_match:
            status = _normalize_adr_status(status_match.group(1))
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


def get_tracked_files(root: Path) -> set[Path] | None:
    """Retrieve the set of git-tracked files in root if inside a git repository.

    Returns:
        Set of resolved Paths for tracked files, or None if git is unavailable or not a repo.
    """
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        return {(root / line.strip()).resolve() for line in res.stdout.splitlines() if line.strip()}
    except Exception:
        return None


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
        tracked_files = get_tracked_files(r)

        # 1. Skills
        skills_dir = r / ".agents" / "skills"
        if skills_dir.exists():
            for p in sorted(skills_dir.glob("**/SKILL.md")):
                if tracked_files is None or p.resolve() in tracked_files:
                    target_paths.append(p)

        # 2. Workflows
        wf_dir = r / ".agents" / "workflows"
        if wf_dir.exists():
            for p in sorted(wf_dir.glob("*.md")):
                if tracked_files is None or p.resolve() in tracked_files:
                    target_paths.append(p)

        # 3. Core markdown files
        for core_f in [
            "AGENTS.md",
            "CONTEXT.md",
            ".agents/AGENTS.md",
            ".md/knowledge/session_learnings.md",
        ]:
            p = r / core_f
            if p.exists() and p not in target_paths:
                if tracked_files is None or p.resolve() in tracked_files:
                    target_paths.append(p)

        # 4. Monorepo packages AGENTS.md
        packages_dir = r / "packages"
        if packages_dir.exists():
            for p in sorted(packages_dir.glob("*/AGENTS.md")):
                if tracked_files is None or p.resolve() in tracked_files:
                    target_paths.append(p)

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


def _render_adr_table_rows(
    adr_list: list[dict[str, Any]],
    matrix: dict[str, list[dict[str, str]]],
    *,
    label_prefix: str,
    url_prefix: str = "",
) -> list[str]:
    """Render markdown table rows for an ADR traceability matrix section."""
    rows: list[str] = []
    for adr in adr_list:
        num_str = adr["num_str"]
        refs = matrix.get(num_str, [])
        status_icon = "✅ ACCEPTED" if adr["status"] == "ACCEPTED" else f"⚠️ {adr['status']}"
        ref_links = (
            "<br>".join(f"`{r['file']}`" for r in refs) if refs else "*Chưa có liên kết trực tiếp*"
        )
        href = f"{url_prefix}{adr['filename']}"
        rows.append(
            f"| [{label_prefix} {num_str}]({href}) | **{adr['title']}** | {status_icon} | {ref_links} |"
        )
    return rows


def _finalize_matrix_doc(lines: list[str], preserved_content: str, target_file: Path) -> str:
    """Append preserved custom sections, normalize trailing newline, and optionally write target_file."""
    if preserved_content:
        lines.extend(
            [
                "---",
                "",
                "<!-- CUSTOM_SECTIONS_START -->",
                preserved_content,
                "<!-- CUSTOM_SECTIONS_END -->",
                "",
            ]
        )
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
    """Generate docs/adr/TRACEABILITY_MATRIX.md for Hub."""
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
        *_render_adr_table_rows(adr_list, matrix, label_prefix="HUB-ADR"),
        "",
    ]
    return _finalize_matrix_doc(lines, preserved_content, target_file)


def compile_two_tier_adr_matrix(
    hub_adrs: list[dict[str, Any]],
    spoke_adrs: list[dict[str, Any]],
    hub_matrix: dict[str, list[dict[str, str]]],
    spoke_matrix: dict[str, list[dict[str, str]]],
    target_file: Path,
    preserved_content: str = "",
) -> str:
    """Generate Two-Tier TRACEABILITY_MATRIX.md for Spoke preserving custom sections."""
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
        *_render_adr_table_rows(
            hub_adrs,
            hub_matrix,
            label_prefix="HUB-ADR",
            url_prefix=f"{HUB_REPO_URL}/blob/main/docs/adr/",
        ),
        "",
        "---",
        "",
        "## 🌐 Tier 2 — Domain-Specific Architecture Decisions (Spoke ADRs)",
        "",
        "> Các quyết định kiến trúc nghiệp vụ đặc thù được ban hành và quản trị độc lập tại Spoke.",
        "",
        "| Mã ADR | Tiêu đề Quyết Định | Trạng thái | Tài Liệu & Skills Đang Tuân Thủ / Viện Dẫn |",
        "| :--- | :--- | :---: | :--- |",
        *_render_adr_table_rows(spoke_adrs, spoke_matrix, label_prefix="Domain ADR"),
        "",
    ]
    return _finalize_matrix_doc(lines, preserved_content, target_file)


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

    # 2. Check CCBA_HUB_PATH environment variable
    env_hub = os.environ.get("CCBA_HUB_PATH")
    if env_hub:
        env_cand = Path(env_hub)
        if not env_cand.is_absolute():
            env_cand = (root_dir / env_cand).resolve()
        else:
            env_cand = env_cand.resolve()
        if env_cand.exists() and env_cand != root_dir.resolve():
            return "spoke", env_cand, root_dir

    # 3. Check workspace_context.yaml
    ws_context = root_dir / ".md" / "workspace_context.yaml"
    if ws_context.exists():
        try:
            cfg = yaml.safe_load(ws_context.read_text(encoding="utf-8"))
            if isinstance(cfg, dict):
                if cfg.get("project", {}).get("name") == "ccba-agent-platform":
                    return "hub", root_dir, None
                hub_path_val = cfg.get("hub_path") or cfg.get("project", {}).get("hub_path")
                if isinstance(hub_path_val, dict):
                    os_key = "windows" if sys.platform == "win32" else "linux"
                    hub_path_val = hub_path_val.get(os_key) or hub_path_val.get("posix")
                if hub_path_val and isinstance(hub_path_val, str):
                    hub_cand = Path(hub_path_val)
                    if not hub_cand.is_absolute():
                        hub_cand = (root_dir / hub_cand).resolve()
                    else:
                        hub_cand = hub_cand.resolve()
                    if hub_cand.exists() and hub_cand != root_dir.resolve():
                        return "spoke", hub_cand, root_dir
        except Exception:
            pass

    # 4. Check for core hub markers
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


def resolve_target_adr_dir(
    target_root: Path,
    is_spoke_mode: bool,
    adr_dir: Path | None = None,
) -> Path | None:
    """Resolve the target ADR directory for Hub or Spoke without creating orphan folders.

    Args:
        target_root: Repository root directory.
        is_spoke_mode: Whether running in Spoke mode.
        adr_dir: Optional explicit ADR directory override (absolute or relative to target_root).

    Returns:
        Resolved Path if explicit or auto-detected, or None in Spoke mode when neither
        ``docs/adr`` nor ``.md/adr`` exists.
    """
    if adr_dir is not None:
        return adr_dir if adr_dir.is_absolute() else (target_root / adr_dir)
    if not is_spoke_mode:
        return target_root / "docs" / "adr"

    docs_adr = target_root / "docs" / "adr"
    if docs_adr.is_dir():
        return docs_adr
    md_adr = target_root / ".md" / "adr"
    if md_adr.is_dir():
        return md_adr
    return None


def _sync_output_file(
    target_path: Path,
    existing: str,
    new_content: str,
    *,
    check_mode: bool,
    dry_run: bool,
    dry_run_msg: str,
    update_msg: str,
) -> bool:
    """Check, dry-run, or write a compiled ADR documentation artifact."""
    if check_mode:
        if existing != new_content:
            print(f"[FAIL] {target_path} is out of sync!")
            diff = difflib.unified_diff(
                existing.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile="existing",
                tofile="expected",
            )
            sys.stdout.writelines(diff)
            return False
        print(f"[PASS] {target_path} is in sync.")
        return True
    if dry_run:
        print(dry_run_msg)
        return True
    target_path.write_text(new_content, encoding="utf-8")
    print(update_msg)
    return True


def _ensure_target_adr_dir(
    target_root: Path,
    is_spoke_mode: bool,
    adr_dir: Path | None,
    check_mode: bool,
    dry_run: bool,
    create_adr_dir: bool,
) -> tuple[Path | None, bool]:
    """Resolve and validate target ADR directory; returns (resolved_dir, should_continue)."""
    target_adr_dir = resolve_target_adr_dir(target_root, is_spoke_mode, adr_dir=adr_dir)
    if target_adr_dir is None:
        if dry_run or check_mode:
            print(
                f"[ERROR] Target ADR directory not found (checked docs/adr and .md/adr) under: {target_root}"
            )
            return None, False
        if create_adr_dir:
            target_adr_dir = target_root / "docs" / "adr"
            target_adr_dir.mkdir(parents=True, exist_ok=True)
            return target_adr_dir, True
        print(
            f"[WARN] Target ADR directory not found (checked docs/adr and .md/adr) under: {target_root} — skipping without creating orphan directory."
        )
        return None, True
    if not target_adr_dir.exists():
        if dry_run or check_mode:
            print(f"[ERROR] Target ADR directory not found at: {target_adr_dir}")
            return None, False
        if is_spoke_mode and not create_adr_dir:
            print(
                f"[ERROR] Specified ADR directory not found at: {target_adr_dir} (pass --create-adr-dir to initialize)."
            )
            return None, False
        target_adr_dir.mkdir(parents=True, exist_ok=True)
    return target_adr_dir, True


def run_pipeline(
    hub_dir: Path,
    spoke_dir: Path | None = None,
    check_mode: bool = False,
    dry_run: bool = False,
    adr_dir: Path | None = None,
    create_adr_dir: bool = False,
) -> bool:
    """Run ADR Matrix compilation pipeline.

    Args:
        hub_dir: Path to Central Hub root.
        spoke_dir: Optional path to Spoke root.
        check_mode: If True, do not modify files, return False if changes detected.
        dry_run: If True, preview generated content without writing.
        adr_dir: Optional explicit ADR directory override.
        create_adr_dir: If True, allow creating missing target ADR directory.

    Returns:
        True if successful / clean, False if check failed or error occurred.
    """
    is_spoke_mode = spoke_dir is not None and spoke_dir.resolve() != hub_dir.resolve()
    target_root = spoke_dir if is_spoke_mode and spoke_dir else hub_dir
    target_adr_dir, ok = _ensure_target_adr_dir(
        target_root, is_spoke_mode, adr_dir, check_mode, dry_run, create_adr_dir
    )
    if target_adr_dir is None:
        return ok

    hub_adr_dir = hub_dir / "docs" / "adr"
    hub_adrs = load_adrs_from_dir(hub_adr_dir)
    all_in_sync = True

    if not is_spoke_mode:
        print(f"[sync_hub_adr_matrix] Running in HUB mode ({len(hub_adrs)} ADRs found)")
        readme_path = hub_adr_dir / "README.md"
        existing_readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
        new_readme = compile_hub_adr_readme(hub_adrs, Path(""))
        all_in_sync &= _sync_output_file(
            readme_path,
            existing_readme,
            new_readme,
            check_mode=check_mode,
            dry_run=dry_run,
            dry_run_msg=f"[DRY-RUN] Would update {readme_path} ({len(hub_adrs)} ADRs)",
            update_msg=f"[sync_hub_adr_matrix] Updated {readme_path}",
        )

        matrix_path = hub_adr_dir / "TRACEABILITY_MATRIX.md"
        existing_matrix = matrix_path.read_text(encoding="utf-8") if matrix_path.exists() else ""
        preserved = extract_preserved_sections(existing_matrix)
        radar = scan_skill_radar(hub_adrs, hub_dir, is_hub=True)
        new_matrix = compile_hub_traceability_matrix(hub_adrs, radar, Path(""), preserved)
        all_in_sync &= _sync_output_file(
            matrix_path,
            existing_matrix,
            new_matrix,
            check_mode=check_mode,
            dry_run=dry_run,
            dry_run_msg=f"[DRY-RUN] Would update {matrix_path}",
            update_msg=f"[sync_hub_adr_matrix] Updated {matrix_path}",
        )
    else:
        assert spoke_dir is not None
        spoke_adrs = load_adrs_from_dir(target_adr_dir)
        print(
            f"[sync_hub_adr_matrix] Running in SPOKE mode (Hub: {len(hub_adrs)} ADRs, Spoke: {len(spoke_adrs)} Domain ADRs)"
        )
        matrix_path = target_adr_dir / "TRACEABILITY_MATRIX.md"
        existing_matrix = matrix_path.read_text(encoding="utf-8") if matrix_path.exists() else ""
        preserved = extract_preserved_sections(existing_matrix)
        spoke_radar = scan_skill_radar(spoke_adrs, spoke_dir, is_hub=False)
        hub_radar = scan_skill_radar(
            hub_adrs, spoke_dir, extra_roots=[hub_dir], is_hub=True, strict_hub_prefix=True
        )
        new_matrix = compile_two_tier_adr_matrix(
            hub_adrs, spoke_adrs, hub_radar, spoke_radar, Path(""), preserved
        )
        all_in_sync &= _sync_output_file(
            matrix_path,
            existing_matrix,
            new_matrix,
            check_mode=check_mode,
            dry_run=dry_run,
            dry_run_msg=f"[DRY-RUN] Would update Spoke Two-Tier Matrix: {matrix_path}",
            update_msg=f"[sync_hub_adr_matrix] Updated Spoke Two-Tier Matrix: {matrix_path}",
        )

    return all_in_sync


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for sync_hub_adr_matrix."""
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
        "--adr-dir",
        type=Path,
        default=None,
        help="Optional explicit ADR directory override (defaults to auto-detect docs/adr or .md/adr on Spoke).",
    )
    parser.add_argument(
        "--create-adr-dir",
        action="store_true",
        help="Explicitly create target ADR directory if missing.",
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
    return parser


def main() -> None:
    """CLI entrypoint for ADR Matrix compilation."""
    args = _build_arg_parser().parse_args()

    root_dir = Path.cwd()
    detected_mode, detected_hub, detected_spoke = detect_environment(root_dir)

    hub_dir = args.hub_dir or detected_hub
    spoke_dir = args.spoke_dir or (detected_spoke if detected_mode == "spoke" else None)

    success = run_pipeline(
        hub_dir=hub_dir,
        spoke_dir=spoke_dir,
        check_mode=args.check,
        dry_run=args.dry_run,
        adr_dir=args.adr_dir,
        create_adr_dir=args.create_adr_dir,
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""compile_skills_docs.py - CCBA Skills Documentation & Static Portal Compiler (ADR-0058).

Pure Python compiler that generates:
1. Standardized 5-section Markdown documentation for each skill (docs/skills/<name>.md)
2. Central Markdown index (docs/skills/INDEX.md)
3. Open standard agent endpoint summaries (docs/llms.txt, docs/llms-full.txt)
4. Offline-first, responsive single-page web portal (docs/index.html)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = HUB_ROOT / ".agents" / "skills"
DOCS_DIR = HUB_ROOT / "docs"
DOCS_SKILLS_DIR = DOCS_DIR / "skills"
PORTALS_YAML_PATH = DOCS_SKILLS_DIR / "portals.yaml"
INDEX_MD_PATH = DOCS_SKILLS_DIR / "INDEX.md"
FAQ_MD_PATH = DOCS_SKILLS_DIR / "FAQ.md"
LLMS_TXT_PATH = DOCS_DIR / "llms.txt"
LLMS_FULL_TXT_PATH = DOCS_DIR / "llms-full.txt"
INDEX_HTML_PATH = DOCS_DIR / "index.html"
TEMPLATE_HTML_PATH = Path(__file__).resolve().parent / "templates" / "skills_portal.html"
DEFAULT_HUB_REPO = "https://github.com/vvChu/ccba-agent-platform"


def load_portals(portals_path: Path = PORTALS_YAML_PATH) -> list[dict[str, Any]]:
    """Load portal taxonomy configuration from YAML."""
    if not portals_path.exists():
        raise FileNotFoundError(f"Portals file not found at {portals_path}")
    data = yaml.safe_load(portals_path.read_text(encoding="utf-8")) or {}
    portals = data.get("portals", [])
    if not isinstance(portals, list):
        raise ValueError("Field 'portals' in portals.yaml must be a list")
    return portals


def load_pipeline_trail(
    portals_path: Path = PORTALS_YAML_PATH,
    expected_skills: set[str] | None = None,
) -> dict[str, dict[str, str]]:
    """Load and validate pipeline_trail mapping from portals.yaml (fail-closed)."""
    if not portals_path.exists():
        raise FileNotFoundError(f"Portals file not found at {portals_path}")
    data = yaml.safe_load(portals_path.read_text(encoding="utf-8")) or {}
    raw_trail = data.get("pipeline_trail")
    if not isinstance(raw_trail, dict) or not raw_trail:
        raise ValueError(f"Missing or invalid 'pipeline_trail' dictionary in {portals_path}")

    validated: dict[str, dict[str, str]] = {}
    for skill_name, entry in raw_trail.items():
        if not isinstance(skill_name, str) or not isinstance(entry, dict):
            raise ValueError(f"Invalid pipeline_trail entry for {skill_name!r}")
        item: dict[str, str] = {}
        for req_key in ("upstream", "downstream", "role"):
            val = entry.get(req_key)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"Skill '{skill_name}' missing non-empty '{req_key}'")
            item[req_key] = val.strip()
        validated[skill_name.strip()] = item

    if expected_skills is not None and set(validated.keys()) != expected_skills:
        missing = sorted(expected_skills - set(validated.keys()))
        extra = sorted(set(validated.keys()) - expected_skills)
        raise ValueError(f"pipeline_trail mismatch: missing={missing}, extra={extra}")
    return validated


PIPELINE_MAP: dict[str, dict[str, str]] = load_pipeline_trail(PORTALS_YAML_PATH)


def extract_frontmatter_and_body(file_path: Path) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and body from a markdown file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return {}, content
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content
        fm = yaml.safe_load(parts[1])
        return (fm if isinstance(fm, dict) else {}), parts[2].strip()
    except Exception as exc:
        print(f"[Warning] Failed to parse {file_path}: {exc}", file=sys.stderr)
        return {}, ""


def extract_body_headings(body: str, limit: int = 8) -> list[str]:
    """Extract up to `limit` H2/H3 headings from a skill markdown body."""
    headings: list[str] = []
    in_code = False
    for raw_line in body.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if stripped.startswith("## ") or stripped.startswith("### "):
            clean = stripped.lstrip("#").strip()
            if clean:
                headings.append(clean)
                if len(headings) >= limit:
                    break
    return headings


def build_skill_portal_map(portals: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Create a mapping from skill name to portal info."""
    mapping: dict[str, dict[str, Any]] = {}
    for p in portals:
        info = {
            "id": p.get("id", ""),
            "name": p.get("name", ""),
            "icon": p.get("icon", ""),
        }
        for s_name in p.get("skills", []):
            mapping[str(s_name).strip()] = info
    return mapping


def _resolve_invocation_meta(user_invocable: bool, disable_model_inv: bool) -> tuple[str, str]:
    """Resolve human-readable invocation display and badge slug."""
    if user_invocable and disable_model_inv:
        return "User-invoked (Chỉ lệnh Slash Command)", "user"
    if user_invocable and not disable_model_inv:
        return "Song song (Slash Command & Model Trigger)", "both"
    if not user_invocable and not disable_model_inv:
        return "Model-invoked (Tự động kích hoạt qua bối cảnh)", "model"
    return "User-invoked (Slash Command)", "user"


def _format_gpi_string(gpi_info: Any) -> str:
    """Format GPI metrics dictionary into standardized display string."""
    if not isinstance(gpi_info, dict):
        return ""
    s = float(gpi_info.get("s", 0))
    k = float(gpi_info.get("k", 0))
    a = float(gpi_info.get("a", 0))
    p = float(gpi_info.get("p", 0))
    score = (s * 2.5) + (k * 2.0) + (a * 2.0) - (p * 1.5)
    return f"S={s:.1f} | K={k:.1f} | A={a:.1f} | P={p:.1f} (GPI: {score:.2f})"


def _parse_single_skill_file(
    sf: Path,
    hub_root: Path,
    portal_map: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Parse a single SKILL.md into structured skill metadata."""
    fm, body = extract_frontmatter_and_body(sf)
    if not fm:
        return None
    name = str(fm.get("name") or sf.parent.name).strip()
    tier_raw = str(fm.get("tier") or "kernel").strip().lower()
    user_inv = bool(fm.get("user-invocable", False))
    disable_model = bool(fm.get("disable-model-invocation", False))
    inv_display, inv_badge = _resolve_invocation_meta(user_inv, disable_model)
    raw_triggers = fm.get("triggers") or fm.get("keywords") or []
    if isinstance(raw_triggers, str):
        raw_triggers = [raw_triggers]
    return {
        "name": name,
        "description": str(fm.get("description") or "").strip(),
        "bundle": str(fm.get("bundle") or "_core").strip(),
        "tier": tier_raw,
        "tier_display": "Tier 3 (Orchestrator)"
        if tier_raw == "orchestrator"
        else "Tier 2B (Kernel)",
        "tier_badge": "orchestrator" if tier_raw == "orchestrator" else "kernel",
        "command": str(fm.get("command") or f"/{name}").strip(),
        "user_invocable": user_inv,
        "disable_model_invocation": disable_model,
        "invocable_display": inv_display,
        "invocable_badge": inv_badge,
        "triggers": [str(t).strip() for t in raw_triggers if str(t).strip()],
        "portal": portal_map.get(
            name, {"id": "governance_upkeep", "name": "Quản trị Nền tảng", "icon": "🛡️"}
        ),
        "gpi_str": _format_gpi_string(fm.get("gpi")),
        "body": body,
        "headings": extract_body_headings(body),
        "skill_path": str(sf.relative_to(hub_root)).replace("\\", "/"),
    }


def get_all_skills_data(hub_root: Path = HUB_ROOT) -> list[dict[str, Any]]:
    """Scan and compile metadata for all active skills in .agents/skills/."""
    portals_path = hub_root / "docs" / "skills" / "portals.yaml"
    portals = load_portals(portals_path)
    portal_map = build_skill_portal_map(portals)
    skills: list[dict[str, Any]] = []
    for sf in sorted((hub_root / ".agents" / "skills").glob("**/SKILL.md")):
        parsed = _parse_single_skill_file(sf, hub_root, portal_map)
        if parsed is not None:
            skills.append(parsed)

    trail = load_pipeline_trail(portals_path, expected_skills={s["name"] for s in skills})
    PIPELINE_MAP.clear()
    PIPELINE_MAP.update(trail)
    for s in skills:
        s["pipeline"] = trail[s["name"]]

    skills.sort(key=lambda s: (0 if s["name"] == "platform-loader" else 1, s["name"]))
    return skills


def _render_skill_md_header_and_constraints(skill: dict[str, Any]) -> str:
    """Render sections 1 and 2 of the standardized 5-section skill Markdown."""
    name, desc, portal = skill["name"], skill["description"], skill["portal"]
    gpi_row = (
        f"| **Điểm Đánh Giá GPI (ADR-0057)** | `{skill['gpi_str']}` |\n" if skill["gpi_str"] else ""
    )
    return f"""# {name}

> **Mô tả ngắn**: {desc}

---

## 1. Action Header & Kích Hoạt Nhanh

### Cú pháp Lệnh (Slash Command)
```bash
{skill["command"]}
```

### Đồng bộ sang Phân vùng Spoke
```bash
python "$CCBA_HUB_PATH/scripts/sync_spoke.py" --spoke . --sync-item {name} --apply
```

### Thông Số & Huy Hiệu Kỹ Năng
| Thuộc tính | Chi tiết |
| :--- | :--- |
| **Cổng Điều Hướng (Portal)** | {portal["icon"]} {portal["name"]} |
| **Phân Tầng Kiến Trúc (Tier)** | `{skill["tier_display"]}` |
| **Gói Bundle** | `{skill["bundle"]}` |
| **Phương Thức Triệu Hồi** | {skill["invocable_display"]} |
{gpi_row}
---

## 2. Mục Đích & Rào Chắn Bất Biến (Defining Constraints)

### Mục Đích Hoạt Động
{desc}

Kỹ năng này hoạt động như một giao diện nhận thức chuẩn mực cho AI Agent và kỹ sư, đảm bảo tính tất định và khả năng tái lập trong toàn bộ vòng đời dự án.

### Rào Chắn Bất Biến (Platform Invariants)
1. **Bảo Vệ Ngân Sách Ngữ Cảnh (ADR-0030)**: Tệp `SKILL.md` của kỹ năng chỉ chứa hướng dẫn tác nghiệp cốt lõi, không chứa văn xuôi tiếp thị hay nội dung dư thừa gây tràn Context Window.
2. **Khóa Cứng Kỷ Luật Hoàn Thành (ADR-0058)**: Agent tuyệt đối không được báo cáo hoàn thành nhiệm vụ nếu bất kỳ lệnh kiểm thử tự động nào trả về mã lỗi khác 0 (`exit code != 0`).
3. **Cô Lập Vùng Ghi (Artifact Scope)**: Mọi tệp thành phẩm sinh ra phải nằm trong thư mục quy định của dự án, không làm ô nhiễm thư mục gốc (Project Root).
4. **Bảo Mật Bí Mật (Zero Secret Leaks)**: Tuyệt đối không hardcode API Keys, mật khẩu hoặc khóa chứng thực vào bất kỳ tệp tài liệu hay mã nguồn nào."""


def _render_skill_md_triggers_and_pipeline(skill: dict[str, Any]) -> str:
    """Render sections 3 and 4 of the standardized 5-section skill Markdown."""
    name, pipeline, triggers = skill["name"], skill["pipeline"], skill["triggers"]
    triggers_list = (
        "\n".join([f"- `{t}`" for t in triggers])
        if triggers
        else "- Không khai báo triggers cụ thể"
    )
    return f"""---

## 3. Khi Nào Sử Dụng & Kích Hoạt (Triggers)

### Từ Khóa Kích Hoạt (Triggers)
{triggers_list}

### Ngữ Cảnh Khuyến Nghị Triệu Hồi
- Khi cần thực thi nghiệp vụ liên quan trực tiếp đến vai trò: {pipeline["role"]}
- Trong chuỗi phát triển khi nhận tín hiệu bàn giao từ: **{pipeline["upstream"]}**

### Khi Nào KHÔNG Nên Dùng (Anti-patterns)
- Không dùng nếu cần tư vấn định hướng ban đầu: hãy gọi `/ccba-ask`.
- Không tự ý sửa đổi thủ công định nghĩa kỹ năng nếu gặp lỗi: hãy dùng `/ccba-skill-repair`.

---

## 4. Vị Trí Trong Chuỗi Giá Trị (The Pipeline Trail)

Kỹ năng `{name}` giữ vị trí then chốt trong chuỗi giá trị tích hợp của nền tảng:

```text
[ {pipeline["upstream"]} ]
          │
          ▼
    >>> [ {name} ] <<<  ({pipeline["role"]})
          │
          ▼
[ {pipeline["downstream"]} ]
```

- **Đầu vào (Upstream)**: Nhận bối cảnh từ `{pipeline["upstream"]}`.
- **Thực thi (In-flight)**: Áp dụng các quy tắc kỹ thuật và công cụ tự động hóa để sản sinh kết quả chuẩn mực.
- **Đầu ra & Bàn giao (Downstream)**: Chuyển giao thành phẩm sạch sẽ sang `{pipeline["downstream"]}`."""


def generate_skill_markdown(skill: dict[str, Any]) -> str:
    """Generate standardized 5-section Markdown doc for a single skill."""
    name = skill["name"]
    part1 = _render_skill_md_header_and_constraints(skill)
    part2 = _render_skill_md_triggers_and_pipeline(skill)
    part3 = f"""---

## 5. Khóa Cứng Kỷ Luật & Tiêu Chí Hoàn Thành (ADR-0058)

### Lệnh Kiểm Thử Tự Động Bắt Buộc
Mọi thay đổi liên quan đến kỹ năng này bắt buộc phải vượt qua toàn bộ các kiểm thử tự động sau:
```bash
python -m ccba_harness verify-patch --preset skill
python scripts/validate_skills.py --file .agents/skills/{name}/SKILL.md --enforce-gpi
```

### Danh Mục Kiểm Thức Hoàn Thành (Definition of Done - DoD)
- [ ] Lệnh kiểm chứng `verify-patch` trả về mã thoát `exit code 0`.
- [ ] Toàn bộ thuộc tính frontmatter trong `SKILL.md` đồng bộ 100% với `catalog.yaml`.
- [ ] Không có liên kết nội bộ bị đứt gãy hoặc tham chiếu file không tồn tại.
- [ ] Thành phẩm sinh ra nằm gọn trong thư mục đích, tuân thủ nguyên tắc KISS."""
    return "\n\n".join((part1, part2, part3)).strip() + "\n"


def _format_index_portal_section(p: dict[str, Any], p_skills: list[dict[str, Any]]) -> list[str]:
    """Render a single portal table section for INDEX.md."""
    rows = [
        f'<a id="{p["id"]}"></a>',
        f"## {p['icon']} {p['name']} ({len(p_skills)} Kỹ Năng)",
        "",
        f"*{p['description']}*",
        "",
        "| Kỹ Năng | Slash Command | Phân Tầng | Triệu Hồi | Tóm Tắt Nhiệm Vụ |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for s in p_skills:
        inv = (
            "User"
            if s["invocable_badge"] == "user"
            else ("Model" if s["invocable_badge"] == "model" else "Both")
        )
        desc = s["description"].replace("\n", " ")
        if len(desc) > 80:
            desc = desc[:77] + "..."
        rows.append(
            f"| [{s['name']}]({s['name']}.md) | `{s['command']}` | `{s['tier_badge']}` | `{inv}` | {desc} |"
        )
    rows.extend(["", "---", ""])
    return rows


def generate_index_markdown(portals: list[dict[str, Any]], skills: list[dict[str, Any]]) -> str:
    """Generate docs/skills/INDEX.md as a readable table of contents for terminals & IDEs."""
    by_portal: dict[str, list[dict[str, Any]]] = {p["id"]: [] for p in portals}
    for s in skills:
        if s["portal"]["id"] in by_portal:
            by_portal[s["portal"]["id"]].append(s)

    lines = [
        "# CCBA Agent Platform — Danh Mục Kỹ Năng (Skills Catalog Index)",
        "",
        f"> **Tổng hợp**: {len(skills)} Kỹ năng Hoạt động được phân loại vào 5 Cổng Điều Hướng theo chuẩn ADR-0047, ADR-0057 và ADR-0058.",
        "",
        "Trang tài liệu này phục vụ tra cứu nhanh cho kỹ sư và AI Coding Agents trong Terminal hoặc IDE.",
        "Xem bản web trực quan tại [docs/index.html](../index.html) hoặc tóm tắt chuẩn máy đọc tại [docs/llms.txt](../llms.txt).",
        "",
        "---",
        "",
        "## Mục Lục Các Cổng Điều Hướng",
        "",
    ]
    for p in portals:
        lines.append(
            f"- [{p['icon']} {p['name']}](#{p['id']}) ({len(by_portal.get(p['id'], []))} skills)"
        )
    lines.extend(["", "---", ""])
    for p in portals:
        lines.extend(_format_index_portal_section(p, by_portal.get(p["id"], [])))
    lines.extend(
        [
            "## Tài Liệu Bổ Trợ & Quy Chuẩn",
            "",
            "- [Hỏi Đáp Thường Gặp (FAQ)](FAQ.md) — Hướng dẫn Hub vs Spoke, xử lý lỗi và đồng bộ.",
            "- [llms.txt](../llms.txt) — Endpoint mô tả nền tảng theo chuẩn mở cho AI Agents.",
            "- [llms-full.txt](../llms-full.txt) — Nội dung hợp nhất chi tiết của toàn bộ kỹ năng.",
            "",
            "---",
            "*CCBA Agent Services Platform — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def generate_llms_txt(portals: list[dict[str, Any]], skills: list[dict[str, Any]]) -> str:
    """Generate docs/llms.txt following the llms.txt standard."""
    lines = [
        "# CCBA Agent Platform Skills",
        "",
        f"> Curated registry of {len(skills)} engineering, BIM, legal, and governance agent skills for the CCBA Agent Services Platform.",
        "",
        "## Navigation Portals",
        "",
    ]
    for p in portals:
        lines.append(f"- [{p['name']}](skills/INDEX.md#{p['id']}): {p['description']}")
    lines.extend(
        [
            "",
            "## Core Endpoints & Documentation",
            "",
            f"- [Skills Index](skills/INDEX.md): Markdown catalog index for all {len(skills)} skills.",
            "- [Skills FAQ](skills/FAQ.md): Frequently asked questions on Hub-Spoke, invocation, and troubleshooting.",
            f"- [Full Consolidated Skills Text](llms-full.txt): Complete full-text documentation of all {len(skills)} skills.",
            "",
            f"## All Active Skills ({len(skills)} Skills)",
            "",
        ]
    )
    for s in skills:
        lines.append(
            f"- [{s['name']}](skills/{s['name']}.md): {s['command']} — {s['description'].replace(chr(10), ' ')}"
        )
    return "\n".join(lines).strip() + "\n"


def generate_llms_full_txt(skills: list[dict[str, Any]]) -> str:
    """Generate docs/llms-full.txt by concatenating all skill docs."""
    chunks = [
        "# CCBA Agent Platform — Full Consolidated Skills Specification",
        "",
        f"> Complete documentation of all {len(skills)} active skills on the CCBA Agent Services Platform.",
        "> Generated for single-pass ingestion by AI coding agents and RAG indexers.",
        "",
        "=" * 80,
        "",
    ]
    for idx, s in enumerate(skills, start=1):
        chunks.append(f"<!-- SKILL {idx}/{len(skills)}: {s['name']} -->")
        chunks.append(generate_skill_markdown(s))
        chunks.append("\n" + "=" * 80 + "\n")
    return "\n".join(chunks).strip() + "\n"


def load_package_seams(hub_root: Path = HUB_ROOT) -> tuple[str, list[dict[str, Any]]]:
    """Load monorepo package seams and hub_repo URL from catalog.yaml."""
    catalog_path = hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    if not catalog_path.exists():
        catalog_path = HUB_ROOT / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    data = (
        yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
        if catalog_path.exists()
        else {}
    )
    hub_repo = str(data.get("hub_repo") or DEFAULT_HUB_REPO).rstrip("/")
    raw_seams = data.get("seams") or []
    seams: list[dict[str, Any]] = []
    for item in raw_seams:
        if isinstance(item, dict):
            seams.append(
                {
                    "package": str(item.get("package") or ""),
                    "path": str(item.get("path") or ""),
                    "description": str(item.get("description") or ""),
                    "public_seams": [str(x) for x in (item.get("public_seams") or [])],
                    "contracts": str(item.get("contracts") or ""),
                    "tests": str(item.get("tests") or ""),
                }
            )
    return hub_repo, seams


def load_seam_contract_cards(hub_root: Path = HUB_ROOT) -> list[dict[str, Any]]:
    """Load ADR-0061 capability contract cards from seam-contracts.yaml."""
    sc_path = hub_root / "seam-contracts.yaml"
    if not sc_path.exists():
        sc_path = HUB_ROOT / "seam-contracts.yaml"
    data = yaml.safe_load(sc_path.read_text(encoding="utf-8")) or {} if sc_path.exists() else {}
    cards: list[dict[str, Any]] = []
    for c in data.get("cards") or []:
        if not isinstance(c, dict):
            continue
        cap = c.get("capability") or {}
        cards.append(
            {
                "seam_id": str(c.get("seam_id") or ""),
                "kind": str(c.get("kind") or "package"),
                "import_path": str(c.get("import_path") or ""),
                "command": str(c.get("command") or ""),
                "skill_path": str(c.get("skill_path") or ""),
                "in": [str(x) for x in (cap.get("in") or [])],
                "out": [str(x) for x in (cap.get("out") or [])],
                "hardware": [str(x) for x in (c.get("hardware") or [])],
                "forbidden_substitute_imports": [
                    str(x) for x in (c.get("forbidden_substitute_imports") or [])
                ],
            }
        )
    return cards


def _build_portal_html_payloads(
    portals: list[dict[str, Any]],
    skills: list[dict[str, Any]],
    hub_repo: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build serializable SKILLS and PORTALS JSON lists for the web portal."""
    skills_json = [
        {
            "name": s["name"],
            "command": s["command"],
            "desc": s["description"],
            "bundle": s["bundle"],
            "tier": s["tier_badge"],
            "tier_display": s["tier_display"],
            "inv": s["invocable_badge"],
            "inv_display": s["invocable_display"],
            "portal_id": s["portal"]["id"],
            "portal_name": s["portal"]["name"],
            "portal_icon": s["portal"]["icon"],
            "triggers": s["triggers"],
            "gpi": s["gpi_str"],
            "upstream": s["pipeline"]["upstream"],
            "downstream": s["pipeline"]["downstream"],
            "role": s["pipeline"]["role"],
            "headings": s.get("headings", []),
            "skill_path": s["skill_path"],
            "blob_url": f"{hub_repo}/blob/main/{s['skill_path']}",
        }
        for s in skills
    ]
    portals_json = [
        {
            "id": p["id"],
            "name": p["name"],
            "icon": p["icon"],
            "desc": p["description"],
            "step": str(p.get("step") or ""),
            "question": str(p.get("question") or ""),
            "start_with": str(p.get("start_with") or ""),
            "spine_order": [str(x) for x in (p.get("spine_order") or [])],
            "guides": list(p.get("guides") or []),
            "count": sum(1 for s in skills if s["portal"]["id"] == p["id"]),
        }
        for p in portals
    ]
    return skills_json, portals_json


def generate_index_html(
    portals: list[dict[str, Any]],
    skills: list[dict[str, Any]],
    hub_root: Path = HUB_ROOT,
) -> str:
    """Generate single-page static HTML web portal from skills_portal.html template."""
    if not TEMPLATE_HTML_PATH.exists():
        raise FileNotFoundError(f"Portal HTML template not found at {TEMPLATE_HTML_PATH}")
    hub_repo, package_seams = load_package_seams(hub_root)
    seam_contracts = load_seam_contract_cards(hub_root)
    skills_json, portals_json = _build_portal_html_payloads(portals, skills, hub_repo)

    def _safe_json(obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")

    template = TEMPLATE_HTML_PATH.read_text(encoding="utf-8")
    return (
        template.replace("__SKILL_COUNT__", str(len(skills)))
        .replace("__SKILLS_JSON__", _safe_json(skills_json))
        .replace("__PORTALS_JSON__", _safe_json(portals_json))
        .replace("__PACKAGE_SEAMS_JSON__", _safe_json(package_seams))
        .replace("__SEAM_CONTRACTS_JSON__", _safe_json(seam_contracts))
    )


def _build_core_doc_targets(
    hub_root: Path,
    portals: list[dict[str, Any]],
    skills: list[dict[str, Any]],
) -> list[tuple[Path, str, str]]:
    """Build (file_path, expected_content, label) tuples for top-level docs."""
    docs_dir = hub_root / "docs"
    return [
        (
            docs_dir / "skills" / "INDEX.md",
            generate_index_markdown(portals, skills),
            "docs/skills/INDEX.md",
        ),
        (docs_dir / "llms.txt", generate_llms_txt(portals, skills), "docs/llms.txt"),
        (docs_dir / "llms-full.txt", generate_llms_full_txt(skills), "docs/llms-full.txt"),
        (
            docs_dir / "index.html",
            generate_index_html(portals, skills, hub_root),
            "docs/index.html",
        ),
    ]


def check_skills_docs_in_sync(hub_root: Path = HUB_ROOT) -> tuple[bool, str]:
    """Check if docs on disk match what compile_skills_docs would generate."""
    skills = get_all_skills_data(hub_root)
    portals = load_portals(hub_root / "docs" / "skills" / "portals.yaml")
    diffs: list[str] = []
    skills_docs_dir = hub_root / "docs" / "skills"

    for s in skills:
        doc_file = skills_docs_dir / f"{s['name']}.md"
        if not doc_file.exists():
            diffs.append(f"Missing documentation file: docs/skills/{s['name']}.md")
        elif doc_file.read_text(encoding="utf-8").strip() != generate_skill_markdown(s).strip():
            diffs.append(f"Content drift in: docs/skills/{s['name']}.md")

    expected_files = {f"{s['name']}.md" for s in skills}
    if skills_docs_dir.exists():
        actual = {
            f.name for f in skills_docs_dir.glob("*.md") if f.name not in ("INDEX.md", "FAQ.md")
        }
        if actual - expected_files:
            diffs.append(f"Orphaned skill documentation files: {sorted(actual - expected_files)}")

    for file_path, expected_text, rel_label in _build_core_doc_targets(hub_root, portals, skills):
        if not file_path.exists():
            diffs.append(f"Missing file: {rel_label}")
        elif file_path.read_text(encoding="utf-8").strip() != expected_text.strip():
            diffs.append(f"Content drift in: {rel_label}")

    if diffs:
        return False, "\n".join(diffs)
    return True, "All skills documentation and web assets are 100% in sync"


def compile_and_write(hub_root: Path = HUB_ROOT) -> None:
    """Compile and write all skill documentation and web assets to disk."""
    skills = get_all_skills_data(hub_root)
    portals = load_portals(hub_root / "docs" / "skills" / "portals.yaml")
    docs_skills_dir = hub_root / "docs" / "skills"
    docs_skills_dir.mkdir(parents=True, exist_ok=True)

    for s in skills:
        (docs_skills_dir / f"{s['name']}.md").write_text(
            generate_skill_markdown(s), encoding="utf-8"
        )
    (docs_skills_dir / "INDEX.md").write_text(
        generate_index_markdown(portals, skills), encoding="utf-8"
    )
    (hub_root / "docs" / "llms.txt").write_text(
        generate_llms_txt(portals, skills), encoding="utf-8"
    )
    (hub_root / "docs" / "llms-full.txt").write_text(
        generate_llms_full_txt(skills), encoding="utf-8"
    )
    (hub_root / "docs" / "index.html").write_text(
        generate_index_html(portals, skills, hub_root), encoding="utf-8"
    )
    print(
        f"[OK] Compiled {len(skills)} skills docs, INDEX.md, llms.txt, llms-full.txt, and index.html."
    )


def _run_check_mode(hub_root: Path) -> int:
    """Execute --check synchronization verification gate."""
    in_sync, msg = check_skills_docs_in_sync(hub_root)
    if in_sync:
        print(
            "[OK] [Skills Docs Compiler] All skills documentation and web assets are 100% in sync."
        )
        return 0
    print("[ERROR] [Skills Docs Compiler] Documentation is OUT OF SYNC:", file=sys.stderr)
    print(f"  {msg}", file=sys.stderr)
    print(
        "\n[INFO] Run 'python scripts/governance/compile_skills_docs.py --write' to regenerate.",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for docs compiler."""
    parser = argparse.ArgumentParser(
        description="CCBA Skills Documentation & Static Portal Compiler (ADR-0058)"
    )
    parser.add_argument("--check", action="store_true", help="Check if docs on disk are in sync.")
    parser.add_argument(
        "--write", action="store_true", help="Compile and write docs to disk (default)."
    )
    parser.add_argument("--stdout", action="store_true", help="Print INDEX.md content to stdout.")
    args = parser.parse_args(argv)

    if args.check:
        return _run_check_mode(HUB_ROOT)
    if args.stdout:
        skills = get_all_skills_data(HUB_ROOT)
        portals = load_portals(PORTALS_YAML_PATH)
        print(generate_index_markdown(portals, skills))
        return 0
    compile_and_write(HUB_ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())

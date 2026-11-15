#!/usr/bin/env python3
"""
Skill Finder for ClaudeKit skills.
Searches and lists available skills in claudekit-engineer/claude/skills/.
"""

import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

_FALLBACK_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)

hub_env = os.environ.get("CCBA_HUB_PATH")
if hub_env and Path(hub_env).exists():
    HUB_ROOT = Path(hub_env).resolve()
else:
    HUB_ROOT = Path(__file__).resolve().parents[2]

if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

SKILLS_DIRS = [
    HUB_ROOT / ".agents" / "skills",
    Path(".agents/skills"),
]


def _parse_stdlib_frontmatter(raw_yaml: str) -> dict[str, Any]:
    """Parse single-line YAML key-value pairs using Python stdlib when PyYAML is missing."""
    data: dict[str, Any] = {}
    for raw_line in raw_yaml.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line[0].isspace() or ":" not in raw_line:
            continue
        key, raw_val = raw_line.split(":", 1)
        clean_key = key.strip()
        if not clean_key:
            continue
        val = raw_val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            data[clean_key] = [
                item.strip().strip("\"'") for item in inner.split(",") if item.strip()
            ]
        else:
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
                val = val[1:-1]
            data[clean_key] = val
    return data


def parse_frontmatter(file_path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter with 3-tier fallback (ccba_harness -> PyYAML -> stdlib)."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return {}
    try:
        from ccba_harness import parse_markdown_frontmatter

        spec = parse_markdown_frontmatter(content, yaml_module=yaml)
        if spec.has_frontmatter and spec.error is None:
            return spec.metadata
        if spec.has_frontmatter and spec.error == "YAML_PACKAGE_MISSING":
            return _parse_stdlib_frontmatter(spec.raw_yaml)
        if spec.has_frontmatter:
            return {}
    except ImportError:
        pass
    match = _FALLBACK_FRONTMATTER_RE.match(content)
    if not match:
        return {}
    raw_yaml = match.group(1)
    if yaml is not None:
        try:
            data = yaml.safe_load(raw_yaml)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return _parse_stdlib_frontmatter(raw_yaml)


def _build_skill_entry(skill_dir: Path, query_lower: str) -> dict[str, Any] | None:
    """Build skill metadata dict if `skill_dir` matches `query_lower`, else return None."""
    if not (skill_dir.is_dir() and not skill_dir.name.startswith(".")):
        return None
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None
    meta = parse_frontmatter(skill_md)
    name = str(meta.get("name", skill_dir.name))
    desc = str(meta.get("description", ""))
    raw_kw = meta.get("keywords", []) or meta.get("triggers", [])
    keywords = [str(k) for k in raw_kw] if isinstance(raw_kw, list) else []
    if query_lower and not (
        query_lower in name.lower()
        or query_lower in desc.lower()
        or any(query_lower in kw.lower() for kw in keywords)
    ):
        return None
    return {
        "name": name,
        "folder": skill_dir.name,
        "command": meta.get("command", f"/{name}"),
        "description": desc,
        "keywords": keywords,
        "source": skill_dir.parent.name,
    }


def find_skills(query: str = "") -> None:
    """Search for skills matching the query in name, description, or keywords."""
    query_lower = query.lower()
    matches: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for skills_dir in SKILLS_DIRS:
        if not skills_dir.exists():
            continue
        for p in sorted(skills_dir.iterdir(), key=lambda entry: entry.name):
            entry = _build_skill_entry(p, query_lower)
            if entry and entry["name"] not in seen_names:
                seen_names.add(entry["name"])
                matches.append(entry)

    if not matches:
        print(f"[Skill Finder] No skills found matching '{query}'.")
        return

    print(f"\n[Skill Finder] Found {len(matches)} matching skills:\n")
    for idx, m in enumerate(matches, 1):
        print(f"{idx}. \x1b[32m{m['command']}\x1b[0m (Skill: {m['name']})")
        desc_preview = (
            m["description"][:120] + "..." if len(m["description"]) > 120 else m["description"]
        )
        print(f"   Description: {desc_preview}")
        if m["keywords"]:
            print(f"   Keywords: {', '.join(m['keywords'][:8])}")
        print()


def main(argv: list[str] | None = None) -> None:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] in ("--seam", "--seams", "-s"):
        keyword = " ".join(args[1:]) if len(args) > 1 else ""
        try:
            from scripts.governance.compile_catalog import query_catalog

            sys.exit(query_catalog(HUB_ROOT, keyword))
        except ImportError:
            catalog_file = HUB_ROOT / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
            if not catalog_file.exists():
                catalog_file = Path(".agents/skills/platform-loader/catalog.yaml")
            if not catalog_file.exists():
                print(f"[ERROR] Catalog file not found at {catalog_file}")
                sys.exit(1)
            try:
                data = yaml.safe_load(catalog_file.read_text(encoding="utf-8")) or {}
                seams = data.get("seams", [])
                kw = keyword.lower()
                matching = []
                for s in seams:
                    pkg = s.get("package", "")
                    desc = s.get("description", "")
                    public_seams = s.get("public_seams", [])
                    text = f"{pkg} {desc} {' '.join(public_seams)}".lower()
                    if kw in text:
                        matching.append(s)
                print("=" * 80)
                print(f"CCBA Seam Catalog Lookup — Query: '{keyword}' (Matches: {len(matching)})")
                print("=" * 80)
                for s in matching:
                    print(f"Package: {s.get('package')} ({s.get('path')})")
                    for ps in s.get("public_seams", []):
                        print(f"  - {ps}")
                    print("-" * 60)
                sys.exit(0)
            except Exception as e:
                print(f"[ERROR] Failed to query catalog: {e}")
                sys.exit(1)

    query = " ".join(args) if args else ""
    find_skills(query)


if __name__ == "__main__":
    main()

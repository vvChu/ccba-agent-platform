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

import yaml

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


def parse_frontmatter(file_path: Path) -> dict[str, Any]:
    """Parse the YAML frontmatter of a SKILL.md file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            yaml_block = match.group(1)
            data = yaml.safe_load(yaml_block)
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def find_skills(query: str = "") -> None:
    """Search for skills matching the query in name, description, or keywords."""
    query_lower = query.lower()
    matches: list[dict[str, Any]] = []

    for skills_dir in SKILLS_DIRS:
        if not skills_dir.exists():
            continue

        for p in skills_dir.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                skill_md = p / "SKILL.md"
                if skill_md.exists():
                    meta = parse_frontmatter(skill_md)
                    name = meta.get("name", p.name)
                    desc = meta.get("description", "")
                    keywords = meta.get("keywords", []) or meta.get("triggers", [])
                    cmd = meta.get("command", f"/{name}")

                    is_match = False
                    if not query:
                        is_match = True
                    else:
                        if (
                            query_lower in name.lower()
                            or query_lower in desc.lower()
                            or any(query_lower in str(kw).lower() for kw in keywords)
                        ):
                            is_match = True

                    if is_match:
                        # Prevent duplicate names
                        if not any(m["name"] == name for m in matches):
                            matches.append(
                                {
                                    "name": name,
                                    "folder": p.name,
                                    "command": cmd,
                                    "description": desc,
                                    "keywords": [str(k) for k in keywords],
                                    "source": p.parent.name,
                                }
                            )

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

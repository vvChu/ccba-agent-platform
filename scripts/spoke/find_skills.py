#!/usr/bin/env python3
"""
Skill Finder for ClaudeKit skills.
Searches and lists available skills in claudekit-engineer/claude/skills/.
"""

import re
import sys
from pathlib import Path
from typing import Any

import yaml

HUB_ROOT = Path(__file__).resolve().parents[2]
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


def main() -> None:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = sys.argv[1:]
    if args and args[0] in ("--seam", "--seams", "-s"):
        keyword = " ".join(args[1:]) if len(args) > 1 else ""
        from scripts.governance.compile_catalog import query_catalog

        sys.exit(query_catalog(HUB_ROOT, keyword))

    query = " ".join(args) if args else ""
    find_skills(query)


if __name__ == "__main__":
    main()

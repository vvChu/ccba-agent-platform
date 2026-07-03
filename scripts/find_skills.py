#!/usr/bin/env python3
"""
Skill Finder for ClaudeKit skills.
Searches and lists available skills in claudekit-engineer/claude/skills/.
"""

import re
import sys
from pathlib import Path

import yaml

# Enforce UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

SKILLS_DIRS = [
    Path("claudekit-engineer/claude/skills"),
    Path(".agents/claudekit-marketing/claude/skills")
]


def parse_frontmatter(file_path: Path) -> dict:
    """Parse the YAML frontmatter of a SKILL.md file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            yaml_block = match.group(1)
            return yaml.safe_load(yaml_block)
    except Exception:
        pass
    return {}


def find_skills(query: str = ""):
    """Search for skills matching the query in name, description, or keywords."""
    query_lower = query.lower()
    matches = []

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
                    keywords = meta.get("keywords", [])

                    is_match = False
                    if not query:
                        is_match = True
                    else:
                        if (query_lower in name.lower() or
                                query_lower in desc.lower() or
                                any(query_lower in kw.lower() for kw in keywords)):
                            is_match = True

                    if is_match:
                        # Prevent duplicate names if both repos have the same skill
                        if not any(m["folder"] == p.name for m in matches):
                            matches.append({
                                "name": name,
                                "folder": p.name,
                                "description": desc,
                                "keywords": keywords,
                                "source": skills_dir.parent.parent.name
                            })

    if not matches:
        print(f"[Skill Finder] No skills found matching '{query}'.")
        return

    print(f"\n[Skill Finder] Found {len(matches)} matching skills:\n")
    for idx, m in enumerate(matches, 1):
        print(f"{idx}. \x1b[32m/ccba-kit {m['folder']}\x1b[0m (Source: {m['source']})")
        desc_preview = m['description'][:120] + "..." if len(m['description']) > 120 else m['description']
        print(f"   Description: {desc_preview}")
        if m['keywords']:
            print(f"   Keywords: {', '.join(m['keywords'])}")
        print()

    # Print results
    if not matches:
        print(f"[Skill Finder] No skills found matching '{query}'.")
        return

    print(f"\n[Skill Finder] Found {len(matches)} matching skills:\n")
    for idx, m in enumerate(matches, 1):
        print(f"{idx}. \x1b[32m/ccba-kit {m['folder']}\x1b[0m (Skill name: {m['name']})")
        # Trim description if too long
        desc_preview = m['description'][:120] + "..." if len(m['description']) > 120 else m['description']
        print(f"   Description: {desc_preview}")
        if m['keywords']:
            print(f"   Keywords: {', '.join(m['keywords'])}")
        print()


def main():
    query = ""
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    find_skills(query)


if __name__ == "__main__":
    main()

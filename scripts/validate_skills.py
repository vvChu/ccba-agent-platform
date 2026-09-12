#!/usr/bin/env python3
"""validate_skills.py - Thin CLI Adapter for CCBA Agent Skill Validation.

Delegates all skill frontmatter, character limits, and step completion criteria
validation logic to the `DocumentAuditor` deep module in `doc_auditor.py`.
"""

import sys
from pathlib import Path

# Add project root to sys.path for cross-environment imports
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.doc_auditor import DocumentAuditor
from scripts.governance.audit_skills_hygiene import check_skills_hygiene
from scripts.governance.compile_catalog import check_catalog_in_sync
from scripts.governance.compile_skills_docs import check_skills_docs_in_sync


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    auditor = DocumentAuditor()
    exit_code = auditor.run_skills_validation_cli(sys.argv[1:])
    if exit_code != 0:
        sys.exit(exit_code)

    # Automated Catalog Sync Check (ADR 0047)
    in_sync, msg = check_catalog_in_sync(project_root)
    if not in_sync:
        print(
            "\n[ERROR] [Catalog Compiler] catalog.yaml is OUT OF SYNC with frontmatters:",
            file=sys.stderr,
        )
        print(f"  {msg}", file=sys.stderr)
        print(
            "\n[INFO] Run 'python scripts/governance/compile_catalog.py' to regenerate catalog.yaml.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Automated Skills Documentation & Web Assets Sync Check (ADR-0058)
    docs_in_sync, docs_msg = check_skills_docs_in_sync(project_root)
    if not docs_in_sync:
        print(
            "\n[ERROR] [Skills Docs Compiler] Documentation/Web assets are OUT OF SYNC with SKILL.md:",
            file=sys.stderr,
        )
        print(f"  {docs_msg}", file=sys.stderr)
        print(
            "\n[INFO] Run 'python scripts/governance/compile_skills_docs.py --write' to regenerate.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Automated Skills Hygiene & Standards Check (HUB-ADR-0058)
    target_file = None
    args_list = sys.argv[1:]
    for i, arg in enumerate(args_list):
        if arg in ("--file", "-f") and i + 1 < len(args_list):
            target_file = args_list[i + 1]
            break

    hygiene_ok, hygiene_msg = check_skills_hygiene(project_root, target_path=target_file)
    if not hygiene_ok:
        print(
            "\n[ERROR] [Skills Hygiene Auditor] Skill hygiene violations detected:",
            file=sys.stderr,
        )
        print(f"  {hygiene_msg}", file=sys.stderr)
        print(
            "\n[INFO] Run 'python scripts/governance/audit_skills_hygiene.py' for full diagnostic report.",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

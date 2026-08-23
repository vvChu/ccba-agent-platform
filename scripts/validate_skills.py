#!/usr/bin/env python3
"""validate_skills.py - Thin CLI Adapter for CCBA Agent Skill Validation.

Delegates all skill frontmatter, character limits, and step completion criteria
validation logic to the `DocumentAuditor` deep module in `doc_auditor.py`.
"""

import sys
from pathlib import Path

from scripts.doc_auditor import DocumentAuditor
from scripts.governance.compile_catalog import check_catalog_in_sync


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

    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""validate_skills.py - Thin CLI Adapter for CCBA Agent Skill Validation.

Delegates all skill frontmatter, character limits, and step completion criteria
validation logic to the `DocumentAuditor` deep module in `doc_auditor.py`.
"""

import sys
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from doc_auditor import DocumentAuditor


def main():
    auditor = DocumentAuditor()
    exit_code = auditor.run_skills_validation_cli(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

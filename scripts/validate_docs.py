#!/usr/bin/env python3
"""validate_docs.py - Thin CLI Adapter for Document & Governance Validation.

Delegates all scanning, frontmatter parsing, link validation, and reporting logic
to the `DocumentAuditor` deep module in `doc_auditor.py`.
"""

import sys
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from doc_auditor import DocumentAuditor


def main():
    auditor = DocumentAuditor()
    exit_code = auditor.run_docs_validation_cli(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

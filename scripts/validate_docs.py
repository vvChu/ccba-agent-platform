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

_auditor_inst = DocumentAuditor()
extract_code_references = _auditor_inst.extract_code_references
extract_env_variables = _auditor_inst.extract_env_variables
extract_internal_links = _auditor_inst.extract_internal_links
validate_markdown_file = _auditor_inst.validate_markdown_file


def scan_orphan_files(bundle_root: Path, *args, **kwargs):
    auditor = DocumentAuditor(project_root=args[0] if args and isinstance(args[0], Path) else None)
    return auditor.scan_orphan_files(bundle_root)


def main():
    auditor = DocumentAuditor()
    exit_code = auditor.run_docs_validation_cli(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""validate_docs.py - Thin CLI Entrypoint & Compatibility Adapter for Document Validation.

Delegates scanning, frontmatter parsing, link validation, and reporting logic
to DocumentAuditor in doc_auditor.py. Maintains backward-compatible helper aliases
for existing test harnesses.
"""

import sys
from pathlib import Path
from typing import Any

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from doc_auditor import DocumentAuditor

_auditor_inst = DocumentAuditor()
extract_code_references = _auditor_inst.extract_code_references
extract_env_variables = _auditor_inst.extract_env_variables
extract_internal_links = _auditor_inst.extract_internal_links
validate_markdown_file = _auditor_inst.validate_markdown_file


def scan_orphan_files(bundle_root: Path, *args: Any, **kwargs: Any) -> list[Path]:
    auditor = DocumentAuditor(project_root=args[0] if args and isinstance(args[0], Path) else None)
    return list(auditor.scan_orphan_files(bundle_root))


def main() -> None:
    """CLI entrypoint: delegates fully to DocumentAuditor.run_docs_validation_cli."""
    auditor = DocumentAuditor()
    exit_code = auditor.run_docs_validation_cli(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

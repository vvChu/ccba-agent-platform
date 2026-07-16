"""Coordinator for document amendment processing in CCBA Legal Intel.

Handles coordination between parser, packager, and registry manager components
without introducing circular dependencies.
"""

from pathlib import Path
from typing import Any

from ccba_legal.formatter import inject_warning_block
from ccba_legal.parser import LegalAnalysisEngine
from ccba_legal.registry import LegalRegistryManager


class LegalProcessor:
    """Coordinates parsing of document amendments, updating the registry, and warning injections."""

    def __init__(self, registry_path: Path | None = None) -> None:
        """Initialize the processor with an underlying registry manager."""
        self.registry_mgr = LegalRegistryManager(registry_path=registry_path)

    def process_amendments_from_document(
        self, source_doc_id: str, source_doc_content: str, source_doc_path: str
    ) -> list[dict[str, Any]]:
        """Parse clause-level changes from the source document, update registry, and inject warnings in target documents."""
        engine = LegalAnalysisEngine()
        modifications = engine.extract_amendments(source_doc_content, source_doc_path)

        for mod in modifications:
            target_doc_id = mod.get("target_doc_id")
            target_anchor = mod.get("target_anchor")
            amendment_source = mod.get("amendment_source")
            mod_source_doc_path = mod.get("source_doc_path", source_doc_path)

            if not target_doc_id or not target_anchor:
                continue

            self.registry_mgr.update_clause_status(
                target_doc_id=target_doc_id,
                clause_anchor=target_anchor,
                status="amended",
                amended_by=amendment_source,
                source_doc_path=mod_source_doc_path,
            )

            target_meta = self.registry_mgr.find_doc_by_id(target_doc_id)
            if target_meta:
                markdown_path = self.registry_mgr.get_markdown_path_for_doc(target_meta)
                if markdown_path and markdown_path.exists():
                    try:
                        content = markdown_path.read_text(encoding="utf-8")
                        updated_content = inject_warning_block(
                            markdown_content=content,
                            target_anchor=target_anchor,
                            amendment_source=amendment_source,
                            source_doc_path=mod_source_doc_path,
                        )
                        markdown_path.write_text(updated_content, encoding="utf-8")
                        print(
                            f"[Registry/Coordinator] Injected warning in target {target_doc_id} at {target_anchor}"
                        )
                    except Exception as e:
                        print(
                            f"[Registry/Coordinator] Error injecting warning into {markdown_path}: {e}"
                        )

        return modifications

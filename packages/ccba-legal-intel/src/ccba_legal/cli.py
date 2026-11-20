"""CCBA Legal Intelligence Unified CLI Dispatcher.

Provides standard command-line interfaces for:
- fetch: Crawl/Download official DOCX/PDF from TVPL VIP
- convert: Convert DOCX to Gold Standard OKF v2.2 Bundles
- process: Generate AST clauses.json and QA Benchmark for OKF Bundles
- consolidate: Patch amending documents into consolidated base document (VBHN)
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

from ccba_legal._cli_crawl_handlers import (
    handle_batch_fetch,
    handle_fetch,
    handle_ingest_gdrive,
    handle_login,
    handle_sync,
)
from ccba_legal._cli_parser import build_parser
from ccba_legal._cli_pipeline_handlers import (
    handle_clean_images,
    handle_consolidate,
    handle_convert,
    handle_hydrate,
    handle_ingest,
    handle_lint,
    handle_process,
)
from ccba_legal._cli_query_handlers import (
    handle_compile_registry,
    handle_get_clause,
    handle_get_table,
    handle_pptx,
    handle_query,
)
from ccba_legal.consolidator import LegislativeConsolidator
from ccba_legal.crawler import TVPLCrawler, get_tvpl_credentials
from ccba_legal.docx_converter import convert_docx_to_okf_bundle
from ccba_legal.gold_standard import GoldStandardProcessor

_COMMAND_HANDLERS: dict[str, Callable[[argparse.Namespace], int]] = {
    "login": handle_login,
    "fetch": handle_fetch,
    "batch-fetch": handle_batch_fetch,
    "convert": handle_convert,
    "process": handle_process,
    "consolidate": handle_consolidate,
    "hydrate": handle_hydrate,
    "lint": handle_lint,
    "sync": handle_sync,
    "ingest": handle_ingest,
    "ingest-gdrive": handle_ingest_gdrive,
    "clean-images": handle_clean_images,
    "query": handle_query,
    "get-clause": handle_get_clause,
    "get-table": handle_get_table,
    "compile-registry": handle_compile_registry,
    "pptx": handle_pptx,
}


def main() -> None:
    """Main CLI entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    handler = _COMMAND_HANDLERS.get(args.command)
    if handler is not None:
        sys.exit(handler(args))
    parser.print_help()
    sys.exit(1)


__all__ = [
    "GoldStandardProcessor",
    "LegislativeConsolidator",
    "TVPLCrawler",
    "build_parser",
    "convert_docx_to_okf_bundle",
    "get_tvpl_credentials",
    "handle_batch_fetch",
    "handle_clean_images",
    "handle_compile_registry",
    "handle_consolidate",
    "handle_convert",
    "handle_fetch",
    "handle_get_clause",
    "handle_get_table",
    "handle_hydrate",
    "handle_ingest",
    "handle_ingest_gdrive",
    "handle_lint",
    "handle_login",
    "handle_pptx",
    "handle_process",
    "handle_query",
    "handle_sync",
    "main",
]

if __name__ == "__main__":
    main()

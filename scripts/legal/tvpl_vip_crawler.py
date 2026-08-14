#!/usr/bin/env python3
"""TVPL VIP Automated Knowledge Pipeline Engine for CCBA Agent Platform.

Thin CLI Delegate and programmatic API for TVPL VIP document crawling,
delegating to LegalIntelPipeline in `packages/ccba-legal-intel`.
Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure packages/ccba-legal-intel/src is in sys.path
_PKG_SRC = Path(__file__).resolve().parents[2] / "packages" / "ccba-legal-intel" / "src"
if _PKG_SRC.exists() and str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

from ccba_legal.coordinator import LegalIntelPipeline
from ccba_legal.crawler import (
    ChromeCDP,
    CookieVault,
    TVPLSessionMutex,
    check_vip_session_health,
    get_tvpl_credentials,
    log_session_audit,
    resolve_project_root,
)

__all__ = [
    "crawl_tvpl_vip_document",
    "ChromeCDP",
    "CookieVault",
    "TVPLSessionMutex",
    "check_vip_session_health",
    "get_tvpl_credentials",
    "log_session_audit",
    "resolve_project_root",
]


def crawl_tvpl_vip_document(url: str, output_dir: Path | None = None) -> dict[str, Any]:
    """Main crawler entry point: Logs in, navigates to document, downloads full text & packages OKF Bundle."""
    project_root = resolve_project_root()
    target_out_dir = output_dir or (project_root / ".md" / "legal_docs")
    target_out_dir.mkdir(parents=True, exist_ok=True)

    pipeline = LegalIntelPipeline(output_dir=target_out_dir)
    res = pipeline.process_document(url)

    return {
        "status": res.status,
        "title": res.metadata.get("title", "TVPL Document"),
        "bundle_path": str(res.bundle_path) if res.bundle_path else "",
        "slug": res.doc_id,
        "error": res.error,
    }


def main() -> None:
    """CLI runner supporting both single URL argument and full flag CLI."""
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        target_url = sys.argv[1]
        res = crawl_tvpl_vip_document(target_url)
        print("Result:", res)
        sys.exit(0 if res.get("status") in ("success", "mocked", "cached") else 1)
    else:
        pipeline = LegalIntelPipeline()
        sys.exit(pipeline.run_cli(sys.argv[1:]))


if __name__ == "__main__":
    main()

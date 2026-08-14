#!/usr/bin/env python3
"""Automated TVPL VIP login and document crawler/downloader via Chrome CDP."""

import sys
from pathlib import Path

# Force UTF-8 encoding on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure packages/ccba-legal-intel/src is in sys.path
_PKG_SRC = Path(__file__).resolve().parents[2] / "packages" / "ccba-legal-intel" / "src"
if _PKG_SRC.exists() and str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

from ccba_legal.coordinator import LegalIntelPipeline


def run_auto_crawler(
    target_url: str = "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Thong-tu-06-2022-TT-BXD-Quy-chuan-ky-thuat-quoc-gia-an-toan-chay-cho-nha-va-cong-trinh-545229.aspx",
) -> bool:
    """Run automated crawler via LegalIntelPipeline."""
    pipeline = LegalIntelPipeline()
    res = pipeline.process_document(target_url)
    if res.status in ("success", "mocked", "cached"):
        print(f"[AutoTVPL] Successfully processed document: {res.doc_id} -> {res.bundle_path}")
        return True
    print(f"[AutoTVPL] Failed to process document: {res.error}")
    return False


if __name__ == "__main__":
    run_auto_crawler()

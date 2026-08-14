"""Automated TVPL VIP login and document crawler/downloader CLI.

Delegates document crawling to the deep ``LegalIntelPipeline`` in ``ccba_legal``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Safe Bootstrap: ensure packages/ccba-legal-intel/src is in sys.path
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


def main() -> None:
    if sys.platform == "win32":
        import io

        try:
            if isinstance(sys.stdout, io.TextIOWrapper):
                sys.stdout.reconfigure(encoding="utf-8")
            if isinstance(sys.stderr, io.TextIOWrapper):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    run_auto_crawler()


if __name__ == "__main__":
    main()

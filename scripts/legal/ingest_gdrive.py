#!/usr/bin/env python3
"""Google Drive Knowledge Ingestor Utility Script.

Discovers and downloads construction & legal knowledge documents (.pdf, .docx, Google Docs)
from Google Drive across 3 zones:
1. My Drive (with recursive folder traversal)
2. Shared with me (with recursive shared folder resolution)
3. Shared Drives (Team Drives)

Equipped with 2-tier deduplication (pre-download metadata match + post-download SHA-256 provenance).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Setup repository root & packages in sys.path
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_LEGAL_PKG = _REPO_ROOT / "packages" / "ccba-legal-intel" / "src"
if _LEGAL_PKG.exists() and str(_LEGAL_PKG) not in sys.path:
    sys.path.insert(0, str(_LEGAL_PKG))

from ccba_legal.sync.drive_client import (
    GOOGLE_API_AVAILABLE,
    get_credentials_dir,
    migrate_drive_credentials,
)
from ccba_legal.sync.drive_ingestor import DEFAULT_OUTPUT_DIR, GoogleDriveIngestor


def check_auth_prerequisites() -> bool:
    """Verify Google Drive API libraries and token availability."""
    if not GOOGLE_API_AVAILABLE:
        print("❌ Lỗi: Thiếu thư viện googleapiclient hoặc google-auth.")
        print("   Vui lòng cài đặt: pip install ccba-legal-intel[cloud]")
        return False

    migrate_drive_credentials()
    token_path = get_credentials_dir() / "drive_token.json"
    if not token_path.exists():
        print("=" * 80)
        print("⚠️ CHƯA PHÁT HIỆN TOKEN XÁC THỰC GOOGLE DRIVE CÁ NHÂN")
        print("=" * 80)
        print(f"Không tìm thấy token tại: {token_path}")
        print("Để kết nối Google Drive, vui lòng chạy lệnh xác thực:")
        print("   python scripts/legal/drive_auth_helper.py")
        print("Hệ thống sẽ thử fallback sang Application Default Credentials (ADC)...\n")
    return True


def parse_args() -> argparse.ArgumentParser:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="ingest_gdrive.py",
        description="🌐 CCBA Google Drive Multi-Scope Knowledge Ingestion Engine",
    )
    parser.add_argument(
        "--scope",
        choices=["all", "my-drive", "shared", "drives"],
        default="all",
        help="Scanning scope: 'all' (default), 'my-drive', 'shared' (Shared with me), 'drives' (Shared Drives)",
    )
    parser.add_argument(
        "--folder-id",
        type=str,
        default=None,
        help="Optional specific Google Drive folder ID to scan",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Target output directory for downloaded assets (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate scanning without downloading files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force redownload even if file is present in registry",
    )
    return parser


def main() -> int:
    """Main execution function."""
    parser = parse_args()
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

    print("=================================================================")
    print("      CCBA PLATFORM - GOOGLE DRIVE KNOWLEDGE INGESTOR 2.0        ")
    print("=================================================================")
    print(f"🌐 Phạm vi quét (Scope): {args.scope}")
    print(f"📂 Thư mục lưu trữ: {args.output_dir.resolve()}")
    if args.folder_id:
        print(f"📁 Mã thư mục mục tiêu: {args.folder_id}")
    if args.dry_run:
        print("🔎 Chế độ: DRY-RUN (Chỉ kiểm tra, không ghi đĩa)")
    if args.force:
        print("⚡ Chế độ: FORCE (Bỏ qua bộ đệm deduplication)")
    print("-----------------------------------------------------------------")

    if not check_auth_prerequisites():
        return 1

    try:
        ingestor = GoogleDriveIngestor(output_dir=args.output_dir)
        stats = ingestor.ingest(
            scope=args.scope,
            folder_id=args.folder_id,
            dest_dir=args.output_dir,
            dry_run=args.dry_run,
            force=args.force,
        )

        print("\n=================================================================")
        print("                BÁO CÁO THỐNG KÊ THU THẬP                        ")
        print("=================================================================")
        print(f"  • Tổng số đối tượng quét qua:     {stats['total_scanned']}")
        print(f"  • Số tài liệu tri thức phù hợp:   {stats['supported_found']}")
        if args.dry_run:
            print("\n  Danh sách tệp tin phát hiện:")
            for idx, item in enumerate(stats["items"][:20], 1):
                name = item.get("name", "")
                mime = item.get("mime_type", "")
                scope = item.get("scope", "")
                print(f"    {idx:02d}. [{scope}] {name} ({mime})")
            if len(stats["items"]) > 20:
                print(f"    ... và {len(stats['items']) - 20} tệp khác.")
        else:
            print(f"  • Đã tải mới & lưu trữ:           {stats['downloaded']}")
            print(f"  • Bỏ qua (đã đồng bộ trước đó):   {stats['skipped']}")
            print(f"  • Thất bại / Lỗi tải:             {stats['failed']}")
            print(f"\n📁 Thư mục đích: {args.output_dir.resolve()}")
            print(f"📜 Registry: {ingestor.registry_path.resolve()}")
        print("=================================================================")
        return 0

    except Exception as e:
        print(f"❌ Lỗi trong quá trình thu thập: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

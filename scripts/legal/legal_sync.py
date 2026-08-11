#!/usr/bin/env python
"""legal_sync.py — Thin CLI wrapper for LegalSyncEngine.

Delegates all business logic to ccba_legal.sync.LegalSyncEngine.
This script preserves the original CLI interface for backward compatibility.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Force UTF-8 on Windows to avoid charmap encoding errors with Vietnamese text
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure scripts/ is importable (for running from repo root)
sys.path.insert(0, str(Path(__file__).parent))

from ccba_legal.sync import DEFAULT_DRIVE_FOLDER, LegalSyncEngine


def main() -> None:
    """Parse CLI arguments and delegate to LegalSyncEngine."""
    parser = argparse.ArgumentParser(
        description="Tự động đồng bộ pháp lý (Legal Auto-Sync Pipeline) cho CCBA"
    )
    parser.add_argument(
        "--registry",
        default=".md/data/legal_registry.yaml",
        help="Đường dẫn file registry pháp lý cục bộ",
    )
    parser.add_argument(
        "--sources-registry",
        default=".md/data/sources_registry.yaml",
        help="Đường dẫn file registry ánh xạ source NotebookLM",
    )
    parser.add_argument(
        "--notebook-id", required=True, help="ID của Google NotebookLM Notebook đích"
    )
    parser.add_argument(
        "--use-drive",
        action="store_true",
        help="Kích hoạt luồng nạp gián tiếp qua Google Drive",
    )
    parser.add_argument(
        "--drive-folder",
        default=DEFAULT_DRIVE_FOLDER,
        help="ID thư mục Google Drive chung mục tiêu",
    )
    parser.add_argument(
        "--download-pdf",
        action="store_true",
        help="Tải bản PDF gốc tạm thời và upload lên Google Drive chung",
    )
    parser.add_argument(
        "--clean-drive",
        action="store_true",
        help="Làm sạch toàn bộ tệp tin trong thư mục Google Drive chung trước khi đồng bộ",
    )

    args = parser.parse_args()

    notebook_id = args.notebook_id or os.environ.get("NOTEBOOKLM_NOTEBOOK_ID")
    if not notebook_id:
        print(
            "[Error] Thiếu Notebook ID. Cung cấp qua --notebook-id "
            "hoặc biến môi trường NOTEBOOKLM_NOTEBOOK_ID."
        )
        sys.exit(1)

    engine = LegalSyncEngine()
    asyncio.run(
        engine.sync_registry_to_notebooklm(
            registry_path=Path(args.registry),
            sources_reg_path=Path(args.sources_registry),
            notebook_id=notebook_id,
            use_drive=args.use_drive,
            drive_folder_id=args.drive_folder,
            download_pdf=args.download_pdf,
            clean_drive=args.clean_drive,
        )
    )


if __name__ == "__main__":
    main()

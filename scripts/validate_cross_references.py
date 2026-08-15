#!/usr/bin/env python3
"""CLI Entrypoint for Cross-Reference Matrix Validation.

Usage:
    python scripts/validate_cross_references.py
    python scripts/validate_cross_references.py --spoke D:/idop-ccba-way
    python scripts/validate_cross_references.py --fix
    python scripts/validate_cross_references.py --warn-only
"""

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

from scripts.governance.cross_ref_validator import validate_cross_references


def main() -> int:
    """CLI Entrypoint."""
    parser = argparse.ArgumentParser(
        description="CCBA Cross-Reference Matrix Validator — Kiểm định ma trận truy vết thể chế cross_references.yaml"
    )
    parser.add_argument(
        "--spoke",
        type=str,
        default=".",
        help="Đường dẫn đến thư mục Spoke (Mặc định: thư mục hiện tại)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Đường dẫn trực tiếp đến tệp cross_references.yaml (Tùy chọn)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Tự động sửa các lỗi liên kết/heading có thể tự khắc phục qua Fuzzy Match",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Chế độ cảnh báo mềm: In cảnh báo nhưng không trả về mã lỗi (Exit 0)",
    )

    args = parser.parse_args()
    spoke_root = Path(args.spoke).resolve()

    if args.file:
        yaml_file = Path(args.file).resolve()
    else:
        # Standard candidates
        candidates = [
            spoke_root / ".md" / "cross_references.yaml",
            spoke_root / "cross_references.yaml",
            spoke_root / ".agents" / "cross_references.yaml",
        ]
        yaml_file = None
        for cand in candidates:
            if cand.exists():
                yaml_file = cand
                break

    if not yaml_file or not yaml_file.exists():
        print(f"❌ Không tìm thấy tệp cross_references.yaml tại: {spoke_root}")
        if args.warn_only:
            return 0
        return 1

    return validate_cross_references(
        yaml_path=yaml_file,
        project_root=spoke_root,
        warn_only=args.warn_only,
        auto_fix=args.fix,
    )


if __name__ == "__main__":
    sys.exit(main())

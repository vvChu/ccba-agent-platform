#!/usr/bin/env python3
"""scripts/eval/log_eval_miner.py - Thin CLI Facade for CCBA Log Eval Miner.

Delegates core log mining, privacy redaction, and EvalItem generation to the
Deep Seam module in `ccba_harness.evals.miner` (ADR-0035, ADR-0057).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ccba_harness.evals.miner import (
    CANONICAL_TO_LEGACY_MAP,
    DEFAULT_CATALOG_RELATIVE_PATH,
    DEFAULT_SCRATCH_DIR,
    DISCLAIMER_KEYWORDS,
    EXCEPTION_KEYWORDS,
    FIRE_SAFETY_KEYWORDS,
    IGNORABLE_CONTROL_COMMANDS,
    LEGACY_SKILL_FILE_MAP,
    LEGACY_TO_CANONICAL_MAP,
    MASKARA_REGEX_PATTERNS,
    OUTDATED_LEGAL_CITATIONS,
    PII_PATTERNS,
    SENSITIVE_PATTERNS,
    SKILL_DOMAIN_EXTENSIONS,
    classify_target_skill,
    clear_catalog_cache,
    extract_clean_user_prompt,
    find_transcript_files,
    generate_eval_spec_item,
    identify_failures,
    load_catalog,
    mine_logs_and_export,
    parse_transcript_logs,
    redact_sensitive_info,
    resolve_catalog_path,
    resolve_log_dir,
    resolve_output_test_file,
    score_skill_match,
    strip_accents,
    to_canonical_skill_name,
    to_legacy_skill_name,
)

__all__ = [
    "CANONICAL_TO_LEGACY_MAP",
    "DEFAULT_CATALOG_RELATIVE_PATH",
    "DEFAULT_SCRATCH_DIR",
    "DISCLAIMER_KEYWORDS",
    "EXCEPTION_KEYWORDS",
    "FIRE_SAFETY_KEYWORDS",
    "IGNORABLE_CONTROL_COMMANDS",
    "LEGACY_SKILL_FILE_MAP",
    "LEGACY_TO_CANONICAL_MAP",
    "MASKARA_REGEX_PATTERNS",
    "OUTDATED_LEGAL_CITATIONS",
    "PII_PATTERNS",
    "SENSITIVE_PATTERNS",
    "SKILL_DOMAIN_EXTENSIONS",
    "classify_target_skill",
    "clear_catalog_cache",
    "extract_clean_user_prompt",
    "find_transcript_files",
    "generate_eval_spec_item",
    "identify_failures",
    "load_catalog",
    "mine_logs_and_export",
    "parse_transcript_logs",
    "redact_sensitive_info",
    "resolve_catalog_path",
    "resolve_log_dir",
    "resolve_output_test_file",
    "score_skill_match",
    "strip_accents",
    "to_canonical_skill_name",
    "to_legacy_skill_name",
    "main",
]


def main() -> int:
    """CLI Entrypoint for Log Eval Miner."""
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="CCBA Production Log Mining & Eval Auto-Tuning Tool"
    )
    parser.add_argument(
        "--log-dir",
        default=None,
        help="Thư mục chứa transcript logs (mặc định tự động tìm ~/.gemini/antigravity/brain)",
    )
    parser.add_argument(
        "--output-dir",
        default=".agents/skills/ccba-eval-gate/test_cases",
        help="Thư mục xuất test_cases JSON",
    )
    parser.add_argument(
        "--catalog-path",
        default=None,
        help="Đường dẫn tùy chỉnh tới catalog.yaml SSOT",
    )
    parser.add_argument("--skill", help="Tên skill cụ thể cần nạp test cases mined")
    parser.add_argument(
        "--taxonomy",
        choices=["ROUTER_DISCLAIMER", "TOOL_EXCEPTION", "OUTDATED_CITATION"],
        help="Lọc loại lỗi cụ thể",
    )
    parser.add_argument(
        "--format",
        choices=["harness", "legacy"],
        default="harness",
        help="Định dạng xuất (harness cho ccba_harness.evals, legacy cho 4-layer assertions)",
    )
    parser.add_argument(
        "--auto-inject",
        action="store_true",
        help="Tự động ghi đè/bổ sung vào file eval test cases của skill",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chạy mô phỏng, xuất kết quả vào .md/scratch/eval_runs/ và không ghi đè vào test suite production",
    )
    parser.add_argument(
        "--scratch-dir",
        default=".md/scratch/eval_runs",
        help="Thư mục scratch để lưu kết quả dry-run (mặc định .md/scratch/eval_runs)",
    )

    args = parser.parse_args()
    log_dir = Path(args.log_dir) if args.log_dir else resolve_log_dir(None)
    output_dir = Path(args.output_dir)
    scratch_dir = Path(args.scratch_dir) if args.scratch_dir else None

    count = mine_logs_and_export(
        log_dir=log_dir,
        output_dir=output_dir,
        skill_filter=args.skill,
        taxonomy=args.taxonomy,
        format_type=args.format,
        auto_inject=args.auto_inject,
        catalog_path=args.catalog_path,
        dry_run=args.dry_run,
        scratch_dir=scratch_dir,
    )
    mode_desc = "[DRY-RUN] " if args.dry_run else ""
    print(f"{mode_desc}Mining hoàn tất: {count} cases được cập nhật.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

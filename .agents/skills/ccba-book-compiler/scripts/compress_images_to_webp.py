"""Thin CLI wrapper delegating retro WebP transcoding and C4 verification to pipeline seams."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[4] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from pipeline.book_excalidraw_verifier import (  # noqa: E402
    _rewrite_markdown_image_refs,
    batch_transcode_and_update_md,
    compress_image_to_webp,
)
from pipeline.book_excalidraw_verifier import (  # noqa: E402
    build_book_compiler_arg_parser as build_arg_parser,
)
from pipeline.book_verification import run_book_verification  # noqa: E402
from pipeline.book_verification import (  # noqa: E402
    verify_concepts_and_excalidraw as _verify_concepts_and_excalidraw,
)

__all__ = [
    "_rewrite_markdown_image_refs",
    "_verify_concepts_and_excalidraw",
    "batch_transcode_and_update_md",
    "build_arg_parser",
    "compress_image_to_webp",
    "main",
    "run_book_verification",
]


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for retro WebP transcoding and book artifact verification."""
    args = build_arg_parser().parse_args(argv)
    if args.verify_book:
        sys.exit(run_book_verification(args))

    conv, md_up, orig_mb, new_mb = batch_transcode_and_update_md(
        args.dir,
        quality=args.quality,
        max_dim=args.max_dim,
        delete_originals=not args.keep_originals,
    )
    saved_mb = orig_mb - new_mb
    saved_pct = (saved_mb / orig_mb * 100) if orig_mb > 0 else 0.0
    print(f"Transcoded {conv} images to WebP. Updated {md_up} markdown files.")
    print(
        f"Original: {orig_mb:.2f} MB -> New: {new_mb:.2f} MB (Saved {saved_mb:.2f} MB / {saved_pct:.1f}%)"
    )


if __name__ == "__main__":
    main()

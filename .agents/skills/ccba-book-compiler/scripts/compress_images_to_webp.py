"""Retro-transcode ebook images to WebP and dispatch deterministic C4 book verification."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment]

_SKILL_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SKILL_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS_DIR))

from verify_book_artifacts import (
    verify_concepts_and_excalidraw as _verify_concepts_and_excalidraw,  # noqa: E402,F401
)


def compress_image_to_webp(
    src_path: Path,
    dest_path: Path,
    quality: int = 80,
    max_dimension: int = 1200,
) -> bool:
    """Compress a single image to WebP with aspect-ratio-preserving resizing."""
    if Image is None:
        print("Error: Pillow is not installed in the environment.", file=sys.stderr)
        return False
    try:
        with Image.open(src_path) as img:
            if img.mode in ("P", "LA"):
                img = img.convert("RGBA")
            elif img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            width, height = img.size
            if max(width, height) > max_dimension:
                scale = max_dimension / float(max(width, height))
                new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            img.save(dest_path, "WEBP", quality=quality, method=6)
            return True
    except OSError as exc:
        print(f"Warning: Failed to compress {src_path.name}: {exc}", file=sys.stderr)
        return False


def _rewrite_markdown_image_refs(root_p: Path, replacements: list[tuple[str, str]]) -> int:
    """Rewrite Obsidian and Markdown image embeds across sorted .md files."""
    if not replacements:
        return 0
    updated_md_count = 0
    md_files = [p for p in sorted(root_p.rglob("*.md"), key=lambda x: str(x)) if p.is_file()]
    for md_p in md_files:
        try:
            text = md_p.read_text(encoding="utf-8")
            orig_text = text
            for old_name, new_name in replacements:
                esc = re.escape(old_name)
                text = re.sub(
                    rf"(!\[\[[^\]]*?){esc}(\|[^\]]*)?(\]\])",
                    rf"\g<1>{new_name}\g<2>\g<3>",
                    text,
                )
                text = re.sub(rf"(!\[[^\]]*\]\([^)]*?){esc}(\))", rf"\g<1>{new_name}\g<2>", text)
            if text != orig_text:
                md_p.write_text(text, encoding="utf-8")
                updated_md_count += 1
        except OSError as exc:
            print(f"Warning: Failed to update markdown {md_p.name}: {exc}", file=sys.stderr)
    return updated_md_count


def batch_transcode_and_update_md(
    target_dir: str,
    quality: int = 80,
    max_dim: int = 1200,
    delete_originals: bool = True,
) -> tuple[int, int, float, float]:
    """Retro-transcode PNG/JPG/JPEG files under target_dir to WebP with stem-collision protection."""
    root_p = Path(target_dir)
    if not root_p.exists():
        print(f"Directory not found: {target_dir}", file=sys.stderr)
        return 0, 0, 0.0, 0.0

    image_exts = {".png", ".jpg", ".jpeg"}
    image_files = [
        p
        for p in sorted(root_p.rglob("*"), key=lambda x: str(x))
        if p.is_file() and p.suffix.lower() in image_exts
    ]
    converted_count, orig_total_bytes, new_total_bytes = 0, 0, 0
    replacements: list[tuple[str, str]] = []
    claimed_webp: set[Path] = set()

    for img_p in image_files:
        orig_total_bytes += img_p.stat().st_size
        webp_p = img_p.with_suffix(".webp")
        if webp_p in claimed_webp or (webp_p.exists() and webp_p != img_p):
            webp_p = img_p.with_name(f"{img_p.stem}_{img_p.suffix.lstrip('.').lower()}.webp")
        claimed_webp.add(webp_p)
        if compress_image_to_webp(img_p, webp_p, quality=quality, max_dimension=max_dim):
            converted_count += 1
            new_total_bytes += webp_p.stat().st_size
            replacements.append((img_p.name, webp_p.name))
            if delete_originals and img_p != webp_p:
                try:
                    img_p.unlink()
                except OSError as exc:
                    print(f"Warning: Failed to unlink {img_p.name}: {exc}", file=sys.stderr)

    updated_md_count = _rewrite_markdown_image_refs(root_p, replacements)
    return (
        converted_count,
        updated_md_count,
        orig_total_bytes / (1024 * 1024),
        new_total_bytes / (1024 * 1024),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for WebP transcoding and C4 book verification."""
    parser = argparse.ArgumentParser(description="Retro WebP transcoder and Book Artifact Verifier")
    parser.add_argument("--dir", required=True, help="Target corpus directory")
    parser.add_argument("--quality", type=int, default=80, help="WebP quality (default: 80)")
    parser.add_argument(
        "--max-dim", type=int, default=1200, help="Max dimension in pixels (default: 1200)"
    )
    parser.add_argument("--keep-originals", action="store_true", help="Keep original PNG/JPG files")
    parser.add_argument(
        "--verify-book", action="store_true", help="Run C4 deterministic artifact verification"
    )
    parser.add_argument("--toc", help="Optional path to workspace _toc.json")
    parser.add_argument("--source", help="Optional path to Source Note (.md) to verify")
    parser.add_argument(
        "--excalidraw", nargs="*", default=[], help="Optional path(s) to .excalidraw.md file(s)"
    )
    parser.add_argument("--concepts", nargs="*", default=[], help="Concept note paths to verify")
    parser.add_argument(
        "--topics", nargs="*", default=[], help="Topic note paths to verify under topic profile"
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for retro WebP transcoding and book artifact verification."""
    args = build_arg_parser().parse_args(argv)
    if args.verify_book:
        from verify_book_artifacts import run_book_verification

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

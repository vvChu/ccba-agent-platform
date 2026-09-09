"""CCBA Platform — YouTube/Video Transcript Fetcher.

Thin CLI Adapter delegating to ccba_pdf_prep.media.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from ccba_pdf_prep.media import (
    extract_youtube_video_id,
    fetch_youtube_transcript,
    format_whisper_transcript,
    group_transcript_segments,
)

_logger = logging.getLogger("ccba.youtube.transcript")


def main() -> None:
    """CLI entry point to fetch and display YouTube transcript."""
    if len(sys.argv) < 2:
        print("Usage: python transcript.py <video_url> [output_dir]")
        sys.exit(1)

    url = sys.argv[1]
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    text = fetch_youtube_transcript(url, out_dir)
    if text:
        print(f"Transcript fetched ({len(text)} chars):\n{text[:500]}...")
    else:
        print("Failed to fetch transcript.")
        sys.exit(1)


if __name__ == "__main__":
    main()

__all__ = [
    "extract_youtube_video_id",
    "format_whisper_transcript",
    "group_transcript_segments",
    "fetch_youtube_transcript",
]

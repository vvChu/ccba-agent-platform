"""CCBA Platform — YouTube/Video Transcript Fetcher.

Extracts transcripts from YouTube via API, falls back to yt-dlp + Whisper STT via ccba-ai SDK.
"""

import logging
import re
import urllib.parse
from pathlib import Path

# Setup logging
_logger = logging.getLogger("ccba.youtube.transcript")


def _download_audio_via_ytdlp(url: str, output_dir: Path) -> Path | None:
    """Download audio from URL using yt-dlp as fallback (worst quality for speed)."""
    try:
        import yt_dlp

        # Make sure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        out_tmpl = str(output_dir / "%(id)s.%(ext)s")

        ydl_opts = {
            "format": "worstaudio/bestaudio",
            "outtmpl": out_tmpl,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None

            video_id = info.get("id", "")
            if not video_id:
                return None

            # Find the downloaded file by its ID (supporting webm, m4a, mp3, etc.)
            for f in output_dir.glob(f"{video_id}.*"):
                if f.is_file():
                    return f
            return None
    except ImportError:
        _logger.warning("yt-dlp is not installed. Run: pip install yt-dlp")
        return None
    except Exception as e:
        _logger.warning(f"yt-dlp audio download failed: {e}")
        return None


def format_whisper_transcript(raw_text: str) -> str:
    """Post-process raw Whisper output text by dividing it into 5-sentence paragraphs."""
    if not raw_text:
        return ""
    # Split by end of sentence punctuations followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", raw_text.strip())
    paragraphs = []
    for i in range(0, len(sentences), 5):
        chunk = " ".join(sentences[i : i + 5]).strip()
        if chunk:
            paragraphs.append(chunk)
    return "\n\n".join(paragraphs)


def fetch_youtube_transcript(url: str, output_dir: Path) -> str:
    """Fetch transcript from YouTube URL, fallback to audio download + Whisper STT via ccba-ai."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        parsed = urllib.parse.urlparse(url)
        video_id = None
        if parsed.hostname in ("youtu.be", "www.youtu.be"):
            video_id = parsed.path[1:]
        elif parsed.hostname in ("youtube.com", "www.youtube.com"):
            if parsed.path == "/watch":
                qs = urllib.parse.parse_qs(parsed.query)
                video_id = qs.get("v", [None])[0]
            elif parsed.path.startswith(("/embed/", "/v/", "/live/")):
                video_id = parsed.path.split("/")[2]

        if not video_id:
            _logger.info(
                "URL is not a standard YouTube URL or video ID missing. Fallback to audio download."
            )
            raise ValueError("Not a standard YouTube video ID.")

        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        try:
            transcript = transcript_list.find_transcript(["vi", "en"])
        except Exception as e:
            codes = [t.language_code for t in transcript_list]
            if not codes:
                raise ValueError("No transcript language codes found.") from e
            transcript = transcript_list.find_transcript(codes)

        data = transcript.fetch()
        formatted_lines = []
        current_group_start = None
        current_group_texts = []

        # Group transcripts into 30-second blocks with timestamps
        for segment in data:
            val_text = segment.text if hasattr(segment, "text") else segment.get("text", "")
            val_text = val_text.strip()
            if not val_text:
                continue

            start = segment.start if hasattr(segment, "start") else segment.get("start", 0.0)

            if current_group_start is None:
                current_group_start = start
                current_group_texts.append(val_text)
            elif start - current_group_start >= 30.0:
                minutes = int(current_group_start // 60)
                seconds = int(current_group_start % 60)
                time_str = f"[{minutes:02d}:{seconds:02d}]"
                formatted_lines.append(f"{time_str} " + " ".join(current_group_texts))
                current_group_start = start
                current_group_texts = [val_text]
            else:
                current_group_texts.append(val_text)

        if current_group_texts and current_group_start is not None:
            minutes = int(current_group_start // 60)
            seconds = int(current_group_start % 60)
            time_str = f"[{minutes:02d}:{seconds:02d}]"
            formatted_lines.append(f"{time_str} " + " ".join(current_group_texts))

        text = "\n\n".join(formatted_lines)
        return text

    except Exception as e:
        _logger.info(
            f"YouTube Transcript API failed ({e}). Fallback to audio download + Whisper STT..."
        )
        audio_path = _download_audio_via_ytdlp(url, output_dir)
        if audio_path:
            try:
                from ccba_ai import ai

                _logger.info(
                    f"Transcribing downloaded audio file: {audio_path.name} via ccba-ai SDK..."
                )
                raw_text = ai.transcribe(audio_path, model="audio-primary", language="vi")
                formatted_text = format_whisper_transcript(raw_text)

                # Clean up audio file
                if audio_path.exists():
                    try:
                        audio_path.unlink()
                    except OSError:
                        pass
                return formatted_text
            except Exception as stt_err:
                _logger.error(f"Whisper transcription failed: {stt_err}")
                if audio_path.exists():
                    try:
                        audio_path.unlink()
                    except OSError:
                        pass
        return ""

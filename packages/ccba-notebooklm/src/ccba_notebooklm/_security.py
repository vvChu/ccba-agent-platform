"""Security gating and Maskara privacy redaction for NotebookLM source ingestion."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from ccba_maskara import (
        MaskaraScanner,
        apply_raw_redactions,
        detect_secrets_in_text,
        is_binary,
    )
except ImportError:
    # Bootstrap fallback if not installed in current interpreter
    _pkg_src = Path(__file__).resolve().parents[4] / "packages" / "ccba-maskara" / "src"
    if _pkg_src.exists() and str(_pkg_src) not in sys.path:
        sys.path.insert(0, str(_pkg_src))
    try:
        from ccba_maskara import (
            MaskaraScanner,
            apply_raw_redactions,
            detect_secrets_in_text,
            is_binary,
        )
    except ImportError:
        MaskaraScanner = None  # type: ignore[assignment,misc]
        detect_secrets_in_text = None  # type: ignore[assignment]
        apply_raw_redactions = None  # type: ignore[assignment]
        is_binary = None  # type: ignore[assignment]


def run_maskara_gate(source_path: str) -> tuple[str, bool]:
    """Kiểm tra bảo mật file cục bộ qua Maskara trước khi nạp lên NotebookLM.

    Args:
        source_path: Đường dẫn tới file hoặc URL.

    Returns:
        tuple: (đường_dẫn_file_để_upload, có_phải_file_tạm_không)
    """
    if source_path.startswith(("http://", "https://")):
        return source_path, False

    if detect_secrets_in_text is None or is_binary is None or apply_raw_redactions is None:
        print(
            "[Warn] Thư viện ccba_maskara không khả dụng. Bỏ qua chốt chặn bảo mật.",
            file=sys.stderr,
        )
        return source_path, False

    file_p = Path(source_path)
    if not file_p.exists():
        return source_path, False

    if is_binary(file_p):
        return source_path, False

    try:
        print(f"[Info] Đang quét bảo mật file '{source_path}' qua Maskara Gate...")
        with open(file_p, "rb") as file_io:
            original_bytes = file_io.read()

        try:
            content = original_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = original_bytes.decode("latin-1")

        findings = detect_secrets_in_text(content, str(file_p), "notebooklm")

        if findings:
            critical_findings = [f for f in findings if f.get("severity") in ("critical", "high")]
            if any(
                f.get("rule_id")
                in ("openai-api-key", "anthropic-api-key", "github-token", "google-api-key")
                for f in critical_findings
            ):
                print(
                    f"\n[CRITICAL SECURITY ERROR] Phát hiện API Key nhạy cảm trong file '{source_path}'!",
                    file=sys.stderr,
                )
                for finding in critical_findings:
                    print(f"  - {finding.get('name')}: Dòng {finding.get('line')}", file=sys.stderr)
                raise ValueError("Tiến trình upload bị CHẶN vì lý do an toàn thông tin.")

            print(
                f"[Warning] Phát hiện {len(findings)} thông tin nhạy cảm. Đang che giấu (redact)..."
            )
            rewritten_bytes, num_redacted = apply_raw_redactions(original_bytes, findings)

            scratch_dir = Path(".md/scratch/redacted")
            scratch_dir.mkdir(parents=True, exist_ok=True)
            temp_redacted_file = scratch_dir / f"redacted_{file_p.name}"
            with open(temp_redacted_file, "wb") as file_out:
                file_out.write(rewritten_bytes)

            print(f"[Info] Đã làm sạch file và xuất tệp tạm: {temp_redacted_file}")
            return str(temp_redacted_file.absolute()), True
    except Exception as e:
        if "CHẶN" in str(e) or "an toàn thông tin" in str(e):
            raise
        print(f"[Warn] Lỗi khi chạy Maskara Gate: {e}", file=sys.stderr)

    return source_path, False


def sanitize_prompt_for_query(prompt: str) -> str:
    """Kiểm tra và che giấu thông tin nhạy cảm trong câu hỏi trước khi gửi tới NotebookLM.

    Args:
        prompt: Nội dung câu hỏi truy vấn RAG.

    Returns:
        str: Câu hỏi đã được làm sạch và che giấu bí mật nếu có.
    """
    if detect_secrets_in_text is None or apply_raw_redactions is None:
        return prompt

    if not prompt or not prompt.strip():
        return prompt

    try:
        findings = detect_secrets_in_text(prompt, "query_prompt", "notebooklm")
        if findings:
            critical_findings = [f for f in findings if f.get("severity") in ("critical", "high")]
            if any(
                f.get("rule_id")
                in ("openai-api-key", "anthropic-api-key", "github-token", "google-api-key")
                for f in critical_findings
            ):
                print(
                    "\n[CRITICAL SECURITY ERROR] Phát hiện API Key nhạy cảm trong câu hỏi RAG!",
                    file=sys.stderr,
                )
                raise ValueError("Truy vấn RAG bị CHẶN vì chứa API key nhạy cảm.")

            print(
                f"[Warning] [Maskara Gate] Phát hiện {len(findings)} thông tin nhạy cảm trong câu hỏi. Đang che giấu (redact)...",
                file=sys.stderr,
            )
            prompt_bytes = prompt.encode("utf-8")
            rewritten_bytes, _ = apply_raw_redactions(prompt_bytes, findings)
            return rewritten_bytes.decode("utf-8")
    except Exception as e:
        if "CHẶN" in str(e) or "nhạy cảm" in str(e):
            raise
        print(f"[Warn] Lỗi khi làm sạch prompt qua Maskara Gate: {e}", file=sys.stderr)

    return prompt

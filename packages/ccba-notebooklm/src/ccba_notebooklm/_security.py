import os
import sys
from pathlib import Path

def run_maskara_gate(source_path: str) -> tuple[str, bool]:
    """
    Kiểm tra bảo mật file cục bộ qua Maskara.
    Trả về: (đường dẫn_file_để_upload, có_phải_file_tạm_không)
    """
    if source_path.startswith(("http://", "https://")):
        return source_path, False

    # Find maskara.py robustly
    candidates = [
        Path("scripts/maskara.py"),
        Path(__file__).parents[4] / "scripts" / "maskara.py",
        Path(__file__).parents[3] / "scripts" / "maskara.py",
    ]
    maskara_path = None
    for cand in candidates:
        if cand.exists():
            maskara_path = cand
            break

    try:
        import importlib.util
        if not maskara_path:
            raise ImportError("maskara.py not found")
        spec = importlib.util.spec_from_file_location("maskara", maskara_path)
        if spec is None or spec.loader is None:
            raise ImportError("Could not load spec for maskara")
        maskara = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(maskara)
    except Exception as e:
        print(f"[Warn] Thư viện maskara.py không import được: {e}. Bỏ qua chốt chặn bảo mật.", file=sys.stderr)
        return source_path, False

    file_p = Path(source_path)
    if not file_p.exists():
        return source_path, False

    if maskara.is_binary(file_p):
        return source_path, False

    try:
        print(f"[Info] Đang quét bảo mật file '{source_path}' qua Maskara Gate...")
        with open(file_p, "rb") as file_io:
            original_bytes = file_io.read()

        try:
            content = original_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = original_bytes.decode("latin-1")

        findings = maskara.detect_secrets_in_text(content, str(file_p), "notebooklm")

        if findings:
            critical_findings = [f for f in findings if f.get("severity") in ("critical", "high")]
            if any(f.get("rule_id") in ("openai-api-key", "anthropic-api-key", "github-token", "google-api-key") for f in critical_findings):
                print(f"\n[CRITICAL SECURITY ERROR] Phát hiện API Key nhạy cảm trong file '{source_path}'!", file=sys.stderr)
                for finding in critical_findings:
                    print(f"  - {finding.get('name')}: Dòng {finding.get('line')}", file=sys.stderr)
                raise ValueError("Tiến trình upload bị CHẶN vì lý do an toàn thông tin.")

            print(f"[Warning] Phát hiện {len(findings)} thông tin nhạy cảm. Đang che giấu (redact)...")
            rewritten_bytes, num_redacted = maskara.apply_raw_redactions(original_bytes, findings)

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

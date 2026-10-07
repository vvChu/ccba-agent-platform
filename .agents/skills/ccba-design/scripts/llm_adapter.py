"""Flexible LLM Adapter cho ccba-design.

Định tuyến chuẩn hóa qua CCBA AI Platform:
- Text Generation: Seam ai_chat.v1 (`ccba_ai:ai`) & model_routing.v1 (`ccba_ai:choose_model`)
- Fail-Fast: Thất bại khi gọi Gateway sẽ báo lỗi ngay lập tức, không fallback ngầm ra SDK cá nhân.
- Image Generation: Dừng báo lỗi Fail-Fast chờ Seam Card chuẩn hóa trong Đợt 4B.
"""

import io
import sys

from ccba_ai import ai
from ccba_ai.routing import ModelArchetype, choose_model

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
except Exception:
    pass


def get_target_model(task_type: str = "general") -> str:
    """Xác định model cần gọi thông qua Seam model_routing.v1.

    Args:
        task_type: Khóa tác vụ định tuyến ('general', 'reasoning', v.v.).

    Returns:
        Tên model đích được cấp phát từ AI Gateway.
    """
    return choose_model(task_type)


def generate_text(prompt: str, default_model: str | None = None) -> str:
    """Sinh nội dung văn bản (Text Generation) qua Seam ai_chat.v1.

    Args:
        prompt: Nội dung prompt gửi cho LLM.
        default_model: Model hoặc khóa tác vụ ('general', 'reasoning'). Mặc định 'general'.

    Returns:
        Văn bản kết quả do LLM sinh ra.

    Raises:
        RuntimeError: Khi Gateway gặp lỗi hoặc kết nối không thành công (Fail-Fast).
    """
    task = default_model or "general"
    model = choose_model(task)
    print(f"[LLM Adapter] Đang gọi sinh văn bản với model: {model}...", file=sys.stderr)

    try:
        response = ai.chat(prompt, model=model)
        if response and isinstance(response, str):
            print("[LLM Adapter] Sinh văn bản thành công qua AI Gateway Spark.", file=sys.stderr)
            return response
        raise RuntimeError("Gateway trả về phản hồi rỗng hoặc không hợp lệ.")
    except Exception as e:
        raise RuntimeError(
            f"[LLM Adapter] Gọi AI Gateway thất bại: {e}. "
            "Vui lòng kiểm tra cấu hình mạng Spark VPN hoặc biến CCBA_API_KEY."
        ) from e


def generate_image(
    prompt: str, default_model: str = "standard-image", aspect_ratio: str = "1:1"
) -> bytes:
    """Sinh ảnh (Image Generation) — Chờ chuẩn hóa Seam Card trong Đợt 4B.

    Raises:
        NotImplementedError: Dừng hàm theo nguyên tắc Fail-Fast khi nền tảng chưa cung cấp Seam Card chính thức.
    """
    raise NotImplementedError(
        "[LLM Adapter] Tính năng sinh ảnh (generate_image) chưa có Seam Capability Card trong catalog.yaml. "
        "Tính năng này sẽ được chuẩn hóa chính thức tại Đợt 4B (gói ccba-media). "
        "Hiện tại chỉ hỗ trợ sinh SVG icons qua generate_text()."
    )

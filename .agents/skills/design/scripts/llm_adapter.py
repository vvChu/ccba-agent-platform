"""Flexible LLM Adapter cho các Kỹ năng được port từ ClaudeKit.

Hỗ trợ định tuyến gọi LLM động:
1. Ưu tiên AI Gateway Spark (LiteLLM) của CCBA Platform.
2. Tự động fallback sang API Google GenAI cục bộ (sử dụng SDK và GEMINI_API_KEY).
3. Tự động fallback sang các CLI có sẵn trên máy (gemini cli, copilot cli) nếu có.
4. Hỗ trợ thay đổi model linh hoạt qua biến môi trường CCBA_MODEL.
"""

# Khắc phục lỗi Console Encoding trên Windows
import io
import os
import shutil
import subprocess
import sys

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
except Exception:
    pass


def get_target_model(default_model: str) -> str:
    """Xác định model cần gọi dựa trên biến môi trường CCBA_MODEL hoặc fallback.

    Args:
        default_model: Model mặc định nếu không khai báo biến môi trường.

    Returns:
        Tên model đích.
    """
    return os.environ.get("CCBA_MODEL", default_model)


def generate_text(prompt: str, default_model: str = "gemini-3.7-flash") -> str:
    """Sinh nội dung văn bản (Text Generation) sử dụng luồng gọi LLM mềm dẻo.

    Args:
        prompt: Nội dung prompt gửi cho LLM.
        default_model: Model mặc định nếu không có cấu hình môi trường.

    Returns:
        Văn bản kết quả do LLM sinh ra.
    """
    model = get_target_model(default_model)
    print(f"[LLM Adapter] Đang gọi sinh văn bản với model: {model}...", file=sys.stderr)

    # 1. Thử gọi qua CCBA AI Gateway (LiteLLM)
    try:
        from ccba_ai import ai

        response = ai.chat(prompt, model=model)
        if response and isinstance(response, str):
            print("[LLM Adapter] Sinh văn bản thành công qua AI Gateway Spark.", file=sys.stderr)
            return response
    except Exception as e:
        print(
            f"[LLM Adapter] Thử qua AI Gateway thất bại: {e}. Thử fallback 1 (SDK cục bộ)...",
            file=sys.stderr,
        )

    # 2. Thử gọi qua Google GenAI API SDK trực tiếp
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai

            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(model=model, contents=prompt)
            if response and response.text:
                print(
                    "[LLM Adapter] Sinh văn bản thành công qua Google GenAI SDK.", file=sys.stderr
                )
                return response.text
        except Exception as e:
            print(
                f"[LLM Adapter] Thử qua Google GenAI SDK thất bại: {e}. Thử fallback 2 (gemini/copilot CLI)...",
                file=sys.stderr,
            )
    else:
        print("[LLM Adapter] Bỏ qua Google GenAI SDK do thiếu GEMINI_API_KEY.", file=sys.stderr)

    # 3. Thử gọi qua gemini CLI cục bộ
    if shutil.which("gemini"):
        try:
            print("[LLM Adapter] Đang gọi qua gemini CLI...", file=sys.stderr)
            result = subprocess.run(
                ["gemini", "run", prompt],
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
            )
            if result.stdout.strip():
                print("[LLM Adapter] Sinh văn bản thành công qua gemini CLI.", file=sys.stderr)
                return result.stdout.strip()
        except Exception as e:
            print(f"[LLM Adapter] Gọi gemini CLI thất bại: {e}", file=sys.stderr)

    # 4. Thử gọi qua copilot CLI cục bộ
    if shutil.which("copilot"):
        try:
            print("[LLM Adapter] Đang gọi qua copilot CLI...", file=sys.stderr)
            result = subprocess.run(
                ["copilot", "explain", prompt],
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
            )
            if result.stdout.strip():
                print("[LLM Adapter] Sinh văn bản thành công qua copilot CLI.", file=sys.stderr)
                return result.stdout.strip()
        except Exception as e:
            print(f"[LLM Adapter] Gọi copilot CLI thất bại: {e}", file=sys.stderr)

    # Lỗi tất cả các luồng
    raise RuntimeError(
        "Lỗi: Tất cả các luồng gọi LLM (AI Gateway, Google SDK, gemini/copilot CLI) đều thất bại hoặc không được cấu hình. "
        "Vui lòng thiết lập biến môi trường GEMINI_API_KEY hoặc kiểm tra kết nối mạng Spark VPN."
    )


def generate_image(
    prompt: str, default_model: str = "gemini-3.1-flash-image-preview", aspect_ratio: str = "1:1"
) -> bytes:
    """Sinh ảnh (Image Generation) sử dụng luồng gọi LLM mềm dẻo.

    Args:
        prompt: Prompt sinh ảnh.
        default_model: Model mặc định sinh ảnh.
        aspect_ratio: Tỷ lệ ảnh (mặc định 1:1 cho logo).

    Returns:
        Bytes dữ liệu ảnh PNG/JPEG.
    """
    model = get_target_model(default_model)
    print(f"[LLM Adapter] Đang gọi sinh ảnh với model: {model}...", file=sys.stderr)

    # 1. Thử gọi qua Google GenAI API SDK trực tiếp (Đây là luồng chính hỗ trợ Native Image Preview của Gemini)
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                ),
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    print(
                        "[LLM Adapter] Sinh ảnh thành công qua Google GenAI SDK.", file=sys.stderr
                    )
                    return part.inline_data.data
        except Exception as e:
            print(
                f"[LLM Adapter] Thử qua Google GenAI SDK thất bại: {e}. Thử fallback 1 (AI Gateway Spark)...",
                file=sys.stderr,
            )
    else:
        print(
            "[LLM Adapter] Bỏ qua Google GenAI SDK do thiếu GEMINI_API_KEY. Thử qua AI Gateway...",
            file=sys.stderr,
        )

    # 2. Thử gọi qua CCBA AI Gateway (LiteLLM OpenAI-Compatible Image Generation API)
    try:
        import requests

        # Thử lấy config gateway từ package ccba-ai
        # LiteLLM endpoint mặc định trên Spark server là http://100.83.192.30:8090/v1/images/generations
        url = "http://100.83.192.30:8090/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('CCBA_API_KEY', 'none')}",
        }
        data = {
            "model": "dall-e-3" if "pro" in model else "stable-diffusion",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024" if aspect_ratio == "1:1" else "1024x768",
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            import base64

            img_data = response.json()["data"][0]
            if "b64_json" in img_data:
                print(
                    "[LLM Adapter] Sinh ảnh thành công qua AI Gateway (b64_json).", file=sys.stderr
                )
                return base64.b64decode(img_data["b64_json"])
            elif "url" in img_data:
                img_url = img_data["url"]
                img_response = requests.get(img_url, timeout=15)
                if img_response.status_code == 200:
                    print(
                        "[LLM Adapter] Sinh ảnh thành công qua AI Gateway (url download).",
                        file=sys.stderr,
                    )
                    return img_response.content
    except Exception as e:
        print(
            f"[LLM Adapter] Thử qua AI Gateway thất bại: {e}. Thử fallback 2 (gemini CLI)...",
            file=sys.stderr,
        )

    # 3. Thử gọi qua gemini CLI cục bộ
    if shutil.which("gemini"):
        try:
            # Giả sử gemini CLI hỗ trợ xuất ảnh ra file bằng: gemini image "prompt" -o temp.png
            print("[LLM Adapter] Đang gọi qua gemini CLI để sinh ảnh...", file=sys.stderr)
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_name = tmp.name

            subprocess.run(
                ["gemini", "image", prompt, "-o", tmp_name], capture_output=True, check=True
            )

            if os.path.exists(tmp_name) and os.path.getsize(tmp_name) > 0:
                with open(tmp_name, "rb") as f:
                    data = f.read()
                os.unlink(tmp_name)
                print("[LLM Adapter] Sinh ảnh thành công qua gemini CLI.", file=sys.stderr)
                return data
        except Exception as e:
            print(f"[LLM Adapter] Gọi gemini CLI sinh ảnh thất bại: {e}", file=sys.stderr)

    raise RuntimeError(
        "Lỗi: Tất cả các luồng gọi sinh ảnh (Google SDK, AI Gateway Spark, gemini CLI) đều thất bại. "
        "Vui lòng cấu hình GEMINI_API_KEY hoặc kiểm tra kết nối mạng."
    )

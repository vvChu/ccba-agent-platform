import os
import fitz
from PIL import Image
from ccba_ai import ai

class IDOPAuditEngine:
    """
    Phối hợp và Audit đa bộ môn bằng kỹ thuật Quad-View.
    """
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_quad_view(self, images_paths, level_label):
        """Ghép 4 ảnh thành collage 2x2."""
        imgs = [Image.open(p).convert("RGB") for p in images_paths[:4]]
        if len(imgs) < 4: return None
        
        w, h = imgs[0].size
        for i in range(1, len(imgs)):
            imgs[i] = imgs[i].resize((w, h)) # Đảm bảo cùng kích thước
            
        collage = Image.new('RGB', (w*2, h*2), (255, 255, 255))
        collage.paste(imgs[0], (0, 0))
        collage.paste(imgs[1], (w, 0))
        collage.paste(imgs[2], (0, h))
        collage.paste(imgs[3], (w, h))
        
        path = os.path.join(self.output_dir, f"{level_label}_QuadView.png")
        collage.save(path)
        return path

    def run_ai_audit(self, collage_path, prompt):
        """Gửi collage lên AI Gateway để phân tích xung đột."""
        # Logic base64 và gọi ai.chat_multi
        # (Đây là phiên bản rút gọn phục vụ định trình Platform)
        return "Báo cáo xung đột từ AI..."

if __name__ == "__main__":
    # Ví dụ khởi chạy
    pass

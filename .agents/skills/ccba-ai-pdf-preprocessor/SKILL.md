---
name: ccba-ai-pdf-preprocessor
description: 'Tối ưu hóa PDF cho LLM: Phân đoạn (Segmenting), Chia nhỏ (Chunking)
  và Tiling cho AI Vision.'
applies_to:
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _qc
gpi:
  s: 3.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- pdf
- preprocessor
- chunk
- tiling
- bản vẽ
- scan
---
# CCBA AI PDF Preprocessor

Skill này cung cấp các công cụ chuyên dụng để chuẩn bị tài liệu PDF trước khi gửi đến AI Gateway. Giúp giải quyết các lỗi `Payload Too Large`, lỗi trích xuất trên bản scan mờ, và tối ưu hóa chi tiết cho bản vẽ kỹ thuật.

## Vai trò
Đây là "bộ lọc" trung tâm cho toàn bộ platform. Bất kỳ Agent nào cần đọc PDF phức tạp (>30 trang hoặc có bản vẽ) đều nên sử dụng skill này.

---

## Cài đặt
```bash
pip install -e "D:\GitHubProjects\ccba-agent-platform\packages\ccba-pdf-prep"
```

---

## Các tính năng chính

### 1. PDF Analyzer & Segmenter
Phân tích cấu trúc file để biết trang nào là Text số, trang nào là Scan (ảnh), và trang nào là Bản vẽ (oversized).

```python
from ccba_pdf_prep import PDFAnalyzer

analyzer = PDFAnalyzer()
report = analyzer.analyze("path/to/document.pdf")

# Lấy các đoạn trang cùng loại để định tuyến model
segments = report.get_segments()
for seg in segments:
    print(f"Pages {seg.start_page}-{seg.end_page}: {seg.page_type}")
```

### 2. Intelligent Chunker
Chia nhỏ PDF thành các khối nhỏ (mặc định 20 trang) để tránh lỗi Gateway Timeout hoặc Payload limit.

```python
from ccba_pdf_prep import split_pdf, get_blind_chunks
from pathlib import Path

source = Path("large_file.pdf")
ranges = get_blind_chunks(total_pages=100, chunk_size=20)
chunk_paths = split_pdf(source, ranges, output_temp_dir=Path("./temp"))
```

### 3. Vision Optimizer (Tiling)
Dành riêng cho **Bản vẽ kỹ thuật (A0-A3)**. Thay vì resize ảnh làm mờ nét vẽ, skill này sẽ "xẻ" bản vẽ thành các mảnh (tiles) độ phân giải cao để AI Vision có thể đọc rõ từng con số, ghi chú.

```python
from ccba_pdf_prep.vision import VisionOptimizer
from pathlib import Path

# Xẻ trang 1 của bản vẽ thành các tile 1024x1024 ở 300 DPI
tiles = VisionOptimizer.tile_page(
    pdf_path=Path("drawing.pdf"),
    page_num=0,
    output_dir=Path("./tiles"),
    dpi=300,
    tile_size_px=1024
)
```

---

## Khi nào nên dùng?
- **File > 30 trang**: Dùng `get_blind_chunks` để xử lý song song.
- **Hybrid PDF (Text + Scan)**: Dùng `get_segments` để chọn model Qwen cho text và Gemini OCR cho scan.
- **Bản vẽ kỹ thuật**: Dùng `VisionOptimizer` để bóc tách thông tin QC bản vẽ.

---

## Liên kết
- **Source**: `packages/ccba-pdf-prep/`
- **Dependencies**: `fitz` (PyMuPDF), `pypdf`.

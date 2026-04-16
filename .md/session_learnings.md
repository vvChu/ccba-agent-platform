## Session Learnings - Kiến thức tích lũy

## Cập nhật gần nhất: 2026-04-15

---

## Patterns (Mẫu tốt)

### 1. Phân mảnh khối lượng tải PDF (PDF Chunking) cho Gateways
- **Ngữ cảnh**: Gửi các tệp PDF scan dày và chằng chịt ảnh nội dung thông qua Base64 Data URI lên AI Provider.
- **Vấn đề giải quyết**: Payload base64 của file 50MB-100MB sẽ lập tức đánh sập cổng cấu hình Proxy limit (ví dụ Nginx / LiteLLM) trước khi kịp chạm tới model.
- **Giải pháp**: Phân chia file PDF gốc thành các khối (chunks) từ 10-20 trang bằng thư viện `pypdf`, xử lý lần lượt qua mạng rồi merge Markdown thuần túy ở đầu cuối. Tránh hoàn toàn lỗi Overflow.
- **Ví dụ code**:
```python
from pypdf import PdfReader, PdfWriter
import io

reader = PdfReader(source_path)
for i in range(0, len(reader.pages), 20):
    writer = PdfWriter()
    for j in range(i, min(i + 20, len(reader.pages))):
        writer.add_page(reader.pages[j])
    chunk_io = io.BytesIO()
    writer.write(chunk_io)
    file_chunks.append(chunk_io.getvalue())
```
- **Nguồn**: Session 54f85dcb-dcf1-423e-98d8-d332bb4fe1d6, 2026-04-09

### 2. Định Tuyến Self-Healing Free-tier (Bất Tử Hóa Models)
- **Ngữ cảnh**: Khi thực thi các task trích xuất RAG cường độ cao (ví dụ Stress-test bắn liên tiếp 40-50 luồng).
- **Vấn đề giải quyết**: Chạm Rate Limit 15 Request/Minute (lỗi HTTP 429) hoặc API Key chết (HTTP 403), khiến toàn bộ script phá sản.
- **Giải pháp**: Xây dựng AI Gateway thông minh (cụ thể là cấu hình Alias model trong LiteLLM). Cho phép Client đẩy mọi loại áp lực tải lên Gateway bất kể cấu hình. Hệ thống sẽ giữ session, ném request lỗi (403/429) vào khe Fallback để lấy API Key khác retry lại. Tỷ lệ thành công 100%.
- **Nguồn**: Session 54f85dcb-dcf1-423e-98d8-d332bb4fe1d6, 2026-04-09

### 3. Xử lý Phân đoạn Tài liệu (Segment-based Processing) cho Hybrid PDF
- **Ngữ cảnh**: Tài liệu PDF có sự pha trộn giữa trang văn bản số (Text-rich) và trang quét (Scanned/OCR), hoặc file có dung lượng cực lớn.
- **Vấn đề giải quyết**: Xử lý nguyên file bằng OCR model gây tốn token và chậm (đối với trang text). Xử lý bằng LLM thuần túy thì lỗi trang scan. Gửi file quá lớn gây lỗi `413 Payload Too Large`.
- **Giải pháp**: 
    1. Sử dụng `PDFAnalyzer` để phân đoạn tài liệu thành các `Segment` liên tục cùng loại.
    2. Chia nhỏ (split) PDF thành các file tạm theo segment.
    3. Thực thi chuyển đổi song song (Concurrent) các segment: trang Text dùng model nhanh/rẻ, trang Scan dùng model OCR.
    4. Hợp nhất nội dung Markdown kèm theo Segment Markers.
- **Nguồn**: Session 3cca2e64-49c0-4c49-aef3-684c8c1d80fd, 2026-04-15

### 4. Xẻ mảnh bản vẽ (High-res Tiling) cho AI Vision
- **Ngữ cảnh**: Xử lý các bản vẽ kỹ thuật khổ lớn (A0-A3) chứa các chi tiết nhỏ hoặc bảng thông số li ti.
- **Vấn đề giải quyết**: Nén cả trang vào một ảnh LLM Vision (2048px) làm mờ nét vẽ.
- **Giải pháp**: 
    1. Render trang ở DPI cao (300+). 
    2. Sử dụng tham số `clip` trong `get_pixmap` để render trực tiếp từng mảnh (tile) 1024-2048px. 
    3. Gửi mảnh ảnh chất lượng gốc cho AI giúp tăng độ chính xác trích xuất.
- **Nguồn**: Session 3cca2e64-49c0-4c49-aef3-684c8c1d80fd, 2026-04-15

---

## Solutions (Giải pháp tham chiếu)

### Xử lý in mã Unicode (Emoji) gây vỡ Console trên Windows PowerShell
- **Vấn đề**: Gọi Python script in Emoji hoặc chữ Tiếng Việt dẫn đến `UnicodeEncodeError: 'charmap' codec can't encode character`. Nguyên nhân là `sys.stdout` map vào kiểu `cp1252`.
- **Giải pháp**: Code cứng ép cấu hình xuất tiêu chuẩn ở đầu Script:
```python
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
```
- **Nguồn**: Session 54f85dcb-dcf1-423e-98d8-d332bb4fe1d6, 2026-04-09

### 2. Đồng bộ hóa quy trình (Pipeline Consistency) trong Watch Mode
- **Vấn đề**: Watch Mode thường bỏ qua các bước xử lý phức tạp (Analyzer, Caching, Post-processing) để tăng tốc độ phản hồi, dẫn đến kết quả khác biệt so với khi chạy thủ công.
- **Giải pháp**: Buộc Watcher phải khởi tạo và gọi thông qua `ProcessingPipeline` thay vì gọi trực tiếp `Converter.convert`. Mọi sự tối ưu (ví dụ: semaphore) phải nằm trong Pipeline để dùng chung cho mọi chế độ chạy.
- **Nguồn**: Session 3cca2e64-49c0-4c49-aef3-684c8c1d80fd, 2026-04-15

### 3. Khắc phục lỗi PyMuPDF Pixmap isinstance TypeError
- **Vấn đề**: Gọi `fitz.Pixmap(pix, rect)` lỗi `TypeError` trên một số phiên bản (isinstance arg 2 must be type).
- **Giải pháp**: Tránh tạo Pixmap trung gian, sử dụng trực tiếp `page.get_pixmap(matrix=matrix, clip=rect)`. Cách này an toàn, tối ưu bộ nhớ và tránh lỗi định dạng nội bộ của thư viện.
- **Nguồn**: Session 3cca2e64-49c0-4c49-aef3-684c8c1d80fd, 2026-04-15

---

## Conventions (Quy định kiến trúc)

### 1. Phân Tách OCR Engines Độc Lập
- **Ngữ cảnh**: Các mô hình LLM chuyên lập trình hoặc text-reasoning (như Sonnet-4.6, Opus) thường rất yếu, chậm và ngốn quá nhiều token khi phân tích ảnh scan PDF nhị phân (đen trắng/chất lượng thấp).
- **Quy ước**: Tích hợp cờ chuyên biệt `--ocr` vào workflow để gọi ngầm alias model `ocr-primary` giúp bảo hành nội dung thị giác máy tính thay vì phó thác cho fallback tree.

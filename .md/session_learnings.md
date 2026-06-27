## Session Learnings - Kiến thức tích lũy

## Cập nhật gần nhất: 2026-06-27

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

### 5. Đóng gói Giải pháp Fallback Ngoại tuyến (Offline ZIP Scaffolding)
- **Ngữ cảnh**: Khi xây dựng các công cụ tích hợp các CLI bên thứ ba (như Microsoft Power Platform CLI `pac`) để đóng gói sản phẩm.
- **Vấn đề giải quyết**: Trong môi trường CI/CD hoặc máy chạy offline thiếu các công cụ CLI này, bộ kiểm định tự động hoặc quá trình build sẽ bị lỗi.
- **Giải pháp**: Viết luồng đóng gói fallback bằng module `zipfile` của Python để tự sinh cấu trúc thư mục giải pháp và file XML siêu dữ liệu (`Solution.xml`) giúp đảm bảo tệp `.zip` đầu ra luôn được tạo ra đồng bộ và hợp lệ cho việc import thủ công.
- **Nguồn**: Session 86ca4b06-4329-478b-8c16-ca53827675de, 2026-06-27

---

## Anti-patterns (Cách tránh)

### 1. Tự ý thay đổi Alias mặc định của AI Gateway
- **Vấn đề**: Khi cập nhật tài liệu hoặc cấu hình, việc tự ý thay thế các định danh alias do Server quy định (như `qwen-local-primary`) bằng tên gốc thực tế của model (như `qwen3.5-35b`) sẽ phá vỡ hệ thống routing, load-balancing và các luồng fallback đã được setup ngầm định trên Gateway.
- **Thay thế bằng**: Luôn tôn trọng và duy trì cấu trúc định danh alias chuẩn (như `qwen-local-primary`, `ocr-primary`, `rag-core`, v.v.) trong mọi file config (`.env`) và mã nguồn mẫu.
- **Nguồn**: Session df3394e5-3891-4d1b-b234-ce3af1d47689, 2026-04-28

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

### 4. Lọc Thư mục CDE dựa trên Tiền tố (Failsafe Prefix Filter)
- **Vấn đề**: Bộ test tự động so sánh danh sách thư mục sinh ra bị lệch khi có thêm các thư mục trung gian (như `IDOP_Solution`).
- **Giải pháp**: Thay vì dùng phép trừ tập hợp tĩnh (`actual_dirs - {"lists", "workflows"}`), hãy dùng bộ lọc tiền tố động (`d.startswith(("01", "02", "03", "04", "05"))`) giúp test-suite cô lập hoàn toàn các thư mục CDE chuẩn cần kiểm tra.
- **Nguồn**: Session 86ca4b06-4329-478b-8c16-ca53827675de, 2026-06-27

### 5. Độ dài Regex linh hoạt trong Bộ quét API Keys (Privacy Guard)
- **Vấn đề**: Các mẫu API keys của các hãng có độ dài thực tế khác nhau (Gemini là 39 ký tự, OpenAI legacy là 51 ký tự, OpenAI project key là 53+ ký tự). Việc code cứng độ dài Regex (như `{35}` hay `{48}`) khiến test suite bị lỗi không bắt được dummy keys.
- **Giải pháp**: Sử dụng độ dài khoảng (như `{30,40}` hoặc `{30,}`) trong Regex để đảm bảo độ bao phủ rộng và an toàn cho mọi loại key.
- **Nguồn**: Session 86ca4b06-4329-478b-8c16-ca53827675de, 2026-06-27

---

## Conventions (Quy định kiến trúc)

### 1. Phân Tách OCR Engines Độc Lập
- **Ngữ cảnh**: Các mô hình LLM chuyên lập trình hoặc text-reasoning (như Sonnet-4.6, Opus) thường rất yếu, chậm và ngốn quá nhiều token khi phân tích ảnh scan PDF nhị phân (đen trắng/chất lượng thấp).
- **Quy ước**: Tích hợp cờ chuyên biệt `--ocr` vào workflow để gọi ngầm alias model `ocr-primary` giúp bảo hành nội dung thị giác máy tính thay vì phó thác cho fallback tree.

---

## Configurations (Cấu hình tối ưu)

| Setting / Alias | Value / Backend | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| `text-gemma` | Gemma 3 27B | Tận dụng Google Free Quota (144k req/ngày) | High-volume NLP, phân loại, summarize |
| `ocr-primary` | Gemini 3.1 Flash Lite | Tận dụng Free Quota Vision (5k req/ngày) | OCR, bóc tách văn bản từ hình ảnh/bản vẽ |
| `reasoning-gemma` | Gemma 4 31B | Logic nâng cao, Free Quota (15k req/ngày)| Các task JSON phức tạp, trích xuất cấu trúc |

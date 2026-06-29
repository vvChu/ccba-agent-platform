## Session Learnings - Kiến thức tích lũy

## Cập nhật gần nhất: 2026-06-28

## Anti-patterns (Cách tránh)

### CLI Monolith for Data Processing
- **Vấn đề**: Viết toàn bộ logic gọi AI, regex lọc text trực tiếp trong file CLI command khiến code không thể tái sử dụng cho các pipeline chạy ngầm và khó unit test.
- **Thay thế bằng**: Sử dụng kiến trúc Clean Architecture - di chuyển core logic xử lý vào `core/` (`FormCleaner`, `LinkPatcher`), CLI chỉ nhận tham số và gọi core.
- **Nguồn**: Session b9348884-dab8-4515-934b-8a55e51d9e56, 2026-06-28

---

## Patterns (Mẫu tốt)

### Align & Extract (Tái cấu trúc bảng Markdown)
- **Ngữ cảnh**: Khi các bảng biểu phức tạp bị convert lỗi thành văn bản thô chạy dọc trong Markdown.
- **Vấn đề giải quyết**: Chuyển đổi thủ công mất thời gian và dễ nhầm lẫn số liệu. Dùng regex thô ráp không xử lý được các ô merge cột/dòng phức tạp.
- **Giải pháp**: Sử dụng `pandoc` với định dạng đầu ra `gfm` (tự động xuất bảng HTML `<table>` để bảo toàn merge cell), sau đó viết script đối chiếu trích xuất đúng bảng HTML đè lại vào vị trí lỗi trong file `.md` hiện tại, giữ nguyên frontmatter gốc.
- **Nguồn**: Session b9348884-dab8-4515-934b-8a55e51d9e56, 2026-06-28

### AI-assisted Title Recovery (Phục hồi tiêu đề biểu mẫu)
- **Ngữ cảnh**: Biểu mẫu thô bị nhận nhầm các dòng placeholder chấm lửng ở đầu làm tiêu đề.
- **Vấn đề giải quyết**: Xóa mù quáng bằng Regex dễ làm mất cấu trúc tiêu đề.
- **Giải pháp**: Gửi 20 dòng đầu của file lên model non-reasoning chuyên bóc tách metadata (như `gemini-3.1-flash-lite`), yêu cầu suy luận ra tiêu đề chính thức của form, sau đó gộp các dòng viết hoa liên tiếp thành 1 dòng duy nhất để cập nhật frontmatter/heading.
- **Nguồn**: Session b9348884-dab8-4515-934b-8a55e51d9e56, 2026-06-28

### Quad-View Generative Audit
- **Ngữ cảnh**: Khi cần kiểm tra đụng độ giữa nhiều bản vẽ (Arch, KC, MEP, PCCC) với nhau mà không có mô hình 3D.
- **Vấn đề giải quyết**: LLMs xử lý rất kém số liệu kích thước và text trải trên 4 pdf khác nhau.
- **Giải pháp**: 
  1. Render từng trang PDF ra ảnh PNG (dpi 150-300).
  2. Gộp 4 ảnh thành 1 mảng 2x2 (Quad-View) với nhãn tên rõ ràng bằng hàm `CompositeBuilder`.
  3. Đẩy 1 ảnh duy nhất (Quad-view) vào multimodal API. AI có khả năng liên kết không gian (Spatial Reasoning) giữa 4 góc nhìn cực kỳ xuất sắc.
- **Nguồn**: QC Audit Khối B BV NTP

### Concurrent Batch AI Processing
- **Ngữ cảnh**: Chạy LLM audit trên quy mô lớn nhiều object/level.
- **Vấn đề giải quyết**: Thời gian chạy tuần tự quá lâu.
- **Giải pháp**: Xây dựng hàm `async` tạo array mapping và gọi `asyncio.gather(*tasks)` để đẩy 5 request lên LiteLLM Gateway đồng thời.
- **Nguồn**: Chạy Batch Audit cho Tầng 1, 2, 3, Mái Khối B.

### Context-Aware Workflow Commands
- **Ngữ cảnh**: Xây dựng Slash Command Workflow (như `/run-qc-pipeline`) yêu cầu truyền đường dẫn project hiện tại.
- **Vấn đề giải quyết**: User phải gõ thủ công đường dẫn rất dài, dễ sai sót.
- **Giải pháp**: Hướng dẫn Agent phân tích `<ADDITIONAL_METADATA>` để trích xuất `TARGET_PROJECT` tự động dựa trên file/cửa sổ đang mở, tự động chèn vào chuỗi lệnh bọc `// turbo`.
- **Nguồn**: Thiết kế workflow `/run-qc-pipeline`.

### Data Hand-off Automation (Zero-Touch UX)
- **Ngữ cảnh**: Chuyển giao dữ liệu từ bước Discovery (OCR Text) sang bước Batch Orchestrator (Render API).
- **Vấn đề giải quyết**: Tránh để con người chạm vào file map dữ liệu như CSV, sinh ra Human Error (gõ nhầm mã bản vẽ).
- **Giải pháp**: Buộc Output chuẩn của Skill 1 (e.g. `Coordination_Matrix.csv`) phải là Input chuẩn của Skill 2. Xóa bỏ hoàn toàn Hardcode mapping.
- **Nguồn**: SDK `ccba-ai-qc-batch-orchestrator`.

---

## Solutions (Giải pháp tham chiếu)

### Unicode Encode Error on Windows Console
- **Vấn đề**: Khi in chuỗi Unicode tiếng Việt ra Windows Console bằng `rich.console` bị crash lỗi `UnicodeEncodeError: 'charmap' codec can't encode character...` do terminal sử dụng encoding mặc định cp1252.
- **Giải pháp**: Thiết lập `sys.stdout.reconfigure(encoding='utf-8')` ở đầu file và bọc các lệnh in console Unicode bằng khối `try...except` với fallback sang `print(text.encode('utf-8', errors='ignore').decode('utf-8'))`.
- **Liên kết**: `clean_form_cmd.py`
- **Nguồn**: Session b9348884-dab8-4515-934b-8a55e51d9e56, 2026-06-28

### Multimodal Call qua AI Gateway
- **Vấn đề**: Hàm `ai.chat` (LiteLLM wrapper chung) bị lỗi kwargs `images` khi model endpoint chối từ.
- **Giải pháp**: Sử dụng client wrapper của `openai.OpenAI` và đưa chuỗi base64 vào format của Vision API:
```text
messages=[{
    "role": "user",
    "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": { "url": f"data:image/png;base64,{b64}" }},
    ]
}]
```
- **Liên kết**: `audit_engine.py`

---

## Configurations (Cấu hình tối ưu)

| Setting | Value | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| Render DPI | 150 | Giảm thời gian load Quad-View nhưng vẫn đủ nét text nhỏ | AI OCR / Vision |
| Concurrency | 4-5 reqs | AI Gateway local DGX Server chịu tải tốt | Xử lý đa tầng |

## 📋 Session Retrospective Summary (Updated)

### Phiên làm việc
- **Ngày**: 2026-06-28
- **Mục tiêu**: Giải quyết triệt để lỗi vỡ bảng biểu, placeholder biểu mẫu trong gói Luật Xây dựng 2025. Tái cấu trúc kỹ năng Markdown thành Master & Sub-skills.
- **Kết quả**: ✅ Hoàn thành. Cập nhật thành công toàn bộ tài liệu pháp lý, nâng cấp `mdconverter` lên Clean Architecture và bổ sung 3 subcommand. Đăng ký catalog và cập nhật workflow 3 bước tự động.

### Kiến thức mới
- [x] 2 patterns mới (Align & Extract, AI-assisted Title Recovery)
- [x] 1 anti-patterns mới (CLI Monolith for Data Processing)
- [x] 1 solutions mới (Unicode Encode Error on Windows Console)

### Đề xuất cập nhật đã hoàn thành
- [x] Cập nhật Workspace Rules (AGENTS.md): Cưỡng chế quy tắc kiểm tra tái sử dụng công cụ từ Hub (Reuse-First Gate) thông qua Kế hoạch triển khai.
- [x] Tạo/Cập nhật workflow: Đã cập nhật `convert-markdown.md` thành quy trình 3 bước tự động.
- [x] Đề xuất/Tạo Skills mới: Đã tạo Master Skill và 3 Sub-skills xử lý Markdown trong `.agent/skills/`.

### Ghi chú cho phiên tiếp theo
Tự động áp dụng quy tắc Reuse-First Gate và gọi các subcommand `process-table`, `clean-form` và `patch-links` của `mdconvert` để làm sạch định dạng tài liệu mới ngay khi ingest.
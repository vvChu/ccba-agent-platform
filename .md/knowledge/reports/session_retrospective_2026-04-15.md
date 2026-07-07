# Session Retrospective: Refactor mdconverter v2.2.0

**Ngày thực hiện:** 2026-04-15
**Phiên làm việc:** `7831c0b4-9f24-4b0b-8771-d252e0e6312f`

---

## 🚀 Thành tựu chính

### 1. Refactor Kiến trúc (Giải quyết 12 Issues)
Chúng ta đã thực hiện một cuộc đại tu kiến trúc để biến `mdconverter` từ một CLI tool đơn giản thành một pipeline xử lý chuyên nghiệp:
- **Registry & Config (C1, C2):** Chuyển sang singleton pattern và lazy initialization, đảm bảo thread-safe và test-safe.
- **Tách biệt Logic (H1, H2):** Di chuyển logic VN Legal ra khỏi base class. Tách business logic từ CLI (`convert_cmd.py`) sang `ConversionPipeline`.
- **Plugin System (H3):** Loại bỏ `PluginManager` phức tạp và không hiệu quả, thay bằng `PostProcessor` protocol tinh gọn.
- **Async Safety (H4, M3):** Xử lý triệt để việc lồng event loop và chặn (blocking) I/O bằng `asyncio.to_thread`.
- **Quality & Error Handling (M1, M4):** Cải thiện công thức tính điểm chất lượng, sửa lỗi timeout cho Gateway.

### 2. PDFAnalyzer & Auto-Routing (v2.2.0)
Tích hợp `PyMuPDF` để phân tích file PDF ngay từ đầu vào:
- **Phân loại 4 cấp độ:** `text_rich`, `scanned`, `hybrid`, `drawing`.
- **Auto-Routing:** Tự động chọn model tối ưu (ví dụ: `qwen3.5-35b` cho văn bản số, `ocr-primary` cho hồ sơ scan).
- **Drawing Filter:** Nhận diện và bỏ qua các bản vẽ kỹ thuật oversized, giúp tiết kiệm chi phí và thời gian.

---

## 📈 Kết quả Kiểm thử
- **Pytest:** 145/145 passed (100% success).
- **Khảo sát thực tế:** Đã test trên bộ dữ liệu 104 file của dự án NTP Hospital (620MB), độ chính xác phân loại đạt ~95%.

---

## 💡 Bài học & Kinh nghiệm
- **PDF Survey là chìa khóa:** Việc khảo sát thực tế cho thấy 75% file là bản vẽ kỹ thuật, giúp chúng ta đưa ra quyết định "mạnh tay" là skip drawings để bảo vệ tài nguyên Gateway.
- **Lazy Init:** Việc lazy loading settings giúp tool khởi động nhanh hơn và tránh lỗi khi môi trường chưa cấu hình đầy đủ API Key.

---

## ⏭️ Tiếp theo (v2.3.0)
Mặc dù v2.2.0 đã rất ổn định, chúng ta vẫn còn các mục tiêu nâng cao:
1. **Hybrid Routing:** Xử lý per-page routing cho tài liệu lai (text + scan).
2. **Payload Chunking:** Phân chia PDF lớn (50MB+) thành các block 10-20 trang trước khi gửi AI.
3. **Drawing Support:** Thêm mode --extract-drawing cho phép dùng Qwen 3.5 để bóc tách text từ bản vẽ.

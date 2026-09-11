---
name: ccba-youtube-learn
description: Khảo cổ học Niềm tin (Belief Archaeology) thông qua bóc tách phụ đề và
  hình ảnh slide học thuật từ các video YouTube/bài giảng.
disable-model-invocation: true
user-invocable: true
command: /ccba-youtube-learn
bundle: _core
tier: kernel
gpi:
  s: 3.0
  k: 2.0
  a: 1.0
  p: 1.0
triggers:
- ccba-youtube-learn
- youtube learn
- bóc tách phụ đề
- slide học thuật
- youtube
- belief archaeology
---
# 🧠 Kỹ năng: youtube-learn (Belief Archaeology)

Kỹ năng này chịu trách nhiệm phân tích sâu các video bài giảng, hội thảo (YouTube hoặc tệp video ngoài) để bóc tách toàn bộ phụ đề và các khung hình chứa slide tri thức học thuật độc nhất (không giới hạn số lượng), từ đó tổng hợp kiến thức bài học và "khảo cổ" thế giới quan, giả định ngầm của diễn giả.

---

## 📋 Tiêu chí hoàn thành (Completion Criteria)

Kỹ năng chỉ được coi là thực hiện thành công khi tạo ra cấu trúc thư mục và tệp tin động thuộc **Cohesive Topic Folder** tương ứng tại thư mục cục bộ của dự án:

```
[project_root]/.md/projects/[Ten_De_Tai]/
├── raw_transcript_[video_id].txt     # Phụ đề được chuẩn hóa định dạng (30s hoặc đoạn văn 5 câu)
├── notes_concept_[video_id].md        # Tổng hợp kiến thức, định nghĩa, sơ đồ và mã nguồn học được
├── notes_worldview_[video_id].md      # Khảo cổ thế giới quan, giả định ngầm của diễn giả
├── notes_speaker_[video_id].md        # Hồ sơ diễn giả (học vị, kinh nghiệm, phong cách)
└── images_[video_id]/                 # Thư mục chứa các ảnh slide tĩnh độc nhất (.webp) của video
    ├── yt_[video_id]_frame_001_ts60.webp
    └── ...
```

---

## 🛠️ Hướng dẫn thực thi các Phase

### Phase 1: Chuẩn bị & Xác thực Đầu vào
*   **Tham số yêu cầu:** 
    *   Địa chỉ URL của video (hoặc đường dẫn tệp video nội bộ).
    *   Tham số tùy chọn `--project` hoặc `-p`: Tên đề tài/dự án `Ten_De_Tai` để định vị thư mục **Cohesive Topic Folder** (mặc định lưu vào `default_topic` nếu chạy độc lập).
    *   Thư mục lưu trữ đầu ra (mặc định tự động trỏ về `.md/projects/[Ten_De_Tai]/` theo cấu trúc Cohesive Topic Folder).
    *   Tham số tùy chọn `--speaker`: Tên diễn giả thực tế (nếu không truyền, hệ thống sẽ tự động gọi LLM trích xuất tên diễn giả từ phụ đề hoặc lấy tên người đăng tải video).
*   **Tiền kiểm duyệt (Pre-checks):** 
    *   Xác minh các thư viện Python: yt_dlp, PIL (Pillow). Nếu thiếu Pillow, in cảnh báo và bỏ qua bước khử trùng lặp ảnh bằng Hash (mặc định đã tích hợp nén WebP chất lượng 80 để tiết kiệm dung lượng).
    *   Xác minh sự hiện diện của `ffmpeg` trong PATH hoặc các đường dẫn Windows WinGet mặc định. Nếu thiếu, tự động kích hoạt chế độ **Text-Only Fallback** (chỉ lấy transcript, bỏ qua bóc hình ảnh).
    *   Đối với các URL không phải YouTube, kiểm tra xem đã cấu hình biến môi trường AI_GATEWAY_KEY (hoặc OPENAI_API_KEY) để gọi Whisper STT chưa. Nếu thiếu, kết thúc tác vụ và in ra thông báo lỗi yêu cầu thiết lập API Key để tiếp tục.
*   **Tiêu chí hoàn thành:** Xác thực thành công các tham số đầu vào, kiểm tra đầy đủ các phụ thuộc hệ thống và ghi nhận chế độ hoạt động (Normal / Text-Only Fallback) trong ngữ cảnh chạy của Agent.

### Phase 2: Ingest Phụ đề & Âm thanh
*   **Phụ đề gốc:** Ưu tiên dùng thư viện YouTubeTranscriptApi để tải phụ đề chính thống từ YouTube (ngôn ngữ ưu tiên: `vi`, `en`). Gom nhóm phụ đề theo mốc thời gian **30 giây** dạng `[mm:ss] text`.
*   **Whisper STT Fallback:** Nếu API phụ đề lỗi hoặc video không phải YouTube, tải luồng âm thanh chất lượng thấp (`worstaudio`), gửi file lên API Gateway bằng `ai.transcribe()` và hậu xử lý chia văn bản thô thành các **đoạn văn 5 câu** liền mạch.
*   **Tiêu chí hoàn thành:** Toàn bộ transcript thô của video được thu thập và lưu trữ thành công dưới dạng văn bản gom nhóm theo mốc thời gian.

### Phase 3: Ingest Hình ảnh Đa phương thức (Visual Ingestion)
*   **Chụp ảnh CDN (Stage 1 Storyboard):** Tìm kiếm và tải ảnh storyboard grid của Google từ YouTube CDN, thực hiện cắt crop theo các mốc thời gian chương học (Chapters) hoặc đỉnh tương tác nhiệt (Viewer Heatmap peaks).
*   **Chụp ảnh video thô (Stage 2 Fallback):** Nếu không có storyboard CDN, tải video phân giải thấp (480p/720p) và dùng `ffmpeg` trích xuất ảnh tĩnh tại các mốc thời gian tương ứng.
*   **Khử trùng lặp ảnh (Deduplication):** Sử dụng hàm băm hình ảnh Perceptual Hash để lọc bỏ các ảnh slide bị lặp lại.
*   **Lọc Talking Head:** Sử dụng mô hình qua `ccba-ai` đóng vai trò LLM-as-Judge để phân tích danh sách ảnh và lọc bỏ triệt để các khung hình chỉ chụp mặt diễn giả đứng nói, giữ lại 100% các slide có biểu đồ, mã nguồn hoặc chữ (không khống chế giới hạn trần 10 ảnh).
*   **Tiêu chí hoàn thành:** Danh sách các ảnh slide WebP tĩnh độc bản được lọc sạch mặt diễn giả và lưu trữ thành công trong thư mục `images_[video_id]/`.

### Phase 4: Tổng hợp Kiến thức (Belief Archaeology Synthesis)
Sử dụng LLM để phân tích toàn bộ Transcript và danh sách hình ảnh đã lọc, sau đó xuất ra:
1.  **`notes_concept.md`**: Tóm tắt kiến thức, lưu trữ hình ảnh slide tương ứng dưới dạng các liên kết markdown `![Alt Text]` `(./images/tên_file.webp)` kèm mô tả alt-text sinh động.
2.  **`notes_worldview.md`**: Bóc tách các giả định ẩn sâu bên dưới lập luận của người thuyết trình.
3.  **`notes_speaker.md`**: Tổng hợp tiểu sử và phương pháp tiếp cận của diễn giả.
*   **Tiêu chí hoàn thành:** Cả 3 tệp tin `notes_concept.md`, `notes_worldview.md`, và `notes_speaker.md` được tạo lập và điền đầy đủ dữ liệu phân tích đúng cấu trúc thư mục Cohesive Topic Folder.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*

---
name: notebooklm-connector
description: Interact with Google NotebookLM to import YouTube, URLs, PDFs, and Drive docs, perform RAG query, generate Audio Overview, and handle auth, polling, and retry loops.
user-invocable: true
when_to_use: Dùng khi cần trích xuất tóm tắt, truy vấn RAG, hoặc sinh các tài liệu cấu trúc (Podcast, Quiz, Slides, Mind Map, Infographic, Video, v.v.) từ các tài liệu lớn, cũng như quản trị Notebooks và Sources trên Cloud.
category: dev-tools
keywords: [notebooklm, rag, summary, youtube, audio, podcast, quiz, slides, mindmap, infographic, admin]
argument-hint: "<source-path-or-url> [--extract|--query|--audio|--quiz|--slides|--mindmap|--infographic|--study-guide|--data-table|--flashcards|--report|--video|--list-notebooks|--delete-notebook|--share-notebook|--list-sources|--delete-source] [args]"
metadata:
  author: CCBA
  version: 1.3.0
---

# NotebookLM Connector

Kỹ năng này dẫn dắt Agent tương tác tự động với Google NotebookLM thông qua thư viện `notebooklm-py` để trích xuất tri thức, RAG query cô lập, sinh các tài liệu cấu trúc (Structured Artifacts) và quản trị Notebooks/Sources.

## Quy trình Vận hành của Agent

---

### Bước 1: Kiểm tra Môi trường và Xác thực (Auth Check)

1.  Kiểm tra xem thư viện `notebooklm` có import được trong Python không. Nếu chưa có, dừng lại và yêu cầu người dùng chạy lệnh:
    `pip install notebooklm-py`
2.  Kiểm tra phương thức xác thực:
    *   **Môi trường headless / chạy ngầm (CI/CD):** Đảm bảo đã cấu hình biến môi trường `NOTEBOOKLM_SESSION_COOKIE` hoặc `NOTEBOOKLM_COOKIES_JSON` trong tệp `.env`. Script helper sẽ tự động chuyển đổi và inject cookie vào Playwright storage tạm.
    *   **Môi trường desktop cục bộ:** Nếu chưa cấu hình cookie, chạy helper script để tự động tải cấu hình lưu sẵn trên hệ thống:
        `python scripts/notebooklm_helper.py check-auth`
3.  Nếu gặp lỗi Authentication:
    *   Agent **bắt buộc** dừng tiến trình.
    *   Hướng dẫn người dùng chạy lệnh đăng nhập một lần trên trình duyệt để cập nhật session cookie:
        `python -m notebooklm login`
    *   Sau khi người dùng đăng nhập xong, chạy lại bước kiểm tra để tiếp tục.

---

### Bước 2: Quét Bảo mật thông qua Maskara Gate

Trước khi tải tài liệu cục bộ lên đám mây của Google, Agent **bắt buộc** phải chạy quét bảo mật qua `scripts/maskara.py`:
1.  **Phát hiện API Keys/Tokens nhạy cảm:** Nếu phát hiện các token OpenAI, Anthropic, Google, hoặc GitHub, tiến trình tải lên sẽ bị chặn đứng lập tức để tránh lộ lọt thông tin.
2.  **Khử PII & Database URL:** Nếu phát hiện số điện thoại, email hoặc URL cơ sở dữ liệu, script sẽ tự động che giấu (redact) thông tin nhạy cảm và xuất một bản copy làm sạch tạm thời tại `.md/scratch/redacted/` để upload. Tệp tạm này sẽ bị xóa ngay sau khi nạp nguồn thành công.

---

### Bước 3: Đối soát nội dung (SHA-256 Hash) & Quản lý Quota

1.  **Unique Source Hashing:** Helper tự động tính mã SHA-256 của file tài liệu và đối chiếu với registry cục bộ tại `.md/knowledge/sources_registry.yaml`.
    *   Nếu phát hiện nội dung hoàn toàn trùng khớp, tái sử dụng `source_id` đã có để tiết kiệm quota và tài nguyên.
    *   Nếu phát hiện nội dung đã thay đổi, tự động xóa bản nguồn cũ trên Cloud trước rồi mới upload bản mới.
2.  **Subscription Tier Quota Warn:** Tự động phát hiện dung lượng giới hạn dựa trên Subscription Tier của tài khoản (Free vs. Pro/Workspace). Nếu số nguồn trong Notebook vượt quá 90% quota, hệ thống sẽ tự động dọn dẹp các nguồn không còn liên kết cục bộ (Garbage Collection).

---

### Bước 4: Nhận diện Usecase và Thực thi

Tùy theo tham số chế độ người dùng yêu cầu, thực thi subcommand tương ứng:

#### A. Nhóm sinh Tri thức cấu trúc (Structured Artifacts)
*   **Extract (Tóm tắt Markdown)**: `python scripts/notebooklm_helper.py extract --source "<source>" --output ".md/extracted_docs/summaries/"`
*   **Query (RAG hỏi đáp)**: `python scripts/notebooklm_helper.py query --source "<source>" --prompt "<câu-hỏi>"`
*   **Audio (Podcast MP3)**: `python scripts/notebooklm_helper.py audio --source "<source>"`
*   **Quiz (Trắc nghiệm JSON)**: `python scripts/notebooklm_helper.py quiz --source "<source>"`
*   **Slides (Slide thuyết trình PDF)**: `python scripts/notebooklm_helper.py slides --source "<source>"`
*   **Mind Map (Sơ đồ tư duy JSON)**: `python scripts/notebooklm_helper.py mindmap --source "<source>"`
*   **Infographic (Infographic PDF)**: `python scripts/notebooklm_helper.py infographic --source "<source>"`
*   **Study Guide (PDF)**: `python scripts/notebooklm_helper.py study-guide --source "<source>"`
*   **Data Table (Bảng trích xuất CSV)**: `python scripts/notebooklm_helper.py data-table --source "<source>" --instructions "<chỉ-dẫn>"`
*   **Flashcards (JSON)**: `python scripts/notebooklm_helper.py flashcards --source "<source>"`
*   **Report (Markdown)**: `python scripts/notebooklm_helper.py report --source "<source>" --format briefing_doc`
*   **Video (MP4)**: `python scripts/notebooklm_helper.py video --source "<source>" --format explainer`

#### B. Nhóm quản trị Sổ tay & Nguồn (CRUD Admin)
*   **List Notebooks (Liệt kê Notebooks)**:
    `python scripts/notebooklm_helper.py list-notebooks`
*   **Delete Notebook (Xóa Notebook)**:
    `python scripts/notebooklm_helper.py delete-notebook --notebook-id "<id>"`
*   **Share Notebook (Chia sẻ & Lấy Share URL)**:
    `python scripts/notebooklm_helper.py share-notebook [--notebook-id "<id>"]`
*   **List Sources (Liệt kê các nguồn trong Notebook)**:
    `python scripts/notebooklm_helper.py list-sources [--notebook-id "<id>"]`
*   **Delete Source (Xóa nguồn trong Notebook)**:
    `python scripts/notebooklm_helper.py delete-source --source-id "<id>" [--notebook-id "<id>"]`

---

## Tiêu chí hoàn thành (Completion Criteria)

*   [x] **Bảo mật:** Mọi tệp tin trước khi tải lên phải pass qua chốt chặn Maskara Gate.
*   [x] **Chất lượng:** Mọi tài liệu đầu ra dạng Markdown hoặc PDF phải được lưu vào đúng thư mục chức năng, được bổ sung Frontmatter truy vết và Disclaimer CCBA.
*   [x] **Đồng bộ Registry:** Lệnh `delete-source` phải tự động gỡ bỏ bản ghi nguồn tương ứng trong registry cục bộ `.md/knowledge/sources_registry.yaml` để tránh dữ liệu bị lệch pha.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*

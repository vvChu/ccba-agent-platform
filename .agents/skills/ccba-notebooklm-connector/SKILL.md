---
name: ccba-notebooklm-connector
description: Interact with Google NotebookLM to import YouTube, URLs, PDFs, and Drive
  docs, perform RAG query, generate Audio Overview, and handle auth, polling, and
  retry loops.
user-invocable: true
command: /ccba-notebooklm-connector
when_to_use: Dùng khi cần trích xuất tóm tắt, truy vấn RAG, hoặc sinh các tài liệu
  cấu trúc (Podcast, Quiz, Slides, Mind Map, Infographic, Video, v.v.) từ các tài
  liệu lớn, cũng như quản trị Notebooks và Sources trên Cloud.
category: dev-tools
gpi:
  s: 3.0
  k: 3.0
  a: 4.0
  p: 1.0
keywords:
- notebooklm
- rag
- summary
- youtube
- audio
- podcast
- quiz
- slides
- mindmap
- infographic
- admin
argument-hint: <source-path-or-url> [--extract|--query|--audio|--quiz|--slides|--mindmap|--infographic|--study-guide|--data-table|--flashcards|--report|--video|--list-notebooks|--delete-notebook|--share-notebook|--list-sources|--delete-source]
  [args]
metadata:
  author: CCBA
  version: 1.3.0
bundle: _core
layer: _core
---
# NotebookLM Connector

Kỹ năng này dẫn dắt Agent tương tác tự động với Google NotebookLM thông qua thư viện `notebooklm-py` để trích xuất tri thức, RAG query cô lập, sinh các tài liệu cấu trúc (Structured Artifacts) và quản trị Notebooks/Sources.

## Quy trình Vận hành của Agent

---

### Bước 1: Kiểm tra Môi trường và Xác thực (Auth Check & Tri-Tier Vault - ADR 0035)

1.  Kiểm tra xem thư viện `notebooklm` có import được trong Python không (`pip install notebooklm-py`).
2.  Kiểm tra phương thức xác thực:
    *   Chạy lệnh đăng nhập phiên VIP/Google trên hệ thống:
        `python -m notebooklm login` (hoặc `python -m ccba_legal login`).
3.  **Đồng bộ Tri thức lên Cloud Vault & NotebookLM (ADR 0023, ADR 0035):**
    *   Chạy script đồng bộ danh mục 308+ tài sản RAG chuẩn hóa:
        ```powershell
        python scripts/sync_notebooklm_knowledge.py --notebook-id <notebook_id>
        # Hoặc qua CLI facade:
        python scripts/spoke/spoke_cli.py sync-notebooklm --notebook-id <notebook_id>
        ```
    *   Khi nạp văn bản mới bằng `python -m ccba_legal ingest ... --upload-drive`, các file Word gốc được tự động đẩy lên Google Drive Vault `CCBA_Legal_Vault` và chuyển đổi sang Native Google Docs sẵn sàng nạp 1-click vào NotebookLM.
- **Tiêu chí hoàn thành:** Môi trường thư viện sẵn sàng và phiên đăng nhập Google/NotebookLM được xác thực hợp lệ.

---

### Bước 2: Quét Bảo mật thông qua Maskara Gate

Trước khi tải tài liệu cục bộ lên đám mây của Google, Agent **bắt buộc** phải chạy quét bảo mật:
1.  **Phát hiện API Keys/Tokens nhạy cảm:** Chặn đứng lập tức nếu phát hiện các token OpenAI, Anthropic, Google, hoặc GitHub.
2.  **Khử PII & Database URL:** Tự động che giấu (redact) thông tin nhạy cảm trước khi đồng bộ.
- **Tiêu chí hoàn thành:** Quét sạch mọi API keys, tokens và thông tin nhạy cảm trước khi đồng bộ lên Cloud.

---

### Bước 3: Đối soát nội dung (SHA-256 Hash) & Quản lý Quota

1.  **Unique Source Hashing:** Helper tự động tính mã SHA-256 của file tài liệu và đối chiếu với registry cục bộ tại `.md/data/sources_registry.yaml`.
    *   Nếu phát hiện nội dung hoàn toàn trùng khớp, tái sử dụng `source_id` đã có để tiết kiệm quota và tài nguyên.
    *   Nếu phát hiện nội dung đã thay đổi, tự động xóa bản nguồn cũ trên Cloud trước rồi mới upload bản mới.
2.  **Subscription Tier Quota Warn:** Tự động phát hiện dung lượng giới hạn dựa trên Subscription Tier của tài khoản (Free vs. Pro/Workspace). Nếu số nguồn trong Notebook vượt quá 90% quota, hệ thống sẽ tự động dọn dẹp các nguồn không còn liên kết cục bộ (Garbage Collection).
- **Tiêu chí hoàn thành:** Mã băm SHA-256 được đối soát để tránh trùng lặp nguồn và quota notebook được kiểm soát an toàn.

---

### Bước 4: Nhận diện Usecase và Thực thi

Tùy theo tham số chế độ người dùng yêu cầu, thực thi subcommand tương ứng:

#### A. Nhóm sinh Tri thức cấu trúc (Structured Artifacts)
*   **Extract (Tóm tắt Markdown)**: `python -m ccba_notebooklm extract --source "<source>" --output ".md/extracted_docs/summaries/"`
*   **Query (RAG hỏi đáp)**: `python -m ccba_notebooklm query --source "<source>" --prompt "<câu-hỏi>"`
*   **Audio (Podcast MP3)**: `python -m ccba_notebooklm audio --source "<source>"`
*   **Quiz (Trắc nghiệm JSON)**: `python -m ccba_notebooklm quiz --source "<source>"`
*   **Slides (Slide thuyết trình PDF)**: `python -m ccba_notebooklm slides --source "<source>"`
*   **Mind Map (Sơ đồ tư duy JSON)**: `python -m ccba_notebooklm mindmap --source "<source>"`
*   **Infographic (Infographic PDF)**: `python -m ccba_notebooklm infographic --source "<source>"`
*   **Study Guide (PDF)**: `python -m ccba_notebooklm study-guide --source "<source>"`
*   **Data Table (Bảng trích xuất CSV)**: `python -m ccba_notebooklm data-table --source "<source>" --instructions "<chỉ-dẫn>"`
*   **Flashcards (JSON)**: `python -m ccba_notebooklm flashcards --source "<source>"`
*   **Report (Markdown)**: `python -m ccba_notebooklm report --source "<source>" --format briefing_doc`
*   **Video (MP4)**: `python -m ccba_notebooklm video --source "<source>" --format explainer`

#### B. Nhóm quản trị Sổ tay & Nguồn (CRUD Admin)
*   **List Notebooks (Liệt kê Notebooks)**:
    `python -m ccba_notebooklm list-notebooks`
*   **Delete Notebook (Xóa Notebook)**:
    `python -m ccba_notebooklm delete-notebook --notebook-id "<id>"`
*   **Share Notebook (Chia sẻ & Lấy Share URL)**:
    `python -m ccba_notebooklm share-notebook [--notebook-id "<id>"]`
*   **List Sources (Liệt kê các nguồn trong Notebook)**:
    `python -m ccba_notebooklm list-sources [--notebook-id "<id>"]`
*   **Delete Source (Xóa nguồn trong Notebook)**:
    `python -m ccba_notebooklm delete-source --source-id "<id>" [--notebook-id "<id>"]`
- **Tiêu chí hoàn thành:** Hoàn tất thực thi usecase chỉ định và xuất artifact đúng định dạng và thư mục quy định.

---

## Tiêu chí hoàn thành (Completion Criteria)

*   [x] **Bảo mật:** Mọi tệp tin trước khi tải lên phải pass qua chốt chặn Maskara Gate.
*   [x] **Chất lượng:** Mọi tài liệu đầu ra dạng Markdown hoặc PDF phải được lưu vào đúng thư mục chức năng, được bổ sung Frontmatter truy vết và Disclaimer CCBA.
*   [x] **Đồng bộ Registry:** Lệnh `delete-source` phải tự động gỡ bỏ bản ghi nguồn tương ứng trong registry cục bộ `.md/data/sources_registry.yaml` để tránh dữ liệu bị lệch pha.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*

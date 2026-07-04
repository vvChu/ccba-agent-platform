# Bản tóm tắt Codebase (Codebase Summary)

Tài liệu này cung cấp cái nhìn tổng quan về cấu trúc thư mục, các packages thành phần và kiến trúc cốt lõi của dự án **ccba-agent-platform**.

---

## 1. Bản đồ Thư mục (Codebase Map)

```text
ccba-agent-platform/
├── .agents/                        # Cấu hình AI Agent & Tri thức Platform (Layer 1)
│   ├── templates/                  # Biểu mẫu tài liệu kỹ thuật chuẩn (PDR, Architecture)
│   ├── skills/                     # Các kỹ năng chuyên biệt của Agent (Docs Validator, Maskara, AI SDK)
│   └── workflows/                  # Các kịch bản chạy Slash Command (/ccba-docs, /ccba-handoff)
├── .md/                            # Central Knowledge Base của dự án (Layer 2)
│   ├── knowledge/                  # Báo cáo nghiên cứu, tài liệu kiến trúc, roadmap tĩnh
│   ├── seminars/                   # Biên bản tóm tắt các buổi thảo luận kỹ thuật
│   └── scratch/                    # Các file tạm, logs, backups và repomix output
├── packages/                       # Các thư viện & packages Python nội bộ
│   └── ccba-ai/                    # SDK kết nối AI Gateway LiteLLM (Server Spark)
├── scripts/                        # Các công cụ tự động hóa & kiểm định
│   ├── validate_docs.py            # Công cụ kiểm định tính chính xác của tài liệu Markdown
│   ├── repomix_pack.py             # Wrapper chạy công cụ đóng gói codebase Repomix
│   └── check_claudekit_updates.py  # Script kiểm tra cập nhật từ thượng nguồn ClaudeKit
├── src/                            # Mã nguồn ứng dụng Platform chính
├── docs/                           # Thư mục tài liệu tĩnh chính thức
└── input_documents/                # Thư mục chứa tài liệu thô đầu vào để xử lý
```

---

## 2. Các Thành phần Công nghệ & Thư viện Chính

- **Python SDK & AI Gateway**:
  - Package **`ccba-ai`** (`packages/ccba-ai`): Đóng vai trò là cổng LLM duy nhất của platform, cho phép gọi `from ccba_ai import ai` và kết nối trực tiếp với LiteLLM Server Spark (`100.83.192.30:8090`).
- **Công cụ Đóng gói & Kiểm định Tài liệu**:
  - **Repomix Wrapper** (`scripts/repomix_pack.py`): Đóng gói codebase tạm thời thành XML để nạp context cho Agent.
  - **Docs Linter** (`scripts/validate_docs.py`): Tự động phát hiện lỗi liên kết tương đối, code refs bị đổi tên/xóa và env vars thiếu trong `.env.example`.

---

## 3. Quy chuẩn Hoạt động của AI Agent
Mọi AI Agent hoạt động trên Platform này bắt buộc phải tuân thủ hiến pháp **`AGENTS.md`** bao gồm:
1.  **Reuse-First Gate**: Đánh giá khả năng tái sử dụng từ Hub catalog trước khi viết code mới.
2.  **Evidence-Based Writing**: Chỉ viết tài liệu dựa trên các ký hiệu có thật trong mã nguồn (được kiểm chứng qua `validate_docs.py`).
3.  **Size Limit Management**: Giới hạn tối đa 800 dòng (LOC) cho mỗi file tài liệu, tự động modular hóa nếu vượt quá.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*

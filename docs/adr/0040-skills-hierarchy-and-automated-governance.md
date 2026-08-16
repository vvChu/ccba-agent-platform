# ADR 0040: Phân Tầng Kỹ Năng Kim Tự Tháp 3 Tầng & Rào Chắn Quản Trị Tự Động (Hard CI Gate)

## Bối cảnh (Context)
Sau đợt tái cấu trúc kiến trúc Monorepo theo ADR-0011 (hoàn thành 4 Deep Seams `ConversionPipeline`, `TVPLCrawler`, `VBHNEngine`, `QCAuditPipeline`), hệ thống Kỹ năng (`.agents/skills/`) đối mặt với các vấn đề:
1. **Context Bloat & Cognitive Overload:** Có tới 85 file `SKILL.md` nằm ngang hàng, làm phình to System Prompt khởi tạo của AI Agent.
2. **Shallow Sub-skills & Trùng lặp vật lý:** Nhiều sub-skills nhỏ (`table-reconstructor`, `form-template-cleaner`, `relative-link-patcher`) thực chất chỉ là các bước nội bộ bên trong Deep Seams nhưng lại tồn tại độc lập ở root `skills/` và bị duplicate trong thư mục con.
3. **Thiếu cơ chế quản trị tự động:** Chưa có rào chắn CI để ngăn chặn việc tạo thêm các skill nông, trùng lặp tên hoặc làm tràn ngân sách ngữ cảnh (*Context Budget Ceiling*).

---

## Quyết định Kiến trúc (Decisions)

### 1. Mô hình Kim Tự Tháp 3 Tầng (3-Tier Skills Hierarchy)

```mermaid
graph TD
    subgraph Tier 1: Master Deep Skills [Model-Invoked — Giới hạn <= 10 Skills / Bundle]
        M1[markdown-document-processing]
        M2[ccba-legal-intel]
        M3[ccba-ai-qc-audit]
        M4[ai-gateway-sdk]
    end

    subgraph Tier 2: Progressive References [Chỉ nạp khi cần chi tiết — Progressive Disclosure]
        M1 --> R1[references/table_reconstruction.md]
        M1 --> R2[references/form_cleaner.md]
        M1 --> R3[references/link_patcher.md]
        M3 --> R4[references/quad_view_matrix.md]
    end

    subgraph Tier 3: User Workflows & Slash Commands [disable-model-invocation: true — 0 Token nền]
        W1[/ccba-convert-markdown]
        W2[/ccba-tvpl-vip-crawler]
        W3[/ccba-run-qc-pipeline]
        W4[/ccba-implement / /ccba-tdd]
    end
```

- **Tier 1 (Master Deep Skills - Model Invoked):** Đại diện cho các năng lực đầu cuối hoàn chỉnh, bảo trợ bởi Deep Seams. Khống chế nghiêm ngặt $\le 10$ skills cho mỗi Bundle (toàn platform duy trì ~25 model-invoked skills). Mô tả `description` súc tích $\le 180$ ký tự để Agent nhận diện trong ngôn ngữ tự nhiên.
- **Tier 2 (Progressive References):** Các tài liệu hướng dẫn kỹ thuật chi tiết của sub-skills được chuyển vào thư mục `references/*.md` của Master Skill tương ứng. Xóa bỏ các thư mục sub-skill trùng lặp ở root.
- **Tier 3 (User Workflows - User Invoked):** 100% các quy trình mang tính nghi thức, có sự điều khiển của con người (`/ccba-implement`, `/ccba-new-feature`, `/ccba-wait-what`...) được gắn `disable-model-invocation: true` để tiêu tốn **0 token** trong System Prompt khởi tạo.

### 2. Bộ Rào Chắn CI 4 Tầng Tự Động (`skill_auditor.py`)

Tích hợp vào `scripts/governance/skill_auditor.py` (chạy qua `validate_skills.py`) các Hard Gates trả về `Exit Code 1` nếu vi phạm:
1. **Zero-Duplicate Gate:** Cấm tuyệt đối trùng lặp `name` hoặc trùng lặp file `SKILL.md` giữa root và thư mục con.
2. **Context Budget Ceiling:** Trong mỗi Bundle (`_core`, `_qc`, `_consulting`, `_bim`), tổng số kỹ năng `model_invoked` không được vượt quá **10 skills** để bảo toàn vùng nhớ *Smart Zone* (< 120k tokens).
3. **Taxonomy Metadata Gate:** Bắt buộc khai báo trường `bundle` và `role` (`master_skill`, `router`, `sub_reference`, `workflow_adapter`).
4. **Shallow Skill Warning Gate:** Cảnh báo và hướng dẫn chuyển đổi nếu một skill độc lập quá ngắn (< 35 dòng) không có Deep Seam bảo trợ.

---

## Hệ quả & Lợi ích (Consequences)

1. **Khử 100% trùng lặp vật lý & Giảm 70% Context-Loaded Skills:** Xóa bỏ 6 thư mục trùng lặp/nông (từ 85 xuống còn 79 tệp `SKILL.md` hợp lệ), giảm số lượng skill nạp vào prompt khởi tạo từ 85 xuống còn 25 `model_invoked` skills (hướng tới lộ trình dài hạn tiếp tục hợp nhất đạt ~35–40 files toàn nền tảng).
2. **Tiết kiệm 75% Context Token ban đầu:** Nhờ chuyển 57 User Workflows và các ritual skills sang `disable-model-invocation: true`.
3. **Bảo tồn Single Source of Truth (SSOT):** Mọi tài liệu tham chiếu đều gom về đúng Master Skill sở hữu nó.

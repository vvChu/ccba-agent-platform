# Bản đồ Định hướng: Tinh chỉnh & Chuẩn hóa Nhóm Skill Xử lý Văn bản (`document-skills-refinement`)

> **Mô tả**: Bản đồ định hướng chuẩn hóa phân cấp (Master Skill vs Sub-Skill) và phân loại ảo (Virtual Tagging) cho nhóm các kỹ năng xử lý văn bản, tài liệu và file văn phòng trên CCBA Agent Platform.

---

## 🎯 Điểm đích (Destination)
Tối ưu hóa khả năng định tuyến (routing) và làm rõ mối quan hệ giữa các kỹ năng xử lý văn bản (Master Skills vs Sub-Skills) trong tài liệu và `catalog.yaml` mà **không thay đổi cấu trúc thư mục vật lý phẳng** của Platform, bảo đảm 100% tính tương thích ngược với các Spoke.

---

## 📌 Ghi chú (Notes)
- **Nguyên tắc cốt lõi**: Giữ cấu trúc thư mục phẳng `.agents/skills/<name>/` (tuân thủ Hiến pháp `AGENTS.md` - Rule KISS & Downstream Sync Safety).
- **Cơ chế phân loại**: Sử dụng **Phân loại Ảo (Virtual Tagging)** trong `catalog.yaml` và **Master/Sub-skill Metadata** trong phần YAML Frontmatter của các tệp `SKILL.md`.

---

## 🟢 Quyết định đã chốt (Decisions so far)

1. **Giữ nguyên cấu trúc thư mục phẳng**: Không gom nhóm thư mục vật lý để tránh phá vỡ script `sync_spoke.py` và CI Gates (`validate_docs.py`).
2. **Phân rã 2 cấp vĩ mô**:
   - **Master Skills**: `xu-ly-van-phong`, `markdown-document-processing`, `copywriting`, `academic_writing`.
   - **Sub-Skills & Utilities**: `docx`, `pptx`, `table-reconstructor`, `form-template-cleaner`, `relative-link-patcher`.

---

## 🧭 Biên giới Công việc & Tickets (Frontier & Open Tickets)

### 🔹 Ticket 1 [AFK]: [Cập nhật Frontmatter & Master-Skill Relationships vào SKILL.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/document-skills-refinement/tickets/01-update-skill-metadata.md)
* **Loại tác vụ**: Research / Docs [AFK]
* **Mục tiêu**: Bổ sung trường metadata `master_skill` hoặc `sub_skills` vào YAML Frontmatter và cập nhật phần mô tả trong `SKILL.md` của các skill xử lý văn bản.
* **Trạng thái**: Open (Unblocked)

### 🔹 Ticket 2 [AFK]: [Bổ sung Phân loại Ảo Virtual Tag _document trong catalog.yaml](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/document-skills-refinement/tickets/02-catalog-virtual-tagging.md)
* **Loại tác vụ**: Research / Config [AFK]
* **Mục tiêu**: Bổ sung tag `_document` hoặc `_writing` vào `catalog.yaml` để hỗ trợ lọc nhanh danh sách skill xử lý văn bản mà không làm xáo trộn các bundles `_core`, `_qc`, `_consulting` hiện tại.
* **Trạng thái**: Open (Unblocked)

### 🔹 Ticket 3 [AFK]: [Cập nhật Hướng dẫn Định tuyến Routing trong platform-loader](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/document-skills-refinement/tickets/03-update-platform-loader-routing.md)
* **Loại tác vụ**: Docs [AFK]
* **Mục tiêu**: Cập nhật chỉ dẫn nạp skill trong `platform-loader/SKILL.md` để Agent ưu tiên kích hoạt Master Skill trước khi gọi các Sub-skill công cụ bên dưới.
* **Trạng thái**: Open (Blocked by Ticket 1, 2)

---

## 🌫️ Chưa xác định rõ (Not yet specified)
- **Auto-Discovery Assistant**: Công cụ hỗ trợ Agent tự động khuyến nghị cặp Master-Skill + Sub-Skill phù hợp khi người dùng tải lên một tệp tin văn phòng cụ thể.

---

## ⛔ Ngoài phạm vi (Out of scope)
- **Physical Directory Restructuring**: Di chuyển hoặc tạo thư mục con lồng nhau trong `.agents/skills/`.
- **Rename Existing Skills**: Đổi tên các skill hiện có làm hỏng lệnh slash commands người dùng đã quen thuộc.

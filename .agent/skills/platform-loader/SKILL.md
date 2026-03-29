---
name: platform-loader
description: Bootstrap skill cho CCBA Agent Services Platform. Đọc file này để biết toàn bộ skills, workflows, và rules available.
---

# CCBA Platform Loader

> **Vai trò**: Đây là điểm khởi đầu duy nhất cho Agent khi cần truy cập bất kỳ service nào của CCBA Platform.
> Đọc file này MỘT LẦN khi bắt đầu phiên → biết mọi thứ available → route task đúng chỗ.

## Hub Location

```
D:\GitHubProjects\ccba-agent-platform
```

Tất cả path bên dưới là **relative** so với Hub root.

---

## Service Catalog (Quick Reference)

### Skills

| Skill | Trigger Keywords | Khi nào dùng |
|-------|-----------------|--------------|
| `legal-document-tracker` | VBPL, nghị định, thông tư, pháp luật | Theo dõi/so sánh VBPL xây dựng |
| `completion-checklist` | HSHT, hồ sơ hoàn thành, nghiệm thu | Danh mục hồ sơ hoàn thành công trình |
| `seminar-builder` | seminar, đào tạo, training, recap | Chuẩn bị nội dung seminar |
| `long-form-writer` | tài liệu dài, whitepaper, quy chế | Viết tài liệu 2000+ words |
| `ai-gateway-sdk` | ai, llm, model, gateway, DGX | Kết nối AI Gateway (22 models) |

### Workflows

| Command | Trigger Keywords | Mô tả |
|---------|-----------------|-------|
| `/prepare-seminar` | chuẩn bị seminar, buổi thảo luận | End-to-end chuẩn bị nội dung seminar |
| `/update-legal-registry` | cập nhật VBPL, văn bản mới | Cập nhật registry VBPL + impact check |
| `/session-retrospective` | retrospective, cuối phiên | Tổng hợp kiến thức cuối phiên |
| `/create-pr` | create PR, pull request | Push code + tạo PR |
| `/release-feature` | release, merge PR | Merge PR + cleanup |
| `/new-feature` | new feature | Tạo feature branch |
| `/discard-feature` | discard, hủy branch | Xóa branch |
| `/convert-markdown` | convert, mdconverter | Chuyển đổi tài liệu sang Markdown bằng mdconverter |

### Rules (tự động áp dụng)

| Rule | Khi nào | File |
|------|---------|------|
| `ccba_identity` | Mọi output mang danh CCBA | `rules/ccba_identity.md` |
| `quality_standards` | QC/testing outputs | `rules/quality_standards.md` |
| `naming_conventions` | Tạo file/folder mới | `rules/naming_conventions.md` |
| `compliance` | Liên quan pháp luật xây dựng | `rules/compliance.md` |

---

## Routing Instructions

Khi nhận task từ user, Agent thực hiện theo logic sau:

### 1. Kiểm tra trigger keywords

Đọc `catalog.yaml` (cùng folder với file này). So sánh request của user với `triggers` trong catalog:

- Match skill → đọc `skill_path` (SKILL.md) của skill đó
- Match workflow → đọc `workflow_path` của workflow đó
- Match cả hai → đọc cả skill + workflow

### 2. Load rules tự động

- Nếu output mang danh CCBA → đọc `rules/ccba_identity.md`
- Nếu liên quan pháp luật → đọc `rules/compliance.md`
- Nếu tạo file mới → tham khảo `rules/naming_conventions.md`

### 3. Cross-workspace loading

Khi Agent **KHÔNG** ở Hub workspace (VD: đang ở QC BIM ver 3.0):

```
Bước 1: Đọc project `.md/workspace_context.yaml` → lấy `hub_ref`
Bước 2: Dùng Hub absolute path để đọc skill/workflow
         VD: view_file("D:\GitHubProjects\ccba-agent-platform\.agent\skills\legal-document-tracker\SKILL.md")
Bước 3: Thực thi skill/workflow
Bước 4: Lưu output VỀ project folder hiện tại (KHÔNG ở Hub)
```

### 4. Knowledge lookup

Trước khi bắt đầu task phức tạp, đọc `knowledge/session_learnings.md` để:
- Tránh lặp lại anti-patterns đã biết
- Áp dụng patterns/solutions đã chứng minh hiệu quả

---

## Machine-Readable Catalog

Chi tiết đầy đủ (triggers, paths, data files) trong:
```
.agent/skills/platform-loader/catalog.yaml
```

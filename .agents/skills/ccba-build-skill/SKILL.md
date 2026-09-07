---
name: ccba-build-skill
description: Nghiên cứu tài liệu từ nhiều nguồn qua NotebookLM và tự động đóng gói
  sinh Skill mới đạt chuẩn CCBA.
user-invocable: true
keywords:
- build-skill
- create-skill
- research
- notebooklm
disable-model-invocation: true
bundle: _core
command: /ccba-build-skill
---
# Workflow: Xây Dựng Kỹ Năng & Quy Trình Chuẩn (/ccba-build-skill)

Khi người dùng kích hoạt lệnh này dưới dạng:
`/ccba-build-skill <danh-sách-nguồn-hoặc-thư-mục> [--name <tên-skill>]`

Agent tiếp nhận lệnh bắt buộc phải tự động thực thi chuỗi tác vụ sau:

---

## 🛡️ 1. Quét Bảo Mật & Nạp Nguồn
- Đọc danh sách nguồn tài liệu được cung cấp (tệp tin cục bộ, URL hoặc video).
- Chạy quét bảo mật qua `scripts/maskara.py` đối với các tệp tin cục bộ để tránh lộ khóa API.
- Nạp nguồn vào Google NotebookLM thông qua CLI helper (`scripts/notebooklm_cli.py`).

---

## 📚 2. Chưng Cất Tri Thức
- Chạy lệnh sinh `study-guide` hoặc `report` của CLI helper để kết xuất cẩm nang tri thức tổng hợp Markdown sạch vào `.md/knowledge/`.
- Đọc tệp cẩm nang này để nắm rõ toàn bộ logic, patterns và API của công cụ cần tạo skill.

---

## 🧩 3. Khởi Tạo Cấu Trúc SKILL.md Đạt Chuẩn (ADR 0001, ADR 0040)
Tạo thư mục tại `.agents/skills/ccba-<tên_skill_dạng_kebab_case>/SKILL.md` theo đúng bộ khung chuẩn:

```markdown
---
name: ccba-<tên-skill-kebab-case>
description: <Mô tả ngắn gọn súc tích <= 180 ký tự>
user-invocable: true # Bắt buộc true nếu là slash command / ritual do người dùng gọi
disable-model-invocation: true # true cho ritual/tool skills (0-token prompt), false nếu là master deep skill
command: /ccba-<tên-skill-kebab-case> # Bắt buộc có dòng command khớp với /{name} theo ADR-0056
category: productivity # productivity | coding | testing | reasoning | documentation | governance
bundle: _core # _core | _software | _qc | _consulting | _bim
triggers:
- <trigger_1>
- <trigger_2>
---
# <Tên Kỹ Năng In Hoa>

<Mô tả mục đích và vai trò của kỹ năng>

## Quy trình thực hiện (Process)

1. **Bước 1: <Tiêu đề bước>**
   - <Hướng dẫn thao tác 1>
   - <Hướng dẫn thao tác 2>
   **Tiêu chí hoàn thành:** <Kết quả cụ thể cần đạt được ở bước này>

2. **Bước 2: <Tiêu đề bước>**
   - <Hướng dẫn thao tác 1>
   **Tiêu chí hoàn thành:** <Kết quả cụ thể cần đạt được ở bước này>
```

---

## ⚡ 4. Kích Hoạt Slash Command Native & Biên Dịch Catalog (ADR 0047, ADR 0056)
Mọi kỹ năng mang định danh `ccba-<tên-lệnh>` trong `name:` phục vụ người dùng gọi trực tiếp bắt buộc phải đăng ký đầy đủ Slash Command trong YAML frontmatter:
- **Bắt buộc có `user-invocable: true`** và **`command: /ccba-<tên-lệnh>`** để IDE Antigravity hiển thị trên popup menu khi người dùng gõ `/`.
- Khai báo `disable-model-invocation: true` nếu là lệnh điều phối/quy trình thủ tục (0-token system prompt).
- Khai báo `triggers:` và `keywords:` để hỗ trợ cả gợi ý tự động lẫn gõ lệnh tường minh.
- Chạy lệnh biên dịch catalog để tự động cập nhật hệ thống:
```bash
python scripts/governance/compile_catalog.py
```

---

## ✅ 5. Kiểm Định Chất Lượng Tự Động (CI Hard Gates)
Chạy toàn bộ bộ công cụ kiểm định để xác nhận đạt chuẩn 100% trước khi bàn giao:
```bash
python scripts/validate_skills.py
python scripts/governance/drift_auditor.py
```

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

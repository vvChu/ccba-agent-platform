---
name: ccba-build-skill
description: Nghiên cứu tài liệu từ nhiều nguồn qua NotebookLM và tự động đóng gói sinh Skill mới đạt chuẩn CCBA.
user-invocable: true
keywords: [build-skill, create-skill, research, notebooklm]
disable-model-invocation: true
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
Tạo thư mục tại `.agents/skills/<tên_skill_dạng_kebab_case>/SKILL.md` theo đúng bộ khung chuẩn:

```markdown
---
name: <tên-skill-kebab-case>
description: <Mô tả ngắn gọn súc tích <= 180 ký tự>
bundle: _core # _core | _software | _qc | _consulting | _bim
disable-model-invocation: true # true cho ritual/tool skills, false nếu là master deep skill
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

## ⚡ 4. Đăng Ký Slash Command Workflow (ADR 0040)
Nếu kỹ năng có thể được kích hoạt trực tiếp từ người dùng bằng slash command, tạo tệp workflow tại `.agents/workflows/ccba-<tên-lệnh>.md` theo khung chuẩn:

```markdown
---
description: <Mô tả chức năng của workflow>
applies_to:
  - "Phần mềm"
bundle: "_core"
disable-model-invocation: true # BẮT BUỘC: 0-token system prompt
---
# Workflow: <Tên Tiếng Việt> (/ccba-<tên-lệnh>)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/<tên-skill>/SKILL.md) để bắt đầu quy trình.
```

---

## ✅ 5. Kiểm Định Chất Lượng Tự Động (CI Hard Gates)
Chạy toàn bộ bộ công cụ kiểm định để xác nhận đạt chuẩn 100% trước khi bàn giao:
```bash
python scripts/validate_skills.py
python scripts/validate_docs.py
python scripts/governance/check_spoke_leakage.py
```

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

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
tier: kernel
command: /ccba-build-skill
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 3.0
  k: 2.0
  a: 2.0
  p: 1.0
triggers:
- ccba-writing-great-skills
- writing-great-skills
- ccba-review-skill
- review-skill
---

# Workflow: Xây Dựng Kỹ Năng & Quy Trình Chuẩn (/ccba-build-skill)

Khi người dùng kích hoạt lệnh này dưới dạng:
`/ccba-build-skill <danh-sách-nguồn-hoặc-thư-mục> [--name <tên-skill>]`

Agent tiếp nhận lệnh bắt buộc phải tự động thực thi chuỗi tác vụ sau:

---

## 🛡️ 1. Quét Bảo Mật & Nạp Nguồn
- Đọc danh sách nguồn tài liệu được cung cấp (tệp tin cục bộ, URL hoặc video).
- Chạy quét bảo mật qua `scripts/maskara.py` đối với các tệp tin cục bộ để tránh lộ khóa API.
- Nạp nguồn vào Google NotebookLM thông qua CLI helper (`python -m ccba_notebooklm`).
- **Tiêu chí hoàn thành:** Toàn bộ nguồn được quét sạch bí mật và nạp thành công vào NotebookLM.

---

## 📚 2. Chưng Cất Tri Thức
- Chạy lệnh sinh `study-guide` hoặc `report` của CLI helper để kết xuất cẩm nang tri thức tổng hợp Markdown sạch vào `.md/knowledge/`.
- Đọc tệp cẩm nang này để nắm rõ toàn bộ logic, patterns và API của công cụ cần tạo skill.
- **Tiêu chí hoàn thành:** Tệp tri thức tổng hợp Markdown được lưu trữ đầy đủ trong `.md/knowledge/`.

---

## ⚖️ 3. Tiền Kiểm Tra Cổng Kiến Trúc & Định Lượng GPI (HUB-ADR-0057)
Trước khi khởi tạo bất kỳ tệp tin nào, Agent bắt buộc chạy bộ kiểm định quyết định 2 giai đoạn:

### Phần 1: Hai Cổng Bất Biến (Structural Invariant Gates)
- **Cổng 0 (Determinism Gate):** Nếu tác vụ giải quyết 100% bằng giải thuật xác định (regex, AST parse, math, file I/O) $\rightarrow$ **DỪNG LẠI**, triển khai tại Tầng 1 (`packages/*/src/`). Nghiêm cấm tạo Skill phẳng độc lập.
- **Cổng 1 (Orchestration Gate):** Nếu tác vụ điều phối đa tác tử song song, StateGraph checkpoints hoặc cần con người phê duyệt (HITL) $\rightarrow$ **DỪNG LẠI**, triển khai tại Tầng 3 (`.agents/workflows/`).

### Phần 2: Định lượng Chỉ số Phân rã Kỹ năng (GPI)
Nếu vượt qua Cổng 0 và Cổng 1, tính toán chỉ số GPI theo barem định lượng:
$$\mathbf{GPI} = (S \times 2.5) + (K \times 2.0) + (A \times 2.0) - (P \times 1.5)$$

*Thang điểm 1.0 – 5.0:*
- **S (Reasoning Steps):** Số bước suy luận nhận thức của mô hình.
- **K (Interface / Schema Complexity):** Độ phức tạp tham số đầu vào/ra.
- **A (Autonomous Model Invocation):** Mức độ cần Agent tự động triệu hồi.
- **P (Parent Domain Coupling):** Mức độ gắn kết với Master Skill sở hữu.

### Quy tắc Định tuyến Đầu ra
- **$GPI < 12.0$ (Tier 2A - Progressive Reference):** Tạo tệp tham chiếu tăng tiến tại `.agents/skills/<parent-skill>/references/<name>.md`. Tuyệt đối không tạo thư mục skill riêng.
- **$GPI \ge 12.0$ (Tier 2B - Standalone Kernel Skill):** Đủ điều kiện tạo thư mục kỹ năng riêng tại `.agents/skills/ccba-<name>/SKILL.md` và tự động chèn khối `gpi: {s: ..., k: ..., a: ..., p: ...}` vào frontmatter.

- **Tiêu chí hoàn thành:** Phân loại đúng tầng kiến trúc và xác định chính xác vị trí lưu trữ (Tier 1, Tier 2A, Tier 2B, hay Tier 3).

---

## 🧩 4. Khởi Tạo Cấu Trúc SKILL.md Đạt Chuẩn (HUB-ADR-0001, HUB-ADR-0040, HUB-ADR-0057)
Nếu $GPI \ge 12.0$, tạo thư mục tại `.agents/skills/ccba-<tên_skill_dạng_kebab_case>/SKILL.md` theo đúng bộ khung chuẩn:

```markdown
---
name: ccba-<tên-skill-kebab-case>
description: <Mô tả ngắn gọn súc tích <= 180 ký tự>
user-invocable: true # Bắt buộc true nếu là slash command / ritual do người dùng gọi
disable-model-invocation: true # true cho ritual/tool skills (0-token prompt), false nếu là master deep skill
command: /ccba-<tên-skill-kebab-case> # Bắt buộc có dòng command khớp với /{name} theo HUB-ADR-0056
category: productivity # productivity | coding | testing | reasoning | documentation | governance
bundle: _core # _core | _software | _qc | _consulting | _bim
triggers:
- <trigger_1>
- <trigger_2>
gpi: {s: 3.0, k: 2.0, a: 2.0, p: 1.0} # Bắt buộc khai báo đầy đủ s, k, a, p theo HUB-ADR-0057
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
- **Tiêu chí hoàn thành:** Tệp SKILL.md được khởi tạo với đầy đủ trường frontmatter chuẩn và khối `gpi:`.

---

## ⚡ 5. Kích Hoạt Slash Command Native & Biên Dịch Catalog (HUB-ADR-0047, HUB-ADR-0056)
Mọi kỹ năng mang định danh `ccba-<tên-lệnh>` trong `name:` phục vụ người dùng gọi trực tiếp bắt buộc phải đăng ký đầy đủ Slash Command trong YAML frontmatter:
- **Bắt buộc có `user-invocable: true`** và **`command: /ccba-<tên-lệnh>`** để IDE Antigravity hiển thị trên popup menu khi người dùng gõ `/`.
- Khai báo `disable-model-invocation: true` nếu là lệnh điều phối/quy trình thủ tục (0-token system prompt).
- Khai báo `triggers:` và `keywords:` để hỗ trợ cả gợi ý tự động lẫn gõ lệnh tường minh.
- Chạy lệnh biên dịch catalog để tự động cập nhật hệ thống:
```bash
python scripts/governance/compile_catalog.py
```
- **Tiêu chí hoàn thành:** Catalog `catalog.yaml` được biên dịch thành công và đồng bộ 100% với frontmatter.

---

## ✅ 6. Kiểm Định Chất Lượng Tự Động (Deterministic Gate & GPI Enforcement)
Chạy cổng kiểm định máy tính một chạm để xác nhận đạt chuẩn 100% trước khi bàn giao:
```bash
python -m ccba_harness verify-patch --preset skill --target .agents/skills/ccba-<tên-skill>
python scripts/governance/drift_auditor.py
```
*Cổng preset `skill` tự động chạy: (1) `validate_skills.py --enforce-gpi` và (2) `compile_catalog.py --check`.*
- **Tiêu chí hoàn thành:** Lệnh `python -m ccba_harness verify-patch --preset skill --target .agents/skills/ccba-<tên-skill>` trả về **Exit Code 0** (Overall Status: PASS). Quy tắc Khóa Cứng (HUB-ADR-0058): Cấm tuyệt đối Agent tuyên bố hoàn tất kỹ năng nếu có bất kỳ lệnh kiểm tra nào thất bại.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/skill_authoring_guide.md` | Cẩm nang hướng dẫn kỹ sư biên soạn tệp chỉ dẫn SKILL.md chuẩn mực |
| `references/skill_review_checklist.md` | Bảng kiểm định chất lượng và tuân thủ thể chế ADR-0057 cho kỹ năng |
| `references/skill_glossary.md` | Bảng thuật ngữ và quy ước định danh kỹ năng chuẩn mực CCBA |


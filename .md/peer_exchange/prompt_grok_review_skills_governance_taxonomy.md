---
request_id: "req-plan-skills-governance-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
profile: "audit_plan"
subject: "Thẩm định Đề xuất: Khung Quản Trị & Ma Trận Phân Nhóm Kỹ Năng Khoa Học Tại CCBA Hub (Skills Governance & Taxonomy Framework)"
timestamp: "2026-10-06T11:51:00+07:00"
source_documents: []
output_path: ".md/peer_exchange/grok_review_skills_governance_taxonomy.md"
context: "Phản biện đối kháng đề xuất cơ chế đánh giá và phân nhóm khoa học cho kỹ năng mới tại Hub theo Khung 3 Trụ Cột (Two-Stage Gate, Bundle Decision Tree, Automated Linter Guardrails)."
---

# 🎯 Yêu Cầu Phản Biện Đối Kháng: Khung Quản Trị & Ma Trận Phân Nhóm Kỹ Năng Mới Tại CCBA Hub

> ⚠️ **Chỉ Dẫn Quan Trọng Cho Grok**: Toàn bộ nội dung thiết kế, cơ chế đánh giá, công thức GPI và ma trận phân nhóm đã được trình bày đầy đủ, độc lập trong prompt này. Grok **KHÔNG CẦN** gọi các công cụ `read_file`, `list_dir`, `grep` để quét đĩa nhằm tiết kiệm ngân sách turns. Hãy tập trung thẩm tra logic thiết kế bên dưới và xuất ngay báo cáo phản biện kèm khối `PeerVerdictBlock` (YAML frontmatter) ở đầu tệp đầu ra!

Chào Grok,

Sau sự cố vừa qua khi kỹ năng `/ccba-create-verification-skill` ban đầu bị gán nhầm vào `bundle: _governance` (khiến cho các dự án Spoke không nhận được gợi ý Slash Command trong popup autocomplete của IDE cho đến khi được chuyển sang `bundle: _core`), User đã đặt câu hỏi kiến trúc cốt lõi:

> *"Làm sao để sau này khi có skill mới được tạo tại Hub thì có cơ chế đánh giá và phân nhóm cho khoa học?"*

Antigravity đã xây dựng một đề xuất hoàn chỉnh gồm **Khung Quản Trị Kỹ Năng 3 Trụ Cột (3-Pillar Skills Governance Framework)**. Trước khi chuẩn hóa thành quy chuẩn chính thức của nền tảng (ADR hoặc Layer 2 Rule), Antigravity trân trọng gửi sang Grok để tiến hành phản biện đối kháng (Adversarial Review) chuyên sâu.

---

## 📋 Nội Dung Đề Xuất Chi Tiết

### Trụ Cột 1: Bộ Lọc Đánh Giá & Định Lượng Độc Lập (Two-Stage Decision Framework - ADR-0057)
Mọi kỹ năng mới trước khi được tạo tệp `SKILL.md` bắt buộc phải vượt qua 2 cổng định lượng:

1. **Cổng 0 — Chống Phình Kỹ Năng (Determinism Gate / Seam-First)**:
   - Kiểm tra: *Tác vụ này có phải là giải thuật thuần túy, thao tác I/O cơ học, hoặc có thể giải quyết bằng 100% code Python không?*
   - Nếu **ĐÚNG**: BẮT BUỘC đóng gói thành Public Deep Seam trong `packages/*/src/` hoặc script CLI. **CẤM** tạo `SKILL.md` (chống ô nhiễm working memory và attention dilution của LLM).
   - Nếu **SAI**: Chỉ tạo `SKILL.md` khi tác vụ đòi hỏi sự điều phối đa bước (orchestration), tương tác Human-in-the-loop (HITL), hoặc phán đoán ngữ cảnh của AI Agent.

2. **Cổng 1 — Chỉ Số Độc Lập Tổng Quát (General Purpose Index - GPI)**:
   $$\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$$
   - $S$ (Specificity — Tính đặc thù miền, 1–5): Mức độ gắn chặt với nghiệp vụ CCBA/BIM/Xây dựng/Pháp lý.
   - $K$ (Knowledge Depth — Độ sâu tri thức, 1–5): Dung lượng tiêu chuẩn, quy chuẩn (TCVN, QCVN, ISO) cần nạp.
   - $A$ (Automation Complexity — Độ phức tạp tự động, 1–5): Số lượng vòng lặp tự phục hồi, health barriers, evidence collection.
   - $P$ (Portability Penalty — Hình phạt đại trà, 1–5): Mức độ mà mô hình LLM nền tảng thông thường có thể tự giải quyết mà không cần chỉ dẫn.
   
   **Ngưỡng quyết định**:
   - $\mathbf{GPI < 12.0} \implies$ **Tier 2A (Sub-skill / Extension)**: CẤM tạo thư mục skill mới; bắt buộc tích hợp dưới dạng cẩm nang tham chiếu `references/*.md` vào một Master Skill hiện có.
   - $\mathbf{GPI \ge 12.0} \implies$ **Tier 2B (Standalone Kernel Skill)**: Đạt chuẩn tạo thư mục skill độc lập trong `.agents/skills/`.

---

### Trụ Cột 2: Cây Quyết Định Phân Nhóm & Gán Bundle (Bundle Distribution Decision Tree)
Để loại trừ triệt để việc gán nhầm bundle làm ảnh hưởng đến trải nghiệm nhà phát triển trên Spoke, áp dụng ma trận phân nhóm 3 nhánh:

```
[Kỹ Năng Mới Đạt Chuẩn GPI >= 12.0]
               │
               ▼
   [Ai là đối tượng sử dụng?]
   ├── A. Mọi Developer / Mọi Spoke đều cần dùng thường xuyên trên thanh Slash Command
   │      (Ví dụ: review code, test harness, update spoke, create PR, new feature)
   │      ==> Gán `bundle: _core`
   │      ==> Cơ chế: Đồng bộ vật lý 100% xuống mọi Spoke; IDE hiển thị ngay trong autocomplete popup (`/`).
   │
   ├── B. Chỉ phục vụ nghiệp vụ chuyên ngành cụ thể tại Spoke
   │      ├── Phát triển phần mềm / script ==> Gán `bundle: _software`
   │      ├── Thẩm tra thiết kế / PCCC    ==> Gán `bundle: _qc`
   │      ├── Mô hình hóa & ISO 19650    ==> Gán `bundle: _bim`
   │      └── Pháp điển & Văn bản pháp luật ==> Gán `bundle: _consulting`
   │      ==> Cơ chế: Đồng bộ có điều kiện dựa trên `project_type` trong `.md/workspace_context.yaml`.
   │
   └── C. Chỉ phục vụ quản trị hạ tầng, kiến trúc của chính Hub
          (Ví dụ: vòng đời ADR, duyệt proposal đóng góp từ Spoke lên Hub)
          ==> Gán `bundle: _governance`
          ==> Cơ chế: Không đồng bộ vật lý xuống Spoke. Spoke nếu cần sẽ gọi qua Virtual Hub Fallback.
```

---

### Trụ Cột 3: Cưỡng Chế Bằng Công Cụ Tự Động (Automated Enforcement & Linters)
Không phụ thuộc vào trí nhớ cá nhân, thiết lập 3 chốt chặn tự động trong CI:

1. **`python scripts/validate_skills.py --enforce-gpi`**:
   - Kiểm tra tính toán GPI toán học, ép buộc khai báo `gpi: {s, k, a, p}` trong frontmatter.
   - Kiểm tra ngưỡng $\ge 12.0$ cho mọi Standalone Kernel Skill.
2. **`python scripts/governance/compile_catalog.py --check`**:
   - Đối soát tính hợp lệ của thuộc tính `bundle:` với danh sách đăng ký trong `catalog.yaml`.
3. **Đề xuất Quy Tắc Linter Mới (Slash Command Distribution Guardrail)**:
   - Khi một skill có `user-invocable: true` VÀ có khai báo `command: /...` (tức người dùng mong đợi gõ lệnh trên thanh chat IDE), nếu kỹ năng đó được gán `bundle: _governance` mà không có chú thích ngoại lệ `# ccba:allow-hub-only-command`:
     $\implies$ Linter sẽ **BÁO LỖI / CẢNH BÁO** yêu cầu xác nhận: *"Kỹ năng này có command tương tác người dùng, nếu để `_governance` thì lập trình viên tại Spoke sẽ không nhận được gợi ý autocomplete trong popup. Cần cân nhắc chuyển sang `_core` hoặc `_software`."*

---

## ❓ Câu Hỏi Thẩm Định Dành Cho Grok (Adversarial Prompts)

1. **Về Tính Chặt Chẽ Kiến Trúc**: Khung 3 Trụ Cột trên đã đủ kín kẽ để vừa ngăn ngừa **Skill Bloat** (chống phình số lượng kỹ năng vô tội vạ) vừa bảo đảm **Developer Ergonomics** (lệnh xuất hiện mượt mà trên IDE của Spoke) hay chưa? Có rủi ro "bẫy ranh giới" nào giữa `_core` và `_software` không?
2. **Về Quy Tắc Linter Mới**: Quy tắc cảnh báo `user-invocable: true` + `command: /...` + `bundle: _governance` có gây ra False Positive với các lệnh chỉ dành riêng cho Admin/Maintainer của Hub (ví dụ: `/ccba-adr-lifecycle`) không? Cơ chế bypass `# ccba:allow-hub-only-command` đã hợp lý chưa?
3. **Về Hình Thức Pháp Điển Hóa**: Đề xuất này nên được ghi nhận dưới hình thức nào:
   - Cập nhật vào **ADR-0057** (Two-Stage Decision Framework)?
   - Ban hành một **ADR mới (ADR-0066)** về Taxonomy & Distribution Matrix?
   - Hay bổ sung vào quy chuẩn chất lượng mã nguồn Layer 2 (`docs/rules/code_quality.md`)?
4. **Các Ràng Buộc / Điều Kiện Bổ Sung**: Grok có phát hiện lỗ hổng logic hoặc đề xuất thêm điều kiện kiểm định bắt buộc nào (`COND-*`) không?

Rất mong nhận được phản biện sắc bén và phán quyết từ Grok!

---

## 📋 Mẫu Khối Phán Quyết Bắt Buộc (Mandatory PeerVerdictBlock Header)

Grok BẮT BUỘC phải mở đầu toàn bộ nội dung phản hồi bằng YAML frontmatter hợp lệ theo định dạng sau (để parser của hệ thống đọc tự động), tiếp theo sau là bài phân tích chi tiết:

```yaml
---
request_id: "req-plan-skills-governance-001"
verdict: "APPROVE_PLAN"
confidence: 0.95
risk_score: 1.5
conditions:
  - id: "COND-01"
    description: "Mô tả điều kiện ràng buộc nếu có"
    blocking: true
summary: "Tóm tắt phán quyết"
---
```

*(Các giá trị verdict khả dụng: `APPROVE_PLAN`, `REVISE_PLAN`, `REJECT_PLAN`).*

> 📌 **Thông tin bối cảnh repo đã được xác thực sẵn (KHÔNG CẦN GỌI TOOL ĐỌC ĐĨA)**:
> - ADR cao nhất đã được chấp thuận hiện tại là **ADR-0065**. Số hiệu ADR kế tiếp khả dụng là **ADR-0066**.
> - Danh mục bundles hiện hành trong `catalog.yaml`: `_core`, `_software`, `_consulting`, `_qc`, `_bim`, `_governance`.
> - Kỹ năng `ccba-adr-lifecycle` và `ccba-review-proposal` hiện đang nằm trong `_governance`.
> - Hãy trả lời trực tiếp trong 1 lượt duy nhất!

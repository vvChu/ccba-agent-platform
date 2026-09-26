# 🗺️ Wayfinder Map: Lộ Trình Giải Phóng Plateau Cho Toàn Bộ Skills

> **Mã định danh:** `plateau-resolution-roadmap`  
> **Trạng thái:** `IN_PROGRESS` (Active Frontier)  
> **Khởi tạo:** 2026-09-26  
> **Kỹ năng điều phối:** `/ccba-wayfinder`

---

## 1. 🎯 Điểm Đích (Destination)

Toàn bộ **74 kỹ năng (skills)** trong nền tảng CCBA Agent Services Platform được ánh xạ chính xác 100% vào đúng **Domain Archetype** và **Evaluation Dataset** tương thích với bản chất nghiệp vụ chuyên môn; triệt tiêu hoàn toàn hiện tượng kẹt điểm trần giả tạo (Plateau) do thi nhầm đề thi (như 30% ở Legal Tooling, 44–60% ở Platform Utilities, 67.6% ở Design), bảo đảm hệ thống Auto-Tuner vận hành tiết kiệm token và thúc đẩy các kỹ năng tự động tiến hóa thực chất.

---

## 2. 📝 Ghi Chú & Thể Chế (Notes & Guardrails)

- **SSOT Archetype Routing Invariant (ADR-0058):** Mọi quy tắc ánh xạ bắt buộc phải quy về `packages/ccba-harness/src/ccba_harness/evals/archetypes.py`. Các bộ từ khóa nhận diện phải tách bạch (disjoint), không được chồng lấn.
- **Bảo toàn Cổng Nghiệm thu (ADR-0058 Hard Completion Lock):** Mọi thay đổi về archetype và dataset phải vượt qua `python -m ccba_harness verify-patch --preset code`.
- **Nguyên tắc Tiết Kiệm Token Tối Đa:** Ưu tiên số 1 là cô lập ngay `ccba-design` để không tiếp tục lãng phí ~1 triệu tokens mỗi đêm vào tập dữ liệu rác `eval_general_domain.json`.
- **Kỹ năng bổ trợ cần nạp:** `/ccba-grilling`, `/ccba-research`, `/ccba-implement`, `/ccba-tdd`.

---

## 3. ✅ Quyết Định Đã Chốt (Decisions So Far)

| Ticket / PR | Tên Quyết Định | Tóm Tắt & Kết Quả |
| :--- | :--- | :--- |
| **PR #378 / #379** | [`Dedicated skill_repair Archetype & Dataset`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/evals/archetypes.py) | Tách `skill-repair` khỏi `orchestration`, tạo archetype `skill_repair`, bộ chấm điểm YAML/GPI/Gate 0 và dataset `eval_skill_repair.json` (5 test cases). Điểm baseline nhảy vọt từ 0.0% lên **100.0%**. |
| **PR #382 / #383** | [`Defense-in-Depth 2-Tier DriftAuditor`](file:///home/vvc/ccba/ccba-agent-platform/scripts/governance/drift_auditor.py) | Khử triệt để False Positive của CI khi bổ sung tệp dữ liệu test case (`eval_*.json`) vào thư mục `test_cases/` của skill. Dọn đường an toàn cho việc mở rộng các bộ test cases mới. |
| **Issue #384 / WF-01** | [`Dedicated visual_design Archetype & Dataset`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/evals/archetypes.py) | Cô lập `ccba-design` khỏi `eval_general_domain.json`, tạo archetype `visual_design`, bộ chấm điểm Design Tokens/Hex/Brand/Typography và dataset `eval_visual_design.json` (5 test cases). Cứu ~1.000.000 tokens mỗi đêm và phá vỡ plateau 67.6%. |

---

## 4. 🌫️ Sương Mù Chiến Trận / Chưa Xác Định Rõ (Not Yet Specified)

1. **[Fog 1] Tiêu chí đánh giá cho nhóm Platform Utilities:**
   - Các kỹ năng như `ccba-create-pr`, `ccba-git-guardrails`, `ccba-youtube-learn`, `ccba-notebooklm-connector` không tạo ra bài văn bản xuôi mà chủ yếu gọi công cụ (tool calling) hoặc xuất định dạng JSON/YAML/CLI.
   - *Vấn đề chưa rõ:* Scorer cho nhóm này nên dựa trên Regex kiểm tra tham số gọi tool, hay dựa trên tính toàn vẹn của artifact xuất ra?
2. **[Fog 2] Phân tách Legal Engineering vs Legal Advisory:**
   - `ccba-tvpl-vip-crawler` và `ccba-legal-ingest` thuần túy là engineering pipeline (cào dữ liệu, xử lý phiên VIP, parse OKF v2.4).
   - *Vấn đề chưa rõ:* Nên tạo 1 archetype gộp chung `legal_engineering` hay tách riêng `legal_crawler` và `legal_ingest`?
3. **[Fog 3 - ĐÃ GIẢI QUYẾT] Tiêu chuẩn đánh giá cho Multimodal / Visual Design:**
   - Đã chốt bộ chấm điểm 4 tiêu chí tại `get_visual_design_scorers()`: Cấu trúc Design Tokens & Hex Colors, Brand Guidelines & Safe Zone (Critical Hard Floor), Typography & Image Prompt Specifications, và Content Depth.

---

## 5. 🚫 Ngoài Phạm Vi (Out Of Scope)

- **Không viết lại SKILL.md thủ công cho 74 skills:** Mục tiêu là chuẩn hóa "Đề thi" và "Giám thị chấm thi" (Dataset & Scorers), để Nightly Auto-Tuner tự động tối ưu hóa SKILL.md.
- **Không thay đổi kiến trúc thuật toán Git-Ratchet Optimizer:** Giữ nguyên vòng lặp ratchet bất biến đã được chứng minh hiệu quả tại PR #377.
- **Không can thiệp vào các skills đã đạt 100%:** `ccba-llm-pipeline-patterns`, `ccba-academic-writing`, `ccba-adr-lifecycle`, `ccba-api-circuit-breaker`, `ccba-ai-pdf-preprocessor`, `ccba-skill-repair`.

---

## 6. 🎫 Danh Sách Ticket Tại Biên Giới (Frontier Tickets)

### ✅ Ticket WF-01: [DONE] Cô Lập Khẩn Cấp `ccba-design` Khỏi Dataset Rác (Issue #384)
- **Mục tiêu:** Cắt đứt ngay lập tức việc tiêu hao ~1M tokens/đêm vào `eval_general_domain.json`.
- **Hành động & Kết quả:**
  1. Thêm `VISUAL_DESIGN_ARCHETYPE_KEYWORDS` và DomainArchetype `visual_design` vào `archetypes.py` (SSOT), bảo đảm disjoint keyword routing loại trừ `codebase-design`.
  2. Tạo bộ dataset benchmark chuẩn `eval_visual_design.json` (5 test cases: Color & Tokens, Typography Scale, Logo Safe Zone, Image Prompt Specs, CIP Program).
  3. Xây dựng scorer `get_visual_design_scorers()` và nhánh giả lập `visual_design` trong `simulation.py`.
- **Đầu ra:** PR giải phóng `ccba-design`, vượt qua ADR-0058 Hard Completion Lock.


### 🟡 Ticket WF-02: [Research & Phân Loại] Tách Nhóm Developer Utilities Khỏi `orchestration` [AFK]
- **Mục tiêu:** Giải phóng 28 skills đang bị kẹt ở mức 44%–60% do phải làm bài thi Forensic Auditor.
- **Hành động:**
  1. Phân loại 28 skills thành 2 nhóm:
     - *Nhóm Pure Orchestration (giữ lại):* `ccba-teamwork`, `ccba-handoff`, `ccba-platform`, `ccba-review-proposal`.
     - *Nhóm Developer / Platform Utilities (tách ra):* `ccba-create-pr`, `ccba-git-guardrails`, `ccba-sync-upstream`, `ccba-youtube-learn`, `ccba-notebooklm-connector`, `ccba-ask`, `ccba-wayfinder`, `ccba-build-skill`, `ccba-setup-skills`...
  2. Thiết lập archetype mới `platform_tooling` với dataset `eval_platform_tooling.json`.
  3. Scorer đánh giá khả năng thực thi lệnh, rào chắn an toàn và tuân thủ giao thức công cụ.
- **Đầu ra:** Báo cáo phân loại chi tiết và bản thiết kế archetype `platform_tooling`.

### 🟡 Ticket WF-03: [Research & Thiết Kế] Định Hình Archetype `legal_tooling` [AFK]
- **Mục tiêu:** Cứu 4 skills (`ccba-tvpl-vip-crawler`, `ccba-legal-ingest`, `ccba-legal-document-tracker`, `ccba-completion-checklist`) thoát khỏi bài thi câu hỏi Luật Xây dựng 2025 (kẹt 30%).
- **Hành động:**
  1. Thiết lập archetype `legal_tooling` với từ khóa `("crawler", "vip", "ingest-pipeline", "document-tracker", "checklist")`.
  2. Xây dựng dataset `eval_legal_tooling.json` với các câu hỏi kiểm tra: xử lý lỗi mạng crawler, kiểm tra format OKF v2.4, thuật toán so khớp diff văn bản, và cấu trúc cây thư mục hồ sơ hoàn thành.
  3. Scorer đánh giá tính trọn vẹn của dữ liệu và rào chắn SHA-256 (ADR-0059).
- **Đầu ra:** Bản thiết kế Seam và bộ dataset đặc thù.

### 🟢 Ticket WF-04: [Task & Dataset] Bổ Sung Test Cases Cho Nhóm Văn Phòng (`eval_copywriting.json`) [AFK]
- **Mục tiêu:** Xóa bỏ tình trạng dataset chỉ có 1 câu hỏi vô lý về "prompt nhiễu", giải phóng `ccba-markdown-document-processing`, `ccba-seminar-builder`, `ccba-copywriting` (kẹt 30%–75%).
- **Hành động:**
  1. Soạn thảo 5 test cases thực tế:
     - Case 1: Thể thức công văn hành chính chuẩn NĐ 30/2020.
     - Case 2: Chuẩn hóa Markdown bảng biểu từ tài liệu Word trích xuất.
     - Case 3: Dàn ý và slide outline cho buổi seminar kỹ thuật.
     - Case 4: Soạn thảo thông cáo truyền thông / bài viết chuyên môn BIM.
     - Case 5: Quy chuẩn Typography và cấu trúc phân cấp đề mục.
  2. Cập nhật `eval_copywriting.json` và kiểm tra lại điểm baseline.
- **Đầu ra:** Tệp `eval_copywriting.json` hoàn chỉnh với 5 test cases chuẩn mực.

---

## 7. 🚀 Thứ Tự Ưu Tiên Thực Hiện (Execution Sequence)

```mermaid
flowchart TD
    WF01["🔴 WF-01: Cô lập ccba-design (Cứu 1M tokens/đêm)"] --> WF04["🟢 WF-04: Mở rộng eval_copywriting.json (5 test cases)"]
    WF04 --> WF03["🟡 WF-03: Archetype legal_tooling (Giải cứu 4 skills kẹt 30%)"]
    WF03 --> WF02["🟡 WF-02: Archetype platform_tooling (Giải cứu 28 skills kẹt 50%)"]
    WF02 --> DEST["🎯 DESTINATION: 100% Skills Thoát Plateau & Tự Động Tiến Hóa"]
```

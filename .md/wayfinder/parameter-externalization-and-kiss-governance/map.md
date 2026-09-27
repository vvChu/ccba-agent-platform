# 🗺️ BẢN ĐỒ ĐỊNH HƯỚNG: QUẢN TRỊ THAM SỐ ĐỘNG & BẢO VỆ NGUYÊN TẮC KISS (WAYFINDER MAP)
> **Mã định danh:** `WAYFINDER-PARAM-KISS-GOVERNANCE`  
> **Trạng thái:** KHỞI LẬP (CHARTED)  
> **Khởi tạo:** `2026-09-27` | **Phiên bản:** `1.0.0`  
> **Phạm vi áp dụng:** Toàn bộ Monorepo Packages, 73 Agent Skills & Governance CI Gates

---

## 🎯 1. Điểm Đích (Destination)

Xây dựng và hoàn thiện **Hệ Thống Quản Trị Tham Số Động & Cơ Chế Cưỡng Chế Cơ Học (Mechanical Parameter Governance)** cho toàn bộ nền tảng CCBA Agent Services Platform, giải quyết triệt để vấn đề AI Agent hardcode tham số, đảm bảo nguyên tắc bất biến:
> **"Mọi siêu tham số và định tuyến phải là Cấu hình Khai báo (Declarative Config) — Tuyệt đối không phẫu thuật mã nguồn logic để tinh chỉnh tham số."**

**Tiêu chí hoàn thành định lượng:**
1. **Xóa sổ 100%** các chuỗi model thô (`"gemini-*"`, `"gpt-*"`, `"claude-*"`) và IP hạ tầng vật lý (`100.83.192.30`) hardcode trong code logic ứng dụng và skills.
2. **Triển khai AST Parameter Linter (`check_hardcoded_parameters.py`)** tích hợp trực tiếp vào `verify-patch` (Gate 0 / Gate 1) ngăn chặn 100% mã mới vi phạm hardcoding.
3. **Hiến pháp hóa Invariant:** Bổ sung *Parameter Externalization & Dynamic Scale Invariant* vào `AGENTS.md`, `.agents/AGENTS.md`, `session_learnings.md` và `docs/rules/code_quality.md` §7.
4. **Declarative Archetypes:** Chuyển đổi toàn bộ từ khóa định tuyến trong `packages/ccba-harness/src/ccba_harness/evals/archetypes.py` sang tệp cấu hình khai báo YAML (`archetypes_catalog.yaml`).
5. **Zero-Regression:** 100% test suites của `ccba-ai`, `ccba-harness` và các packages liên quan đạt PASS mà không làm suy giảm hiệu năng benchmark.

---

## 📝 2. Ghi Chú (Notes)
- **Kỹ năng liên quan:** `/ccba-implement`, `/ccba-tdd`, `/ccba-review-proposal`, `/ccba-grilling`.
- **Hiến pháp đối chiếu:** [ADR-0025](../../docs/adr/0025-ai-gateway-client-configuration-standardization.md), [ADR-0047](../../docs/adr/0047-hub-spoke-non-destructive-synchronization-engine.md), [ADR-0058](../../docs/adr/0058-live-collaboration-artifacts-workspace-mirroring-and-charter-alignment.md), [RULE-1.10 Platform-Aware KISS](../knowledge/session_learnings.md).
- **Nguyên tắc hành động:** *"Plan, don't do"* — mỗi ticket chỉ tập trung vào một quyết định kiến trúc hoặc một đơn vị thực thi khép kín.

---

## ✅ 3. Quyết Định Đã Chốt (Decisions So Far)

*   `[DECISION-001] [Xác nhận thực trạng & nguyên nhân qua Boost Investigation]`: Hoàn thành điều tra chuyên sâu `BOOST-INV-20260927-HARDCODE-KISS`, định danh 18 điểm vi phạm thực tế và chỉ rõ nghịch lý: Seam `ccba_ai.routing` đã có từ ADR-0025 nhưng bị vi phạm do thiếu AST linter cưỡng chế cơ học.
*   `[DECISION-002] [Mô hình kiểm soát 3 lớp]`: Áp dụng mô hình bảo vệ 3 lớp:
    1. *Lớp 1 (Pháp lý):* Cập nhật Hiến pháp Nền tảng (`AGENTS.md`, `code_quality.md` §15).
    2. *Lớp 2 (Cơ học):* AST Linter trong `verify-patch` chặn đứng commit vi phạm.
    3. *Lớp 3 (Kiến trúc):* Declarative YAML Catalog cho `ccba-harness/evals` và Enforce `ccba_ai.routing`.
*   `[TICKET-001] [AST Parameter Linter & CI Gate Integration]`: Đã triển khai `scripts/governance/check_hardcoded_parameters.py` và bộ test suite `tests/governance/test_hardcoded_parameters.py` (10/10 tests PASS). Hỗ trợ phát hiện raw model string (`gemini-*`, `gpt-*`, `claude-*`), raw network IPs, và Windows machine paths với cơ chế chú thích miễn trừ (`# ccba:allow-raw-model`, `# ccba:allow-raw-ip`, `# ccba:allow-machine-path`).
*   `[TICKET-002] [Hiến Pháp Hóa Invariant: Parameter Externalization & Dynamic Scale]`: Đã bổ sung điều khoản bất biến vào `AGENTS.md`, `.agents/AGENTS.md`, `session_learnings.md` (RULE-1.12), và `docs/rules/code_quality.md` §15. Bảo đảm ngân sách working memory `session_learnings.md` $\le 10$ KB (9,948 bytes, 8/8 tests pass, 246/246 governance tests pass).

---

## ⚡ 4. Rìa Biên Giới & Các Ticket Hành Động (The Frontier Tickets)

Các ticket unblocked có thể triển khai ngay:

*   **[TICKET-003] [Chuẩn Hóa Model Routing Across Skills & Core Packages]** `[Task | AFK]`:
    - *Mô tả:* Sử dụng linter mới `check_hardcoded_parameters.py` để quét và refactor các vị trí vi phạm trong `.agents/skills/` (`ccba-eval-gate`, `ccba-youtube-learn`, `ccba-design`, `ccba-legal-intel`) và core packages sang sử dụng `ccba_ai.routing.choose_model()` hoặc `ModelArchetype`.
    - *Trạng thái:* `READY TO CLAIM` (Unblocked sau khi TICKET-001 & TICKET-002 hoàn tất)

---

## 🌫️ 5. Sương Mù Chiến Trận (Not Yet Specified)

*Nơi ghi nhận các câu hỏi kiến trúc dự kiến sẽ giải quyết nhưng cần làm rõ thêm:*

*   **[FOG-001] [Declarative Archetype Catalog Schema & Parsing Overhead]:**
    - *Câu hỏi:* Khi chuyển `CODING_ARCHETYPE_KEYWORDS` ra file `archetypes_catalog.yaml`, làm thế nào để đảm bảo tốc độ nạp (parsing time) dưới 2ms và không ảnh hưởng đến benchmark loop của nightly auto-tuner? Cần in-memory singleton cache hay compile sang pre-baked python map trong build step?
*   **[FOG-002] [Scorers Hyperparameter Configuration Interface]:**
    - *Câu hỏi:* Các trọng số `weight=0.4`, `min_length=20` trong `scorers.py` nên được cấu hình qua YAML dataset item hay qua Pydantic Settings? Làm sao để backward compatible với các test cases hiện hữu?
*   **[FOG-003] [Dynamic Model Discovery & Capabilities Handshake]:**
    - *Câu hỏi:* Có nên bổ sung cơ chế để `ccba-ai` tự động bắt tay (handshake) với LiteLLM Gateway `/v1/models` để fallback model khi quota bị cạn kiệt (như lỗi 429 vừa gặp)?

---

## 🚫 6. Ngoài Phạm Vi (Out of Scope)

*   **Không** can thiệp hoặc thay thế gateway LiteLLM trên Server Spark.
*   **Không** cấm các chuỗi model string trong các mock test cases hoặc benchmark assertions cố tình kiểm tra model cụ thể.
*   **Không** xây dựng hệ thống quản lý config phân tán phức tạp (như Consul/ZooKeeper); chỉ sử dụng file cấu hình cục bộ YAML/JSON và Biến môi trường hệ thống.

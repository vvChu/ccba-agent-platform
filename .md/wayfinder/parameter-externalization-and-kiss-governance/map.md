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
*   `[TICKET-003] [Chuẩn Hóa Model Routing Across Skills & Core Packages]`: Đã xóa sổ 100% hardcoded model strings (`gemini-*`, `qwen-*`, `claude-*`), raw network IPs (`100.83.192.30`), và Windows machine paths trên 74 skills và toàn bộ core packages (`ccba-ai`, `ccba-qc-core`, `mdconverter`, `ccba-legal-intel`, `ccba-pdf-prep`, `ccba-ooxml`, `ccba-harness`). Đạt **0 violations toàn sàn**, 544/544 package tests PASS, 439/439 legal tests PASS, 246/246 governance tests PASS (Commit `a404d1c6`).
*   `[TICKET-004] [Declarative Archetype Catalog & Benchmark Schema Externalization]`: Đã tách toàn bộ bảng từ khóa định tuyến của 17 domain archetypes sang tệp cấu hình khai báo `archetypes_catalog.yaml` với cơ chế In-Memory Singleton Caching (đo thực tế latency < 0.05ms $\ll$ 2ms, giải quyết dứt điểm [FOG-001]). Bảo đảm 100% backward compatibility cho tất cả caller và unit tests. 404/404 harness tests PASS, 6/6 catalog tests PASS (Commit `f859799b`).
*   `[TICKET-005] [Scorers Hyperparameter Externalization & Declarative Thresholds]`: Đã khai báo SSOT `scorers_config.yaml` cho toàn bộ 18 scorer suites (weights, is_critical, min_length, max_length). Triển khai `load_scorers_config()`, `reload_scorers_config()`, và hàm phân giải ưu tiên 3 cấp `get_scorer_params()` kết hợp Singleton Caching (latency < 0.001ms $\ll$ 0.05ms, giải quyết dứt điểm [FOG-002]). Bổ sung cơ chế ghi đè linh hoạt động theo từng test item (`BaseScorer.get_effective_weight()`, `get_effective_is_critical()`, `LengthBoundsScorer` item metadata override). Toàn bộ 411/411 harness tests PASS, 7/7 scorers_config tests PASS, linter 0 violations (Commit `ff448de6`).

---

## ⚡ 4. Rìa Biên Giới & Các Ticket Hành Động (The Frontier Tickets)

Các ticket unblocked có thể triển khai ngay:

*   **[TICKET-006] [Tuner Hyperparameters & Ratchet Thresholds Externalization]** `[Task | AFK]`:
    - *Mô tả:* Tách các tham số thuật toán ratchet/tuner trong `packages/ccba-harness/src/ccba_harness/tuner/` (ví dụ: `default_max_iterations`, `deadband_thresholds`, `patience`, `min_improvement_delta`) thành file cấu hình khai báo YAML hoặc dataclass settings có thể tinh chỉnh độc lập, giữ nguyên giao diện API hiện hành.
    - *Trạng thái:* `READY TO CLAIM` (Unblocked sau khi TICKET-005 hoàn tất)

---

## 🌫️ 5. Sương Mù Chiến Trận (Not Yet Specified)

*Nơi ghi nhận các câu hỏi kiến trúc dự kiến sẽ giải quyết nhưng cần làm rõ thêm:*

*   `[FOG-001] [RESOLVED in TICKET-004]`: Sử dụng In-Memory Singleton Caching trong `load_archetypes_catalog()`, nạp lần đầu < 3ms, các lần tiếp theo O(1) latency < 0.05ms, không gây bất kỳ overhead nào cho benchmark loop.
*   `[FOG-002] [RESOLVED in TICKET-005]`: Sử dụng mô hình Double-Pass Precedence: `override_config` (truyền vào factory) > `item.metadata["scorer_config"]` (từng bài test item) > `scorers_config.yaml` (khai báo SSOT) > fallback code defaults. Bộ nhớ đệm O(1) Singleton Cache đảm bảo độ trễ đo thực tế < 0.001ms.
*   **[FOG-003] [Dynamic Model Discovery & Capabilities Handshake]:**
    - *Câu hỏi:* Có nên bổ sung cơ chế để `ccba-ai` tự động bắt tay (handshake) với LiteLLM Gateway `/v1/models` để fallback model khi quota bị cạn kiệt (như lỗi 429 vừa gặp)?

---

## 🚫 6. Ngoài Phạm Vi (Out of Scope)

*   **Không** can thiệp hoặc thay thế gateway LiteLLM trên Server Spark.
*   **Không** cấm các chuỗi model string trong các mock test cases hoặc benchmark assertions cố tình kiểm tra model cụ thể.
*   **Không** xây dựng hệ thống quản lý config phân tán phức tạp (như Consul/ZooKeeper); chỉ sử dụng file cấu hình cục bộ YAML/JSON và Biến môi trường hệ thống.

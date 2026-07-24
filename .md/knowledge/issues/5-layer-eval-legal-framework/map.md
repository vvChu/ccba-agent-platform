# Wayfinder Master Navigation Map: Khung Phòng Vệ 5 Tầng AI Skills Evals & Thống Nhất Ngôn Ngữ Pháp Lý

**Mã vấn đề**: `issue-5-layer-eval-legal-framework`  
**Tài liệu báo cáo gốc**: [brainstorm_skills_eval_legal_guardrails.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/brainstorm_skills_eval_legal_guardrails.md)  
**Trạng thái bản đồ**: 🟢 **Đã hoàn thành 100%** — Đã triển khai và nghiệm thu 100% 5 Tầng Phòng Vệ  
**Khởi tạo**: 2026-07-24  

---

## 🎯 1. Điểm đích (Destination)
Thiết lập và vận hành hoàn chỉnh **Mô hình Giải pháp Phòng vệ 5 Tầng Khép Kín** cho CCBA Agent Platform, bao gồm:
1. **Tầng 1 (Domain-Adjacent Standard)**: 100% negative test cases trong `eval_*.json` tuân thủ quy chuẩn lân cận nghiệp vụ và Cross-Skill Evaluation.
2. **Tầng 2 (Disclaimer-Aware Assertions)**: 100% assertions sử dụng Primary Artifact Identifiers thay vì tên khái niệm chính.
3. **Tầng 3 (Automated Noise Linter)**: Tự động chặn pattern prompt rác (`quicksort`, `fibonacci`, `sick leave`...) qua `eval_runner.py --dry-run`.
4. **Tầng 4 (Superseded Legal Doc Linter & CI Gate)**: Tự động phát hiện và ép chuẩn hóa số hiệu văn bản pháp luật hiện hành (**Luật Xây dựng 2025 số 135/2025/QH15** & **NĐ 105/2025/NĐ-CP**) trong `scripts/validate_docs.py`.
5. **Tầng 5 (Production Log Mining & Auto-Tuning)**: Xây dựng CLI tool `log_eval_miner.py` bóc tách prompt thực tế từ `transcript.jsonl`, bảo mật qua `maskara-privacy` và tự động cập nhật bộ test cases thực chiến.

---

## 📝 2. Ghi chú (Notes)
- **Single Source of Truth**: File `resources/legal_registry.yaml` là nguồn duy nhất xác định trạng thái hiệu lực pháp lý (`status: current` vs `status: superseded`).
- **Single Responsibility Principle**: Giữ `legal-document-tracker` (vĩ mô) và `bigbim-vbpl-digest` (vi mô) là 2 deep modules chuyên biệt độc lập.
- **Scoped Execution**: Mọi kiểm thử mã nguồn cho runner hay miner phải chạy qua CLI wrapper `python scripts/safe_pytest.py -f <test_file>`.

---

## ✅ 3. Quyết định đã chốt (Decisions so far)

- [Tích hợp Noise Prompt Linter vào dry-run validator](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/eval-gate/scripts/eval_runner.py#L400-L425): Đã loại bỏ 100% prompt rác trong 11 skills evals. *(Ticket 1 & Ticket 3)*
- [Tích hợp Superseded Legal Doc Linter vào validate_docs.py](file:///d:/GitHubProjects/ccba-agent-platform/scripts/validate_docs.py#L510-L530): Đã cưỡng chế tham chiếu Luật Xây dựng 2025 (135/2025/QH15) & NĐ 105/2025/NĐ-CP. *(Ticket 4)*
- [Chuẩn hóa ADR 0010 và Registry](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0010-skills-integration-and-rag-boundaries.md#L24): Đã cập nhật chú thích thay thế NĐ 105/2025 cho NĐ 06/2021. *(Ticket 4)*

---

## 🚀 4. Vé Biên giới & Lộ trình Thực thi (Frontier Tickets)

### Nhóm A: Tầng 1 đến Tầng 4 (Refactoring & Linters — Đã hoàn thành)
- ✅ [Ticket 1: Rà soát & Tái thiết kế Schema Test Cases](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/5-layer-eval-legal-framework/tickets.md#ticket-5-layer-1) — 11 skills pass 100%.
- ✅ [Ticket 2: Nâng cấp Robustness & Dry-run Noise Linter](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/5-layer-eval-legal-framework/tickets.md#ticket-5-layer-2) — `eval_runner.py --dry-run` OK.
- ✅ [Ticket 3: Superseded Legal Doc Linter & Alignment](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/5-layer-eval-legal-framework/tickets.md#ticket-5-layer-3) — `validate_docs.py` check Luật 135 & NĐ 105 OK.

### Nhóm B: Tầng 5 (Production Log Mining & Auto-Tuning — Chưa thực thi)
- 🟢 [Ticket 5.1: Thiết kế Parser log & Redaction với Maskara](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/5-layer-eval-legal-framework/tickets.md#ticket-5-layer-5-1) `Task [AFK]` — Đọc `transcript.jsonl` và redact nhạy cảm.
- 🟡 [Ticket 5.2: Thuật toán Failure-Driven Auto-Tuning](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/5-layer-eval-legal-framework/tickets.md#ticket-5-layer-5-2) `Task [AFK]` — Bóc tách edge cases & router failures thành test cases mới.
- 🟡 [Ticket 5.3: Tích hợp CLI Runner `--mine-logs` & Unit Tests](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/5-layer-eval-legal-framework/tickets.md#ticket-5-layer-5-3) `Task [AFK]` — Viết `test_log_eval_miner.py` và kiểm thử qua `safe_pytest.py`.

---

## 🌫️ 5. Sương mù chiến trận / Chưa xác định rõ (Not yet specified)
- Cơ chế tự động đồng bộ telemetry log từ Server Spark (:8090) về Hub theo cron job tuần tự.

---

## ⛔ 6. Ngoài phạm vi (Out of scope)
- Gộp `legal-document-tracker` và `bigbim-vbpl-digest` thành 1 monolith skill.
- Thay đổi kiến trúc LiteLLM Proxy trên Server Spark.

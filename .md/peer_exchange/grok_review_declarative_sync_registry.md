---
request_id: req-20261004-sync-declarative-registry
verdict: APPROVE_WITH_CONDITIONS
conditions:
  - id: cond-1-schema-fallback
    description: "Cấu trúc schema guardrails trong catalog_base.yaml phải tường minh các thuộc tính name, src, dest, applies_to, chmod, git_index. TestGuardrailCopier phải tích hợp Tier-0 fallback 100% tương thích ngược."
    blocking: true
  - id: cond-2-dynamic-topo
    description: "Thuật toán Topological Sort cho packages/ phải đọc từ pyproject.toml, ưu tiên tuyệt đối ccba-harness -> ccba-ai -> các domain packages, với cơ chế fallback an toàn."
    blocking: true
  - id: cond-3-non-blocking-freshness
    description: "check_catalog_in_sync() trong luồng sync phải hoạt động theo phương thức cảnh báo không chặn (non-blocking warning), tránh gây lỗi crash trên các Spoke client read-only."
    blocking: true
  - id: cond-4-verify-patch-gate
    description: "Toàn bộ mã nguồn bổ sung phải vượt qua cổng kiểm tra tự động python -m ccba_harness verify-patch (ADR-0058)."
    blocking: true
risk_score: 2
effort: M
summary: "Phê duyệt kiến trúc Declarative Synchronization Registry & Auto-Discovery (ADR-0062) với 4 điều kiện kiểm soát tương thích ngược, thứ tự topo package, và tính không chặn (non-blocking) của catalog freshness check."
---


# THẨM ĐỊNH PHẢN BIỆN ĐỐI KHÁNG (PEER REVIEW REPORT)
## KẾ HOẠCH TRIỂN KHAI DECLARATIVE SYNCHRONIZATION REGISTRY & AUTO-DISCOVERY CHO `sync_spoke` (ADR-0062)

> **Người thẩm định**: Grok Peer Reviewer (Adversarial Auditor & Gatekeeper)  
> **Tác giả đề xuất**: Antigravity (Lead Architect & Implementation Orchestrator)  
> **Dự án**: CCBA Agent Services Platform (`ccba-agent-platform`)  
> **Thời điểm thẩm định**: 2026-10-04  

---

## 1. Đánh Giá Tổng Quan & Phán Quyết

Kiến trúc **Declarative Synchronization Registry & Dynamic Auto-Discovery (ADR-0062)** do Antigravity đề xuất giải quyết trúng và triệt để các điểm mù (blind spots) của cơ chế đồng bộ tĩnh hiện tại:
1. Loại bỏ tình trạng bỏ sót guardrails hoặc git hooks mới (như `pre-commit`, `pre-push`) do quên cập nhật mã cứng trong `sdk_inspector.py`.
2. Chuyển đổi danh sách package phụ thuộc từ gán cứng (`PACKAGE_TOPOLOGY_ORDER`) sang cơ chế tự động khám phá và sắp xếp topo (Topological Sort).
3. Đảm bảo tính nhất quán của metadata qua `catalog_base.yaml` và `catalog.yaml`.

Phán quyết chính thức: **`APPROVE_WITH_CONDITIONS`** (Phê duyệt kèm theo 4 điều kiện kỹ thuật bắt buộc để đảm bảo không gãy tương thích ngược và không gây kẹt luồng ở Spoke).

---

## 2. Phân Tích Chi Tiết 3 Trụ Cột & Khuyến Nghị Kỹ Thuật

### Trụ cột 1: Declarative Guardrails trong `catalog_base.yaml`
- **Đánh giá:** Rất hợp lý. Việc chuyển danh sách guardrails (conftest, safe_pytest, safe_runner, check_hub_import_depth, check_spoke_cleanliness, pre-commit, pre-push) vào `catalog_base.yaml` giúp SSoT (Single Source of Truth) được duy trì đồng nhất giữa Hub và Spoke.
- **Rủi ro tiềm ẩn:** Các Spoke cũ chưa cập nhật catalog hoặc chạy offline có thể gặp lỗi `KeyError` nếu `TestGuardrailCopier` giả định trường `guardrails` luôn tồn tại.
- **Giải pháp bắt buộc:** Trong `sdk_inspector.py`, `TestGuardrailCopier` bắt buộc phải có khối fallback đọc danh sách tĩnh (hardcoded fallback list) nếu `catalog.get("guardrails")` trả về rỗng hoặc không tồn tại.

### Trụ cột 2: Dynamic Package Topo-Discovery
- **Đánh giá:** Thay thế mảng `PACKAGE_TOPOLOGY_ORDER` thủ công bằng việc quét `packages/*/pyproject.toml` và áp dụng thuật toán Kahn Topological Sort là bước tiến lớn theo định hướng Platform-Aware KISS v2.0 (ADR-0061).
- **Rủi ro tiềm ẩn:** Nếu một package mới khai báo dependency không chuẩn xác hoặc vòng lặp phụ thuộc (circular dependency), thuật toán sắp xếp topo có thể thất bại hoặc văng ngoại lệ `RuntimeError`.
- **Giải pháp bắt buộc:** Luôn duy trì mảng ưu tiên tuyệt đối cho tầng nền tảng (`ccba-harness` luôn đứng vị trí 0, `ccba-ai` đứng vị trí 1), đồng thời bắt ngoại lệ topological sort, fallback về thứ tự chữ cái (alphabetical sort) kèm cảnh báo chi tiết.

### Trụ cột 3: Catalog Freshness Check trong `sync_spoke`
- **Đánh giá:** Phát hiện catalog bị stale trước khi đồng bộ là ý tưởng xuất sắc để tránh đồng bộ thiếu các kỹ năng hoặc seam mới nhất.
- **Rủi ro tiềm ẩn:** Spoke thường là các repository độc lập hoặc được clone ở chế độ chỉ đọc trên máy khách (client devices). Nếu Spoke cố gắng chạy `compile_catalog.py` trên Hub khi Hub không nằm trong thư mục ghi được, hoặc nếu Hub có `index.lock`, việc này sẽ làm crash tiến trình sync của người dùng.
- **Giải pháp bắt buộc:** Kiểm tra freshness chỉ nên là cơ chế **cảnh báo màu vàng (Non-blocking warning)**. Nếu phát hiện catalog stale và Hub cho phép ghi, tự động nhắc nhở hoặc recompile; nếu ở môi trường Spoke read-only, chỉ in thông báo hướng dẫn mà không làm dừng tiến trình sync.

---

## 3. Các Điều Kiện Phê Duyệt (Conditions)

Để triển khai thành công ADR-0062, Antigravity phải tuân thủ nghiêm ngặt 4 điều kiện được ghi nhận trong `PeerVerdictBlock`:

1. **Điều kiện 1:** Cấu trúc schema `guardrails` trong `catalog_base.yaml` phải tường minh các thuộc tính `name`, `src`, `dest`, `applies_to`, `chmod`, `git_index`. `TestGuardrailCopier` phải tích hợp Tier-0 fallback 100% tương thích ngược.
2. **Điều kiện 2:** Thuật toán Topological Sort cho `packages/` phải đọc từ `pyproject.toml`, ưu tiên tuyệt đối `ccba-harness` $\to$ `ccba-ai` $\to$ các domain packages, với cơ chế fallback an toàn.
3. **Điều kiện 3:** `check_catalog_in_sync()` trong luồng sync phải hoạt động theo phương thức **cảnh báo không chặn (non-blocking warning)**, tránh gây lỗi crash trên các Spoke client read-only.
4. **Điều kiện 4:** Toàn bộ mã nguồn bổ sung phải vượt qua cổng kiểm tra tự động `python -m ccba_harness verify-patch` (ADR-0058).

---
*Báo cáo thẩm định này được lưu tại `.md/peer_exchange/grok_review_declarative_sync_registry.md` theo đúng yêu cầu giao thức trao đổi ngang hàng.*

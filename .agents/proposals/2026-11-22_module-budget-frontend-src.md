---
proposal_id: "2026-11-22_module-budget-frontend-src"
type: "tool"
name: "module-budget-frontend-src"
status: "open"
priority: "Trung bình"
related_issue: "#865"
proposed_by_project: "IBST_UNIFIED_ERP"
proposed_by_archetype: "enterprise_governance"
proposed_date: "2026-11-22"
applies_to:
  - "Phần mềm"
  - "Tất cả Spokes"
---

# RFC Proposal: Bổ sung `frontend/src` vào `DEFAULT_PRODUCTION_ROOTS` của Module Size Budget

- **Tác giả đề xuất:** Spoke `IBST_UNIFIED_ERP` (hậu Sóng 3 + Live Browser UAT)
- **Ngày lập:** 2026-11-22
- **Liên kết Issue:** `#865`
- **Phân loại phản hồi:** Điểm rơi 5 (Deterministic Omission trên Seam Tier-0 dùng chung)

---

## 1. Bối cảnh & Vấn đề Thực tế (Context)

1. Seam Tier-0 `packages/ccba-harness/src/ccba_harness/_module_size_budget.py` đã đăng ký `.js .ts .tsx` trong `TRACKED_EXTENSIONS` và loại trừ `node_modules` trong `PRUNED_DIRS`, nhưng `DEFAULT_PRODUCTION_ROOTS` chỉ liệt kê `packages/*/src tools services backend formulas scripts` mà bỏ sót `frontend/src`.
2. Trên Spoke `IBST_UNIFIED_ERP`, toàn bộ mã nguồn Next.js nằm dưới `frontend/src/` (bao gồm tệp 818 dòng `frontend/src/app/dashboard/ai-agent/page.tsx`) nên âm thầm lọt qua `check_module_size_budget` và `scripts/spoke/check_spoke_cleanliness.py`, buộc Spoke phải giữ cổng bổ sung cục bộ trong `verify-erp`.
3. Ngoài ra, `scripts/spoke/check_spoke_cleanliness.py` lặp lại hằng số `_DEFAULT_BUDGET_ROOTS` và truyền trực tiếp biến cục bộ vào `seam.iter_production_files(...)` thay vì đọc từ `seam.DEFAULT_PRODUCTION_ROOTS` trên Spoke.

---

## 2. Đánh Giá Giá Trị × Rủi Ro × KISS

| Tiêu chí | Đánh giá | Bằng chứng |
|---|---|---|
| **Giá trị (Value)** | Cao | Kích hoạt chuẩn trần 800 LOC / ratchet cho mọi Spoke Next.js/React dùng `frontend/src/` mà không cần script cục bộ |
| **Độ phức tạp (Complexity)** | Rất thấp | Thêm 1 token `"frontend/src"` và ưu tiên `seam.DEFAULT_PRODUCTION_ROOTS` làm SSOT khi chạy trên Spoke |
| **Rủi ro (Risk)** | Thấp / Có kiểm soát | Spoke có tệp `.tsx` di sản > 800 dòng chỉ cần cập nhật `scripts/_guardrails/module_budget_baseline.json` qua `--update-budget-baseline` khi đồng bộ |
| **KISS** | Đạt 100% | Không thêm config mới, không sửa signature công khai, giữ `_module_size_budget.py` <= 120 LOC |

---

## 3. Đặc Tả Kỹ Thuật (Technical Specification)

1. **`packages/ccba-harness/src/ccba_harness/_module_size_budget.py`:** Bổ sung `"frontend/src"` vào `DEFAULT_PRODUCTION_ROOTS`.
2. **`scripts/spoke/check_spoke_cleanliness.py`:** Đồng bộ `_DEFAULT_BUDGET_ROOTS` và lấy `getattr(seam, "DEFAULT_PRODUCTION_ROOTS", roots)` làm nguồn chuẩn cho `_append_module_budget_violations` và `_run_ratchet_update` khi quét Spoke.
3. **`packages/ccba-harness/tests/test_module_size_budget_seam.py`:** Bổ sung test hồi quy xác nhận `frontend/src/*.tsx` vượt 800 LOC bị chặn, `node_modules` bị bỏ qua, ratchet baseline hoạt động đúng và `_DEFAULT_BUDGET_ROOTS == DEFAULT_PRODUCTION_ROOTS`.

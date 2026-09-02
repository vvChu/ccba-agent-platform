# Ticket T03: Thiết lập Autonomous Docs & Deadlink Maintenance Daemon

* **Loại Ticket:** `Task [AFK]`
* **Assignee:** Unassigned
* **Trạng thái:** ⛔ Cancelled (Đóng do Trùng lặp & Rủi ro Hallucination)
* **Bản đồ trực thuộc:** [Hệ Sinh Thái CLI & Tự Động Hoá Agentic](../map.md)

---

## 🎯 Lý Do Hủy Bỏ (Adversarial Review Findings)
1. **Trùng lặp công cụ:** Hệ thống đã có sẵn [`validate_docs.py`](../../../../scripts/validate_docs.py), [`update_arch_stats.py`](../../../../scripts/update_arch_stats.py), và `compile_catalog.py` tự động cập nhật metrics và kiểm tra tính toàn vẹn 100% trong quy trình CI.
2. **Rủi ro vận hành (Hallucination):** Chạy LLM daemon ngầm tự sửa docs và auto-create PR bằng `--dangerously-skip-permissions` dễ tạo PR rác, sửa sai các quy chuẩn và anchor links trong `docs/adr/`.
3. **Cơ chế HITL ưu việt hơn:** Các tài liệu kiến trúc yêu cầu Human-In-The-Loop review qua Planning Mode (Quy tắc Toàn cục #4).

---

## 🏁 Kết Luận
Không phát triển daemon ngầm. Tiếp tục duy trì cơ chế Shift-Left CI Eval Gates sẵn có.

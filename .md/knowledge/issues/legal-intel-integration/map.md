# Wayfinder Map: Triển Khai Ứng Viên #3 - Legal Intel Pipeline Refactoring

## 🎯 Điểm Đích (Destination)
Hoàn thành việc refactor monolithic script [legal_sync.py](../../../../scripts/legal_sync.py) (878 dòng) về đúng package [packages/ccba-legal-intel](../../../../packages/ccba-legal-intel) dưới dạng deep module `LegalSyncManager` trong `ccba_legal.sync`, biến `scripts/legal_sync.py` thành thin CLI adapter và đảm bảo 100% test suite `ccba-legal-intel` trôi qua thành công.

---

## 📌 Ghi Chú (Notes)
- Tuân thủ Layer 1 Constitution, Reuse-First Gate và các nguyên lý `codebase-design`.
- Giữ nguyên khả năng tương thích ngược cho mọi lệnh CLI `python scripts/legal_sync.py`.

---

## ✅ Quyết Định Đã Chốt (Decisions So Far)
- **[Làm sâu DocumentAuditor]**: Gom 6 hàm regex nông trong `doc_core.py` và validator trong `validate_skills.py` vào `DocumentAuditor` deep module (Chi tiết: [walkthrough.md](file:///C:/Users/chuvu/.gemini/antigravity/brain/e7bc59b9-6695-4373-ad6e-95f623b0ae4e/walkthrough.md)).
- **[Làm sâu EvalOrchestrator]**: Gom logic runner, timeout watchdog và singleton process lock vào `ccba_harness.orchestrator.EvalOrchestrator` (Chi tiết: [walkthrough.md](file:///C:/Users/chuvu/.gemini/antigravity/brain/e7bc59b9-6695-4373-ad6e-95f623b0ae4e/walkthrough.md)).
- **[Nguyên nhân lỗi command_status]**: Lỗi `command task-151 not found` xảy ra do hệ thống vừa bị Server Restart ngắt các background tasks ngầm.

---

## 🚩 Danh Sách Ticket Mở (Frontier / Unblocked Tickets)

1. **[Kiểm thử đơn lập suite ccba-legal-intel](ticket-1-run-tests.md)** `[Task - AFK]`
   - Chạy test suite `packages/ccba-legal-intel/tests` trực tiếp trên từng file test nhỏ để tránh timeout.
2. **[Đóng gói LegalSyncManager vào ccba_legal](ticket-2-refactor-sync.md)** `[Task - AFK]`
   - Di chuyển core class `LegalSyncManager` vào `packages/ccba-legal-intel/ccba_legal/sync.py` và re-export tại `ccba_legal.__init__`.
3. **[Chuyển scripts/legal_sync.py thành thin adapter](ticket-3-thin-adapter.md)** `[Task - AFK]`
   - Rút gọn `scripts/legal_sync.py` thành CLI adapter mỏng chỉ còn 30-40 dòng code.

---

## 🌫️ Chưa Xác Định Rõ (Not Yet Specified)
- Tích hợp nâng cao khóa TVPLSessionMutex khi đồng bộ đồng thời nhiều văn bản pháp luật lớn qua Google Drive API.

---

## 🚫 Ngoài Phạm Vi (Out of Scope)
- Sửa đổi cấu trúc file OKF Bundle JSON/Markdown hoặc thay đổi Google Drive API scopes hiện tại.

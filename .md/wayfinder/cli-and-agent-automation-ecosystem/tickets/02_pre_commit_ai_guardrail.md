# Ticket T02: Xây dựng Pre-commit AI Guardrail kiểm soát Security & AGENTS.md

* **Loại Ticket:** `Task [AFK]`
* **Assignee:** Unassigned
* **Trạng thái:** 🟢 Ready
* **Bản đồ trực thuộc:** [Hệ Sinh Thái CLI & Tự Động Hoá Agentic](../map.md)

---

## 🎯 Câu Hỏi Cần Làm Rõ / Mục Tiêu
Làm thế nào để tích hợp `agy` vào `.pre-commit-config.yaml` hoặc `.git/hooks/pre-commit` để tự động chặn các commit có chứa API key, mật khẩu, hoặc vi phạm nghiêm trọng hiến pháp `AGENTS.md` trước khi đẩy lên remote?

---

## 📋 Đề Xuất Kịch Bản Triển Khai
1. Xây dựng script Python/PowerShell `scripts/hooks/ai_pre_commit_guard.py`:
   - Trích xuất `git diff --cached`.
   - Nếu diff rỗng $\rightarrow$ bỏ qua.
   - Gửi diff vào `agy -p "Audit for hardcoded secrets, password leaks, or AGENTS.md violations..."`.
   - Nếu phát hiện lỗi $\rightarrow$ exit code 1 kèm lý do rõ ràng.
2. Tích hợp cấu hình vào pre-commit pipeline của dự án.

---

## 🏁 Tiêu Chí Hoàn Thành (Definition of Done)
- [ ] Script hook được viết gọn (< 50 dòng, tuân thủ KISS).
- [ ] Chạy thử nghiệm phát hiện commit chứa mock secret và pass đối với commit an toàn.

# Upstream Sync — Chuyển Tiếp Tham Chiếu (Pointer Guide)

> [!NOTE]
> **Phân định phạm vi kiến trúc (Architectural Scope):**
> - **Lệnh `/ccba-update-spoke`** chuyên trách đồng bộ **Downstream (Hub $\rightarrow$ Spoke)**: Đẩy kỹ năng, workflows, hiến pháp `AGENTS.md` và guardrails từ Hub về các Spoke.
> - **Lệnh `/ccba-sync-upstream`** chuyên trách trinh sát và kéo tri thức **Upstream (GitHub Thượng Nguồn $\rightarrow$ Hub)**: Giám sát các kho chứa như ClaudeKit, MattPocock theo thể chế ADR-0057 và chuyển giao porting cho `/ccba-xia`.

---

## 🎯 Chỉ Dẫn Triệu Hồi

Nếu bạn đang tìm kiếm quy trình:
1. Giám sát thay đổi mã nguồn/kỹ năng từ các kho chứa thượng nguồn.
2. Kiểm tra bản quyền giấy phép (License Audit).
3. Đánh giá tính năng mới qua AI Gateway theo thể chế ADR-0057 (Cổng 0, Cổng 1, GPI).
4. Sinh lệnh 1-Click Porting sang `/ccba-xia`.

👉 **Vui lòng truy cập kỹ năng chuẩn hóa duy nhất:**
- **Lệnh thực thi:** `/ccba-sync-upstream`
- **Đặc tả chi tiết:** [`.agents/skills/ccba-sync-upstream/SKILL.md`](../../ccba-sync-upstream/SKILL.md)
- **Danh mục nguồn theo dõi:** [`.md/knowledge/upstream_sources.yaml`](../../../../.md/knowledge/upstream_sources.yaml)

---
*Tài liệu tham chiếu thuộc CCBA Agent Services Platform.*

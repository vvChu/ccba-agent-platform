# ADR 0013: Kiến Trúc Vòng Lặp Tiến Hóa Tri Thức & Vai Trò của `ccba-build-skill`

**Trạng thái:** Accepted
**Ngày:** 2026-08-14
**Tác giả:** AI Agent (Antigravity) & Ban Kiến Trúc CCBA

---

## Bối Cảnh

Trong quá trình vận hành CCBA Agent Platform, tri thức kỹ thuật và kinh nghiệm xử lý lỗi thường xuyên được sinh ra qua các phiên làm việc (chat sessions). Nếu các tri thức này chỉ dừng lại ở nhật ký hội thoại hoặc file tạm thời, chúng sẽ bị phân mảnh và biến mất khi kết thúc phiên.

Cần một cơ chế chuẩn mực để chuyển đổi **kinh nghiệm cá nhân của một phiên làm việc** thành **năng lực dùng chung vĩnh viễn (Reusable Platform Capabilities)** cho toàn bộ mạng lưới Hub và các dự án vệ tinh (Spokes).

---

## Các Quyết Định Kiến Trúc (Đã Qua Phỏng Vấn Socrates / Grilling Loop)

### 1. Phân Tầng Vòng Lặp Tiến Hóa 3 Cấp Độ (3-Tier Evolution Loop)

Tại bước kết thúc phiên làm việc ([`/ccba-session-retrospective`](../../../.agents/workflows/ccba-session-retrospective.md)), Agent phân loại tri thức đúc kết theo 3 cấp độ:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🧬 3 CẤP ĐỘ TIẾN HÓA TRI THỨC TRONG CCBA PLATFORM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🔹 Cấp 1 (Micro - Rules & Lessons Learned):                                │
│    - Các Anti-patterns, bẫy cú pháp, sự cố OS/I/O mới phát hiện.            │
│    - Hành động: Ghi trực tiếp vào `.md/knowledge/session_learnings.md`      │
│      (7 Trụ Cột Tri Thức Cốt Lõi) để các phiên sau tự động nạp.             │
│                                                                             │
│ 🔹 Cấp 2 (Meso - Tối Ưu Hóa Kỹ Năng / Refactor):                           │
│    - Các kỹ năng hiện có bị thiếu tính năng hoặc chưa tối ưu luồng.         │
│    - Hành động: Cập nhật trực tiếp `SKILL.md` hoặc script con tương ứng     │
│      (Ví dụ: Nâng cấp `--all` Dynamic Discovery cho runner).                │
│                                                                             │
│ 🔹 Cấp 3 (Macro - Đóng Gói Kỹ Năng Mới):                                    │
│    - Một chuỗi logic/quy trình nghiệp vụ hoàn chỉnh có khả năng tái sử dụng.│
│    - Hành động: Xuất phân tích khuyến nghị và gợi ý lệnh `/ccba-build-skill`│
│      để khởi động quy trình đóng gói tự động trong phiên tiếp theo.         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Mô Hình Kích Hoạt Tách Rời (Decoupled Recommendation Pattern)

- **Quyết định:** `/ccba-session-retrospective` **KHÔNG** tự động kích hoạt ngầm quy trình tạo Skill mới trong cùng phiên.
- **Lý do:** Giữ cho việc dọn dẹp và kết thúc phiên làm việc diễn ra nhanh chóng, dứt khoát, tuân thủ nguyên tắc KISS và bảo toàn Context Budget sạch cho phiên làm việc tạo Skill tiếp theo.
- **Hành vi:** Retrospective chỉ xuất ra gợi ý lệnh cụ thể:
  `👉 Gợi ý lệnh: /ccba-build-skill <target_artifacts> --name ccba-<ten-skill>`

### 3. Nguồn Dữ Liệu Chưng Cất Xác Thực (Canonical Artifacts & Code Seams)

- **Quyết định:** Nguồn đầu vào (`input`) cho `/ccba-build-skill` **phải là các tệp mã nguồn, test cases và specs đã được kiểm chứng thực tế** trong repo (Signal-to-Noise Ratio cao nhất), thay vì đọc thô từ nhật ký `transcript.jsonl` (chứa nhiều nhiễu).

### 4. Định Vị `/ccba-build-skill` là Meta-Skill (The Skill Factory)

- `/ccba-build-skill` đóng vai trò là "Nhà máy Sản xuất Kỹ năng" tự động hóa toàn trình:
  1. Quét an toàn thông tin nhạy cảm qua `Maskara`.
  2. Nạp và chưng cất tri thức qua Google NotebookLM RAG.
  3. Sinh cấu trúc thư mục `.agents/skills/<name>/SKILL.md` chuẩn form CCBA.
  4. Đăng ký Slash Command `.agents/workflows/ccba-<name>.md`.
  5. Kiểm định chất lượng tài liệu qua `validate_docs.py`.
  6. **Phân định Hub/Spoke:**
     - Tại **Hub**: Đăng ký vào `catalog.yaml` và tạo branch/PR.
     - Tại **Spoke**: Lưu cục bộ và xuất gợi ý `/ccba-propose-to-hub`.

---

## Hệ Quả

| Khía cạnh | Trước | Sau |
|---|---|---|
| Tri thức sau mỗi phiên | Dừng lại ở log chat hoặc file tạm | Tự động phân loại 3 cấp độ và lưu trữ dài hạn |
| Tạo Skill mới | Thủ công viết tay file markdown, dễ lỗi schema | Tự động hóa qua Skill Factory `/ccba-build-skill` |
| Bàn giao ca | Lẫn lộn giữa handoff ngắn hạn và học hỏi dài hạn | Phân định rõ `/ccba-handoff` vs `/ccba-session-retrospective` |
| Đồng bộ Hub/Spoke | Rời rạc, thiếu rào chắn | Gắn liền với Vòng lặp Upstream Loop (`/ccba-propose-to-hub`) |

---

## Tài Liệu Liên Quan

- [AGENTS.md](../../../.agents/AGENTS.md) — Hiến pháp Layer 1
- [CONTEXT.md](../../../CONTEXT.md) — Từ điển Thuật ngữ & System Metaphor
- [session_retrospective/SKILL.md](../../../.agents/skills/session_retrospective/SKILL.md) — Quy trình Retrospective
- [ccba-build-skill.md](../../../.agents/workflows/ccba-build-skill.md) — Quy trình Skill Factory

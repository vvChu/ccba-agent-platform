---
name: ccba-session-retrospective
description: Tự động tổng hợp tri thức cuối phiên làm việc (Retrospective), tiến hóa
  kỹ năng trực tiếp, kích hoạt Governance Gate và dọn dẹp workspace.
disable-model-invocation: true
category: workflow
keywords:
- retrospective
- session learnings
- skill evolution
- governance gate
- tổng kết phiên
- bài học kinh nghiệm
- kiểm định quản trị
metadata:
  author: CCBA
  version: 1.2.0
bundle: _core
triggers:
- retrospective
- session learnings
- skill evolution
- governance gate
- tổng kết phiên
- bài học kinh nghiệm
- kiểm định quản trị
- ccba-session-retrospective
---
# Quy trình Tổng kết Phiên làm việc (Session Retrospective)

Kỹ năng này được kích hoạt ở cuối mỗi phiên làm việc để:
- Chắt lọc tri thức thực chiến (Evidence-Backed Learnings) và cập nhật vào Knowledge Base trung tâm.
- **Tiến hóa Kỹ năng Trực tiếp (Skill Evolution Loop):** Sửa đổi, nâng cấp và bump version các tệp `SKILL.md` liên quan ngay khi phát hiện khiếm khuyết trong phiên.
- Kích hoạt **Governance & Architecture Drift Gate** nhằm bảo đảm tài liệu, môi trường và test suite hoàn toàn đồng bộ trước khi đóng phiên.
- Dọn dẹp tệp tin rác trong workspace.

---

## Quy trình Thực hiện (Process)

### Bước 1: Thu thập & Chắt lọc Tri thức (Evidence-Backed Learnings)
- Đọc [`.md/knowledge/session_learnings.md`](../../../.md/knowledge/session_learnings.md) để nắm context 7 Trụ Cột Tri thức hiện tại và chống trùng lặp.
- Phân tích toàn bộ diễn biến phiên làm việc hiện tại để nhận diện:
  * **Vấn đề & Điểm nghẽn:** Những giả định sai lầm, hiểu lầm về SDK/Transport, hoặc các vòng lặp phản biện/sửa lỗi kéo dài.
  * **Giải pháp & Deep Seams:** Các mẫu thiết kế thành công giúp đơn giản hóa hệ thống (High Leverage & Locality).
  * **Độ Chuẩn xác Định danh (Naming Precision):** Đặt tên Core Patterns / Anti-Patterns phản ánh đúng bản chất kỹ thuật (ví dụ: *Embedded Domain Logic* thay vì *Undocumented Domain Logic*).
- **Tiêu chí hoàn thành:** Lập danh sách tri thức mới kèm dẫn chứng cụ thể từ codebase (tên class, tên module, mã lỗi) và phân loại chuẩn vào đúng Trụ Cột.

### Bước 2: Cập nhật Knowledge Base Hệ thống & Mutation Log
- Ghi nhận các Core Patterns (P) và Anti-Patterns (AP) mới vào [`.md/knowledge/session_learnings.md`](../../../.md/knowledge/session_learnings.md).
- Ghi nhận nhật ký dòng thời gian vào [`.md/knowledge/log.md`](../../../.md/knowledge/log.md) theo chuẩn `## [YYYY-MM-DD] [operation] | Title` nếu phiên làm việc có nạp/sửa đổi/ban hành tài liệu mới.
- Cập nhật mục lục danh mục [`.md/knowledge/index.md`](../../../.md/knowledge/index.md) nếu có thêm tệp tài liệu mới.
- Giữ nguyên cấu trúc phân loại theo Trụ Cột, sử dụng đúng bộ từ vựng thiết kế Deep Modules (`/ccba-codebase-design`).
- **Tiêu chí hoàn thành:** Tệp `session_learnings.md` và `log.md` được cập nhật gọn gàng, định dạng Markdown chuẩn, không tạo orphan notes.

### Bước 3: Tiến hóa Kỹ năng Trực tiếp (Direct Skill Evolution Loop)
- **Nguyên tắc "Học đi đôi với Hành":** Không dừng lại ở việc ghi nhận thụ động vào `session_learnings.md`. Nếu bài học ở Bước 2 chỉ ra một quy trình trong `SKILL.md` (như `ccba-improve-codebase-architecture`, `ccba-code-review`, `ccba-tvpl-vip-crawler`...) còn thiếu rào chắn hoặc gây sai lệch:
  * **Bổ sung bước rà soát cụ thể:** Đưa các câu hỏi tự phản biện (Pre-Proposal Self-Check) hoặc rào chắn kỹ thuật vào quy trình của Skill tương ứng.
  * **Bắt buộc có Tiêu chí hoàn thành (Exit Criteria):** Mọi bước rà soát mới thêm vào Skill phải có tiêu chí đo lường rõ ràng (ví dụ: bảng xác nhận ✅/❌ 4 dòng, tỷ lệ phục hồi, mã thoát CLI).
  * **Bump Version:** Cập nhật version trong frontmatter của tệp `SKILL.md` được sửa đổi (ví dụ: `1.1.0` $\rightarrow$ `1.2.0`).
- **Rào chắn Phạm vi (Scope Creep Guard):** Agent **KHÔNG** tự ý sửa tất cả các SKILL.md phát hiện có khiếm khuyết. Thay vào đó, Agent phải **đề xuất danh sách các Skill cần sửa** kèm lý do cụ thể (1-2 dòng mỗi Skill) rồi **chờ người dùng quyết định** Skill nào sẽ được sửa trong phiên hiện tại.
- **Tiêu chí hoàn thành:** Danh sách đề xuất được hiển thị cho người dùng; các `SKILL.md` được người dùng phê duyệt đã được cập nhật hoàn chỉnh và nhất quán.

### Bước 4: Rào chắn Kiểm định Quản trị & Đồng bộ (Governance & Drift Gate)
Trước khi kết thúc phiên, Agent **bắt buộc** phải chạy bộ 4 lệnh kiểm tra tự động:
1. **Kiểm tra tính hợp lệ của Skills:**
   ```bash
   python scripts/validate_skills.py
   ```
2. **Kiểm tra Sức khỏe LLM-Wiki Knowledge Hub:**
   ```bash
   python scripts/governance/wiki_health_linter.py
   ```
3. **Kiểm tra Tài liệu, Biến môi trường & Architecture Drift:**
   ```bash
   python scripts/validate_docs.py
   ```
   *Nếu phát hiện cảnh báo Structural Drift hoặc thiếu biến môi trường, Agent phải cập nhật ngay `README.md`, `PLATFORM.md`, và `.env.example` trước khi tiếp tục.*
4. **Kiểm tra Test Suite cục bộ:**
   ```bash
   pytest -m "not slow" tests/
   ```
- **Tiêu chí hoàn thành:** Cả 4 lệnh kiểm định đều chạy thành công (Exit code 0). Lưu ý: `validate_docs.py` có thể trả về Exit code 0 kèm cảnh báo `[WARN]` (ví dụ: code refs trong ADR chưa triển khai) — đây là chấp nhận được. Chỉ khi Exit code 1 (`[ERROR]` — hard errors như architecture drift hoặc broken links) mới phải sửa trước khi tiếp tục.

### Bước 5: Dọn dẹp Workspace & Trạng thái Git Sạch sẽ
- **Dọn dẹp tệp tạm:** Xóa bỏ các file debug nháp, log tạm, hoặc script một lần trong `.md/scratch/` không có giá trị lưu trữ lâu dài.
- **Phân phối tài liệu thô (nếu có):** Di chuyển các file tài liệu đã xử lý từ `input_documents/` sang `.md/extracted_docs/` hoặc vị trí lưu trữ phù hợp theo quy định của dự án.
- **Commit toàn bộ thay đổi:** Tạo commit với message chuẩn `docs(knowledge): session retrospective ...`.
- **Tiêu chí hoàn thành:** `git status` trả về trạng thái hoàn toàn sạch sẽ (`clean`), không còn file untracked.

### Bước 6: Xuất Báo cáo Tóm tắt (Session Retrospective Summary)
Xuất báo cáo tổng kết ra màn hình chat theo định dạng:
- **Mục tiêu & Kết quả:** Tóm tắt 2-4 dòng kết quả đã hoàn thành.
- **Tri thức & Kỹ năng Tiến hóa:** Bảng liệt kê các Patterns/Anti-patterns mới và các `SKILL.md` đã được nâng cấp.
- **Trạng thái Kiểm định:** Kết quả chạy bộ 3 Governance Gate.
- **Mã Commit:** Hash commit cuối cùng của phiên.
- **Tiêu chí hoàn thành:** Báo cáo tổng kết hiển thị đầy đủ 4 mục trên trong cửa sổ chat, kèm liên kết Markdown dẫn đến các tệp tri thức vừa cập nhật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*


**Tiêu chí hoàn thành:** Báo cáo tổng kết phiên được xuất đầy đủ ra màn hình chat.
